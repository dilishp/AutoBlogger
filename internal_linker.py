"""
Internal linking and backreference system for blog posts
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from openai import OpenAI
from config import config
import re
from bs4 import BeautifulSoup

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
        """Extract key topics and keywords from a post"""
        topics = labels.copy()
        
        # Add title words (excluding common words)
        title_words = re.findall(r'\b\w{3,}\b', title.lower())
        common_words = {'the', 'and', 'for', 'with', 'about', 'this', 'that', 'from', 'have', 'been', 'will', 'can', 'are', 'was', 'were', 'been', 'be', 'is', 'a', 'an', 'in', 'on', 'at', 'to', 'by', 'or', 'as', 'if', 'when', 'how', 'what', 'which', 'who', 'where', 'why', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there', 'then', 'once', 'get', 'got', 'use', 'using', 'make', 'making', 'take', 'taking', 'come', 'coming', 'could', 'would', 'should', 'may', 'might', 'must', 'shall'}
        topics.extend([w for w in title_words if w not in common_words])
        
        # Extract keywords from content (frequent meaningful words)
        # Remove HTML tags first
        clean_content = re.sub(r'<[^>]+>', ' ', content)
        words = re.findall(r'\b\w{4,}\b', clean_content.lower())
        
        # Count word frequency
        word_freq = {}
        for word in words:
            if word not in common_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Add top frequent words as topics (appearing 3+ times)
        for word, freq in word_freq.items():
            if freq >= 3:
                topics.append(word)
        
        # Extract technical terms and phrases (capitalized words, hyphenated terms)
        tech_terms = re.findall(r'\b[A-Z][a-zA-Z]+\b', content)
        topics.extend([term.lower() for term in tech_terms])
        
        # Extract hyphenated terms
        hyphenated = re.findall(r'\b\w+-\w+\b', content)
        topics.extend(hyphenated)
        
        # Remove duplicates
        topics = list(set(topics))
        
        return topics
    
    def find_linking_opportunities(self, new_post: Dict, 
                                   content_index: Dict[str, Dict],
                                   min_links: int = 3,
                                   max_links: int = 5) -> List[InternalLink]:
        """Find internal linking opportunities using simple keyword matching"""
        logger.info("Finding internal linking opportunities...")
        
        new_title = new_post.get('title', '')
        new_content = new_post.get('content', '')
        new_tags = new_post.get('tags', [])
        new_topics = self._extract_topics(new_title, new_content, new_tags)
        
        logger.info(f"New post topics extracted: {len(new_topics)} topics")
        
        opportunities = []
        
        for post_id, post_data in content_index.items():
            # Skip if it's the same post
            if post_data['url'] == new_post.get('url', ''):
                continue
            
            # Simple keyword matching - check if any keywords match
            keyword_matches = self._find_keyword_matches(new_content, post_data['topics'], post_data['title'])
            
            # Also check if topics overlap
            topic_overlap = set(new_topics) & set(post_data['topics'])
            
            # If we have any keyword matches or topic overlap, add as opportunity
            if keyword_matches or topic_overlap:
                # Generate anchor text
                anchor_text = self._generate_anchor_text(new_content, post_data)
                
                if anchor_text:
                    link = InternalLink(
                        anchor_text=anchor_text,
                        target_url=post_data['url'],
                        target_title=post_data['title'],
                        context=f"Related to {post_data['title']}",
                        relevance_score=len(keyword_matches) + len(topic_overlap)
                    )
                    opportunities.append(link)
                    logger.info(f"Found link opportunity: {post_data['title']} (matches: {len(keyword_matches)} keywords, {len(topic_overlap)} topics)")
        
        # Ensure minimum number of links by adding recent posts if needed
        if len(opportunities) < min_links and len(content_index) > 0:
            logger.info(f"Only {len(opportunities)} links found, adding recent posts to meet minimum of {min_links}")
            
            # Get posts not already linked
            linked_urls = {link.target_url for link in opportunities}
            for post_id, post_data in content_index.items():
                if post_data['url'] not in linked_urls and post_data['url'] != new_post.get('url', ''):
                    anchor_text = self._generate_anchor_text(new_content, post_data)
                    if anchor_text:
                        link = InternalLink(
                            anchor_text=anchor_text,
                            target_url=post_data['url'],
                            target_title=post_data['title'],
                            context=f"Related post",
                            relevance_score=1
                        )
                        opportunities.append(link)
                        logger.info(f"Added recent post for minimum links: {post_data['title']}")
                        
                        if len(opportunities) >= min_links:
                            break
        
        # Limit to max_links
        opportunities = opportunities[:max_links]
        
        logger.info(f"Found {len(opportunities)} linking opportunities (minimum: {min_links})")
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
    
    def _find_keyword_matches(self, content: str, topics: List[str], title: str) -> List[str]:
        """Find keywords from existing posts that appear in the new content"""
        matches = []
        content_lower = content.lower()
        
        # Remove HTML tags for better matching
        clean_content = re.sub(r'<[^>]+>', ' ', content_lower)
        
        for topic in topics:
            topic_lower = topic.lower()
            # Check if topic appears as a whole word in content
            if re.search(r'\b' + re.escape(topic_lower) + r'\b', clean_content):
                matches.append(topic)
        
        # Also check title words
        title_words = re.findall(r'\b\w{3,}\b', title.lower())
        for word in title_words:
            if re.search(r'\b' + re.escape(word) + r'\b', clean_content):
                if word not in matches:
                    matches.append(word)
        
        return matches
    
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
        """Add links to matching prose text nodes, never to code or existing links."""
        from urllib.parse import urlparse

        soup = BeautifulSoup(content, 'html.parser')
        applied = 0
        for link in links:
            anchor = str(link.anchor_text or '').strip()
            url = str(link.target_url or '').strip()
            if not anchor or urlparse(url).scheme not in {'http', 'https'}:
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
                tag = soup.new_tag('a', href=url, title=str(link.target_title or '')[:200])
                tag.string = value[match.start():match.end()]
                nodes.append(tag)
                if value[match.end():]:
                    nodes.append(value[match.end():])
                text_node.replace_with(*nodes)
                applied += 1
                break
        logger.info(f"Applied {applied}/{len(links)} internal links")
        return str(soup)

    def process_link_placeholders(self, content: str,
                                content_index: Dict[str, Dict]) -> str:
        """Replace link markers in prose while leaving code samples untouched."""
        from difflib import SequenceMatcher
        from urllib.parse import urlparse

        soup = BeautifulSoup(content, 'html.parser')
        placeholder_re = re.compile(r'\[LINK:\s*([^\]]+)\]', re.IGNORECASE)
        converted = 0
        for text_node in list(soup.find_all(string=placeholder_re)):
            if text_node.parent.name in {'a', 'code', 'pre', 'script', 'style'}:
                continue
            value = str(text_node)
            pieces = []
            cursor = 0
            for match in placeholder_re.finditer(value):
                if value[cursor:match.start()]:
                    pieces.append(value[cursor:match.start()])
                topic = match.group(1).strip()
                best_match = None
                best_score = 0
                for post in content_index.values():
                    title = str(post.get('title', ''))
                    score = 20 if topic.casefold() == title.casefold() else (10 if topic.casefold() in title.casefold() else 0)
                    for candidate in post.get('topics', []) + post.get('tags', []):
                        candidate = str(candidate)
                        if topic.casefold() == candidate.casefold():
                            score = max(score, 15)
                        elif topic.casefold() in candidate.casefold():
                            score = max(score, 8)
                    score = max(score, int(SequenceMatcher(None, topic.casefold(), title.casefold()).ratio() * 10))
                    if score > best_score:
                        best_match, best_score = post, score
                url = str(best_match.get('url', '')) if best_match and best_score >= 6 else ''
                if urlparse(url).scheme in {'http', 'https'}:
                    anchor = soup.new_tag('a', href=url, title=str(best_match.get('title', topic))[:200])
                    anchor.string = topic
                    pieces.append(anchor)
                    converted += 1
                else:
                    pieces.append(topic)
                cursor = match.end()
            if value[cursor:]:
                pieces.append(value[cursor:])
            text_node.replace_with(*pieces)
        logger.info(f"Converted {converted} link placeholders")
        return str(soup)

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
