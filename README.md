# Instagram Auto Poster (EC2 Edition)

An automated solution for posting images to Instagram from an S3 bucket. This project now runs securely and reliably on AWS EC2 with Docker Compose and AWS Secrets Manager.

## Features

- Automatically posts the least-recent image from an S3 bucket to Instagram
- Validates images against Instagram requirements
- **Advanced image processing with quality optimization**
- **Automatic image resizing to meet Instagram's 1440px resolution limit**
- **Maximum quality preservation (100%) within Instagram's 8MB file size limit**
- Handles failures and exceptions gracefully
- Uses AWS EC2 and Docker Compose for persistent, static-IP deployment
- Implements secure credential management with AWS Secrets Manager
- Includes comprehensive unit tests
- Uses free tier services only

## Recent Improvements (Latest Update)

### 🎯 **Image Processing Enhancements**
- **Smart Image Resizing**: Automatically resizes images to Instagram's maximum resolution (1440px) while preserving aspect ratio
- **Quality Optimization**: Uses maximum JPEG quality (100%) since we have plenty of room within Instagram's 8MB limit
- **Aspect Ratio Handling**: Adds white padding for images with extreme aspect ratios to meet Instagram's requirements
- **File Size Management**: Intelligent compression when needed to stay under 8MB limit

### 🚀 **Performance Optimizations**
- **Increased EC2 Resources**: You can now scale your EC2 instance for better image processing performance
- **Efficient Docker Builds**: Optimized Docker image builds for EC2
- **Robust Error Handling**: Enhanced error handling for image processing and Instagram posting

### ✅ **Production Ready**
- **Successfully Deployed**: The service is now live and processing images from S3 to Instagram on EC2
- **Fixed Instagram Integration**: Resolved file path issues for reliable Instagram posting
- **Comprehensive Testing**: Thorough local and AWS testing with real images
- **Security Best Practices**: All credentials properly managed via AWS Secrets Manager

### 📊 **Example Results**
- **Original Image**: 5312x2988 pixels, 5.47MB
- **Processed Image**: 1440x810 pixels, 0.30MB (100% quality)
- **Result**: Perfect Instagram compliance with maximum quality preservation

## 🎉 **Deployment Status - SUCCESS!**

### **✅ Production Deployment Complete**
The Instagram Auto Poster is now **successfully deployed and running** on AWS EC2! 

**Latest Test Results:**
- **EC2 Instance**: Running and healthy
- **Docker Compose**: Manages the app container
- **Last Execution**: ✅ Successfully processed and posted image to Instagram
- **Response**: `{"statusCode": 200, "body": "{\"message\": \"Successfully processed image and posted to Instagram\"}"}`

### **🔧 Final Optimizations Applied**
- **EC2 Instance**: You can scale resources as needed
- **Image Quality**: Maximum quality (100%) within Instagram's 8MB limit
- **Error Handling**: Robust temporary file management for Instagram posting
- **Security**: All credentials properly managed via AWS Secrets Manager

### **🚀 Ready for Production Use**
The system is now fully operational and can be:
- **Manually triggered** via Docker Compose
- **Scheduled** via your own cron or automation (see EC2 docs)
- **Monitored** via logs and health endpoints
- **Scaled** as needed for higher posting frequency

**Next Steps**: Set up your own scheduling (e.g., cron on EC2) for automated daily posts!

## Architecture

The solution consists of the following components:

1. **S3 Bucket**: Stores images to be posted
2. **AWS EC2**: Runs the posting script on schedule (via Docker Compose)
3. **Docker Container**: Packages and runs the application
4. **Instagram API**: Handles posting to Instagram
5. **AWS Secrets Manager**: Securely stores credentials

## Setup

1. Create an S3 bucket for storing images
2. Set up AWS EC2 with Docker Compose and the provided Dockerfile
3. Set up AWS Secrets Manager for credentials
4. (Optional) Set up your own scheduling (e.g., cron) on EC2

### Environment Variables and Secrets

- **Production:** All credentials are loaded from AWS Secrets Manager (not from environment variables or .env files)
- **Local Testing:** You can still use a `.env` file for local runs (see below)

## Project Structure

```
.
├── src/
│   ├── handlers/
│   │   └── lambda_handler.py
│   ├── services/
│   │   ├── instagram_service.py
│   │   └── s3_service.py
│   ├── utils/
│   │   ├── image_validator.py
│   │   └── image_processor.py
│   └── config.py
├── main.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile.ec2
├── logs/
└── README_EC2.md
```

## Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Build and run Docker container (for EC2):
   ```bash
   docker-compose up -d --build
   ```

## Security Considerations

- All credentials are stored in AWS Secrets Manager (never in code or .env in production)
- No hardcoded secrets in the code
- Secure handling of Instagram credentials
- Proper error handling and logging
- Input validation and sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Prerequisites

