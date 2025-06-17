import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from ..config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME

class S3Service:
    def __init__(self):
        """Initialize S3 client with credentials."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        self.bucket_name = S3_BUCKET_NAME

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