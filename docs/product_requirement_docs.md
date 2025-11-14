# Product Requirements Document: Instagram Auto Poster (EC2 Edition)

This document outlines the product requirements for the Instagram Auto Poster, an automated solution designed to post images from an S3 bucket to Instagram, deployed securely and efficiently on AWS EC2.

## 1. Introduction

The Instagram Auto Poster aims to automate the process of publishing visual content to Instagram, ensuring images meet platform requirements and are posted reliably from an AWS S3 source. The system prioritizes automation, image quality, and secure credential management.

## 2. Key Features and Functionality

### 2.1 Core Posting Mechanism
- The system shall automatically select and post the least-recent image from a designated S3 bucket.
- Upon successful posting, the system should handle the image appropriately (e.g., mark as posted, move to an archive, or delete from the active bucket).

### 2.2 Image Processing & Optimization
- The system shall validate images against Instagram's requirements (e.g., file type, dimensions, aspect ratio).
- The system shall automatically resize images to Instagram's maximum resolution (1440px on the longest side) while preserving the aspect ratio.
- The system shall optimize image quality, aiming for 100% JPEG quality within Instagram's 8MB file size limit.
- For images with extreme aspect ratios, the system shall add white padding to meet Instagram's display requirements.
- The system shall intelligently compress images only when necessary to stay under the 8MB file size limit.

### 2.3 Error Handling & Robustness
- The system shall gracefully handle failures and exceptions during the image processing and Instagram posting phases.
- The system shall include robust temporary file management to prevent issues during posting.

### 2.4 Deployment & Scalability
- The application shall be deployable on AWS EC2 using Docker Compose.
- The deployment shall allow for persistent operation and utilize a static IP address.
- The EC2 instance resources (CPU, memory) shall be configurable to allow for scaling based on image processing performance needs.
- Docker image builds shall be optimized for efficient deployment on EC2.

### 2.5 Security & Credential Management
- All sensitive credentials (Instagram username/password, AWS access keys, S3 bucket name) shall be stored and retrieved securely from AWS Secrets Manager.
- The system shall not contain any hardcoded secrets.
- The EC2 instance shall utilize an IAM role (e.g., `SecretsManagerReadWrite`) to access AWS Secrets Manager, adhering to the principle of least privilege.

### 2.6 Monitoring & Debugging
- The application shall expose health endpoints (e.g., `/health`, `/status`) to monitor service health.
- Debug endpoints (e.g., `/debug/session`, `/debug/ip`) shall be available for troubleshooting and diagnostics.
- Comprehensive logging shall be implemented to track system operations and aid in debugging.

## 3. Operational Requirements

- The system should operate using AWS free tier services where applicable.
- The system shall be capable of being manually triggered via Docker Compose.
- The system shall support integration with external scheduling mechanisms (e.g., cron jobs on EC2) for automated posting.

## 4. Performance Expectations

- Image processing and posting should be efficient, with minimal latency.
- The system should maintain maximum image quality within Instagram's file size constraints.

## 5. Security Requirements

- Strict adherence to AWS security best practices for credential management and access control.
- Input validation and sanitization for all external inputs (e.g., image metadata).

## 6. Future Considerations

- Potential for user interface for manual image upload and scheduling.
- Integration with other social media platforms.
- Advanced analytics and reporting on posting activities.

## 7. Project Status & Recommendations (Nov 2025)

- **Status**: The project has been paused/discontinued after repeated Instagram anti-bot countermeasures blocked the EC2 IP and API-based login attempts.
- **Finding**: Instagram’s unofficial API endpoints now aggressively fingerprint IP, device, and behaviour. Continuing would require constant reverse engineering, which defeats the goal of a low-maintenance autoposter.
- **Recommendation**:
  - If someone wants to revive this effort, first perform a deep review of current anti-ban techniques used in actively maintained open-source projects.
  - Consider switching to Android automation frameworks such as **Insomniac** (UI-level automation) which are harder to detect, or move to the official but limited **Instagram Graph API**.
  - Alternatively, pivot to a platform with an official posting API to avoid the cat-and-mouse game entirely.

This document will be regularly updated to reflect new requirements or changes in existing functionalities.
