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
1. Main themes and topics covered (focus on programming/technical concepts)
2. Content gaps (what's missing in programming/technical topics)
3. Overlapping topics that could be consolidated
4. Audience interests based on content (software developers)

IMPORTANT: Ignore DevOps, CI/CD, Docker, Kubernetes, infrastructure, deployment, cloud services, build tools, monitoring tools topics. Focus ONLY on programming concepts, algorithms, data structures, programming languages, software engineering fundamentals.

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
                    CRITICAL: Focus ONLY on programming concepts, algorithms, data structures, programming languages, software engineering fundamentals, and technical concepts.
                    EXCLUDE: DevOps, CI/CD, Docker, Kubernetes, infrastructure, deployment, cloud services, build tools, monitoring tools, and any operational/deployment topics.
                    Always return valid JSON with an 'opportunities' array."""
                },
                {
                    "role": "user",
                    "content": f"""Suggest exactly {num_opportunities} blog topic opportunities for a {self.blog_niche} blog targeting {self.target_audience}.

Requirements:
1. High search demand topics
2. Low SEO difficulty
3. Fit the blog niche perfectly - PROGRAMMING CONCEPTS ONLY
4. Appeal to the target audience - SOFTWARE DEVELOPERS
5. Fill content gaps
6. EXCLUDE DevOps, CI/CD, Docker, Kubernetes, infrastructure, deployment, cloud services, build tools, monitoring tools
7. FOCUS ON: programming languages, algorithms, data structures, design patterns, software architecture, debugging techniques, code optimization, language features, frameworks concepts

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
        """Generate fallback topic opportunities when AI fails"""
        logger.info("Using fallback topic opportunities")
        
        fallback_topics = [
            {
                "topic": "Recursion Fundamentals",
                "keywords": ["recursion", "programming concepts", "algorithms", "computer science"],
                "search_volume": 78,
                "difficulty": 28,
                "opportunity_score": 88,
                "trend": "stable",
                "suggested_title": "Understanding Recursion: From Basics to Advanced Patterns",
                "content_outline": ["What is recursion", "Base case and recursive case", "Common recursion patterns", "Stack overflow prevention", "Real-world examples", "When to use recursion vs iteration"]
            },
            {
                "topic": "Algorithm Efficiency Analysis",
                "keywords": ["big o notation", "algorithm complexity", "time complexity", "space complexity"],
                "search_volume": 82,
                "difficulty": 32,
                "opportunity_score": 85,
                "trend": "rising",
                "suggested_title": "Big O Notation Explained: How to Analyze Algorithm Efficiency",
                "content_outline": ["Why algorithm efficiency matters", "Understanding Big O notation", "Common complexity classes", "Time vs space complexity", "Practical analysis examples", "Optimization strategies"]
            },
            {
                "topic": "Design Patterns Essentials",
                "keywords": ["design patterns", "software architecture", "object oriented", "software design"],
                "search_volume": 75,
                "difficulty": 35,
                "opportunity_score": 82,
                "trend": "stable",
                "suggested_title": "Design Patterns Every Developer Should Know: Singleton to Observer",
                "content_outline": ["What are design patterns", "Creational patterns", "Structural patterns", "Behavioral patterns", "When to use each pattern", "Real-world implementation examples"]
            },
            {
                "topic": "JavaScript Async Programming",
                "keywords": ["async await", "promises", "javascript concurrency", "event loop"],
                "search_volume": 80,
                "difficulty": 30,
                "opportunity_score": 86,
                "trend": "rising",
                "suggested_title": "Async/Await vs Promises: Modern JavaScript Concurrency",
                "content_outline": ["Synchronous vs asynchronous", "Promise fundamentals", "Async/await syntax", "Error handling", "Common pitfalls", "Performance considerations"]
            },
            {
                "topic": "Database Fundamentals",
                "keywords": ["database indexing", "sql vs nosql", "database optimization", "data structures"],
                "search_volume": 77,
                "difficulty": 33,
                "opportunity_score": 83,
                "trend": "stable",
                "suggested_title": "Database Indexing: Speed Up Your Queries Dramatically",
                "content_outline": ["Why indexing matters", "How database indexes work", "Types of indexes", "Query optimization", "When to index", "Performance impact"]
            },
            {
                "topic": "Python Decorators",
                "keywords": ["python decorators", "python metaprogramming", "python functions", "python advanced"],
                "search_volume": 72,
                "difficulty": 38,
                "opportunity_score": 80,
                "trend": "stable",
                "suggested_title": "Python Decorators: Simplify Your Code with Elegant Patterns",
                "content_outline": ["What are decorators", "Function decorators", "Class decorators", "Decorator with arguments", "Real-world use cases", "Best practices"]
            },
            {
                "topic": "TypeScript Generics",
                "keywords": ["typescript generics", "type safety", "typescript advanced", "generic programming"],
                "search_volume": 74,
                "difficulty": 36,
                "opportunity_score": 81,
                "trend": "rising",
                "suggested_title": "TypeScript Generics: Write Flexible, Type-Safe Code",
                "content_outline": ["Why generics matter", "Basic generic syntax", "Generic constraints", "Generic functions", "Generic classes", "Real-world examples"]
            },
            {
                "topic": "Hash Tables Deep Dive",
                "keywords": ["hash tables", "hashing", "data structures", "algorithm efficiency"],
                "search_volume": 70,
                "difficulty": 34,
                "opportunity_score": 79,
                "trend": "stable",
                "suggested_title": "Understanding Hash Tables: The Backbone of Fast Lookups",
                "content_outline": ["What is a hash table", "Hash functions", "Collision resolution", "Time complexity", "Implementation examples", "When to use hash tables"]
            },
            {
                "topic": "Binary Search Trees",
                "keywords": ["binary search trees", "bst", "tree data structures", "algorithms"],
                "search_volume": 68,
                "difficulty": 37,
                "opportunity_score": 78,
                "trend": "stable",
                "suggested_title": "Binary Search Trees: Efficient Data Organization Explained",
                "content_outline": ["What is a BST", "BST properties", "Insertion and deletion", "Traversal methods", "Time complexity analysis", "Real-world applications"]
            },
            {
                "topic": "REST vs GraphQL",
                "keywords": ["rest api", "graphql", "api design", "web development"],
                "search_volume": 76,
                "difficulty": 32,
                "opportunity_score": 84,
                "trend": "rising",
                "suggested_title": "REST vs GraphQL: Choosing the Right API Architecture",
                "content_outline": ["REST fundamentals", "GraphQL fundamentals", "Key differences", "When to use REST", "When to use GraphQL", "Migration strategies"]
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

IMPORTANT: Focus ONLY on programming concepts, algorithms, data structures, programming languages, software engineering fundamentals. Ignore DevOps, CI/CD, Docker, Kubernetes, infrastructure, deployment, cloud services, build tools, monitoring tools topics.

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

IMPORTANT: Focus ONLY on programming concepts, algorithms, data structures, programming languages, software engineering fundamentals. Ignore DevOps, CI/CD, Docker, Kubernetes, infrastructure, deployment, cloud services, build tools, monitoring tools topics.

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

CRITICAL: Focus ONLY on programming concepts, algorithms, data structures, programming languages, software engineering fundamentals, and technical concepts.
EXCLUDE: DevOps, CI/CD, Docker, Kubernetes, infrastructure, deployment, cloud services, build tools, monitoring tools, and any operational/deployment topics.

Focus on:
- Recent developments in programming languages and frameworks
- Emerging programming concepts and patterns
- Popular programming techniques and best practices
- New features in programming languages
- Software engineering methodologies
- Debugging and optimization techniques

Return as a simple list."""
                }
            ],
        )
        
        topics = response.choices[0].message.content.split('\n')
        topics = [t.strip().lstrip('- ').strip('*').strip() for t in topics if t.strip()]
        
        logger.info(f"Found {len(topics)} trending topics")
        return topics
