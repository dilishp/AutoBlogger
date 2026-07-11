"""
Social media post generator for LinkedIn, Facebook, and Twitter
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from openai import OpenAI
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SocialMediaPost:
    """Represents a social media post"""
    platform: str
    content: str
    hashtags: List[str]
    image_suggestion: Optional[str] = None
    character_count: int = 0


class SocialMediaGenerator:
    """Generates promotional posts for social media platforms"""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.openai_api_key)
        self.blog_domain = config.blog_domain
    
    def generate_all_platforms(self, blog_post: Dict) -> Dict[str, SocialMediaPost]:
        """Generate posts for all configured platforms"""
        logger.info("Generating social media posts for all platforms...")
        
        posts = {}
        
        # Generate for each platform
        posts['linkedin'] = self.generate_linkedin_post(blog_post)
        posts['facebook'] = self.generate_facebook_post(blog_post)
        posts['twitter'] = self.generate_twitter_post(blog_post)
        
        logger.info(f"Generated posts for {len(posts)} platforms")
        return posts
    
    def generate_linkedin_post(self, blog_post: Dict) -> SocialMediaPost:
        """Generate a LinkedIn promotional post"""
        logger.info("Generating LinkedIn post...")
        
        title = blog_post.get('title', '')
        content = blog_post.get('content', '')
        url = blog_post.get('url', f'https://{self.blog_domain}')
        
        # Extract key points
        key_points = self._extract_key_points(content)
        
        response = self.client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": """You are a LinkedIn content specialist. Write engaging, professional posts 
                    that drive engagement and clicks. LinkedIn posts should be conversational yet professional,
                    use proper formatting, and include clear calls-to-action."""
                },
                {
                    "role": "user",
                    "content": f"""Create a LinkedIn promotional post for this blog post:

Blog Title: {title}
Blog URL: {url}
Key Points:
{chr(10).join(f'- {point}' for point in key_points[:5])}

Requirements:
1. Hook readers in the first 2 lines
2. Share a personal insight or perspective
3. Include 3-5 key takeaways from the post
4. Use relevant emojis (but not excessive)
5. Add 5-7 relevant hashtags
6. Include clear call-to-action to read the full post
7. Keep under 3000 characters
8. Use line breaks for readability
9. Make it conversational and engaging

Return as JSON with:
- content (the post text)
- hashtags (array)
- character_count"""
                }
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        try:
            data = json.loads(response.choices[0].message.content)
            post = SocialMediaPost(
                platform='linkedin',
                content=data['content'],
                hashtags=data['hashtags'],
                character_count=data['character_count']
            )
            logger.info(f"LinkedIn post generated ({post.character_count} chars)")
            return post
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LinkedIn post: {e}")
            return SocialMediaPost(
                platform='linkedin',
                content=f"Check out my latest post: {title} {url}",
                hashtags=['#blog', '#newpost'],
                character_count=0
            )
    
    def generate_facebook_post(self, blog_post: Dict) -> SocialMediaPost:
        """Generate a Facebook promotional post"""
        logger.info("Generating Facebook post...")
        
        title = blog_post.get('title', '')
        content = blog_post.get('content', '')
        url = blog_post.get('url', f'https://{self.blog_domain}')
        
        key_points = self._extract_key_points(content)
        
        response = self.client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": """You are a Facebook content specialist. Write engaging, shareable posts 
                    that encourage likes, comments, and shares. Facebook posts should be friendly,
                    relatable, and include questions to drive engagement."""
                },
                {
                    "role": "user",
                    "content": f"""Create a Facebook promotional post for this blog post:

Blog Title: {title}
Blog URL: {url}
Key Points:
{chr(10).join(f'- {point}' for point in key_points[:5])}

Requirements:
1. Start with an engaging hook
2. Share the main value proposition
3. Ask a question to encourage comments
4. Use 3-5 relevant emojis
5. Add 5-10 relevant hashtags
6. Include clear call-to-action
7. Keep under 63206 characters (Facebook limit)
8. Make it conversational and friendly
9. Focus on benefits and value

Return as JSON with:
- content (the post text)
- hashtags (array)
- character_count"""
                }
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        try:
            data = json.loads(response.choices[0].message.content)
            post = SocialMediaPost(
                platform='facebook',
                content=data['content'],
                hashtags=data['hashtags'],
                character_count=data['character_count']
            )
            logger.info(f"Facebook post generated ({post.character_count} chars)")
            return post
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Facebook post: {e}")
            return SocialMediaPost(
                platform='facebook',
                content=f"Just published: {title} Read more at {url}",
                hashtags=['#blog', '#newpost'],
                character_count=0
            )
    
    def generate_twitter_post(self, blog_post: Dict) -> SocialMediaPost:
        """Generate a Twitter/X promotional post"""
        logger.info("Generating Twitter post...")
        
        title = blog_post.get('title', '')
        content = blog_post.get('content', '')
        url = blog_post.get('url', f'https://{self.blog_domain}')
        
        # Twitter has 280 character limit
        response = self.client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": """You are a Twitter/X content specialist. Write concise, engaging tweets
                    that drive clicks. Twitter threads should use thread format if needed."""
                },
                {
                    "role": "user",
                    "content": f"""Create a Twitter promotional post for this blog post:

