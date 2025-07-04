# Technical Design Document: Instagram Auto Poster (EC2 Edition)

This document details the technical design and implementation aspects of the Instagram Auto Poster, focusing on the codebase structure, key services, and deployment specifics.

## 1. Project Structure

The project follows a modular structure, separating concerns into handlers, services, and utilities.

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
└── README.md
```

## 2. Core Components and Technologies

### 2.1 Backend (Python & FastAPI)
- **Language**: Python 3.8+
- **Web Framework**: FastAPI (used for exposing health and debug endpoints, and potentially for triggering the posting process via HTTP requests).
- **Dependency Management**: `requirements.txt` for Python packages.

### 2.2 Docker
- **`Dockerfile.ec2`**: Defines the Docker image for the application, including dependencies and application code.
- **`docker-compose.yml`**: Orchestrates the Docker container(s) for deployment on EC2, managing environment variables, port mappings, and service dependencies.

### 2.3 AWS Services
- **AWS EC2**: The compute instance where the Dockerized application runs.
- **AWS S3**: Used for storing images to be posted. The `s3_service.py` handles interactions with S3.
- **AWS Secrets Manager**: Securely retrieves and manages sensitive credentials. The application fetches secrets at runtime.

## 3. Key Modules and Functionality

### 3.1 `src/config.py`
- Handles configuration loading, primarily responsible for retrieving credentials from AWS Secrets Manager.

### 3.2 `src/handlers/lambda_handler.py`
- While the primary deployment is EC2, this file suggests a potential Lambda compatibility or a previous design. It would typically contain the entry point for AWS Lambda functions, processing events and orchestrating calls to services.

### 3.3 `src/services/instagram_service.py`
- Encapsulates all logic related to interacting with the Instagram API. This includes:
    - User authentication.
    - Posting images to Instagram.
    - Handling Instagram API responses and errors.

### 3.4 `src/services/s3_service.py`
- Manages all interactions with the AWS S3 bucket, including:
    - Listing objects (images).
    - Downloading the least-recent image.
    - Potentially deleting or moving images after they are posted.

### 3.5 `src/utils/image_validator.py`
- Contains logic to validate images against Instagram's posting requirements (e.g., supported file types, minimum/maximum dimensions, aspect ratio constraints).

### 3.6 `src/utils/image_processor.py`
- Handles advanced image manipulation, including:
    - Resizing images to target dimensions (e.g., 1440px).
    - Optimizing image quality (e.g., 100% JPEG quality).
    - Adding white padding to adjust aspect ratios.
    - Intelligent compression to meet file size limits (8MB).

### 3.7 `main.py`
- The main entry point of the application when run outside a serverless context (e.g., directly via Python or within the Docker container as a standalone script).
- Orchestrates the flow: fetch image from S3 -> process image -> post to Instagram.

## 4. Deployment Workflow

1. **Prerequisites**: Ensure AWS CLI, AWS Tools for PowerShell, Docker Desktop, and Python 3.8+ are installed.
2. **AWS Setup**: Create S3 bucket, set up IAM Role for EC2 with `SecretsManagerReadWrite` policy, and store credentials in AWS Secrets Manager.
3. **Cloning & Dependencies**: Clone the repository and install Python dependencies for local testing.
4. **Docker Deployment**: Build and run the Docker container on EC2 using `docker-compose up -d --build`.
5. **Execution**: The application loads credentials from AWS Secrets Manager and proceeds to process and post images.

## 5. Security Implementation

- **Secrets Management**: Credentials are dynamically loaded from AWS Secrets Manager at runtime, preventing hardcoding.
- **IAM Roles**: EC2 instances are configured with IAM roles, granting specific permissions rather than using explicit access keys within the application.
- **Input Validation**: `image_validator.py` ensures that only valid images are processed.

## 6. Performance Considerations

- **Image Processing**: Optimized algorithms in `image_processor.py` aim to maintain high quality while meeting size constraints. EC2 instance sizing can impact processing speed.
- **Docker Optimization**: Efficient Docker builds contribute to faster deployments and restarts.

## 7. Monitoring and Debugging

- **Health Endpoints**: FastAPI endpoints (`/health`, `/status`, `/debug/session`, `/debug/ip`) provide real-time status and debugging information.
- **Logging**: The application is expected to have comprehensive logging for operational insights and troubleshooting.

This document serves as a living guide and will be updated as the technical landscape of the project evolves.