**Tip:** You may need to restart your shell after each installation or you'll get "The term 'aws' is not recognized as the name of a cmdlet, function, script file, or operable program.". 
Another option is to update path variables manually, e.g.: $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Before starting the setup, ensure you have the following tools installed:

### 1. AWS CLI
- **Installation:** Download and install from [AWS CLI official website](https://aws.amazon.com/cli/)
- **Verification:** Run `aws --version` in your terminal
- **Configuration:** Run `aws configure` to set up your AWS credentials

### 2. AWS Tools for PowerShell
- **Installation:** Install from PowerShell Gallery:
  ```powershell
  Install-Module -Name AWS.Tools.ECR -Force -Scope CurrentUser
  Install-Module -Name AWS.Tools.Common -Force -Scope CurrentUser
  ```
- **Verification:** Run `Get-AWSPowerShellVersion` in PowerShell

### 3. Docker Desktop
- **Installation:** Download and install from [Docker official website](https://www.docker.com/products/docker-desktop/)
- **Verification:** Run `docker --version` in your terminal
- **Start Docker:** Ensure Docker Desktop is running before proceeding

### 4. Python 3.8+
- **Verification:** Run `python --version` in your terminal

## End-to-End Setup Guide

Follow these steps to set up and run the Instagram Auto Poster end-to-end:

### 1. Prerequisites
- **AWS Account** (for EC2, S3, Secrets Manager)
- **Instagram Account** (username & password)
- **Docker** installed on your EC2 instance
- **Python 3.9+** (for local testing)
- **IAM Role** with `SecretsManagerReadWrite` attached to your EC2 instance
- **AWS Region**: `il-central-1` (Israel)

### 2. Clone the Repository
```bash
git clone https://github.com/yourusername/instagram-auto-poster.git
cd instagram-auto-poster
```

### 3. Install Python Dependencies (for local testing)
```bash
pip install -r requirements.txt
```

### 4. Create and Configure AWS S3 Bucket
- Log in to your AWS Console and navigate to the S3 service.
- Click "Create bucket".
- Enter a unique bucket name (e.g., `my-instagram-images-il`).
- Choose your preferred AWS region (`il-central-1` recommended for static IP).
- Leave other settings as default, or adjust as needed.
- Click "Create bucket".
- Click on your new bucket, then "Upload" to add a few images that meet Instagram's requirements (see validator section below).
- Complete the upload.

**Tip:** Images must meet Instagram's requirements (see validator in the code or below for details on size, aspect ratio, and file type).

### 5. Set Up AWS IAM Role for EC2
- Go to the IAM service in AWS Console.
- Click "Roles" > "Create role".
- Choose "EC2" as the trusted entity.
- Attach the `SecretsManagerReadWrite` policy (or a custom policy with at least `secretsmanager:GetSecretValue` and S3 access).
- Name the role (e.g., `instaAutoAIPostEC2Role`).
- Attach this role to your EC2 instance.

### 6. Store Credentials in AWS Secrets Manager
- Go to AWS Secrets Manager in the AWS Console.
- Click "Store a new secret".
- Choose "Other type of secret".
- Add the following key-value pairs:
  - `INSTAGRAM_USERNAME`
  - `INSTAGRAM_PASSWORD`
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `S3_BUCKET_NAME`
- Name the secret: `insta-auto-ai-post-secrets`
- Set the region to `il-central-1`
- Save the secret.

### 7. Build and Deploy the App to EC2
- Ensure Docker and Docker Compose are installed on your EC2 instance.
- In your project directory, run:
  ```bash
  docker-compose up -d --build
  ```
- The app will automatically:
  - Load credentials from AWS Secrets Manager
  - Start the FastAPI web server on port 8000
  - Attempt to post the oldest image from S3 to Instagram

### 8. Health and Debug Endpoints
- Check service health:
  - `http://<your-ec2-ip>:8000/health`
  - `http://<your-ec2-ip>:8000/status`
  - `http://<your-ec2-ip>:8000/debug/session`
  - `http://<your-ec2-ip>:8000/debug/ip`
  - `http://<your-ec2-ip>:8000/debug/device`
  - `http://<your-ec2-ip>:8000/debug/rate_limit`

### 9. Updating the Service
- To deploy new code, update your repo and run:
  ```bash
  docker-compose up -d --build
  ```
- Logs are available in the `logs/` directory and via `docker-compose logs app`

### 10. Local End-to-End Testing (Optional)
You can test the full workflow locally before deploying to AWS EC2. This is useful for debugging and verifying your setup.

#### Steps for Local E2E Testing

1. **Ensure your `.env` file is present in the project root** with all required variables:
   ```
   INSTAGRAM_USERNAME=your_instagram_username
   INSTAGRAM_PASSWORD=your_instagram_password
   AWS_ACCESS_KEY_ID=your_access_key_id
   AWS_SECRET_ACCESS_KEY=your_secret_access_key
   S3_BUCKET_NAME=your_s3_bucket_name
   ```
2. **Upload at least one valid image to your S3 bucket** (see validator requirements).

3. **Test the handler locally:**
   ```bash
   python -c "from src.handlers.lambda_handler import lambda_handler; import json; result = lambda_handler({}, None); print('Lambda handler test result:'); print(json.dumps(result, indent=2))"
   ```
   - This will attempt to fetch the oldest image from your S3 bucket, validate it, post it to Instagram, and delete it from S3.
   - Output and errors will be printed to the console.

4. **Check Instagram and S3** to confirm the post and deletion.

#### Troubleshooting Local Runs
- If you see errors about missing environment variables, double-check your `.env` file and variable names.
- If you get authentication errors, verify your AWS and Instagram credentials.
- If the script cannot find images, ensure your S3 bucket name is correct and the bucket contains images.
- If you get image validation errors, check the image size, aspect ratio, and file type.
- For more details, add print statements or increase logging verbosity in the code.

---

## Manual Steps Required
- AWS account setup (S3, EC2, Secrets Manager)
- Instagram account setup
- IAM user/role creation and permissions
- Docker installation and authentication
- Secrets Manager configuration
- Manual upload of images to S3

---
## FAQ
- **Q:** Why do I need to use my own Instagram credentials?
  **A:** Instagram does not provide a public API for posting; automation requires your credentials. Use a dedicated account for safety.
- **Q:** Can I use this for business/brand accounts?
  **A:** Yes, but be aware of Instagram's automation policies.
- **Q:** Is this free?
  **A:** All AWS services used have a free tier. Stay within limits to avoid charges.

## Instagram API Best Practices & Anti-Ban Measures

To reduce the risk of Instagram bans or rate limits, this project now follows best practices from the [instagrapi usage guide](https://subzeroid.github.io/instagrapi/usage-guide/best-practices.html):

- **Consistent IP Address:** Instagram is less likely to flag activity if requests come from a consistent IP. Since dedicated proxies are not free, we moved all AWS resources to the Israel region (`il-central-1`) to ensure requests originate from the same country as your account. This helps reduce suspicious login attempts and ban risk.
- **Delays Between Requests:** The code is designed to mimic real user behavior by adding random delays between requests. This helps avoid triggering Instagram's anti-bot systems.
- **Session Reuse:** Instead of logging in with your username and password on every run, the project uses session storage and reuse. This mimics how a real device stays logged in, further reducing suspicious activity.

For more details and advanced anti-ban strategies, see the [instagrapi best practices guide](https://subzeroid.github.io/instagrapi/usage-guide/best-practices.html).

---

## Transition from Lambda to EC2: Why and How

This project was originally built for AWS Lambda, but was migrated to EC2 for the following reasons:
- **Static IP**: Instagram is less likely to flag activity from a consistent IP. Lambda uses dynamic IPs, which can trigger bans.
- **Persistent Sessions**: EC2 allows for persistent session storage, reducing login frequency and ban risk. Lambda is stateless and cannot persist sessions easily.
- **Secrets Management**: AWS Secrets Manager and IAM roles provide secure, automated credential management on EC2.
- **Reliability**: EC2 with Docker Compose is more reliable for long-running, stateful services.

### Previous Lambda-Based Configuration (for Reference)
- **ECR (Elastic Container Registry):** Docker images were built locally and pushed to an ECR repository (`insta-auto-ai-post-repo`).
- **Lambda Container Image:** AWS Lambda pulled the image from ECR and ran it as a serverless function.
- **EventBridge Scheduling:** AWS EventBridge was used to trigger the Lambda function on a schedule (e.g., daily posting).
- **Environment Variables:** Credentials and configuration were managed via Lambda environment variables (except for AWS keys, which were provided by the Lambda execution role).

### Current EC2 + Docker Compose Configuration
- **No ECR required:** Docker images are built and run directly on the EC2 instance using Docker Compose. ECR is not referenced or needed for this workflow.
- **Persistent Service:** The app runs as a long-lived service with a static IP and persistent session storage.
- **Secrets Management:** All credentials are loaded from AWS Secrets Manager using the EC2 instance's IAM role.
- **Scheduling:** If needed, posting can be scheduled using cron or other automation on the EC2 instance.

> **Migration Tip:** The transition process involved many experimental scripts and chat-driven iterations. Most of these were not pushed to the repo, as Cursor and AI-driven workflows tend to generate a lot of temporary files and scripts. **If you need to transition or refactor, it is strongly recommended to start fresh rather than trying to clean up or refactor everything.** In the current state of Cursor and AI models, starting from a clean slate is faster and less error-prone.

--- 