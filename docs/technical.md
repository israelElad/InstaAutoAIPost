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
    - User authentication with session persistence.
    - Posting images to Instagram with location tagging.
    - Handling Instagram API responses and errors.
    - GPS location extraction from image EXIF data.
    - Instagram location search and tagging.
    - Retry mechanisms with exponential backoff.
    - User agent management to avoid detection.

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
- **Session Monitoring**: Instagram session persistence is monitored and validated to ensure reliable authentication.

## 8. Session Management and Authentication

### 8.1 Instagram Session Persistence
- **Session File**: `session.json` stores Instagram authentication tokens and device settings
- **Session Validation**: Automatic validation of session validity before API calls
- **Fallback Authentication**: Graceful fallback to username/password login if session is invalid

### 8.2 Session Debugging Findings
- **EC2 Environment**: ✅ Working session persistence (1364 bytes session file)
- **Local Environment**: ❌ Session file issues due to missing user agent configuration
- **Root Cause**: CSRF token errors prevented session save when user agent was not set
- **Fix Applied**: User agent now properly configured in `InstagramService.__init__()`

### 8.3 Session File Structure
```json
{
    "uuids": { "phone_id", "uuid", "client_session_id", ... },
    "authorization_data": { "ds_user_id", "sessionid" },
    "device_settings": { "app_version", "android_version", ... },
    "user_agent": "Instagram 269.0.0.18.75 Android...",
    "last_login": 1751623901.9124508
}
```

## Instagram Login Lockout Mechanism

To prevent repeated failed login attempts and potential account/IP blacklisting, the application now implements a lockout mechanism:

- On any Instagram login failure (including session validation failure), a lock file named `login_failed.lock` is created in the project root (or as specified by the `INSTAGRAM_LOCK_FILE` environment variable).
- On startup, if this lock file exists, the app will exit immediately and will not attempt any further Instagram API calls.
- This mechanism ensures that after a failed login, the app does not enter a restart loop or risk further lockouts from Instagram.
- To clear the lockout and allow the app to attempt login again, manually delete the `login_failed.lock` file after resolving the underlying issue (e.g., updating credentials or resolving security alerts).

## 9. Operational Considerations and Failure Handling

This section describes the application's behavior in various operational scenarios.

### 9.1 Successful Post

If the application successfully processes an image and posts it to Instagram:
- A success message is logged.
- The application exits with code 0.
- The Docker container stops.
- The `login_failed.lock` file is *not* created.

### 9.2 Expected Graceful Failure

If there's an expected failure during image processing or validation (e.g., `ImageValidationError`):
- An error message is logged.
- A JSON response with a 400 status code and an error message is returned.
- The application exits with code 0.
- The Docker container stops.
- The `login_failed.lock` file is *not* created.

### 9.3 Unexpected Failure

If there's an unexpected exception during the application's execution:
- An error message is logged.
- A JSON response with a 500 status code and an error message is returned.
- The application exits with code 0.
- The Docker container stops.
- The `login_failed.lock` file is *not* created.

### 9.4 EC2 Instance Shutdown/Crash

If the EC2 instance is shut down or crashes:
- The Docker container is also shut down.
- Upon EC2 instance restart, the Docker container will *not* automatically restart due to `restart: on-failure:0` in `docker-compose.yml`.
- The application will only run again if the `deploy_ec2.py` script is executed.

### 9.5 Instagram Login/Session Failures

If the application fails to log in to Instagram or validate the session:
- The application will attempt to log in up to 3 times with exponential backoff.
- If all login attempts fail, the `login_failed.lock` file is created.
- The application exits with code 0.
- The Docker container stops.
- The application will *not* automatically retry posting. Manual intervention is required to resolve the login issue and delete the `login_failed.lock` file.

### 9.6 Preventing Bot-Like Behavior

The application is designed to minimize the risk of being flagged as a bot by Instagram:
- The application processes and attempts to post only *one* image per execution.
- The `login_failed.lock` mechanism prevents repeated login attempts.
- The `InstagramService` implements a retry mechanism with exponential backoff for API calls.
- A proxy server (if configured) provides a consistent IP address.

However, it's still possible to trigger rate limits or account blocks if the credentials are invalid, the session is consistently invalid, or the application exhibits other suspicious behavior. Regular monitoring of the application logs and adherence to Instagram's API usage guidelines are recommended.

This document serves as a living guide and will be updated as the technical landscape of the project evolves.

## 10. November 2025 Findings

- Recent redeployments proved that the infrastructure, Secrets Manager integration, and session handling all work correctly.
- Instagram now returns **BadPassword/blacklist** responses even with valid credentials, explicitly instructing us to change IP or verify by email.
- Repeated attempts quickly lead to rate-limit responses (missing encryption headers), forcing long cooldowns.
- Conclusion: Continuing to use Instagrapi + EC2 is no longer viable without substantial anti-detection work. Future users/contributors should review other OSS implementations, Android automation (e.g., Insomniac), or restricted official APIs.
