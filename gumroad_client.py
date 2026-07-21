"""
Gumroad API client for creating and managing digital products
"""
import logging
import os
import json
import requests
from typing import Dict, Optional, List
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GumroadClient:
    """Client for interacting with Gumroad API"""
    
    def __init__(self):
        self.access_token = os.getenv('GUMROAD_ACCESS_TOKEN')
        self.base_url = "https://api.gumroad.com/v2"
        self.enabled = bool(self.access_token)
        
        if not self.enabled:
            logger.warning("Gumroad access token not configured. Product creation will be disabled.")
        else:
            logger.info("Gumroad client initialized")
    
    def create_product(self, name: str, description: str, price: float, 
                      file_path: Optional[str] = None, 
                      tags: Optional[List[str]] = None) -> Optional[Dict]:
        """Create a new product on Gumroad with retry logic"""
        if not self.enabled:
            logger.warning("Gumroad not configured, skipping product creation")
            return None
        
        # Validate and sanitize inputs
        if len(name) > 255:
            logger.warning(f"Product name too long ({len(name)} chars), truncating to 255")
            name = name[:255]
        
        # Ensure minimum price of 0.99 (Gumroad requirement)
        if price < 0.99:
            logger.warning(f"Price too low (${price}), setting to minimum $0.99")
            price = 0.99
        
        # Validate and sanitize tags (max 20 characters per tag)
        if tags:
            validated_tags = []
            for tag in tags:
                if len(tag) > 20:
                    logger.warning(f"Tag too long ({len(tag)} chars), truncating to 20: {tag}")
                    tag = tag[:20]
                validated_tags.append(tag)
            tags = validated_tags
        
        # Log final price being sent
        logger.info(f"Final price after validation: ${price} (type: {type(price).__name__})")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/products"
                headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
                
                data = {
                    'name': name,
                    'description': description,
                    'price': int(price * 100),  # Gumroad expects price in cents (e.g., 1499 for $14.99)
                    'published': True,
                    'require_shipping': False
                }
                
                # Log the exact data being sent for debugging
                logger.info(f"Sending data to Gumroad: {json.dumps(data, indent=2)}")
                logger.info(f"Original price: ${price}")
                logger.info(f"Price in cents: {int(price * 100)}")
                
                if tags:
                    data['tags'] = tags
                
                logger.info(f"Creating Gumroad product: {name} (price: ${price}, attempt {attempt + 1}/{max_retries})")
                response = requests.post(url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                
                if 'success' in result and result['success']:
                    product_id = result.get('product', {}).get('id')
                    logger.info(f"Successfully created Gumroad product: {product_id}")
                    return result
                else:
                    logger.error(f"Failed to create product: {result}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying product creation...")
                        continue
                    return None
                
            except requests.exceptions.Timeout as e:
                logger.error(f"Timeout creating Gumroad product: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying after timeout...")
                    continue
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error creating Gumroad product: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying after network error...")
                    continue
                return None
            except Exception as e:
                logger.error(f"Error creating Gumroad product: {e}")
                return None
        
        return None
    
    def upload_product_file(self, product_id: str, file_path: str) -> Optional[str]:
        """Upload a file to an existing Gumroad product"""
        if not self.enabled:
            logger.warning("Gumroad not configured, skipping file upload")
            return None
        
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            url = f"{self.base_url}/products/{product_id}/contents"
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            files = {
                'file': open(file_path, 'rb')
            }
            
            logger.info(f"Uploading file to Gumroad product: {product_id}")
            response = requests.post(url, headers=headers, files=files)
            response.raise_for_status()
            
            result = response.json()
            
            if 'success' in result and result['success']:
                logger.info(f"Successfully uploaded file to product: {product_id}")
                return result.get('content', {}).get('id')
            else:
                logger.error(f"Failed to upload file: {result}")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error uploading file: {e}")
            return None
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return None
        finally:
            if 'files' in locals():
                files['file'].close()
    
    def get_product_url(self, product_id: str) -> Optional[str]:
        """Get the public URL for a Gumroad product"""
        if not self.enabled:
            return None
        
        try:
            url = f"{self.base_url}/products/{product_id}"
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            if 'success' in result and result['success']:
                product_url = result.get('product', {}).get('short_url')
                if product_url:
                    logger.info(f"Retrieved product URL: {product_url}")
                    return product_url
            
            logger.error(f"Failed to get product URL: {result}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting product URL: {e}")
            return None
    
    def update_product(self, product_id: str, **kwargs) -> bool:
        """Update an existing Gumroad product"""
        if not self.enabled:
            return False
        
        try:
            url = f"{self.base_url}/products/{product_id}"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.put(url, headers=headers, json=kwargs)
            response.raise_for_status()
            
            result = response.json()
            
            if 'success' in result and result['success']:
                logger.info(f"Successfully updated product: {product_id}")
                return True
            
            logger.error(f"Failed to update product: {result}")
            return False
            
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            return False
    
    def delete_product(self, product_id: str) -> bool:
        """Delete a Gumroad product"""
        if not self.enabled:
            return False
        
        try:
            url = f"{self.base_url}/products/{product_id}"
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            if 'success' in result and result['success']:
                logger.info(f"Successfully deleted product: {product_id}")
                return True
            
            logger.error(f"Failed to delete product: {result}")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            return False
