import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime
import os
import logging
from ..config import S3_BUCKET_NAME

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class S3Service:
    def __init__(self):
        """Initialize S3 client using Lambda execution role credentials or local credentials."""
        try:
            region = os.getenv('AWS_REGION', 'us-east-1')
            logger.info(f"Initializing S3Service. Detected region: {region}")
            logger.info(f"S3_BUCKET_NAME: {S3_BUCKET_NAME}")
            if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
                logger.info("Running on AWS Lambda. Using execution role credentials.")
                self.s3_client = boto3.client('s3', region_name=region)
                logger.info("boto3 client initialized with Lambda execution role.")
            else:
                aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
                aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
                if aws_access_key and aws_secret_key:
                    logger.info("Running locally. Using explicit AWS credentials from environment variables.")
                    logger.info(f"AWS_ACCESS_KEY_ID: {'*' * (len(aws_access_key) - 4) + aws_access_key[-4:]}")
                    self.s3_client = boto3.client(
                        's3',
                        aws_access_key_id=aws_access_key,
                        aws_secret_access_key=aws_secret_key,
                        region_name=region
                    )
                else:
                    logger.info("Running locally. Using default AWS credentials (CLI config, IAM role, etc.).")
                    self.s3_client = boto3.client('s3', region_name=region)
            self.bucket_name = S3_BUCKET_NAME
        except NoCredentialsError:
            logger.error("AWS credentials not found. On Lambda, ensure the execution role has S3 permissions. Locally, set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
            raise Exception("AWS credentials not found. On Lambda, ensure the execution role has S3 permissions. Locally, set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
        except ClientError as e:
            logger.error(f"ClientError initializing S3 client: {str(e)}")
            if e.response['Error']['Code'] == 'InvalidAccessKeyId':
                raise Exception("Invalid AWS Access Key ID. Please check your credentials or Lambda execution role.")
            elif e.response['Error']['Code'] == 'SignatureDoesNotMatch':
                raise Exception("Invalid AWS Secret Access Key. Please check your credentials or Lambda execution role.")
            else:
                raise Exception(f"Error initializing S3 client: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error initializing S3 client: {str(e)}")
            raise

    def get_oldest_image(self):
        """
        Get the oldest image from the S3 bucket.
        
        Returns:
            tuple: (image_data, image_key) or (None, None) if no images found
        """
        try:
            # List all objects in the bucket
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' not in response:
                return None, None
            
            # Sort objects by LastModified date
            objects = sorted(response['Contents'], key=lambda x: x['LastModified'])
            
            # Get the oldest object
            oldest_object = objects[0]
            image_key = oldest_object['Key']
            
            # Download the image
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=image_key)
            image_data = response['Body'].read()
            
            return image_data, image_key
            
        except ClientError as e:
            raise Exception(f"Error accessing S3: {str(e)}")

    def delete_image(self, image_key: str):
        """
        Delete an image from the S3 bucket.
        
        Args:
            image_key (str): The key of the image to delete
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=image_key)
        except ClientError as e:
            raise Exception(f"Error deleting image from S3: {str(e)}")

    def upload_image(self, image_data: bytes, image_key: str):
        """
        Upload an image to the S3 bucket.
        
        Args:
            image_data (bytes): The image data to upload
            image_key (str): The key to use for the image
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=image_key,
                Body=image_data
            )
        except ClientError as e:
            raise Exception(f"Error uploading image to S3: {str(e)}") 