Blog Title: {title}
Blog URL: {url}

Requirements:
1. Keep under 280 characters (including URL space)
2. Use 1-2 relevant hashtags
3. Include the URL
4. Make it punchy and engaging
5. Focus on the main benefit
6. Use 1-2 emojis max

Return as JSON with:
- content (the tweet text)
- hashtags (array)
- character_count"""
                }
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        try:
            data = json.loads(response.choices[0].message.content)
            post = SocialMediaPost(
                platform='twitter',
                content=data['content'],
                hashtags=data['hashtags'],
                character_count=data['character_count']
            )
            logger.info(f"Twitter post generated ({post.character_count} chars)")
            return post
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Twitter post: {e}")
            # Fallback: create simple tweet
            short_title = title[:50] + "..." if len(title) > 50 else title
            tweet = f"{short_title} {url}"
            post = SocialMediaPost(
                platform='twitter',
                content=tweet,
                hashtags=['#blog'],
                character_count=len(tweet)
            )
            return post
    
    def generate_twitter_thread(self, blog_post: Dict, num_tweets: int = 5) -> List[SocialMediaPost]:
        """Generate a Twitter thread for longer content"""
        logger.info(f"Generating Twitter thread with {num_tweets} tweets...")
        
        title = blog_post.get('title', '')
        content = blog_post.get('content', '')
        url = blog_post.get('url', f'https://{self.blog_domain}')
        
        key_points = self._extract_key_points(content)
        
        response = self.client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": """You are a Twitter thread specialist. Create engaging threads that tell a story
                    and drive engagement. Each tweet should be under 280 characters."""
                },
                {
                    "role": "user",
                    "content": f"""Create a Twitter thread of {num_tweets} tweets for this blog post:

Blog Title: {title}
Blog URL: {url}
Key Points:
{chr(10).join(f'- {point}' for point in key_points[:10])}

Requirements:
1. Each tweet under 280 characters
2. Thread format (1/{num_tweets}, 2/{num_tweets}, etc.)
3. First tweet hooks readers
4. Middle tweets provide value
5. Last tweet includes CTA and URL
6. Use relevant hashtags in last tweet
7. Make it engaging and valuable

Return as JSON array of tweets with:
- content (tweet text)
- tweet_number (position in thread)
- character_count"""
                }
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        try:
            data = json.loads(response.choices[0].message.content)
            tweets = []
            
            for tweet_data in data.get('tweets', []):
                tweet = SocialMediaPost(
                    platform='twitter',
                    content=tweet_data['content'],
                    hashtags=[],
                    character_count=tweet_data['character_count']
                )
                tweets.append(tweet)
            
            logger.info(f"Twitter thread generated with {len(tweets)} tweets")
            return tweets
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Twitter thread: {e}")
            return []
    
    def _extract_key_points(self, content: str, max_points: int = 10) -> List[str]:
        """Extract key points from blog content"""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Extract the key points from content as a simple list."
                    },
                    {
                        "role": "user",
                        "content": f"Extract {max_points} key points from this content:\n\n{content[:3000]}"
                    }
                ]
            )
            
            points = response.choices[0].message.content.split('\n')
            points = [p.strip().lstrip('- ').strip('*').strip() for p in points if p.strip()]
            return points[:max_points]
        
        except Exception as e:
            logger.error(f"Error extracting key points: {e}")
            return []
    
    def schedule_posts(self, posts: Dict[str, SocialMediaPost], 
                      schedule_times: Optional[Dict[str, str]] = None) -> Dict:
        """Generate scheduling recommendations for social media posts"""
        logger.info("Generating post schedule recommendations...")
        
        if schedule_times is None:
            # Default optimal times
            schedule_times = {
                'linkedin': 'Tuesday 10:00 AM',
                'facebook': 'Wednesday 12:00 PM',
                'twitter': 'Thursday 9:00 AM'
            }
        
        schedule = {}
        
        for platform, post in posts.items():
            schedule[platform] = {
                'content': post.content,
                'hashtags': post.hashtags,
                'scheduled_time': schedule_times.get(platform, 'TBD'),
                'character_count': post.character_count,
                'status': 'ready_to_post'
            }
        
        logger.info("Schedule recommendations generated")
        return schedule
