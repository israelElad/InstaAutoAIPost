# Important Commands

This document stores frequently used and important terminal commands for the project's development and deployment. For commands containing sensitive information, a redacted version is provided here, while the full unredacted version is stored securely in `docs/.sensitive_commands.mdc`.

## 1. General Commands

-   `pip install -r requirements.txt`: Installs all required Python dependencies for the project.
    ```bash
    pip install -r requirements.txt
    ```

-   `python -m pip install --upgrade pip setuptools wheel`: Upgrades pip, setuptools, and wheel to their latest versions.
    ```bash
    python -m pip install --upgrade pip setuptools wheel
    ```

-   `pytest`: Runs all unit tests to ensure code functionality and prevent regressions.
    ```bash
    pytest
    ```

-   `docker-compose up -d --build`: Builds the Docker images (if not already built) and starts the services defined in `docker-compose.yml` in detached mode (in the background).
    ```bash
    docker-compose up -d --build
    ```

-   `docker-compose down`: Stops and removes containers, networks, and volumes created by `docker-compose up`.
    ```bash
    docker-compose down
    ```

-   `docker-compose ps`: Lists containers for the current Docker Compose project.
    ```bash
    docker-compose ps
    ```

-   `docker-compose logs <service_name> [--tail=<lines>]`: Displays logs from a specific service container.
    ```bash
    docker-compose logs app --tail=20
    ```

-   `docker-compose restart <service_name>`: Restarts a specific service container.
    ```bash
    docker-compose restart app
    ```

-   `docker-compose build --no-cache`: Builds Docker images without using cache.
    ```bash
    docker-compose build --no-cache
    ```

-   `aws --version`: Verifies the installation and version of the AWS CLI.
    ```bash
    aws --version
    ```

-   `Get-AWSPowerShellVersion`: Verifies the installation and version of AWS Tools for PowerShell.
    ```powershell
    Get-AWSPowerShellVersion
    ```

-   `docker --version`: Verifies the installation and version of Docker.
    ```bash
    docker --version
    ```

-   `python --version`: Verifies the installation and version of Python.
    ```bash
    python --version
    ```

-   `git clone <repository_url>`: Clones a Git repository into a new directory.
    ```bash
    git clone https://github.com/yourusername/instagram-auto-poster.git
    ```

-   `git add .` or `git add <file>`: Stages changes for the next commit.
    ```bash
    git add .
    ```

-   `git commit -m "Commit message"`: Records staged changes to the repository.
    ```bash
    git commit -m "Fix: My commit message"
    ```

-   `git push`: Uploads local repository changes to a remote repository.
    ```bash
    git push
    ```

-   `git pull origin <branch_name>`: Fetches and integrates changes from a remote repository.
    ```bash
    git pull origin main
    ```

-   `git status`: Shows the working tree status.
    ```bash
    git status
    ```

-   `git branch -a`: Lists all local and remote branches.
    ```bash
    git branch -a
    ```

-   `git fetch --all`: Downloads objects and refs from all configured remotes.
    ```bash
    git fetch --all
    ```

-   `git log --oneline [-<num>]`: Shows commit logs in a concise format.
    ```bash
    git log --oneline -5
    ```

-   `git show --name-only <commit_hash>`: Shows changes related to a specific commit, listing only file names.
    ```bash
    git show --name-only 98e0527
    ```

-   `git show --stat <commit_hash>`: Shows changes related to a specific commit, including statistics.
    ```bash
    git show --stat 98e0527
    ```

-   `git show <commit_hash>:<file_path>`: Shows the content of a file at a specific commit.
    ```bash
    git show 98e0527:src/config.py
    ```

-   `git ls-files | grep -E "<pattern>"`: Lists files in the index, filtered by a regex pattern. (Note: `grep` might not be available on all systems, `Select-String` for PowerShell)
    ```bash
    git ls-files | grep -E "\.(env|key|secret|credential)"
    ```

-   `git merge <branch_name>`: Joins two or more development histories together.
    ```bash
    git merge origin/cursor/create-and-run-image-unit-tests-6fec
    ```

-   `git merge --abort`: Aborts the current merge operation.
    ```bash
    git merge --abort
    ```

-   `curl <url>`: Transfers data from or to a server.
    ```bash
    curl http://51.16.86.204:8000/health
    ```

-   `wget -qO- <url>`: Non-interactive network downloader (quiet output, send to stdout).
    ```bash
    wget -qO- http://localhost:8000/health
    ```

-   `ls -la <path>`: Lists directory contents in long format, including hidden files.
    ```bash
    ls -la /opt/insta-auto-ai-post/
    ```

-   `cat <file>`: Concatenates files and prints on the standard output.
    ```bash
    cat local_run_log.txt
    ```

-   `grep -n '<pattern>' <file>`: Searches for a pattern in a file, displaying line numbers.
    ```bash
    grep -n 'S3_BUCKET_NAME' /opt/insta-auto-ai-post/src/config.py
    ```

-   `rm -f <file>`: Removes files or directories forcefully.
    ```bash
    rm -f temp_*.txt
    ```

-   `chmod <permissions> <file>`: Changes file permissions.
    ```bash
    chmod 600 docker-compose.yml
    ```

-   `chown -R <user>:<group> <path>`: Changes file owner and group recursively.
    ```bash
    sudo chown -R ec2-user:ec2-user logs
    ```

-   `tail -<lines> <file>`: Outputs the last part of files.
    ```bash
    tail -20 /opt/insta-auto-ai-post/src/config.py
    ```

-   `head -<lines> <file>`: Outputs the first part of files.
    ```bash
    head -10 /opt/insta-auto-ai-post/src/services/s3_service.py
    ```

