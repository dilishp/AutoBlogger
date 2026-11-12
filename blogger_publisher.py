"""
Blogger publishing integration for managing blog post publication
"""
import logging
from typing import Dict, Optional
from pathlib import Path
from blogger_client import BloggerClient
from content_generator import BlogPost
from config import config
import re
from bs4 import BeautifulSoup, Comment

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
        
        # Validate and sanitize HTML content
        content = self._validate_and_sanitize_html(content)
        
        return content
    
    def _insert_images_with_metadata(self, content: str, image_prompts: list, image_paths: list = None) -> str:
        """Replace image markers with safely escaped image nodes."""
        soup = BeautifulSoup(content, 'html.parser')
        markers = list(soup.find_all(string=re.compile(r'\[IMAGE:.*?\]')))
        markers = [marker for marker in markers
                   if marker.parent.name not in {'code', 'pre', 'script', 'style'}]
        for i, prompt in enumerate(image_prompts):
            image_url = None
            if image_paths and i < len(image_paths):
                path = image_paths[i]
                if isinstance(path, str) and path.startswith(('https://', 'http://')):
                    image_url = path
            if not image_url:
                from urllib.parse import quote_plus
                image_url = 'https://via.placeholder.com/1024x1024/4A90E2/FFFFFF?text=' + quote_plus(str(prompt)[:40])
                logger.warning(f"No hosted image URL available for image {i + 1}; using placeholder")

            alt_text = re.sub(r'\s+', ' ', str(prompt)).strip()[:160]
            image = soup.new_tag('img', src=image_url, alt=alt_text)
            image['title'] = alt_text[:80]
            image['class'] = ['blog-image']
            image['style'] = 'max-width:100%;height:auto;margin:20px 0;border-radius:8px'
            if i < len(markers):
                marker = markers[i]
                paragraph = marker.parent if marker.parent.name == 'p' else None
                marker.replace_with(image)
                if paragraph and not paragraph.get_text(strip=True) and not paragraph.find('img'):
                    paragraph.decompose()
            elif i == 0:
                first_paragraph = soup.find('p')
                if first_paragraph:
                    first_paragraph.insert_after(image)
        return str(soup)

    def _add_code_styling(self, content: str) -> str:
        """Style code elements through the parsed tree without rewriting their text."""
        soup = BeautifulSoup(content, 'html.parser')
        for pre in soup.find_all('pre'):
            pre['style'] = (pre.get('style', '') + ';background-color:#2d2d2d;color:#f8f8f2;'
                            'padding:15px;border-radius:5px;overflow-x:auto;'
                            'font-family:Consolas,Monaco,monospace;font-size:0.9em;line-height:1.5').lstrip(';')
        for code in soup.find_all('code'):
            if code.find_parent('pre'):
                continue
            code['style'] = (code.get('style', '') + ';background-color:#f4f4f4;padding:2px 6px;'
                             'border-radius:3px;font-family:Consolas,Monaco,monospace;'
                             'font-size:0.9em;color:#d63384').lstrip(';')
        return str(soup)

    def _validate_and_sanitize_html(self, content: str) -> str:
        """Repair HTML fragments while preserving escaped code examples as text."""
        soup = BeautifulSoup(content, 'html.parser')
        for comment in soup.find_all(string=lambda value: isinstance(value, Comment)):
            comment.extract()
        allowed_tags = {
            'a', 'p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'blockquote', 'pre', 'code', 'strong', 'b',
            'em', 'i', 'img', 'br', 'hr', 'table', 'thead', 'tbody', 'tr',
            'th', 'td'
        }
        for tag in soup.find_all(True):
            if tag.name.lower() not in allowed_tags:
                tag.unwrap()
                continue
            if tag.name.lower() == 'h1':
                tag.name = 'h2'  # Blogger renders the post title as the page's H1.
            for attribute in list(tag.attrs):
                if attribute.lower().startswith('on'):
                    del tag.attrs[attribute]
            for attribute in ('href', 'src'):
                value = tag.get(attribute)
                if value and re.match(r'\s*(javascript|data|vbscript):', str(value), re.IGNORECASE):
                    del tag.attrs[attribute]
            style = tag.get('style')
            if style and re.search(r'(expression\s*\(|url\s*\(|javascript:)', style, re.IGNORECASE):
                del tag.attrs['style']
        for image in soup.find_all('img'):
            image['alt'] = str(image.get('alt', '')).strip()
        # Return fragment content only; Blogger supplies the document wrapper.
        return ''.join(str(node) for node in soup.contents)

    def _apply_internal_links(self, content: str, internal_links: list) -> str:
        """Link the first matching text node without changing code or existing links."""
        soup = BeautifulSoup(content, 'html.parser')
        for link in internal_links:
            anchor = str(link.get('anchor_text', '')).strip()
            url = str(link.get('target_url', '')).strip()
            if not anchor or not url:
                continue
            pattern = re.compile(r'\b' + re.escape(anchor) + r'\b', re.IGNORECASE)
            for text_node in soup.find_all(string=True):
                if text_node.parent.name in {'a', 'code', 'pre', 'script', 'style'}:
                    continue
                match = pattern.search(str(text_node))
                if not match:
                    continue
                value = str(text_node)
                nodes = []
                if value[:match.start()]:
                    nodes.append(value[:match.start()])
                linked = soup.new_tag('a', href=url)
                linked['style'] = 'color:#0066cc;text-decoration:none'
                linked.string = value[match.start():match.end()]
                nodes.append(linked)
                if value[match.end():]:
                    nodes.append(value[match.end():])
                text_node.replace_with(*nodes)
                break
        return str(soup)

    def _apply_font_style(self, content: str, font_style: str) -> str:
        """Apply consistent font style to content, preserving code block fonts"""
        soup = BeautifulSoup(content, 'html.parser')
        wrapper = soup.new_tag('div')
        wrapper['style'] = f'font-family:{font_style};line-height:1.6'
        for child in list(soup.contents):
            wrapper.append(child.extract())
        soup.append(wrapper)
        return str(soup)
    
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
