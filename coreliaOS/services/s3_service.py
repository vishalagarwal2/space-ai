"""
AWS S3 service for handling file uploads
"""
import os
import uuid
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)

class S3Service:
    """Service class for handling S3 operations"""
    
    def __init__(self):
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.region = settings.AWS_S3_REGION_NAME
        self.s3_client = None
        
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=self.region,
                    config=boto3.session.Config(
                        signature_version='s3v4',
                        s3={
                            'addressing_style': 'virtual'
                        }
                    )
                )
                logger.info(f"S3 client initialized successfully for region {self.region}")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {str(e)}")
                self.s3_client = None
    
    def is_available(self):
        """Check if S3 service is available"""
        return self.s3_client is not None
    
    def upload_file(self, file, file_path=None, content_type=None):
        """
        Upload a file to S3 bucket
        
        Args:
            file: Django UploadedFile object or file-like object
            file_path: Optional custom file path, if not provided, generates unique path
            content_type: Optional content type, if not provided, tries to detect from file
            
        Returns:
            str: S3 URL of uploaded file or None if upload failed
        """
        if not self.is_available():
            logger.error("S3 service not available - missing credentials")
            return None
        
        try:
            if not file_path:
                file_extension = self._get_file_extension(file.name)
                file_path = f"images/uploads/{uuid.uuid4()}{file_extension}"
            
            if not content_type:
                content_type = self._get_content_type(file.name)
            
            file.seek(0)
            file_content = file.read()
            
            upload_params = {
                'Bucket': self.bucket_name,
                'Key': file_path,
                'Body': file_content,
            }
            
            if content_type:
                upload_params['ContentType'] = content_type
            
            if settings.AWS_DEFAULT_ACL and settings.AWS_DEFAULT_ACL.lower() not in ['none', '']:
                upload_params['ACL'] = settings.AWS_DEFAULT_ACL
            
            response = self.s3_client.put_object(**upload_params)
            
            file_url = self.generate_signed_url(file_path)
            
            return file_url
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"AWS ClientError during upload - Code: {error_code}, Message: {error_message}")
            return None
        except NoCredentialsError:
            logger.error("AWS credentials not found or invalid")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {str(e)}", exc_info=True)
            return None
    
    def upload_business_logo(self, file, user_id):
        """
        Upload business logo with standardized naming convention
        
        Args:
            file: Django UploadedFile object
            user_id: User ID for organizing files
            
        Returns:
            str: S3 URL of uploaded logo or None if upload failed
        """
        if not self.is_available():
            logger.error("Service not available - missing AWS credentials")
            return None
        
        if not self._is_valid_image(file.name):
            logger.error(f"Invalid image file type: {file.name}")
            return None
        
        file_extension = self._get_file_extension(file.name)
        file_path = f"images/logos/user-{user_id}-{uuid.uuid4()}{file_extension}"
        
        result = self.upload_file(file, file_path, self._get_content_type(file.name))
        
        return result
    
    def generate_signed_url(self, file_path, expiration=604800):  # 1 week = 60*60*24*7 (AWS maximum)
        """
        Generate a signed URL for secure access to S3 objects
        
        Args:
            file_path: S3 object key/path
            expiration: URL expiration time in seconds (default: 1 week - AWS maximum)
            
        Returns:
            str: Signed URL for accessing the file
        """
        if not self.is_available():
            return None
            
        try:
            signed_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name, 
                    'Key': file_path
                },
                ExpiresIn=expiration,
                HttpMethod='GET'
            )
            
            return signed_url
        except Exception as e:
            logger.error(f"Error generating signed URL: {str(e)}")
            return None
    
    def upload_post_image(self, file, user_id, post_id=None):
        """
        Upload post image with standardized naming convention
        
        Args:
            file: Django UploadedFile object
            user_id: User ID for organizing files
            post_id: Optional post ID for organizing files
            
        Returns:
            str: S3 URL of uploaded image or None if upload failed
        """
        if not self.is_available():
            return None
        
        if not self._is_valid_image(file.name):
            logger.error(f"Invalid image file type: {file.name}")
            return None
        
        file_extension = self._get_file_extension(file.name)
        if post_id:
            file_path = f"images/posts/user-{user_id}/post-{post_id}-{uuid.uuid4()}{file_extension}"
        else:
            file_path = f"images/posts/user-{user_id}-{uuid.uuid4()}{file_extension}"
        
        return self.upload_file(file, file_path, self._get_content_type(file.name))
    
    def upload_post_video(self, file, user_id, post_id=None):
        """
        Upload post video with standardized naming convention
        
        Args:
            file: Django UploadedFile object
            user_id: User ID for organizing files
            post_id: Optional post ID for organizing files
            
        Returns:
            str: S3 URL of uploaded video or None if upload failed
        """
        if not self.is_available():
            return None
        
        if not self._is_valid_video(file.name):
            logger.error(f"Invalid video file type: {file.name}")
            return None
        
        file_extension = self._get_file_extension(file.name)
        if post_id:
            file_path = f"videos/posts/user-{user_id}/post-{post_id}-{uuid.uuid4()}{file_extension}"
        else:
            file_path = f"videos/posts/user-{user_id}-{uuid.uuid4()}{file_extension}"
        
        return self.upload_file(file, file_path, self._get_content_type(file.name))
    
    def delete_file(self, file_url):
        """
        Delete a file from S3 using its URL
        
        Args:
            file_url: Full S3 URL of the file to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            file_key = self._extract_key_from_url(file_url)
            if not file_key:
                logger.error(f"Could not extract file key from URL: {file_url}")
                return False
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            logger.info(f"File deleted successfully from S3: {file_key}")
            return True
            
        except ClientError as e:
            logger.error(f"AWS ClientError during deletion: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during S3 deletion: {str(e)}")
            return False
    
    def _get_file_extension(self, filename):
        """Extract file extension from filename"""
        if '.' in filename:
            return '.' + filename.split('.')[-1].lower()
        return ''
    
    def _get_content_type(self, filename):
        """Get content type based on file extension"""
        extension = self._get_file_extension(filename).lower()
        content_types = {
            # Image types
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
            # Video types
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
        }
        return content_types.get(extension, 'application/octet-stream')
    
    def _is_valid_image(self, filename):
        """Check if file is a valid image type"""
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
        extension = self._get_file_extension(filename).lower()
        return extension in valid_extensions
    
    def _is_valid_video(self, filename):
        """Check if file is a valid video type"""
        valid_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
        extension = self._get_file_extension(filename).lower()
        return extension in valid_extensions
    
    def _extract_key_from_url(self, file_url):
        """Extract S3 key from full URL (handles both regular and signed URLs)"""
        try:
            if "?" in file_url:
                base_url = file_url.split("?")[0]
            else:
                base_url = file_url
            
            if f"{self.bucket_name}.s3.{self.region}.amazonaws.com/" in base_url:
                key = base_url.split(f"{self.bucket_name}.s3.{self.region}.amazonaws.com/")[-1]
            elif f"{self.bucket_name}.s3.amazonaws.com/" in base_url:
                key = base_url.split(f"{self.bucket_name}.s3.amazonaws.com/")[-1]
            elif f"s3.{self.region}.amazonaws.com/{self.bucket_name}/" in base_url:
                key = base_url.split(f"s3.{self.region}.amazonaws.com/{self.bucket_name}/")[-1]
            elif f"s3.amazonaws.com/{self.bucket_name}/" in base_url:
                key = base_url.split(f"s3.amazonaws.com/{self.bucket_name}/")[-1]
            elif f"s3://{self.bucket_name}/" in base_url:
                key = base_url.split(f"s3://{self.bucket_name}/")[-1]
            else:
                logger.error(f"Unrecognized S3 URL format: {file_url}")
                return None
                
            return key
        except Exception as e:
            logger.error(f"Error extracting key from URL: {str(e)}")
            return None


s3_service = S3Service()
