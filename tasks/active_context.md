# Active Context

This document captures the current active context and immediate focus areas for the Instagram Auto Poster project.

## Current Objective:

- **Project Paused**: Work is halted because Instagram now blocks the EC2 IP and flags Instagrapi logins despite valid credentials.

## Key Information:

- **Project Name**: Instagram Auto Poster (EC2 Edition)
- **Core Functionality**: Automated posting of images from S3 to Instagram with AI-generated captions.
- **Deployment Environment**: AWS EC2 with Docker Compose.
- **Credential Management**: AWS Secrets Manager.
- **Image Processing**: Advanced resizing, quality optimization, and validation.
- **AI Integration**: Gemini API for Hebrew caption generation with location-aware content.

## Recent Deployment and Troubleshooting Findings:

- Infrastructure, credentials, and session handling were all verified through multiple redeployments.
- Instagram now alternates between rate-limit responses (missing encryption headers) and explicit **BadPassword/IP blacklist** errors, even with correct credentials.
- Latest response instructs us to change IP or confirm via email, proving the current EC2 IP/device fingerprint is blocked.

## Immediate Next Steps (if project is revived):

1. Review current anti-ban techniques used by actively maintained OSS projects.
2. Consider Android UI automation (e.g., Insomniac) or the official Graph API despite its limits.
3. If sticking with Instagrapi, plan for rotating IPs, device fingerprints, and more human-like automation.

## Open Questions/Assumptions:

- Would Android automation provide a sustainable path forward?
- Is there appetite/budget for managed rotating proxies?
- Should the project pivot to another platform with an official API?

This document will be continuously updated to reflect changes in project focus, immediate tasks, and relevant contextual information. 

- Instagram login lockout: On any login failure, a `login_failed.lock` file is created. If this file exists, the app exits immediately on startup, preventing further Instagram API calls. To clear the lockout, delete the file after resolving the issue. 