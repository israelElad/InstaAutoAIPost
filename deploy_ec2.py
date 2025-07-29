#!/usr/bin/env python3
"""
Force EC2 Deployment with Aggressive Cleanup
"""

import boto3
import os
import tarfile
import tempfile
import subprocess
import time
import requests
from pathlib import Path
import shutil

def create_deployment_package():
    """Create a deployment package with the latest code."""
    print("📦 Creating deployment package...")
    
    # Create a temporary directory for the package
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = Path(temp_dir) / "deployment"
        package_dir.mkdir()
        
        # Copy source files
        source_files = [
            "src/",
            "requirements.txt",
            "Dockerfile.ec2",
            "docker-compose.yml",
            "main.py"
        ]
        
        for item in source_files:
            src_path = Path(item)
            dst_path = package_dir / item
            
            if src_path.is_dir():
                # Copy directory
                import shutil
                shutil.copytree(src_path, dst_path)
            else:
                # Copy file
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(src_path, dst_path)
        
        # Create an empty session.json file within the package_dir
        session_file_path = package_dir / "session.json"
        session_file_path.touch()
        print(f"✅ Created empty session file: {session_file_path}")

        # Create tar.gz package
        package_file = "deployment_force.tar.gz"
        with tarfile.open(package_file, "w:gz") as tar:
            tar.add(package_dir, arcname=".")
        
        print(f"✅ Created deployment package: {package_file}")

        # Verify Dockerfile.ec2 is in the package
        dockerfile_path = package_dir / "Dockerfile.ec2"
        if not dockerfile_path.exists():
            print(f"❌ ERROR: Dockerfile.ec2 is missing from the deployment package!")
            raise FileNotFoundError("Dockerfile.ec2 missing from deployment package")

        return package_file

def get_ec2_instance():
    """Get EC2 instance details."""
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Name', 'Values': ['InstaAutoAIPostEC2']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    
    if not response['Reservations']:
        print("❌ No running EC2 instance found")
        return None
    
    instance = response['Reservations'][0]['Instances'][0]
    public_ip = instance.get('PublicIpAddress')
    instance_id = instance['InstanceId']
    
    print(f"✅ Found EC2 instance: {instance_id} ({public_ip})")
    return public_ip, instance_id

def upload_to_s3(package_file):
    """Upload deployment package to S3."""
    print("📤 Uploading to S3...")
    
    s3 = boto3.client('s3')
    bucket_name = "insta-auto-ai-post-bucket"
    s3_key = f"deployments/{package_file}"
    
    try:
        s3.upload_file(package_file, bucket_name, s3_key)
        print(f"✅ Uploaded to s3://{bucket_name}/{s3_key}")
        return True
    except Exception as e:
        print(f"❌ S3 upload failed: {e}")
        return False

