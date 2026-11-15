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
1. Main themes and topics covered in the blog's configured niche
2. Content gaps in those themes
3. Overlapping topics that could be consolidated
4. Audience interests based on existing content and the configured target audience

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
                    "content": """You are an SEO research expert. Identify high-demand, low-competition blog topics that fit the supplied niche and audience.
                    Always return valid JSON with an 'opportunities' array."""
                },
                {
                    "role": "user",
                    "content": f"""Suggest exactly {num_opportunities} blog topic opportunities for a {self.blog_niche} blog targeting {self.target_audience}. Preferred post format: {config.blog_post_type}.

Requirements:
1. High search demand topics
2. Low SEO difficulty
3. Fit the configured blog niche and post type
4. Appeal to the configured target audience
5. Fill content gaps
6. Avoid unrelated topics; do not impose a narrower theme than the configured niche
7. Select formats and angles that suit the configured blog post type

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
            
            # Filter out DevOps/build topics
            devops_keywords = ['devops', 'ci/cd', 'docker', 'kubernetes', 'infrastructure', 'deployment', 'cloud', 'build', 'monitoring', 'github actions', 'jenkins', 'terraform', 'ansible', 'helm', 'istio', 'nginx', 'apache', 'server', 'hosting', 'vps', 'aws', 'azure', 'gcp', 'ec2', 's3', 'lambda', 'serverless']
            filtered_opportunities = []
            for opp in opportunities:
                topic_lower = opp.topic.lower()
                keywords_lower = ' '.join(opp.keywords).lower()
                title_lower = opp.suggested_title.lower()
                
                # Check if topic contains DevOps keywords
                is_devops = any(keyword in topic_lower or keyword in keywords_lower or keyword in title_lower 
                               for keyword in devops_keywords)
                
                if not is_devops:
                    filtered_opportunities.append(opp)
                else:
                    logger.warning(f"Filtered out DevOps topic: {opp.topic}")
            
            # Sort by opportunity score
            filtered_opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)
            
            logger.info(f"Found {len(filtered_opportunities)} topic opportunities (filtered from {len(opportunities)})")
            return filtered_opportunities
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Raw response: {response.choices[0].message.content[:1000]}")
            return self._get_fallback_opportunities(num_opportunities)
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            return self._get_fallback_opportunities(num_opportunities)
    
    def _get_fallback_opportunities(self, num_opportunities: int) -> List[TopicOpportunity]:
        """Create niche-aware fallback topics without assuming a fixed subject."""
        niche = self.blog_niche.strip() or "general"
        audience = self.target_audience.strip() or "general readers"
        post_type = config.blog_post_type.strip() or "informative guide"
        templates = [
            (f"A beginner's guide to {niche}", f"Understanding {niche}: A Beginner's Guide", [f"What {niche} means", "Core concepts", "A practical example", "Common questions", "Next steps"]),
            (f"Choosing the right approach to {niche}", f"How to Choose the Right Approach to {niche}", ["The decision to make", "Options to consider", "Comparison criteria", "Common tradeoffs", "A decision framework"]),
            (f"Common mistakes with {niche}", f"Common {niche} Mistakes and How to Avoid Them", ["Why mistakes happen", "Frequent pitfalls", "How to recognize them", "Practical fixes", "Prevention checklist"]),
            (f"Best practices for {niche}", f"{niche}: Practical Best Practices for {audience}", ["Goals and constraints", "Recommended practices", "Examples", "What to avoid", "A practical checklist"]),
        ]
        opportunities = []
        for topic, title, outline in templates[:max(0, num_opportunities)]:
            words = [word.strip('.,:') for word in topic.split() if len(word.strip('.,:')) > 3]
            opportunities.append(TopicOpportunity(
                topic=topic,
                keywords=list(dict.fromkeys([topic.lower(), *[word.lower() for word in words]]))[:5],
                search_volume=0,
                difficulty=50,
                opportunity_score=50,
                trend="stable",
                suggested_title=title,
                content_outline=outline,
            ))
        logger.info("Generated %d fallback opportunities for niche %s and format %s", len(opportunities), niche, post_type)
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
- Relevant developments and trends within the configured blog niche
- Emerging ideas, products, methods, or practices relevant to the audience
- Frequently asked questions and seasonal interests for the niche

Return as a simple list."""
                }
            ],
        )
        
        topics = response.choices[0].message.content.split('\n')
        topics = [t.strip().lstrip('- ').strip('*').strip() for t in topics if t.strip()]
        
        logger.info(f"Found {len(topics)} trending topics")
        return topics
