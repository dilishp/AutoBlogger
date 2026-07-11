"""
Image generation and selection system for blog posts
"""
import logging
from typing import List, Optional
from pathlib import Path
from openai import OpenAI
from config import config
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generates and selects images for blog posts"""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.openai_api_key)
        self.stability_key = config.stability_ai_key
        self.output_dir = config.output_dir / "images"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_images(self, prompts: List[str], 
                       use_dalle: bool = True,
                       use_stability: bool = False) -> List[str]:
        """Generate images from prompts"""
        logger.info(f"Generating {len(prompts)} images...")
        
        image_paths = []
        
        for i, prompt in enumerate(prompts):
            try:
                if use_dalle:
                    image_path = self._generate_with_dalle(prompt, i)
                elif use_stability and self.stability_key:
                    image_path = self._generate_with_stability(prompt, i)
                else:
                    logger.warning("No image generation service configured")
                    continue
                
                if image_path:
                    image_paths.append(image_path)
                    logger.info(f"Generated image {i+1}/{len(prompts)}")
            
            except Exception as e:
                logger.error(f"Error generating image {i+1}: {e}")
                continue
        
        logger.info(f"Successfully generated {len(image_paths)} images")
        return image_paths
    
    def _generate_with_dalle(self, prompt: str, index: int) -> Optional[str]:
        """Generate image using DALL-E"""
        try:
            response = self.client.images.generate(
                model="dall-e-2",
                prompt=prompt,
                size="512x512",
                n=1,
            )
            
            image_url = response.data[0].url
            
            # Download the image
            image_path = self.output_dir / f"image_{index}.png"
            response = requests.get(image_url)
            response.raise_for_status()
            
            with open(image_path, 'wb') as f:
                f.write(response.content)
            
            return str(image_path)
        
        except Exception as e:
            logger.error(f"DALL-E generation failed: {e}")
            return None
    
    def _generate_with_stability(self, prompt: str, index: int) -> Optional[str]:
        """Generate image using Stability AI"""
        try:
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            
            headers = {
                "Authorization": f"Bearer {self.stability_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            body = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "steps": 30,
                "samples": 1
            }
            
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            
            data = response.json()
            image_data = data["artifacts"][0]["base64"]
            
            # Save image
            import base64
            image_path = self.output_dir / f"image_{index}.png"
            with open(image_path, 'wb') as f:
                f.write(base64.b64decode(image_data))
            
            return str(image_path)
        
        except Exception as e:
            logger.error(f"Stability AI generation failed: {e}")
            return None
    
    def select_stock_images(self, topic: str, num_images: int = 3) -> List[str]:
        """Search for and select stock images (placeholder for integration with stock APIs)"""
        logger.info(f"Searching for stock images for topic: {topic}")
        
        # This is a placeholder - in production, integrate with:
        # - Unsplash API
        # - Pexels API
        # - Pixabay API
        # - Shutterstock API
        
        # For now, return empty list
        logger.warning("Stock image selection not implemented - requires API integration")
        return []
    
    def optimize_image_for_web(self, image_path: str) -> str:
        """Optimize image for web (compress, resize)"""
        try:
            from PIL import Image
            
            img = Image.open(image_path)
            
            # Resize if too large
            max_size = (1200, 1200)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Save optimized version
            optimized_path = image_path.replace('.png', '_optimized.jpg')
            img.save(optimized_path, 'JPEG', quality=85, optimize=True)
            
            logger.info(f"Optimized image: {image_path}")
            return optimized_path
        
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return image_path
    
    def generate_alt_text(self, image_prompt: str, context: str) -> str:
        """Generate SEO-friendly alt text for images"""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an accessibility specialist. Generate descriptive alt text for images."
                    },
                    {
                        "role": "user",
                        "content": f"""Generate SEO-friendly alt text for this image:

Image description: {image_prompt}
Blog context: {context[:200]}

Requirements:
- Descriptive and specific
- Include relevant keywords if natural
- Keep under 125 characters
- Focus on what's visually important

Return only the alt text."""
                    }
                ]
            )
            
            alt_text = response.choices[0].message.content.strip()
            return alt_text
        
        except Exception as e:
            logger.error(f"Alt text generation failed: {e}")
            return "Blog post image"
    
    def create_image_varations(self, image_path: str, num_variations: int = 2) -> List[str]:
        """Create variations of an image using DALL-E"""
        logger.info(f"Creating {num_variations} image variations...")
        
        variations = []
        
        try:
            with open(image_path, 'rb') as f:
                response = self.client.images.create_variation(
                    image=f,
                    n=num_variations,
                    size="1024x1024"
                )
            
            for i, img_data in enumerate(response.data):
                # Download variation
                image_url = img_data.url
                variation_path = self.output_dir / f"variation_{i}.png"
                
                resp = requests.get(image_url)
                resp.raise_for_status()
                
                with open(variation_path, 'wb') as f:
                    f.write(resp.content)
                
                variations.append(str(variation_path))
            
            logger.info(f"Created {len(variations)} image variations")
            return variations
        
        except Exception as e:
            logger.error(f"Image variation creation failed: {e}")
            return []
