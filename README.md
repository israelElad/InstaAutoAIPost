# Instagram Auto Poster

An automated solution for posting images to Instagram from an S3 bucket. This project uses AWS Lambda and EventBridge to schedule posts at specific times throughout the day.

## Features

- Automatically posts the least-recent image from an S3 bucket to Instagram
- Validates images against Instagram requirements
- Handles failures and exceptions gracefully
- Uses AWS Lambda and EventBridge for scheduling
- Implements secure credential management
- Includes comprehensive unit tests
- Uses free tier services only

## Architecture

The solution consists of the following components:

1. **S3 Bucket**: Stores images to be posted
2. **AWS Lambda**: Runs the posting script on schedule
3. **EventBridge**: Schedules the Lambda function
4. **Docker Container**: Packages the Lambda function
5. **Instagram API**: Handles posting to Instagram

## Setup

1. Create an S3 bucket for storing images
2. Set up AWS Lambda with the provided Docker container
3. Configure EventBridge rules for scheduling
4. Set up environment variables for credentials

### Environment Variables

Create a `.env` file with the following variables:

```
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket_name
```

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
│   │   └── error_handler.py
│   └── config.py
├── tests/
│   ├── test_instagram_service.py
│   ├── test_s3_service.py
│   └── test_image_validator.py
├── Dockerfile
├── requirements.txt
└── README.md
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

3. Build Docker container:
   ```bash
   docker build -t instagram-auto-poster .
   ```

## Security Considerations

- All credentials are stored as environment variables
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
- **AWS Account** (for Lambda, S3, ECR, EventBridge)
- **Instagram Account** (username & password)
- **Docker** installed locally
- **Python 3.9+** (for local testing)

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
- Enter a unique bucket name (e.g., `my-instagram-images`).
- Choose your preferred AWS region.
- Leave other settings as default, or adjust as needed.
- Click "Create bucket".
- Click on your new bucket, then "Upload" to add a few images that meet Instagram's requirements (see validator section below).
- Complete the upload.

**Tip:** Images must meet Instagram's requirements (see validator in the code or below for details on size, aspect ratio, and file type).

### 5. Set Up AWS IAM User for Programmatic Access
- Log in to your AWS Console and navigate to the IAM service.
- Click "Users" in the left sidebar, then "Create user".
- Enter a username (e.g., `instagram-auto-poster`).
- **Select "Command Line Interface (CLI)"** for programmatic access (this generates the Access Key ID and Secret Access Key).
- Click "Next: Permissions".
- Choose "Attach policies directly".
- Search for and select "AmazonS3FullAccess" (or create a custom policy for more restricted access).
- Click "Next: Tags" (optional), then "Next: Review".
- Click "Create user".
- **Important:** Copy the Access Key ID and Secret Access Key immediately. You won't be able to see the secret again.
- Add these to your `.env` file:
  ```
  AWS_ACCESS_KEY_ID=your_access_key_id
  AWS_SECRET_ACCESS_KEY=your_secret_access_key
  ```

### 6. Create a `.env` File
- In your project root, create a file named `.env`.
- Add the following, replacing with your actual values:
  ```
  INSTAGRAM_USERNAME=your_instagram_username
  INSTAGRAM_PASSWORD=your_instagram_password
  AWS_ACCESS_KEY_ID=your_access_key_id
  AWS_SECRET_ACCESS_KEY=your_secret_access_key
  S3_BUCKET_NAME=your_s3_bucket_name
  ```

### 7. Build and Push Docker Image to AWS ECR

**Prerequisites Check:**
- Ensure Docker Desktop is running
- Verify AWS CLI or AWS Tools for PowerShell are installed
- Confirm you have ECR permissions in your AWS account

**Authentication Methods:**

**Option A: Using AWS CLI (Recommended)**
```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.<your-region>.amazonaws.com

# Build the Docker image
docker build -t <your-repo-name> .

# Tag the image for ECR
docker tag <your-repo-name>:latest <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/<your-repo-name>:latest

# Push to ECR
docker push <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/<your-repo-name>:latest
```

