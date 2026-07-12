"""
Blogger publishing integration for managing blog post publication
"""
import logging
from typing import Dict, Optional
from pathlib import Path
from blogger_client import BloggerClient
from content_generator import BlogPost
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BloggerPublisher:
    """Manages publishing workflow for Blogger"""
    
    def __init__(self):
        self.client = BloggerClient()
        self.output_dir = config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def publish_blog_post(self, blog_post: BlogPost, 
                         as_draft: bool = True,
                         add_images: bool = True,
                         font_style: Optional[str] = None,
                         image_paths: list = None,
                         content_index: dict = None) -> Dict:
        """Publish a blog post to Blogger"""
        logger.info(f"Publishing blog post: {blog_post.title}")
        
        # Prepare content with images and styling
        content = self._prepare_content(blog_post, add_images, image_paths, content_index)
        
        # Apply consistent font if provided
        if font_style:
            content = self._apply_font_style(content, font_style)
        
        # Create the post with search description
        try:
            result = self.client.create_post(
                title=blog_post.title,
                content=content,
                labels=blog_post.tags,
                is_draft=as_draft,
                search_description=blog_post.meta_description
            )
            
            logger.info(f"Post {'created as draft' if as_draft else 'published'}: {result['id']}")
            
            # Save metadata
            self._save_post_metadata(result, blog_post)
            
            return {
                'success': True,
                'post_id': result['id'],
                'url': result.get('url', ''),
                'status': 'draft' if as_draft else 'published',
                'title': blog_post.title
            }
        
        except Exception as e:
            logger.error(f"Failed to publish post: {e}")
            return {
                'success': False,
                'error': str(e),
                'title': blog_post.title
            }
    
    def _prepare_content(self, blog_post: BlogPost, add_images: bool, image_paths: list = None, content_index: dict = None) -> str:
        """Prepare content with images and formatting"""
        content = blog_post.content
        
        # Process link placeholders first
        if content_index:
            from internal_linker import InternalLinker
            linker = InternalLinker()
            content = linker.process_link_placeholders(content, content_index)
        
        # Add image placeholders if enabled with proper metadata
        if add_images and blog_post.image_prompts:
            content = self._insert_images_with_metadata(content, blog_post.image_prompts, image_paths)
        
        # Apply internal links
        if blog_post.internal_links:
            content = self._apply_internal_links(content, blog_post.internal_links)
        
        # Add code block styling
        content = self._add_code_styling(content)
        
        # Add SEO meta tags (as HTML comments)
        seo_comment = f"""
<!-- 
Meta Description: {blog_post.meta_description}
Keywords: {', '.join(blog_post.keywords)}
-->
"""
        
        content = seo_comment + content
        
        return content
    
    def _insert_images_with_metadata(self, content: str, image_prompts: list, image_paths: list = None) -> str:
        """Insert images with proper metadata (alt text, title) at strategic locations"""
        import re
        
        for i, prompt in enumerate(image_prompts):
            # Generate alt text from prompt
            alt_text = prompt.replace('"', "'").replace('\n', ' ')[:100]
            title_text = f"Image {i+1}: {alt_text[:50]}"
            
            # Use placeholder image URL (Blogger doesn't support local file uploads via API)
            # Using a reliable placeholder service
            image_url = f"https://via.placeholder.com/1024x1024/4A90E2/FFFFFF?text={alt_text[:20].replace(' ', '+')}"
            
            # If we have actual image paths, try to use them (but this won't work in Blogger)
            if image_paths and i < len(image_paths):
                # For now, we'll use placeholder since Blogger API doesn't support image uploads
                # In production, you'd need to upload to a cloud service first
                logger.warning(f"Note: Blogger API doesn't support direct image uploads. Using placeholder URL.")
            
            # Look for image markers
            marker_pattern = r'\[IMAGE:.*?\]'
            
            if re.search(marker_pattern, content):
                # Replace first marker with proper image HTML
                image_html = f'<img src="{image_url}" alt="{alt_text}" title="{title_text}" class="blog-image" style="max-width:100%;height:auto;margin:20px 0;border-radius:8px;" />'
                content = re.sub(marker_pattern, image_html, content, count=1)
            else:
                # Insert after first paragraph if no markers
                first_para_end = content.find('</p>')
                if first_para_end != -1:
                    image_html = f'<img src="{image_url}" alt="{alt_text}" title="{title_text}" class="blog-image" style="max-width:100%;height:auto;margin:20px 0;border-radius:8px;" />'
                    content = content[:first_para_end + 4] + image_html + content[first_para_end + 4:]
        
        return content
    
    def _add_code_styling(self, content: str) -> str:
        """Add proper styling for code blocks"""
        import re
        
        # First, convert markdown-style code blocks to HTML
        # Handle ```code``` blocks (multi-line)
        content = re.sub(
            r'```(\w+)?\n(.*?)```',
            r'<pre><code class="\1">\2</code></pre>',
            content,
            flags=re.DOTALL
        )
        
        # Handle `code` (inline)
        content = re.sub(
            r'`([^`]+)`',
            r'<code>\1</code>',
            content
        )
        
        # Wrap code blocks in pre tags with styling
        # Look for existing code blocks and enhance them
        content = re.sub(
            r'<code>(.*?)</code>',
            r'<code style="background-color:#f4f4f4;padding:2px 6px;border-radius:3px;font-family:Consolas,Monaco,monospace;font-size:0.9em;color:#d63384;">\1</code>',
            content,
            flags=re.DOTALL
        )
        
        # Handle multi-line code blocks (pre tags)
        content = re.sub(
            r'<pre><code class="([^"]*)">(.*?)</code></pre>',
            r'<pre style="background-color:#2d2d2d;color:#f8f8f2;padding:15px;border-radius:5px;overflow-x:auto;font-family:Consolas,Monaco,monospace;font-size:0.9em;line-height:1.5;"><code class="\1">\2</code></pre>',
            content,
            flags=re.DOTALL
        )
        
        # Handle pre tags without code inside
        content = re.sub(
            r'<pre>(.*?)</pre>',
            r'<pre style="background-color:#2d2d2d;color:#f8f8f2;padding:15px;border-radius:5px;overflow-x:auto;font-family:Consolas,Monaco,monospace;font-size:0.9em;line-height:1.5;">\1</pre>',
            content,
            flags=re.DOTALL
        )
        
        return content
    
    def _apply_internal_links(self, content: str, internal_links: list) -> str:
        """Apply internal links to content"""
        import re
        
        for link in internal_links:
            anchor = link.get('anchor_text', '')
            url = link.get('target_url', '')
            
            if anchor and url:
                # Replace first occurrence of anchor text with link
                pattern = re.escape(anchor)
                replacement = f'<a href="{url}" style="color:#0066cc;text-decoration:none;">{anchor}</a>'
                content = re.sub(pattern, replacement, content, count=1)
        
        return content
    
    def _apply_font_style(self, content: str, font_style: str) -> str:
        """Apply consistent font style to content"""
        # Wrap the entire content in a div with consistent font
        font_div = f'<div style="font-family:{font_style};line-height:1.6;">{content}</div>'
        return font_div
    
    def _update_search_description(self, post_id: str, description: str):
        """Update the search description for a post"""
        # Blogger API doesn't directly support search description updates via API
        # We'll add it as a meta description tag in the content HTML
        # This is a known limitation of the Blogger API
        logger.info("Note: Blogger API doesn't support search description updates via API")
        logger.info("Meta description is included in HTML comments for reference")
    
    def analyze_font_style(self, posts: list) -> str:
        """Analyze existing posts to determine consistent font style"""
        if not posts:
            return "Arial, sans-serif"  # Default fallback
        
        # Analyze a few posts to find common font patterns
        font_patterns = []
        
        for post in posts[:5]:  # Analyze first 5 posts
            content = post.get('content', '')
            
            # Look for font-family in style attributes
            import re
            font_matches = re.findall(r'font-family\s*:\s*([^;]+)', content)
            font_patterns.extend(font_matches)
        
        # Find most common font
        if font_patterns:
            from collections import Counter
            most_common = Counter(font_patterns).most_common(1)
            if most_common:
                return most_common[0][0].strip()
        
        return "Arial, sans-serif"  # Default if no pattern found
    
    def _save_post_metadata(self, blogger_result: Dict, blog_post: BlogPost):
        """Save post metadata for reference"""
        metadata = {
            'blogger_id': blogger_result['id'],
            'url': blogger_result.get('url', ''),
            'title': blog_post.title,
            'keywords': blog_post.keywords,
            'tags': blog_post.tags,
            'meta_description': blog_post.meta_description,
            'internal_links': blog_post.internal_links,
            'image_prompts': blog_post.image_prompts
        }
        
        import json
        metadata_path = self.output_dir / f"post_{blogger_result['id']}_metadata.json"
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved metadata to {metadata_path}")
    
    def publish_draft(self, post_id: str) -> Dict:
        """Publish a draft post"""
        logger.info(f"Publishing draft post: {post_id}")
        
        try:
            result = self.client.publish_post(post_id)
            
            logger.info(f"Post published: {result['id']}")
            
            return {
                'success': True,
                'post_id': result['id'],
                'url': result.get('url', ''),
                'status': 'published'
            }
        
        except Exception as e:
            logger.error(f"Failed to publish draft: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_post(self, post_id: str, blog_post: BlogPost) -> Dict:
        """Update an existing post"""
        logger.info(f"Updating post: {post_id}")
        
        content = self._prepare_content(blog_post, add_images=False)
        
        try:
            result = self.client.update_post(
                post_id=post_id,
                title=blog_post.title,
                content=content,
                labels=blog_post.tags
            )
            
            logger.info(f"Post updated: {result['id']}")
            
            return {
                'success': True,
                'post_id': result['id'],
                'url': result.get('url', ''),
                'status': 'updated'
            }
        
        except Exception as e:
            logger.error(f"Failed to update post: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_post(self, post_id: str) -> Dict:
        """Delete a blog post"""
        logger.info(f"Deleting post: {post_id}")
        
        try:
            self.client.delete_post(post_id)
            
            logger.info(f"Post deleted: {post_id}")
            
            return {
                'success': True,
                'post_id': post_id,
                'status': 'deleted'
            }
        
        except Exception as e:
            logger.error(f"Failed to delete post: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def schedule_post(self, blog_post: BlogPost, 
                     publish_date: str) -> Dict:
        """Schedule a post for future publication (Blogger doesn't support this natively)"""
        logger.info(f"Scheduling post for: {publish_date}")
        
        # Blogger doesn't have native scheduling, so we create as draft
        # with metadata about scheduled time
        result = self.publish_blog_post(blog_post, as_draft=True)
        
        if result['success']:
            # Save schedule info
            schedule_info = {
                'post_id': result['post_id'],
                'scheduled_date': publish_date,
                'status': 'scheduled'
            }
            
            import json
            schedule_path = self.output_dir / f"scheduled_{result['post_id']}.json"
            
            with open(schedule_path, 'w') as f:
                json.dump(schedule_info, f, indent=2)
            
            logger.info(f"Post scheduled (as draft): {result['post_id']}")
        
        return result
    
    def get_post_stats(self, post_id: str) -> Dict:
        """Get statistics for a post (views, comments, etc.)"""
        logger.info(f"Fetching stats for post: {post_id}")
        
        try:
            post = self.client.get_post(post_id)
            comments = self.client.get_post_comments(post_id)
            
            stats = {
                'post_id': post_id,
                'title': post.get('title', ''),
                'url': post.get('url', ''),
                'published': post.get('published', ''),
                'updated': post.get('updated', ''),
                'comment_count': len(comments),
                'labels': post.get('labels', [])
            }
            
            logger.info(f"Stats fetched for post: {post_id}")
            return stats
        
        except Exception as e:
            logger.error(f"Failed to fetch post stats: {e}")
            return {}
