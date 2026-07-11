"""
SEO research module for discovering high-demand, low-competition topics
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from openai import OpenAI
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TopicOpportunity:
    """Represents a potential blog topic with SEO metrics"""
    topic: str
    keywords: List[str]
    search_volume: int
    difficulty: int  # 0-100 scale
    opportunity_score: float
    trend: str  # "rising", "stable", "declining"
    suggested_title: str
    content_outline: List[str]


class SEOResearcher:
    """Researches SEO opportunities using AI and external APIs"""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.openai_api_key)
        self.blog_niche = config.blog_niche
        self.target_audience = config.target_audience
    
    def analyze_existing_content(self, posts: List[Dict]) -> Dict:
        """Analyze existing blog content to understand current focus"""
        logger.info("Analyzing existing blog content...")
        
        # Extract topics and keywords from existing posts
        topics = []
        all_content = []
        
        for post in posts:
            title = post.get('title', '')
            content = post.get('content', '')
            labels = post.get('labels', [])
            
            topics.append({
                'title': title,
                'labels': labels,
                'url': post.get('url', '')
            })
            all_content.append(f"{title}\n{content}")
        
        # Use AI to analyze content themes
        content_summary = "\n\n".join(all_content[:20])  # Limit to first 20 posts
        
        response = self.client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an SEO expert. Analyze blog content and identify themes, gaps, and opportunities."
                },
                {
                    "role": "user",
                    "content": f"""Analyze this blog content and provide:
