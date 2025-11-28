import os
import json
from typing import List, Optional, Union, BinaryIO
from google.cloud import storage
from google.cloud.exceptions import NotFound, Forbidden
from pathlib import Path


class GCSHandler:
    """
    A comprehensive Google Cloud Storage handler class for file operations.
    """
    
    def __init__(self, bucket_name: str, credentials_path: Optional[str] = None, 
                 credentials_dict: Optional[dict] = None):
        """
        Initialize the GCS handler.
        
        Args:
            bucket_name (str): Name of the GCS bucket
            credentials_path (str, optional): Path to service account JSON file
            credentials_dict (dict, optional): Service account credentials as dictionary
        """
        import logging
        self.logger = logging.getLogger(__name__)
        self.bucket_name = bucket_name

        
        
        # Initialize client and bucket
        try:
            if credentials_dict:
                self.logger.info("Initializing GCS client with credentials dictionary.")
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_info(credentials_dict)
                self.client = storage.Client(credentials=credentials)
            elif credentials_path:
                self.logger.info(f"Initializing GCS client with credentials file: {credentials_path}")
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.client = storage.Client(credentials=credentials)
            else:
                self.logger.info("Initializing GCS client with default credentials.")
                self.client = storage.Client()
            
            self.bucket = self.client.bucket(bucket_name)
            self.logger.info(f"GCSHandler initialized for bucket: {bucket_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize GCS client: {str(e)}")
            raise Exception(f"Failed to initialize GCS client: {str(e)}")
    
    def create_bucket(self, location: str = "US") -> bool:
        """
        Create a new bucket if it doesn't exist.
        
        Args:
            location (str): Bucket location (default: US)
            
        Returns:
            bool: True if bucket was created or already exists
        """
        try:
            bucket = self.client.bucket(self.bucket_name)
            bucket.location = location
            bucket = self.client.create_bucket(bucket)
            print(f"Bucket {self.bucket_name} created in {location}")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Bucket {self.bucket_name} already exists")
                return True
            print(f"Error creating bucket: {str(e)}")
            return False
    
    def upload_file(self, local_file_path: str, gcs_file_path: str, 
                   content_type: Optional[str] = None) -> bool:
        """
        Upload a file to GCS.
        
        Args:
            local_file_path (str): Path to local file
            gcs_file_path (str): Destination path in GCS bucket
            content_type (str, optional): MIME type of the file
            
        Returns:
            bool: True if upload successful
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            
            # Set content type if provided
            if content_type:
                blob.content_type = content_type
            
            with open(local_file_path, 'rb') as file:
                blob.upload_from_file(file)
            
            print(f"File {local_file_path} uploaded to {gcs_file_path}")
            return True
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            return False
    
    def upload_from_string(self, content: Union[str, bytes], gcs_file_path: str,
                          content_type: str = "text/plain") -> bool:
        """
        Upload content from string or bytes to GCS.
        
        Args:
            content (Union[str, bytes]): Content to upload
            gcs_file_path (str): Destination path in GCS bucket
            content_type (str): MIME type of the content
            
        Returns:
            bool: True if upload successful
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            blob.content_type = content_type
            blob.upload_from_string(content, content_type=content_type)
            
            print(f"Content uploaded to {gcs_file_path}")
            return True
        except Exception as e:
            print(f"Error uploading content: {str(e)}")
            return False
    
    def create_folder_and_upload(self, local_file_path: str, folder_path: str, 
                                filename: Optional[str] = None) -> bool:
        """
        Create a folder (prefix) and upload file to it.
        
        Args:
            local_file_path (str): Path to local file
            folder_path (str): Folder path in GCS (will be created as prefix)
            filename (str, optional): Custom filename, uses original if None
            
        Returns:
            bool: True if upload successful
        """
        try:
            if filename is None:
                filename = os.path.basename(local_file_path)
            
            # Ensure folder path ends with /
            if not folder_path.endswith('/'):
                folder_path += '/'
            
            gcs_file_path = f"{folder_path}{filename}"
            return self.upload_file(local_file_path, gcs_file_path)
        except Exception as e:
            print(f"Error creating folder and uploading: {str(e)}")
            return False
    
    def upload_to_nested_folder(self, local_file_path: str, *folder_path_parts: str,
                               filename: Optional[str] = None) -> bool:
        """
        Upload file to nested folder structure.
        
        Args:
            local_file_path (str): Path to local file
            *folder_path_parts (str): Variable number of folder path components
            filename (str, optional): Custom filename, uses original if None
            
        Returns:
            bool: True if upload successful
        """
        try:
            if filename is None:
                filename = os.path.basename(local_file_path)
            
            # Create nested path
            nested_path = '/'.join(folder_path_parts)
            if nested_path and not nested_path.endswith('/'):
                nested_path += '/'
            
            gcs_file_path = f"{nested_path}{filename}"
            return self.upload_file(local_file_path, gcs_file_path)
        except Exception as e:
            print(f"Error uploading to nested folder: {str(e)}")
            return False
    
    def download_file(self, gcs_file_path: str, local_file_path: str) -> bool:
        """
        Download a file from GCS.
        
        Args:
            gcs_file_path (str): Path to file in GCS bucket
            local_file_path (str): Local destination path
            
        Returns:
            bool: True if download successful
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            
            # Create local directory if it doesn't exist
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            
            blob.download_to_filename(local_file_path)
            print(f"File downloaded from {gcs_file_path} to {local_file_path}")
            return True
        except NotFound:
            print(f"File {gcs_file_path} not found in bucket")
            return False
        except Exception as e:
            print(f"Error downloading file: {str(e)}")
            return False
    
    def get_file_content(self, gcs_file_path: str) -> Optional[bytes]:
        """
        Get file content as bytes.
        
        Args:
            gcs_file_path (str): Path to file in GCS bucket
            
        Returns:
            bytes: File content or None if error
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            return blob.download_as_bytes()
        except NotFound:
            print(f"File {gcs_file_path} not found in bucket")
            return None
        except Exception as e:
            print(f"Error getting file content: {str(e)}")
            return None
    
    def yield_blobs(self, prefix: str = ""):
        """
        Yield blob objects for all files under the given prefix in the bucket.
        """
        blobs = self.bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            yield blob

    def get_file_as_string(self, gcs_file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """
        Get file content as string.
        
        Args:
            gcs_file_path (str): Path to file in GCS bucket
            encoding (str): Text encoding (default: utf-8)
            
        Returns:
            str: File content or None if error
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            return blob.download_as_text(encoding=encoding)
        except NotFound:
            print(f"File {gcs_file_path} not found in bucket")
            return None
        except Exception as e:
            print(f"Error getting file as string: {str(e)}")
            return None
    
    def delete_file(self, gcs_file_path: str) -> bool:
        """
        Delete a file from GCS.
        
        Args:
            gcs_file_path (str): Path to file in GCS bucket
            
        Returns:
            bool: True if deletion successful
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            blob.delete()
            print(f"File {gcs_file_path} deleted successfully")
            return True
        except NotFound:
            print(f"File {gcs_file_path} not found in bucket")
            return False
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
    
    def delete_folder(self, folder_path: str) -> bool:
        """
        Delete all files in a folder (prefix).
        
        Args:
            folder_path (str): Folder path to delete
            
        Returns:
            bool: True if deletion successful
        """
        try:
            if not folder_path.endswith('/'):
                folder_path += '/'
            
            blobs = self.bucket.list_blobs(prefix=folder_path)
            deleted_count = 0
            
            for blob in blobs:
                blob.delete()
                deleted_count += 1
            
            print(f"Deleted {deleted_count} files from folder {folder_path}")
            return True
        except Exception as e:
            print(f"Error deleting folder: {str(e)}")
            return False
    
    def list_files(self, prefix: str = "", max_results: Optional[int] = None) -> List[str]:
        """
        List files in bucket with optional prefix filter.
        
        Args:
            prefix (str): Prefix to filter files
            max_results (int, optional): Maximum number of results
            
        Returns:
            List[str]: List of file paths
        """
        try:
            self.logger.info(f"Listing files with prefix '{prefix}' and max_results={max_results}")
            blobs = self.bucket.list_blobs(prefix=prefix, max_results=max_results)
            file_list = [blob.name for blob in blobs]
            self.logger.info(f"Found {len(file_list)} files with prefix '{prefix}'")
            return file_list
        except Exception as e:
            self.logger.error(f"Error listing files: {str(e)}")
            return []
    def file_exists(self, gcs_file_path: str) -> bool:
        """
        Check if a file exists in GCS.
        
        Args:
            gcs_file_path (str): Path to file in GCS bucket
            
        Returns:
            bool: True if file exists
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            return blob.exists()
        except Exception as e:
            print(f"Error checking file existence: {str(e)}")
            return False
    
    def get_file_info(self, gcs_file_path: str) -> Optional[dict]:
        """
        Get file metadata information.
        
        Args:
            gcs_file_path (str): Path to file in GCS bucket
            
        Returns:
            dict: File metadata or None if error
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            blob.reload()
            
            return {
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'created': blob.time_created,
                'updated': blob.updated,
                'etag': blob.etag,
                'md5_hash': blob.md5_hash,
                'public_url': blob.public_url
            }
        except NotFound:
            print(f"File {gcs_file_path} not found in bucket")
            return None
        except Exception as e:
            print(f"Error getting file info: {str(e)}")
            return None
    
    def copy_file(self, source_path: str, destination_path: str) -> bool:
        """
        Copy a file within the same bucket.
        
        Args:
            source_path (str): Source file path
            destination_path (str): Destination file path
            
        Returns:
            bool: True if copy successful
        """
        try:
            source_blob = self.bucket.blob(source_path)
            destination_blob = self.bucket.blob(destination_path)
            
            destination_blob.upload_from_string(
                source_blob.download_as_bytes(),
                content_type=source_blob.content_type
            )
            
            print(f"File copied from {source_path} to {destination_path}")
            return True
        except Exception as e:
            print(f"Error copying file: {str(e)}")
            return False
    
    def move_file(self, source_path: str, destination_path: str) -> bool:
        """
        Move a file within the same bucket.
        
        Args:
            source_path (str): Source file path
            destination_path (str): Destination file path
            
        Returns:
            bool: True if move successful
        """
        try:
            if self.copy_file(source_path, destination_path):
                return self.delete_file(source_path)
            return False
        except Exception as e:
            print(f"Error moving file: {str(e)}")
            return False


# # Example usage
# if __name__ == "__main__":
#     # Initialize the GCS handler
#     gcs = GCSHandler(
#         bucket_name="your-bucket-name",
#         credentials_path="path/to/your/service-account.json"  # Optional
#     )
    
#     # Create bucket (if needed)
#     gcs.create_bucket()
    
#     # Upload a file
#     gcs.upload_file("local/path/to/file.txt", "remote/path/file.txt")
    
#     # Create folder and upload
#     gcs.create_folder_and_upload("local/file.txt", "documents")
    
#     # Upload to nested folders
#     gcs.upload_to_nested_folder("local/file.txt", "projects", "2024", "data")
    
#     # Download a file
#     gcs.download_file("remote/path/file.txt", "local/downloaded/file.txt")
    
#     # Get file content
#     content = gcs.get_file_content("remote/path/file.txt")
    
#     # List files
#     files = gcs.list_files(prefix="documents/")
    
#     # Check if file exists
#     exists = gcs.file_exists("remote/path/file.txt")
    
#     # Get file info
#     info = gcs.get_file_info("remote/path/file.txt")
    
#     # Delete file
#     gcs.delete_file("remote/path/file.txt")