def run_ssh_command(public_ip, command, description="", user="ec2-user"):
    """Run SSH command on EC2 instance with verbose output and user selection."""
    if description:
        print(f"🔧 {description}...")
    
    ssh_key = "insta-auto-ai-post-key.pem"
    if not os.path.exists(ssh_key):
        print(f"❌ SSH key not found: {ssh_key}")
        return False
    
    ssh_cmd = [
        "ssh", 
        "-i", ssh_key,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        f"{user}@{public_ip}",
        command
    ]
    print(f"[SSH] Running: {' '.join(ssh_cmd)}")
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=180)
        print(f"[SSH STDOUT]:\n{result.stdout}")
        print(f"[SSH STDERR]:\n{result.stderr}")
        if result.returncode == 0:
            print(f"   ✅ Success (exit code 0)")
            return True
        else:
            print(f"   ❌ Failed (exit code {result.returncode})")
            return False
    except subprocess.TimeoutExpired:
        print(f"   ❌ Timeout")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def force_deploy_to_ec2(public_ip, package_file):
    """Force deploy the package to EC2 with aggressive cleanup, but always preserve session.json and login_failed.lock unless explicitly resetting the session. Avoid any memory-resetting commands."""
    print(f"🚀 Force deploying to EC2 ({public_ip})...")

    DEPLOY_DIR = "/opt/insta-auto-ai-post"
    SESSION_FILE = "/app/session.json"
    SESSION_BACKUP = "/app/session_backup.json"
    LOCK_FILE = "/app/locks/login_failed.lock"

    # Step 0: Backup session.json if it exists
    backup_session_cmd = f"if [ -f {SESSION_FILE} ]; then cp {SESSION_FILE} {SESSION_BACKUP}; fi"
    run_ssh_command(public_ip, backup_session_cmd, "Backing up session.json if it exists")

    # Step 1: Stop the app container (safe, no memory reset)
    run_ssh_command(public_ip, f"cd {DEPLOY_DIR} && docker-compose stop app", "Stopping app container (safe, no memory reset)")

    # Step 2: Delete the lock file if it exists
    run_ssh_command(public_ip, f"sudo rm -f {LOCK_FILE}", "Deleting lock file if it exists")

    # Step 3: Force rebuild Docker image without cache
    if not run_ssh_command(public_ip, f"cd {DEPLOY_DIR} && docker-compose build --no-cache", "Force rebuilding Docker image without cache"):
        print("   ❌ Failed to force rebuild Docker image")
        return False

    # Step 4: Start containers (safe, no memory reset)
    if not run_ssh_command(public_ip, f"cd {DEPLOY_DIR} && docker-compose up -d", "Starting containers safely (no memory reset)"):
        print("   ❌ Failed to start containers")
        return False

    # Step 5: Download package from S3
    download_cmd = f"aws s3 cp s3://insta-auto-ai-post-bucket/deployments/{package_file} /tmp/{package_file}"
    if not run_ssh_command(public_ip, download_cmd, "Downloading deployment package"):
        return False

    # Step 6: Backup and completely clean deploy directory, but preserve session.json and login_failed.lock
    cleanup_cmd = f"cd {DEPLOY_DIR} && find . ! -name 'session.json' ! -name 'login_failed.lock' ! -name '.' -maxdepth 1 -exec sudo rm -rf {{}} +"
    if not run_ssh_command(public_ip, cleanup_cmd, "Cleaning deploy directory but preserving session.json and login_failed.lock"):
        return False

    # Step 7: Extract new package to /tmp/deployment, then copy to deploy directory
    extract_cmd = f"rm -rf /tmp/deployment && mkdir -p /tmp/deployment && cd /tmp && tar -xzf {package_file} -C /tmp/deployment && sudo cp -a /tmp/deployment/. {DEPLOY_DIR}/ && sudo chown -R ec2-user:ec2-user {DEPLOY_DIR}"
    if not run_ssh_command(public_ip, extract_cmd, "Extracting new package, copying to deploy directory, and setting ownership"):
        return False

    # Step 8: Restore session.json if it was backed up
    restore_session_cmd = f"if [ -f {SESSION_BACKUP} ]; then mv {SESSION_BACKUP} {SESSION_FILE}; fi"
    run_ssh_command(public_ip, restore_session_cmd, "Restoring session.json if it was backed up")

    # Step 9: Set permissions
    if not run_ssh_command(public_ip, f"chmod +x {DEPLOY_DIR}/main.py", "Setting file permissions"):
        return False

    # Step 10: Restart containers again to ensure new code is loaded (safe, no memory reset)
    if not run_ssh_command(public_ip, f"cd {DEPLOY_DIR} && docker-compose restart app", "Restarting app container (safe, no memory reset)"):
        return False

    # Step 11: Wait for containers to be ready
    if not run_ssh_command(public_ip, "sleep 10", "Waiting for containers to start"):
        return False

    # Step 12: Check container status
    if not run_ssh_command(public_ip, f"cd {DEPLOY_DIR} && docker-compose ps", "Checking container status"):
        return False

    print("✅ Force deployment completed!")
    return True

def verify_deployment(public_ip):
    """Verify the deployment was successful using AWS CLI and SSH commands."""
    print(f"\n🔍 Verifying deployment on {public_ip} using AWS CLI and SSH...")

    DEPLOY_DIR = "/opt/insta-auto-ai-post"

    # Verify deployment package on S3
    s3_check_cmd = "aws s3 ls s3://insta-auto-ai-post-bucket/deployments/deployment_force.tar.gz"
    if not run_ssh_command(public_ip, s3_check_cmd, "Verifying package on S3"):
        print("❌ Deployment package not found on S3.")
        return False

    # Verify Docker container status
    docker_status_cmd = f"cd {DEPLOY_DIR} && docker-compose ps --services --filter \"status=running\""
    result = subprocess.run(
        ["ssh", "-i", "insta-auto-ai-post-key.pem", "-o", "StrictHostKeyChecking=no",
         "-o", "UserKnownHostsFile=/dev/null", f"ec2-user@{public_ip}", docker_status_cmd],
        capture_output=True, text=True, timeout=60
    )

    if "app" in result.stdout.strip():
        print("✅ 'app' container is running.")
        return True
    else:
        print(f"❌ 'app' container is not running. Status:\n{result.stdout}\n{result.stderr}")
        return False

def main():
    """Main function."""
    print("🚀 Force EC2 Deployment")
    print("=" * 50)
    
    # Create deployment package
    package_file = create_deployment_package()
    
    # Get EC2 instance
    instance_info = get_ec2_instance()
    if not instance_info:
        return
    
    public_ip, instance_id = instance_info
    
    # Upload to S3
    if not upload_to_s3(package_file):
        return
    
    # Force deploy to EC2
    if not force_deploy_to_ec2(public_ip, package_file):
        return
    
    # Verify deployment
    if not verify_deployment(public_ip):
        print("❌ Deployment verification failed")
        return
    
    print(f"\n🎉 Force deployment completed!")

if __name__ == "__main__":
    main()