-   `echo '<text>'`: Displays a line of text.
    ```bash
    echo '---'
    ```

-   `netstat -tlnp | grep <port>`: Displays network connections, routing tables, interface statistics, etc., filtered by port.
    ```bash
    netstat -tlnp | grep 8000
    ```

-   `sleep <seconds>`: Pauses execution for a specified time.
    ```bash
    sleep 10
    ```

-   `scp -i <key_file> <source> <destination>`: Securely copies files between hosts.
    ```bash
    scp -i insta-auto-ai-post-key.pem test_secrets_manager.py ec2-user@51.16.86.204:/opt/insta-auto-ai-post/
    ```

## 2. AWS and Deployment Commands (Redacted)

Commands in this section contain sensitive information and are presented in a redacted format. The full, unredacted versions are available in `docs/.sensitive_commands.mdc`.

-   `aws configure`: Configures AWS CLI with access keys, secret keys, region, and output format.
    ```bash
    aws configure
    # Example of prompts:
    # AWS Access Key ID [****************YOUR_ACCESS_KEY_ID]: [REDACTED_AWS_ACCESS_KEY_ID]
    # AWS Secret Access Key [****************YOUR_SECRET_ACCESS_KEY]: [REDACTED_AWS_SECRET_ACCESS_KEY]
    # Default region name [us-east-1]: il-central-1
    # Default output format [json]: json
    ```

-   `aws ecr create-repository --repository-name <repo_name>`: Creates a new Amazon ECR repository.
    ```bash
    aws ecr create-repository --repository-name [REDACTED_ECR_REPO_NAME]
    ```

-   `aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account_id>.dkr.ecr.<region>.amazonaws.com`: Authenticates Docker to an Amazon ECR registry.
    ```bash
    aws ecr get-login-password --region [REDACTED_AWS_REGION] | docker login --username AWS --password-stdin [REDACTED_AWS_ACCOUNT_ID].dkr.ecr.[REDACTED_AWS_REGION].amazonaws.com
    ```

-   `docker build -t <image_name> .`: Builds a Docker image from a Dockerfile.
    ```bash
    docker build -t [REDACTED_DOCKER_IMAGE_NAME] .
    ```

-   `docker tag <image_name>:latest <account_id>.dkr.ecr.<region>.amazonaws.com/<repo_name>:latest`: Tags a Docker image for pushing to ECR.
    ```bash
    docker tag [REDACTED_DOCKER_IMAGE_NAME]:latest [REDACTED_AWS_ACCOUNT_ID].dkr.ecr.[REDACTED_AWS_REGION].amazonaws.com/[REDACTED_ECR_REPO_NAME]:latest
    ```

-   `docker push <account_id>.dkr.ecr.<region>.amazonaws.com/<repo_name>:latest`: Pushes a Docker image to an ECR repository.
    ```bash
    docker push [REDACTED_AWS_ACCOUNT_ID].dkr.ecr.[REDACTED_AWS_REGION].amazonaws.com/[REDACTED_ECR_REPO_NAME]:latest
    ```

-   `aws lambda update-function-code --function-name <function_name> --image-uri <image_uri> --region <region>`: Updates the code of an AWS Lambda function with a new Docker image.
    ```bash
    aws lambda update-function-code --function-name [REDACTED_LAMBDA_FUNCTION_NAME] --image-uri [REDACTED_ECR_IMAGE_URI] --region [REDACTED_AWS_REGION]
    ```

-   `aws s3 cp <local-file> s3://[REDACTED_S3_BUCKET_NAME]/<remote-path>`: Uploads a file to a specified S3 bucket.
    ```bash
    aws s3 cp my-image.jpg s3://[REDACTED_S3_BUCKET_NAME]/images/my-image.jpg
    ```

-   `aws s3 ls`: Lists S3 buckets or objects within a bucket.
    ```bash
    aws s3 ls
    ```

-   `aws secretsmanager get-secret-value --secret-id [REDACTED_SECRET_ID] --query SecretString --output text`: Retrieves the value of a secret from AWS Secrets Manager.
    ```bash
    aws secretsmanager get-secret-value --secret-id [REDACTED_SECRET_ID] --query SecretString --output text
    ```

-   `aws sts get-caller-identity`: Displays information about the IAM entity that is used to make the API call.
    ```bash
    aws sts get-caller-identity
    ```

-   `aws configure list`: Lists the configured AWS CLI profiles.
    ```bash
    aws configure list
    ```

-   `aws configure get <property_name>`: Retrieves a specific configuration property.
    ```bash
    aws configure get aws_access_key_id
    ```

-   `aws configure set <property_name> <value>`: Sets a specific configuration property.
    ```bash
    aws configure set aws_access_key_id ''
    ```

-   `ssh -i [REDACTED_KEY_FILE] -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ec2-user@[REDACTED_EC2_IP] '<command>'`: Executes a command on the EC2 instance via SSH.
    ```bash
    ssh -i [REDACTED_KEY_FILE] -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ec2-user@[REDACTED_EC2_IP] 'cd /opt/insta-auto-ai-post && docker-compose exec app python main.py'
    ```

-   `python3 <script_name>.py`: Executes a Python script using python3.
    ```bash
    python3 test_secrets_manager.py
    ```

## 3. How to Add New Commands

-   **General Commands**: Add directly to Section 1 of this file (`docs/commands.md`).
-   **Sensitive Commands**:
    1.  Add a redacted version to Section 2 of this file (`docs/commands.md`), using placeholders like `[REDACTED_INFO]`.
    2.  Add the full, unredacted version to `docs/.sensitive_commands.mdc`.
    3.  Ensure `docs/.sensitive_commands.mdc` is listed in `.gitignore`. 