import os
import urllib.request
import urllib.parse
import logging
import imghdr
import boto3
from PIL import Image
from fastAPI.config import PROJECT_ROOT, AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY
from typing import Tuple, Optional

# S3 클라이언트 생성
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

def is_s3_image_url(url: str) -> bool:
    # Check if URL is from S3
    if not ('s3.amazonaws.com' in url or 's3.ap-northeast-2.amazonaws.com' in url):
        return False
        
    # Check if URL ends with common image extensions
    img_extensions = ['.jpg', '.jpeg', '.png']
    return any(url.lower().endswith(ext) for ext in img_extensions)

def download_image_from_s3(memberId: str, font_name:str, url: str, logger: logging.Logger) -> Tuple[bool, Optional[str]]:
    if not is_s3_image_url(url):
        logger.error(f"URL is not a valid S3 image URL: {url}")
        raise ValueError(f"URL is not a valid S3 image URL: {url}")
        
    # Create 'written' directory if it doesn't exist
    written_dir = os.path.join(PROJECT_ROOT, "written")
    os.makedirs(written_dir, exist_ok=True)
    
    try:
        # Generate a unique filename preserving the extension
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path
        file_extension = os.path.splitext(path)[1]
        if not file_extension:
            file_extension = '.jpg'  # Default extension if none is provided
            
        unique_filename = f"{memberId}-{font_name}{file_extension}"
        download_path = os.path.join(written_dir, unique_filename)
        
        # Download the file
        logger.info(f"Downloading image from {url} to {download_path}")
        urllib.request.urlretrieve(url, download_path)
        
        # Verify that the downloaded file is actually an image
        try:
            with Image.open(download_path) as img:
                img.verify()
        except Exception as e:
            os.remove(download_path)
            logger.error(f"Downloaded file is not a valid image: {url}, reason: {e}")
            raise ValueError(f"Downloaded file is not a valid image: {url}")
        # img_type = imghdr.what(download_path)
        # if img_type is None:
        #     os.remove(download_path)
        #     logger.error(f"Downloaded file is not an image: {url}")
        #     raise ValueError(f"Downloaded file is not an image: {url}")
            
        logger.info(f"Successfully downloaded and verified image: {unique_filename}")
        return True, download_path
        
    except Exception as e:
        logger.error(f"Error downloading image from {url}")
        raise

"""
Args:
    file_path: 업로드할 로컬 파일 경로
    target_name: S3에 저장될 파일 이름
    bucket_name: 업로드할 S3 버킷 이름
    logger: 로깅을 위한 logger 객체

Returns:
    Tuple[bool, str]: 성공 여부와 S3 URL
"""
def upload_file_to_s3(file_path: str, target_name: str, bucket_name: str, logger: logging.Logger = None) -> Tuple[bool, str]:
    if logger is None:
        logger = logging.getLogger(__name__)
    
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        raise FileNotFoundError(f"File does not exist: {file_path}")
    
    try:
        # 파일 업로드
        logger.info(f"Uploading file {file_path} to s3://{bucket_name}/{target_name}")
        s3_client.upload_file(file_path, bucket_name, target_name)
        
        # S3 URL 생성
        s3_url = f"https://{bucket_name}.s3.{AWS_REGION}.amazonaws.com/{target_name}"
        logger.info(f"File uploaded successfully: {s3_url}")
        
        return True, s3_url
        
    except Exception as e:
        logger.error(f"Error uploading file to S3: {str(e)}")
        raise