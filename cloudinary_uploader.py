"""
Cloudinary image uploader for hosting blog images
"""
import logging
import os
from pathlib import Path
from typing import Optional
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CloudinaryUploader:
    """Handles uploading images to Cloudinary"""
    
    def __init__(self):
        self.cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
        self.api_key = os.getenv('CLOUDINARY_API_KEY')
        self.api_secret = os.getenv('CLOUDINARY_API_SECRET')
        
        self.enabled = bool(self.cloud_name and self.api_key and self.api_secret)
        
        if not self.enabled:
            logger.warning("Cloudinary credentials not configured. Image upload will be disabled.")
        else:
            logger.info("Cloudinary uploader initialized")
    
    def upload_image(self, image_path: str, folder: str = "blog_images") -> Optional[str]:
        """Upload an image to Cloudinary and return the URL"""
        if not self.enabled:
            logger.warning("Cloudinary not configured, skipping upload")
            return None
        
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None
            
            # Prepare upload parameters
            upload_url = f"https://api.cloudinary.com/v1_1/{self.cloud_name}/image/upload"
            
            # Generate public ID from filename
            filename = Path(image_path).stem
            public_id = f"{folder}/{filename}"
            
            # Use signed uploads only (requires API key and secret)
            if not self.api_key or not self.api_secret:
                logger.error("Cloudinary API key and secret required for signed uploads")
                return None
            
            import hashlib
            import time
            timestamp = str(int(time.time()))
            
            # Build parameters for signature
            params_to_sign = {
                'public_id': public_id,
                'timestamp': timestamp,
                'folder': folder
            }
            
            # Sort parameters and create signature string
            sorted_params = sorted(params_to_sign.items())
            signature_str = '&'.join([f"{k}={v}" for k, v in sorted_params]) + self.api_secret
            signature = hashlib.sha1(signature_str.encode()).hexdigest()
            
            # Prepare the upload data
            files = {'file': open(image_path, 'rb')}
            data = {
                'api_key': self.api_key,
                'timestamp': timestamp,
                'signature': signature,
                'public_id': public_id,
                'folder': folder
            }
            
            logger.info(f"Uploading image to Cloudinary: {image_path}")
            logger.info(f"Cloud name: {self.cloud_name}, Public ID: {public_id}")
            response = requests.post(upload_url, files=files, data=data, timeout=30)
            
            # Log response status
            logger.info(f"Cloudinary response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Cloudinary upload failed with status {response.status_code}")
                logger.error(f"Response body: {response.text}")
                return None
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Cloudinary response keys: {list(result.keys())}")
            
            # Check for secure_url first, then url
            if 'secure_url' in result:
                image_url = result['secure_url']
                logger.info(f"Successfully uploaded image: {image_url}")
                return image_url
            elif 'url' in result:
                image_url = result['url']
                logger.info(f"Successfully uploaded image (non-secure): {image_url}")
                return image_url
            else:
                logger.error(f"Upload response missing both secure_url and url: {result}")
                return None
            
        except requests.exceptions.Timeout:
            logger.error("Cloudinary upload timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Cloudinary network error: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to upload image to Cloudinary: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
        finally:
            # Ensure file is closed
            if 'files' in locals() and 'file' in files:
                files['file'].close()
    
    def upload_multiple_images(self, image_paths: list, folder: str = "blog_images") -> list:
        """Upload multiple images to Cloudinary"""
        urls = []
        
        for i, image_path in enumerate(image_paths):
            logger.info(f"Uploading image {i+1}/{len(image_paths)}")
            url = self.upload_image(image_path, folder)
            if url:
                urls.append(url)
            else:
                logger.warning(f"Failed to upload image {i+1}, skipping")
        
        logger.info(f"Successfully uploaded {len(urls)}/{len(image_paths)} images")
        return urls