1. Main themes and topics covered
2. Content gaps (what's missing)
3. Overlapping topics that could be consolidated
4. Audience interests based on content

Blog niche: {self.blog_niche}
Target audience: {self.target_audience}

Content sample:
{content_summary[:10000]}"""
                }
            ]
        )
        
        analysis = response.choices[0].message.content
        
        logger.info("Content analysis completed")
        return {
            'topics': topics,
            'analysis': analysis,
            'total_posts': len(posts)
        }
    
    def discover_topic_opportunities(self, content_analysis: Dict, 
                                    num_opportunities: int = 10) -> List[TopicOpportunity]:
        """Discover high-demand, low-competition topic opportunities"""
        logger.info("Discovering topic opportunities...")
        
        # Use AI to generate topic opportunities based on content analysis
        response = self.client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": """You are an SEO research expert. Identify high-demand, low-competition blog topics.
                    Always return valid JSON with an 'opportunities' array."""
                },
                {
                    "role": "user",
                    "content": f"""Suggest exactly {num_opportunities} blog topic opportunities for a {self.blog_niche} blog targeting {self.target_audience}.

Requirements:
1. High search demand topics
2. Low SEO difficulty
3. Fit the blog niche perfectly
4. Appeal to the target audience
5. Fill content gaps

For each topic, provide:
- topic: string (the main topic)
- keywords: array of 3-5 strings
- search_volume: number (0-100)
- difficulty: number (0-100, lower is easier)
- opportunity_score: number (0-100)
- trend: "rising" or "stable" or "declining"
- suggested_title: string (catchy blog title)
- content_outline: array of 5-7 strings

Return ONLY this JSON structure:
{{
  "opportunities": [
    {{
      "topic": "example topic",
      "keywords": ["keyword1", "keyword2"],
      "search_volume": 75,
      "difficulty": 30,
      "opportunity_score": 85,
      "trend": "rising",
      "suggested_title": "Example Title",
      "content_outline": ["point1", "point2"]
    }}
  ]
}}"""
                }
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        try:
            ai_response = response.choices[0].message.content
            logger.info(f"AI Response length: {len(ai_response)}")
            logger.info(f"AI Response preview: {ai_response[:500]}")
            
            data = json.loads(ai_response)
            opportunities = []
            
            # Handle different possible response structures
            items = []
            if 'opportunities' in data:
                items = data['opportunities']
            elif 'topics' in data:
                items = data['topics']
            elif isinstance(data, list):
                items = data
            else:
                # Try to create from the data directly
                items = [data] if 'topic' in data else []
            
            for item in items:
                try:
                    opportunity = TopicOpportunity(
                        topic=item.get('topic', 'Unknown Topic'),
                        keywords=item.get('keywords', []),
                        search_volume=item.get('search_volume', 50),
                        difficulty=item.get('difficulty', 50),
                        opportunity_score=item.get('opportunity_score', 70),
                        trend=item.get('trend', 'stable'),
                        suggested_title=item.get('suggested_title', item.get('topic', 'New Post')),
                        content_outline=item.get('content_outline', [])
                    )
                    opportunities.append(opportunity)
                except Exception as e:
                    logger.warning(f"Error parsing individual opportunity: {e}")
                    continue
            
            # Sort by opportunity score
            opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)
            
            logger.info(f"Found {len(opportunities)} topic opportunities")
            return opportunities
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Raw response: {response.choices[0].message.content[:1000]}")
            return self._get_fallback_opportunities(num_opportunities)
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            return self._get_fallback_opportunities(num_opportunities)
    
    def _get_fallback_opportunities(self, num_opportunities: int) -> List[TopicOpportunity]:
        """Generate fallback topic opportunities when AI fails"""
        logger.info("Using fallback topic opportunities")
        
        fallback_topics = [
            {
                "topic": "Clean Code Principles",
                "keywords": ["clean code", "software quality", "code refactoring", "programming best practices"],
                "search_volume": 75,
                "difficulty": 35,
                "opportunity_score": 85,
                "trend": "stable",
                "suggested_title": "Clean Code Principles Every Developer Should Know",
                "content_outline": ["What is clean code", "Naming conventions", "Functions and methods", "Comments and documentation", "Error handling", "Refactoring techniques"]
            },
            {
                "topic": "API Design Best Practices",
                "keywords": ["API design", "REST API", "API development", "software architecture"],
                "search_volume": 65,
                "difficulty": 40,
                "opportunity_score": 80,
                "trend": "rising",
                "suggested_title": "API Design Best Practices for Modern Applications",
                "content_outline": ["REST vs GraphQL", "API versioning", "Authentication methods", "Error handling", "Rate limiting", "Documentation standards"]
            },
            {
                "topic": "Debugging Techniques",
                "keywords": ["debugging", "troubleshooting", "software debugging", "development tools"],
                "search_volume": 70,
                "difficulty": 30,
                "opportunity_score": 82,
                "trend": "stable",
                "suggested_title": "Advanced Debugging Techniques for Developers",
                "content_outline": ["Debugging mindset", "Logging strategies", "Breakpoint mastery", "Memory debugging", "Performance profiling", "Remote debugging"]
            },
            {
                "topic": "Microservices Architecture",
                "keywords": ["microservices", "software architecture", "distributed systems", "system design"],
                "search_volume": 80,
                "difficulty": 45,
                "opportunity_score": 78,
                "trend": "rising",
                "suggested_title": "Microservices Architecture: A Practical Guide",
                "content_outline": ["Monolith vs microservices", "Service decomposition", "Communication patterns", "Data management", "Deployment strategies", "Monitoring and observability"]
            },
            {
                "topic": "Testing Strategies",
                "keywords": ["software testing", "unit testing", "integration testing", "test automation"],
                "search_volume": 60,
                "difficulty": 38,
                "opportunity_score": 76,
                "trend": "stable",
                "suggested_title": "Comprehensive Testing Strategies for Software Projects",
                "content_outline": ["Testing pyramid", "Unit testing best practices", "Integration testing", "End-to-end testing", "Test-driven development", "Continuous testing"]
            }
        ]
        
        opportunities = []
        for i, topic_data in enumerate(fallback_topics[:num_opportunities]):
            opportunity = TopicOpportunity(
                topic=topic_data["topic"],
                keywords=topic_data["keywords"],
                search_volume=topic_data["search_volume"],
                difficulty=topic_data["difficulty"],
                opportunity_score=topic_data["opportunity_score"],
                trend=topic_data["trend"],
                suggested_title=topic_data["suggested_title"],
                content_outline=topic_data["content_outline"]
            )
            opportunities.append(opportunity)
        
        logger.info(f"Generated {len(opportunities)} fallback opportunities")
        return opportunities
    
    def generate_seo_keywords(self, topic: str, existing_keywords: List[str]) -> Dict:
        """Generate SEO-friendly keywords for a topic"""
        logger.info(f"Generating SEO keywords for topic: {topic}")
        
        response = self.client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an SEO keyword specialist. Generate relevant, high-value keywords."
                },
                {
                    "role": "user",
                    "content": f"""Generate SEO keywords for the topic: "{topic}"

Blog niche: {self.blog_niche}
Target audience: {self.target_audience}
Existing keywords to avoid: {', '.join(existing_keywords[:20])}

Provide:
1. Primary keyword (main focus)
2. Secondary keywords (5-7 related terms)
3. Long-tail keywords (5-7 specific phrases)
4. LSI keywords (5-7 latent semantic indexing terms)
5. Negative keywords (terms to avoid)

Return as JSON."""
                }
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            logger.error("Error parsing keyword response")
            return {}
    
    def analyze_competitors(self, topic: str) -> List[Dict]:
        """Analyze competitor content for a given topic"""
        logger.info(f"Analyzing competitors for topic: {topic}")
        
        response = self.client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a competitive analysis expert. Identify top content and gaps."
                },
                {
                    "role": "user",
                    "content": f"""For the topic "{topic}" in the {self.blog_niche} niche:

1. Identify what type of content ranks well
2. Find content gaps (what's missing from top results)
3. Suggest unique angles or perspectives
4. Recommend content format (how-to, listicle, guide, etc.)
5. Suggest ideal word count and depth

Provide analysis as structured JSON."""
                }
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            logger.error("Error parsing competitor analysis")
            return {}
    
    def get_trending_topics(self) -> List[str]:
        """Get trending topics in the blog's niche"""
        logger.info("Fetching trending topics...")
        
        response = self.client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a trend-spotting expert. Identify trending topics in specific niches."
                },
                {
                    "role": "user",
                    "content": f"""Identify 10 trending topics in the {self.blog_niche} niche that would appeal to {self.target_audience}.

Focus on:
- Recent developments
- Seasonal relevance
- Emerging problems
- Popular solutions

Return as a simple list."""
                }
            ],
        )
        
        topics = response.choices[0].message.content.split('\n')
        topics = [t.strip().lstrip('- ').strip('*').strip() for t in topics if t.strip()]
        
        logger.info(f"Found {len(topics)} trending topics")
        return topics
