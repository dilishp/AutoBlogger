"""
Gumroad API client for creating and managing digital products
"""
import logging
import os
import requests
from typing import Dict, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GumroadClient:
    """Client for interacting with Gumroad API"""
    
    def __init__(self):
        self.access_token = os.getenv('GUMROAD_ACCESS_TOKEN')
        self.base_url = "https://api.gumroad.com/v2"
        enabled_value = os.getenv('ENABLE_DIGITAL_PRODUCTS', 'true').strip().lower()
        self.enabled = bool(self.access_token) and enabled_value not in {'0', 'false', 'no', 'off'}
        
        if not self.enabled:
            logger.warning("Gumroad access token not configured. Product creation will be disabled.")
        else:
            logger.info("Gumroad client initialized")
    
    def create_product(self, name: str, description: str, price: float,
                       file_path: Optional[str] = None,
                       tags: Optional[List[str]] = None) -> Optional[Dict]:
        """Product creation and file uploads are not supported by Gumroad's public REST API.

        Use Gumroad's official MCP integration or upload the prepared package in the
        Gumroad dashboard. This method intentionally avoids undocumented endpoints.
        """
        if not self.enabled:
            logger.warning("Gumroad access token is not configured")
            return None
        logger.error(
            "Gumroad REST API cannot create products or upload product content. "
            "Use the official Gumroad MCP integration or upload the prepared ZIP manually: %s",
            file_path or '(no package supplied)'
        )
        return None

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
