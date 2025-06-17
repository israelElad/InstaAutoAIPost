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