**Option B: Using AWS Tools for PowerShell**
```powershell
# Authenticate Docker to ECR
(Get-ECRLoginCommand -Region <your-region>).Password | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.<your-region>.amazonaws.com

# Build the Docker image
docker build -t <your-repo-name> .

# Tag the image for ECR
docker tag <your-repo-name>:latest <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/<your-repo-name>:latest

# Push to ECR
docker push <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/<your-repo-name>:latest
```

**Note:** Replace `<your-account-id>`, `<your-region>`, and `<your-repo-name>` with your actual AWS account ID, AWS region, and ECR repository name.

### 8. Create Lambda Function from Container Image
- Go to AWS Lambda Console.
- Click "Create function".
- Choose "Container image".
- Enter a function name (e.g., `InstagramAutoPoster`).
- For Container image URI, use the ECR image URI you pushed.
- Set environment variables from your `.env` file (in the Lambda console, add each variable under the Configuration > Environment variables section).
- Set the handler to: `src.handlers.lambda_handler.lambda_handler`
- Set the timeout to at least 1 minute (increase if you expect large images or slow network).

### 9. Set Up EventBridge (CloudWatch Events) for Scheduling
- Go to AWS EventBridge Console.
- Create a new rule.
- Choose "Schedule" and set your desired cron or rate expression (e.g., `cron(0 12 * * ? *)` for every day at noon UTC).
- Add the Lambda function as the target.

### 10. Test the Setup
- Upload a test image to your S3 bucket (if not already done).
- Trigger the Lambda manually from the AWS Lambda console (Actions > Invoke) or wait for the scheduled EventBridge rule.
- Check Instagram for the new post.
- Check S3 to confirm the image was deleted.

**Troubleshooting:**
- Check Lambda logs in AWS CloudWatch for errors.
- Ensure your IAM user has the correct permissions.
- Make sure your Instagram credentials are correct and not locked by Instagram.
- Ensure your images meet Instagram's requirements (see validator section below).
- If you encounter issues, review the error messages and consult AWS and Instagram documentation as needed.

### 11. Troubleshooting
- Check Lambda logs in AWS CloudWatch for errors
- Ensure your IAM user has the correct permissions
- Make sure your Instagram credentials are correct and not locked by Instagram
- Ensure your images meet Instagram's requirements (see validator)

### 12. Local Testing (Optional)
You can run the handler locally for testing:
```bash
python -m src.handlers.lambda_handler
```

## Local End-to-End Testing

You can test the full workflow locally before deploying to AWS Lambda. This is useful for debugging and verifying your setup.

### Steps for Local E2E Testing

1. **Ensure your `.env` file is present in the project root** with all required variables:
   ```
   INSTAGRAM_USERNAME=your_instagram_username
   INSTAGRAM_PASSWORD=your_instagram_password
   AWS_ACCESS_KEY_ID=your_access_key_id
   AWS_SECRET_ACCESS_KEY=your_secret_access_key
   S3_BUCKET_NAME=your_s3_bucket_name
   ```
2. **Upload at least one valid image to your S3 bucket** (see validator requirements).

3. **Run the Lambda handler locally:**
   ```bash
   python -m src.handlers.lambda_handler
   ```
   - This will attempt to fetch the oldest image from your S3 bucket, validate it, post it to Instagram, and delete it from S3.
   - Output and errors will be printed to the console.

4. **Check Instagram and S3** to confirm the post and deletion.

### Troubleshooting Local Runs
- If you see errors about missing environment variables, double-check your `.env` file and variable names.
- If you get authentication errors, verify your AWS and Instagram credentials.
- If the script cannot find images, ensure your S3 bucket name is correct and the bucket contains images.
- If you get image validation errors, check the image size, aspect ratio, and file type.
- For more details, add print statements or increase logging verbosity in the code.

---

## Manual Steps Required
- AWS account setup (S3, Lambda, ECR, EventBridge)
- Instagram account setup
- IAM user creation and permissions
- Docker installation and ECR authentication
- Environment variable configuration
- Manual upload of images to S3

---

## FAQ
- **Q:** Why do I need to use my own Instagram credentials?
  **A:** Instagram does not provide a public API for posting; automation requires your credentials. Use a dedicated account for safety.
- **Q:** Can I use this for business/brand accounts?
  **A:** Yes, but be aware of Instagram's automation policies.
- **Q:** Is this free?
  **A:** All AWS services used have a free tier. Stay within limits to avoid charges.
