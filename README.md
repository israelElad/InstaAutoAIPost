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
- Go to the AWS S3 console
- Click "Create bucket"
- Name your bucket (e.g., `my-instagram-images`)
- Leave all other settings as default or adjust as needed
- Upload a few test images to the bucket

### 5. Set Up AWS IAM User for Programmatic Access
- Go to AWS IAM console
- Create a new user with programmatic access
- Attach the following policies:
  - `AmazonS3FullAccess` (or restrict to your bucket)
  - `AWSLambda_FullAccess`
  - `AmazonEventBridgeFullAccess`
  - `AmazonEC2ContainerRegistryFullAccess`
- Save the Access Key ID and Secret Access Key

### 6. Create a `.env` File
Create a `.env` file in the project root with:
```
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
S3_BUCKET_NAME=your_s3_bucket_name
```

### 7. Build and Push Docker Image to AWS ECR
- Go to AWS ECR console
- Create a new repository (e.g., `instagram-auto-poster`)
- Authenticate Docker to your ECR:
  ```bash
  aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.<your-region>.amazonaws.com
  ```
- Build and tag the Docker image:
  ```bash
  docker build -t instagram-auto-poster .
  docker tag instagram-auto-poster:latest <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/instagram-auto-poster:latest
  ```
- Push the image:
  ```bash
  docker push <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/instagram-auto-poster:latest
  ```

### 8. Create Lambda Function from Container Image
- Go to AWS Lambda console
- Click "Create function"
- Choose "Container image"
- Enter a function name (e.g., `InstagramAutoPoster`)
- For Container image URI, use the ECR image URI you pushed
- Set environment variables from your `.env` file
- Set the handler to: `src.handlers.lambda_handler.lambda_handler`
- Set the timeout to at least 1 minute

### 9. Set Up EventBridge (CloudWatch Events) for Scheduling
- Go to AWS EventBridge console
- Create a new rule
- Choose "Schedule" and set your desired cron or rate expression (e.g., `cron(0 12 * * ? *)` for every day at noon UTC)
- Add the Lambda function as the target

### 10. Test the Setup
- Upload a test image to your S3 bucket
- Trigger the Lambda manually or wait for the schedule
- Check Instagram for the new post
- Check S3 to confirm the image was deleted

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
