import os
import urllib.request
import urllib.parse
import uuid
import logging
import imghdr
from typing import Tuple, Optional
from fastAPI.config import PROJECT_ROOT

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
        img_type = imghdr.what(download_path)
        if img_type is None:
            os.remove(download_path)
            logger.error(f"Downloaded file is not an image: {url}")
            raise ValueError(f"Downloaded file is not an image: {url}")
            
        logger.info(f"Successfully downloaded and verified image: {unique_filename}")
        return True, download_path
        
    except Exception as e:
        logger.error(f"Error downloading image from {url}")
        raise