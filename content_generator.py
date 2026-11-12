"""
Content generation engine with SEO optimization
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
import re
from bs4 import BeautifulSoup
from openai import OpenAI
from config import config
from seo_researcher import TopicOpportunity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BlogPost:
    """Represents a complete blog post"""
    title: str
    content: str
    meta_description: str
    keywords: List[str]
    tags: List[str]
    headings: Dict[str, str]  # H2, H3 headings
    image_prompts: List[str]
    internal_links: List[Dict[str, str]]


class ContentGenerator:
    """Generates SEO-optimized blog content"""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.openai_api_key)
        self.blog_niche = config.blog_niche
        self.target_audience = config.target_audience
        self.blog_domain = config.blog_domain
    
    def generate_blog_post(self, opportunity: TopicOpportunity, 
                          existing_posts: List[Dict],
                          competitor_analysis: Optional[Dict] = None) -> BlogPost:
        """Generate a complete SEO-optimized blog post"""
        logger.info(f"Generating blog post for topic: {opportunity.topic}")
        
        # Generate the main content
        content_data = self._generate_content(opportunity, competitor_analysis)
        
        # Add internal links
        internal_links = self._generate_internal_links(
            opportunity.topic, 
            content_data['content'],
            existing_posts
        )
        
        # Generate image prompts
        image_prompts = self._generate_image_prompts(opportunity, content_data)
        
        # Create blog post object
        blog_post = BlogPost(
            title=content_data['title'],
            content=content_data['content'],
            meta_description=content_data['meta_description'],
            keywords=opportunity.keywords,
            tags=self._generate_tags(opportunity),
            headings=content_data['headings'],
            image_prompts=image_prompts,
            internal_links=internal_links
        )
        
        logger.info(f"Blog post generated: {blog_post.title}")
        return blog_post
    
    def _generate_content(self, opportunity: TopicOpportunity,
                         competitor_analysis: Optional[Dict] = None) -> Dict:
        """Generate the main blog content"""
        
        competitor_info = ""
        if competitor_analysis:
            competitor_info = f"\nCompetitor Analysis:\n{competitor_analysis}"
        
        response = self.client.chat.completions.create(
            model=config.openai_model_content,
            max_tokens=max(config.max_tokens_content, 3000),
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an elite content writer and SEO specialist specializing in {self.blog_niche}. 
                    You write engaging, well-structured blog posts that are optimized for search engines and provide genuine value to {self.target_audience}.
                    
                    Your writing style:
                    - Technical yet accessible
                    - Educational with clear explanations
                    - Practical with code examples
                    - Authoritative with deep technical knowledge
                    - Focused on programming concepts, algorithms, and software engineering fundamentals
                    - Backed by computer science theory and best practices
                    
                    Blog niche: {self.blog_niche}
                    Target audience: {self.target_audience}
                    Blog domain: {self.blog_domain}
                    
                    Quality standards:
                    - Include specific technical details, code examples, and diagrams descriptions
                    - Use real-world programming scenarios and use cases
                    - Provide clear explanations of complex concepts
                    - Include complexity analysis (time/space) where relevant
                    - Reference authoritative sources like CLRS, Design Patterns, or language documentation
                    - Avoid oversimplification - respect the technical depth
                    - Include practical implementation tips and common pitfalls
                    - Do not invent benchmarks, statistics, quotes, studies, or source URLs
                    - Separate established facts from assumptions; explain when evidence is unavailable
                    - Use a concrete worked example and explain why each step matters
                    - Avoid repetitive introductions, keyword stuffing, generic filler, and unsupported claims"""
                },
                {
                    "role": "user",
                    "content": f"""Write a high-quality, engaging blog post based on this topic opportunity:

Topic: {opportunity.topic}
Suggested Title: {opportunity.suggested_title}
Keywords: {', '.join(opportunity.keywords)}
Search Volume: {opportunity.search_volume if hasattr(opportunity, 'search_volume') else 'N/A'}
Competition Level: {opportunity.competition if hasattr(opportunity, 'competition') else 'N/A'}
Content Outline:
{chr(10).join(f'- {point}' for point in opportunity.content_outline)}
{competitor_info}

Requirements:
1. Use the suggested title or create a better SEO-optimized title that includes primary keyword
2. Write 1000-1500 words of high-quality, useful technical content (clear, educational format)
3. Include 2-3 specific technical details, code examples, or algorithmic analysis
4. Include at least 1 real-world programming scenario or use case
5. Format code examples using HTML: <code> for inline code, <pre><code> for multi-line code blocks
6. Use proper HTML formatting throughout (paragraphs, headings, lists, code blocks)
7. Include [IMAGE: description] markers where diagrams or visualizations should be inserted
8. Include a compelling introduction that explains why this concept matters to developers
9. Use clear H2 and H3 headings for structure
10. Include practical implementation tips and common pitfalls to avoid
11. Write in a technical yet accessible tone suitable for software developers
12. Include a strong conclusion with call-to-action to subscribe to the YouTube channel
13. Naturally incorporate the primary and secondary keywords
14. Add placeholder markers for internal links using SPECIFIC, DESCRIPTIVE topic names like: [LINK: recursion fundamentals], [LINK: algorithm efficiency analysis], [LINK: design patterns essentials] - NOT generic terms like "related topic"
15. Focus on clear explanations of concepts - provide depth without overwhelming
16. Include this linked call-to-action in the conclusion: <a href="https://www.youtube.com/@catchybytes71">Subscribe to CatchyBytes by Techy on YouTube</a> for more programming tutorials
17. Add a unique technical insight or perspective that differentiates this from similar content
18. Include complexity analysis (Big O notation) where relevant
19. Reference authoritative sources only when confident they exist; never fabricate links or citations
20. Ensure each HTML element is properly nested and closed; keep code examples escaped inside <pre><code>

Return as JSON with these fields:
- title
- content (HTML formatted)
- meta_description (150-160 characters)
- headings (dict with h2 and h3 arrays)
- key_statistics (array of statistics/data points used)
- examples (array of real-world examples mentioned)"""
                }
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            raw = (response.choices[0].message.content or '').strip()
            raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.IGNORECASE)
            data = json.loads(raw)
            title = str(data.get('title') or opportunity.suggested_title).strip()
            body = str(data.get('content') or '').strip()
            if len(re.sub(r'<[^>]+>', ' ', body).split()) < 500:
                raise ValueError('Generated article is too short or missing')
            soup = BeautifulSoup(body, 'html.parser')
            for tag in soup.find_all(['script', 'style', 'iframe', 'object']):
                tag.decompose()
            body = ''.join(str(node) for node in soup.contents)
            meta = re.sub(r'\s+', ' ', str(data.get('meta_description') or '')).strip()
            if len(meta) > 160:
                meta = meta[:157].rsplit(' ', 1)[0] + '...'
            if len(meta) < 80:
                meta = (title + ' — practical guidance, examples, and implementation advice.')[:157]
            return {
                'title': title,
                'content': body,
                'meta_description': meta,
                'headings': data.get('headings') or {'h2': [], 'h3': []}
            }
        except (json.JSONDecodeError, ValueError, TypeError, AttributeError, IndexError) as e:
            logger.error(f"Invalid content response: {e}")
            raise ValueError(f"Content generation returned invalid or incomplete article: {e}") from e
    
    def _generate_internal_links(self, current_topic: str, 
                                 content: str,
                                 existing_posts: List[Dict]) -> List[Dict[str, str]]:
        """Generate internal linking opportunities"""
        logger.info("Generating internal links...")
        
        # Get summaries of existing posts
        post_summaries = []
        for post in existing_posts[:50]:  # Limit to 50 most relevant
            post_summaries.append({
                'title': post.get('title', ''),
                'url': post.get('url', ''),
                'labels': post.get('labels', [])
            })
        
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model_content,
                max_tokens=1000,
                messages=[
                {
                    "role": "system",
                    "content": "You are an internal linking specialist. Identify opportunities to link to existing content."
                },
                {
                    "role": "user",
                    "content": f"""For this new blog post about "{current_topic}", identify 3-5 opportunities to link to existing posts.

Existing posts:
{chr(10).join(f"- {p['title']}: {p['url']}" for p in post_summaries[:20])}

New content excerpt:
{content[:2000]}

Return as JSON array with:
- anchor_text (the text to link)
- target_url (which post to link to)
- context (why this link is valuable)"""
                }
                ],
                response_format={"type": "json_object"}
            )
        except Exception as exc:
            logger.warning(f"Internal-link suggestions unavailable; continuing without them: {exc}")
            return []
        
        import json
        try:
            links = json.loads(response.choices[0].message.content).get('links', [])
            logger.info(f"Generated {len(links)} internal link opportunities")
            return links
        except (json.JSONDecodeError, AttributeError, TypeError) as exc:
            logger.error(f"Error parsing internal links response: {exc}")
            return []
    
    def _generate_image_prompts(self, opportunity: TopicOpportunity,
                               content_data: Dict) -> List[str]:
        """Generate image prompts for the blog post"""
        logger.info("Generating image prompts...")
        
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model_content,
                max_tokens=800,
                messages=[
                {
                    "role": "system",
                    "content": "You are an image prompt specialist. Create detailed prompts for AI image generation."
                },
                {
                    "role": "user",
                    "content": f"""Generate 3-5 detailed image prompts for a blog post about "{opportunity.topic}".

Blog niche: {self.blog_niche}
Target audience: {self.target_audience}

Requirements:
1. Each prompt should be descriptive and specific
2. Include style, mood, and composition details
3. Ensure images are professional and attention-grabbing
4. One featured image (hero image)
5. 2-4 supporting images for sections

Return as JSON array of prompt strings."""
                }
                ],
                response_format={"type": "json_object"}
            )
        except Exception as exc:
            logger.warning(f"Image prompt generation unavailable; continuing without images: {exc}")
            return []
        
        import json
        try:
            prompts = json.loads(response.choices[0].message.content).get('prompts', [])
            # Ensure all prompts are strings
            prompts = [str(p) if not isinstance(p, str) else p for p in prompts]
            logger.info(f"Generated {len(prompts)} image prompts")
            return prompts
        except (json.JSONDecodeError, AttributeError, TypeError) as exc:
            logger.error(f"Error parsing image prompts response: {exc}")
            return []
    
    def _generate_tags(self, opportunity: TopicOpportunity) -> List[str]:
        """Generate blog tags/labels"""
        tags = opportunity.keywords.copy()
        
        # Add niche-specific tags
        niche_tags = self.blog_niche.split('/')
        tags.extend(niche_tags)
        
        # Add trend tags if applicable
        if opportunity.trend == "rising":
            tags.append("trending")
        
        # Remove duplicates and limit to 10
        tags = list(set(tags))[:10]
        
        return tags
    
    def optimize_content_for_seo(self, blog_post: BlogPost) -> BlogPost:
        """Further optimize content for SEO"""
        logger.info("Optimizing content for SEO...")
        
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model_seo,
                max_tokens=max(config.max_tokens_seo, 3000),
                messages=[
                {
                    "role": "system",
                    "content": "You are an experienced technical editor. Improve clarity, usefulness, accuracy, and structure while preserving HTML and technical meaning. Never add unsupported facts or citations. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": f"""Edit this complete blog article for usefulness and readability:

Title: {blog_post.title}
Keywords: {', '.join(blog_post.keywords)}
Meta Description: {blog_post.meta_description}

Content HTML:
{blog_post.content[:18000]}

Improve vague or repetitive passages, make steps/examples concrete, preserve useful details, all image/link markers, and the exact CatchyBytes YouTube subscription link, use concise paragraphs and a logical H2/H3 structure, and do not keyword-stuff. Keep code escaped inside pre/code blocks. Return JSON with title, content (HTML fragment), and meta_description. Do not include markdown fences."""
                }
                ],
                response_format={"type": "json_object"}
            )
        except Exception as exc:
            logger.warning(f"Editorial optimization request failed; keeping original content: {exc}")
            return blog_post
        try:
            raw = (response.choices[0].message.content or '').strip()
            raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.IGNORECASE)
            revised = json.loads(raw)
            body = str(revised.get('content') or '').strip()
            if len(re.sub(r'<[^>]+>', ' ', body).split()) >= 500:
                soup = BeautifulSoup(body, 'html.parser')
                for tag in soup.find_all(['script', 'style', 'iframe', 'object']):
                    tag.decompose()
                blog_post.content = ''.join(str(node) for node in soup.contents)
                blog_post.title = str(revised.get('title') or blog_post.title).strip()
                blog_post.meta_description = str(revised.get('meta_description') or blog_post.meta_description).strip()[:160]
            else:
                logger.warning("SEO edit was incomplete; keeping the original generated content")
        except (json.JSONDecodeError, ValueError, TypeError, AttributeError, IndexError) as exc:
            logger.warning(f"SEO edit could not be applied; keeping original content: {exc}")
        logger.info("Editorial optimization completed")
        return blog_post
    
    def generate_content_variations(self, blog_post: BlogPost, 
                                   num_variations: int = 2) -> List[BlogPost]:
        """Generate alternative versions of the blog post"""
        logger.info(f"Generating {num_variations} content variations...")
        
        variations = []
        for i in range(num_variations):
            response = self.client.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a creative content writer. Create engaging variations of blog posts."
                    },
                    {
                        "role": "user",
                        "content": f"""Create a variation of this blog post with a different angle or approach:

Original title: {blog_post.title}
Original content excerpt: {blog_post.content[:1500]}

Make it:
- More conversational/casual
- Or more data-driven/analytical
- Or more story-driven/narrative

Keep the same core topic and keywords but change the approach."""
                    }
                ]
            )
            
            # Create variation (simplified)
            variation = BlogPost(
                title=f"{blog_post.title} (Variation {i+1})",
                content=response.choices[0].message.content,
                meta_description=blog_post.meta_description,
                keywords=blog_post.keywords,
                tags=blog_post.tags,
                headings=blog_post.headings,
                image_prompts=blog_post.image_prompts,
                internal_links=blog_post.internal_links
            )
            variations.append(variation)
        
        logger.info(f"Generated {len(variations)} content variations")
        return variations
