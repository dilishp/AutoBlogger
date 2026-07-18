"""
Content generation engine with SEO optimization
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
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
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an elite content writer and SEO specialist specializing in {self.blog_niche}. 
                    You write engaging, well-structured blog posts that are optimized for search engines and provide genuine value to {self.target_audience}.
                    
                    Your writing style:
                    - Authoritative yet accessible
                    - Data-driven with specific examples
                    - Action-oriented with clear takeaways
                    - Current with industry trends and best practices
                    - Focused on solving real problems
                    
                    Blog niche: {self.blog_niche}
                    Target audience: {self.target_audience}
                    Blog domain: {self.blog_domain}
                    
                    Quality standards:
                    - Include specific statistics, metrics, or research findings
                    - Use real-world examples and case studies
                    - Provide actionable insights readers can implement immediately
                    - Avoid fluff and generic advice
                    - Include unique perspectives or contrarian views when appropriate
                    - Reference industry leaders or authoritative sources"""
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
2. Write 800-1200 words of high-quality content (shorter overview format)
3. Include 2-3 specific statistics, research findings, or data points
4. Include at least 1 real-world example or case study
5. Format code examples using HTML: <code> for inline code, <pre><code> for multi-line code blocks
6. Use proper HTML formatting throughout (paragraphs, headings, lists)
7. Include [IMAGE: description] markers where images should be inserted
8. Include a compelling introduction that hooks the reader with a surprising fact or statistic
9. Use clear H2 and H3 headings for structure
10. Include practical examples and actionable advice
11. Write in a conversational yet professional tone
12. Include a strong conclusion with call-to-action to the digital product
13. Naturally incorporate the primary and secondary keywords
14. Add placeholder markers for internal links using SPECIFIC, DESCRIPTIVE topic names like: [LINK: API design best practices], [LINK: debugging techniques], [LINK: microservices architecture] - NOT generic terms like "related topic"
15. Focus on overview and key concepts - detailed implementation will be in the digital product
16. Include a clear call-to-action: "Get the complete guide with templates and checklists in our digital product"
17. Add a unique insight or perspective that differentiates this from similar content

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
        
        import json
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing content response: {e}")
            return {
                'title': opportunity.suggested_title,
                'content': '',
                'meta_description': '',
                'headings': {'h2': [], 'h3': []}
            }
    
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
        
        response = self.client.chat.completions.create(
            model=config.openai_model,
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
        
        import json
        try:
            links = json.loads(response.choices[0].message.content).get('links', [])
            logger.info(f"Generated {len(links)} internal link opportunities")
            return links
        except json.JSONDecodeError:
            logger.error("Error parsing internal links response")
            return []
    
    def _generate_image_prompts(self, opportunity: TopicOpportunity,
                               content_data: Dict) -> List[str]:
        """Generate image prompts for the blog post"""
        logger.info("Generating image prompts...")
        
        response = self.client.chat.completions.create(
            model=config.openai_model,
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
        
        import json
        try:
            prompts = json.loads(response.choices[0].message.content).get('prompts', [])
            logger.info(f"Generated {len(prompts)} image prompts")
            return prompts
        except json.JSONDecodeError:
            logger.error("Error parsing image prompts response")
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
        
        response = self.client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an SEO optimization expert. Improve content for search engines."
                },
                {
                    "role": "user",
                    "content": f"""Optimize this blog content for SEO:

Title: {blog_post.title}
Keywords: {', '.join(blog_post.keywords)}
Meta Description: {blog_post.meta_description}

Content excerpt:
{blog_post.content[:3000]}

Optimize for:
1. Keyword density (2-3% for primary keyword)
2. Readability (short paragraphs, clear sentences)
3. Heading structure (H1, H2, H3 hierarchy)
4. Internal link placement
5. Image alt text suggestions
6. Schema markup suggestions

Return the optimized content and any specific recommendations."""
                }
            ]
        )
        
        # Apply optimizations (simplified - in production would parse and apply specific changes)
        logger.info("SEO optimization completed")
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
