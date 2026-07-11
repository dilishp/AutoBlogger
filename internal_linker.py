"""
Internal linking and backreference system for blog posts
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from openai import OpenAI
from config import config
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class InternalLink:
    """Represents an internal link opportunity"""
    anchor_text: str
    target_url: str
    target_title: str
    context: str
    relevance_score: float


class InternalLinker:
    """Manages internal linking between blog posts"""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.openai_api_key)
        self.blog_domain = config.blog_domain
    
    def build_content_index(self, posts: List[Dict]) -> Dict[str, Dict]:
        """Build an index of existing content for linking"""
        logger.info("Building content index from existing posts...")
        
        index = {}
        
        for post in posts:
            post_id = post.get('id', '')
            title = post.get('title', '')
            content = post.get('content', '')
            url = post.get('url', '')
            labels = post.get('labels', [])
            
            # Extract key topics and concepts
            topics = self._extract_topics(title, content, labels)
            
            index[post_id] = {
                'title': title,
                'url': url,
                'content': content,
                'labels': labels,
                'topics': topics,
                'word_count': len(content.split())
            }
        
        logger.info(f"Built index with {len(index)} posts")
        return index
    
    def _extract_topics(self, title: str, content: str, labels: List[str]) -> List[str]:
        """Extract key topics from a post"""
        topics = labels.copy()
        
        # Add title words (excluding common words)
        title_words = re.findall(r'\b\w{3,}\b', title.lower())
        topics.extend([w for w in title_words if w not in ['the', 'and', 'for', 'with', 'about']])
        
        # Remove duplicates
        topics = list(set(topics))
        
        return topics
    
    def find_linking_opportunities(self, new_post: Dict, 
                                   content_index: Dict[str, Dict],
                                   max_links: int = 5) -> List[InternalLink]:
        """Find internal linking opportunities for a new post"""
        logger.info("Finding internal linking opportunities...")
        
        new_title = new_post.get('title', '')
        new_content = new_post.get('content', '')
        new_topics = self._extract_topics(new_title, new_content, new_post.get('tags', []))
        
        opportunities = []
        
        for post_id, post_data in content_index.items():
            # Skip if it's the same post
            if post_data['url'] == new_post.get('url', ''):
                continue
            
            # Calculate relevance
            relevance = self._calculate_relevance(new_topics, post_data['topics'])
            
            if relevance > 0.3:  # Threshold for relevance
                # Generate anchor text
                anchor_text = self._generate_anchor_text(new_content, post_data)
                
                if anchor_text:
                    link = InternalLink(
                        anchor_text=anchor_text,
                        target_url=post_data['url'],
                        target_title=post_data['title'],
                        context=f"Related to {post_data['title']}",
                        relevance_score=relevance
                    )
                    opportunities.append(link)
        
        # Sort by relevance and limit
        opportunities.sort(key=lambda x: x.relevance_score, reverse=True)
        opportunities = opportunities[:max_links]
        
        logger.info(f"Found {len(opportunities)} linking opportunities")
        return opportunities
    
    def _calculate_relevance(self, topics1: List[str], topics2: List[str]) -> float:
        """Calculate relevance score between two sets of topics"""
        if not topics1 or not topics2:
            return 0.0
        
        set1 = set(t.lower() for t in topics1)
        set2 = set(t.lower() for t in topics2)
        
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _generate_anchor_text(self, content: str, target_post: Dict) -> Optional[str]:
        """Generate appropriate anchor text for linking"""
        target_title = target_post['title']
        target_topics = target_post['topics']
        
        # Try to find natural anchor text in content
        for topic in target_topics:
            if topic.lower() in content.lower():
                return topic
        
        # Use title as fallback
        return target_title
    
    def apply_internal_links(self, content: str, 
                            links: List[InternalLink]) -> str:
        """Apply internal links to content"""
        logger.info(f"Applying {len(links)} internal links to content...")
        
        modified_content = content
        links_applied = 0
        
        for link in links:
            # Find the anchor text in content
            anchor_pattern = re.escape(link.anchor_text)
            
            # Replace first occurrence with link
            pattern = rf'(?<!href="[^"]*)({anchor_pattern})(?![^<]*</a>)'
            replacement = f'<a href="{link.target_url}" title="{link.target_title}">\\1</a>'
            
            new_content = re.sub(pattern, replacement, modified_content, count=1)
            
            if new_content != modified_content:
                modified_content = new_content
                links_applied += 1
                logger.info(f"Applied link: {link.anchor_text} -> {link.target_title}")
        
        logger.info(f"Applied {links_applied}/{len(links)} internal links")
        return modified_content
    
    def process_link_placeholders(self, content: str, 
                                content_index: Dict[str, Dict]) -> str:
        """Process [LINK: topic] placeholders and convert them to actual links"""
        import re
        
        logger.info("Processing link placeholders...")
        
        # Find all [LINK: topic] placeholders
        placeholder_pattern = r'\[LINK:\s*([^\]]+)\]'
        placeholders = re.findall(placeholder_pattern, content)
        
        if not placeholders:
            logger.info("No link placeholders found")
            return content
        
        logger.info(f"Found {len(placeholders)} link placeholders")
        
        modified_content = content
        links_converted = 0
        
        for placeholder_topic in placeholders:
            # Search for matching post in content index
            best_match = None
            best_score = 0
            
            for post_id, post_data in content_index.items():
                # Calculate relevance score
                score = 0
                post_title = post_data.get('title', '').lower()
                post_topics = post_data.get('topics', [])
                
                # Check if placeholder matches title
                if placeholder_topic.lower() in post_title:
                    score += 10
                
                # Check if placeholder matches topics
                for topic in post_topics:
                    if placeholder_topic.lower() in topic.lower():
                        score += 5
                
                if score > best_score:
                    best_score = score
                    best_match = post_data
            
            if best_match and best_score > 0:
                # Replace placeholder with actual link
                post_url = best_match.get('url', '')
                post_title = best_match.get('title', placeholder_topic)
                
                if post_url:
                    link_html = f'<a href="{post_url}" title="{post_title}">{placeholder_topic}</a>'
                    modified_content = modified_content.replace(f'[LINK: {placeholder_topic}]', link_html)
                    links_converted += 1
                    logger.info(f"Converted placeholder: {placeholder_topic} -> {post_title}")
            else:
                # Remove placeholder if no match found
                modified_content = modified_content.replace(f'[LINK: {placeholder_topic}]', placeholder_topic)
                logger.warning(f"No match found for placeholder: {placeholder_topic}")
        
        logger.info(f"Converted {links_converted}/{len(placeholders)} link placeholders")
        return modified_content
    
    def suggest_backlinks(self, new_post: Dict,
                         content_index: Dict[str, Dict]) -> List[Dict]:
        """Suggest existing posts that should link to the new post"""
        logger.info("Suggesting backlink opportunities...")
        
        new_title = new_post.get('title', '')
        new_content = new_post.get('content', '')
        new_topics = self._extract_topics(new_title, new_content, new_post.get('tags', []))
        new_url = new_post.get('url', '')
        
        backlink_suggestions = []
        
        for post_id, post_data in content_index.items():
            if post_data['url'] == new_url:
                continue
            
            # Calculate relevance
            relevance = self._calculate_relevance(new_topics, post_data['topics'])
            
            if relevance > 0.4:  # Higher threshold for backlinks
                backlink_suggestions.append({
                    'post_title': post_data['title'],
                    'post_url': post_data['url'],
                    'relevance_score': relevance,
                    'suggested_anchor': new_title,
                    'reason': f"Post covers similar topics: {', '.join(set(new_topics) & set(post_data['topics']))}"
                })
        
        # Sort by relevance
        backlink_suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"Suggested {len(backlink_suggestions)} backlink opportunities")
        return backlink_suggestions
    
    def generate_linking_report(self, new_post: Dict,
                               content_index: Dict[str, Dict]) -> Dict:
        """Generate a comprehensive linking report"""
        logger.info("Generating linking report...")
        
        # Find outgoing links
        outgoing_links = self.find_linking_opportunities(new_post, content_index)
        
        # Find backlink opportunities
        backlink_opportunities = self.suggest_backlinks(new_post, content_index)
        
        report = {
            'post_title': new_post.get('title', ''),
            'post_url': new_post.get('url', ''),
            'outgoing_links': [
                {
                    'anchor': link.anchor_text,
                    'target': link.target_title,
                    'target_url': link.target_url,
                    'relevance': link.relevance_score
                }
                for link in outgoing_links
            ],
            'backlink_opportunities': backlink_opportunities,
            'total_outgoing': len(outgoing_links),
            'total_backlink_opportunities': len(backlink_opportunities)
        }
        
        logger.info("Linking report generated")
        return report
    
    def update_old_posts_with_links(self, new_post: Dict,
                                   content_index: Dict[str, Dict],
                                   blogger_client) -> int:
        """Update old posts to link to the new post"""
        logger.info("Updating old posts with new links...")
        
        backlink_opportunities = self.suggest_backlinks(new_post, content_index)
        updated_count = 0
        
        for opportunity in backlink_opportunities[:3]:  # Limit to top 3
            try:
                # Get the post
                post_url = opportunity['post_url']
                post_id = post_url.split('/')[-1]  # Extract ID from URL
                
                old_post = blogger_client.get_post(post_id)
                
                # Add link to content
                old_content = old_post.get('content', '')
                new_url = new_post.get('url', '')
                new_title = new_post.get('title', '')
                
                # Add link at the end or in relevant section
                link_html = f'\n<p><strong>Related:</strong> <a href="{new_url}">{new_title}</a></p>'
                updated_content = old_content + link_html
                
                # Update the post
                blogger_client.update_post(
                    post_id,
                    old_post.get('title', ''),
                    updated_content,
                    old_post.get('labels', [])
                )
                
                updated_count += 1
                logger.info(f"Updated post: {opportunity['post_title']}")
            
            except Exception as e:
                logger.error(f"Failed to update post {opportunity['post_title']}: {e}")
                continue
        
        logger.info(f"Updated {updated_count} old posts with new links")
        return updated_count
