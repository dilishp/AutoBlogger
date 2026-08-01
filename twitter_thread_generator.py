"""
Twitter Thread Generator - Converts blog content into viral Twitter threads
A focused utility that content creators will pay for to save time and increase engagement
"""
import logging
import json
from typing import Dict, List, Optional
from openai import OpenAI
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TwitterThreadGenerator:
    """Generates viral Twitter threads from blog content"""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.openai_api_key)
    
    def generate_thread(self, blog_title: str, blog_content: str, 
                       target_audience: str = "general") -> Dict:
        """Generate a complete Twitter thread from blog content"""
        logger.info(f"Generating Twitter thread for: {blog_title}")
        
        thread_data = {
            'hook': self._generate_viral_hook(blog_title, blog_content),
            'tweets': self._generate_thread_tweets(blog_title, blog_content, target_audience),
            'cta': self._generate_cta(blog_title),
            'hashtags': self._generate_hashtags(blog_title, blog_content),
            'thread_structure': self._analyze_thread_structure(blog_title, blog_content),
            'engagement_tips': self._generate_engagement_tips()
        }
        
        # Validate thread quality
        quality_score = self._validate_thread_quality(thread_data)
        thread_data['quality_score'] = quality_score
        logger.info(f"Thread quality score: {quality_score}/100")
        
        return thread_data
    
    def _generate_viral_hook(self, blog_title: str, blog_content: str) -> str:
        """Generate a viral hook for the first tweet"""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at writing viral Twitter hooks. Your hooks:
- Start with powerful statements or questions
- Create immediate curiosity or urgency
- Use numbers and specific results
- Are under 280 characters
- Make people want to read the entire thread"""
                    },
                    {
                        "role": "user",
                        "content": f"""Write a viral Twitter hook for a thread about: {blog_title}

Blog content: {blog_content[:500]}...

Requirements:
- Maximum 280 characters
- Create immediate curiosity
- Include a number or specific result
- Make it impossible to scroll past
- Use power words and emotional triggers

Return ONLY the hook, nothing else."""
                    }
                ]
            )
            
            hook = response.choices[0].message.content.strip()
            # Ensure it's under 280 characters
            if len(hook) > 280:
                hook = hook[:277] + "..."
            return hook
        except Exception as e:
            logger.error(f"Error generating hook: {e}")
            return f"The secret to {blog_title} will change how you think forever 🧵"
    
    def _generate_thread_tweets(self, blog_title: str, blog_content: str, 
                               target_audience: str) -> List[Dict]:
        """Generate individual tweets for the thread"""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an expert at creating viral Twitter threads. Your tweets:
- Each tells a complete thought but connects to the next
- Use simple, punchy language
- Include specific examples and data
- End with teasers for the next tweet
- Are under 280 characters each
- Use emojis strategically (1-2 per tweet max)
- Include line breaks for readability
- Target audience: {target_audience}"""
                    },
                    {
                        "role": "user",
                        "content": f"""Create a viral Twitter thread (8-12 tweets) about: {blog_title}

Blog content: {blog_content}

Requirements:
- 8-12 tweets total
- Each tweet under 280 characters
- Each tweet should be a complete thought
- Include specific examples, data, or actionable tips
- Use 1-2 emojis per tweet maximum
- End tweets 2-11 with teasers for the next tweet
- Final tweet should have a strong conclusion
- Focus on actionable value, not fluff
- Make it shareable and quotable

Return in this JSON format:
{{
  "tweets": [
    {{
      "number": 1,
      "content": "tweet content here",
      "character_count": 123
    }}
  ]
}}"""
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            
            tweets = result.get('tweets', [])
            
            # Validate each tweet
            validated_tweets = []
            for tweet in tweets:
                tweet_content = tweet.get('content', '')
                if len(tweet_content) > 280:
                    tweet_content = tweet_content[:277] + "..."
                    logger.warning(f"Tweet {tweet.get('number')} truncated to 280 chars")
                
                validated_tweets.append({
                    'number': tweet.get('number', len(validated_tweets) + 1),
                    'content': tweet_content,
                    'character_count': len(tweet_content)
                })
            
            logger.info(f"Generated {len(validated_tweets)} tweets")
            return validated_tweets
            
        except Exception as e:
            logger.error(f"Error generating thread tweets: {e}")
            return self._generate_fallback_tweets(blog_title)
    
    def _generate_fallback_tweets(self, blog_title: str) -> List[Dict]:
        """Generate fallback tweets if AI generation fails"""
        return [
            {'number': 1, 'content': f"{blog_title} - Here's what nobody tells you:", 'character_count': 50},
            {'number': 2, 'content': "Most people get this completely wrong 🧵", 'character_count': 45},
            {'number': 3, 'content': "Let me explain why this matters...", 'character_count': 35},
        ]
    
    def _generate_cta(self, blog_title: str) -> str:
        """Generate a compelling call-to-action"""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at writing Twitter CTAs that drive engagement. Your CTAs are specific, actionable, and create urgency."
                    },
                    {
                        "role": "user",
                        "content": f"""Write a compelling CTA for a Twitter thread about: {blog_title}

The CTA should:
- Be under 280 characters
- Ask for a specific action (retweet, comment, follow)
- Create urgency or FOMO
- Be authentic and not spammy
- Include relevant emoji

Return ONLY the CTA, nothing else."""
                    }
                ]
            )
            
            cta = response.choices[0].message.content.strip()
            if len(cta) > 280:
                cta = cta[:277] + "..."
            return cta
        except Exception as e:
            logger.error(f"Error generating CTA: {e}")
            return "Retweet if this helped you 🔥 Follow for more threads like this"
    
    def _generate_hashtags(self, blog_title: str, blog_content: str) -> List[str]:
        """Generate relevant hashtags for the thread"""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at Twitter hashtag research. You generate high-performing, relevant hashtags that increase discoverability."
                    },
                    {
                        "role": "user",
                    "content": f"""Generate 5-8 relevant hashtags for a Twitter thread about: {blog_title}

Blog content: {blog_content[:300]}...

Requirements:
- 5-8 hashtags total
- Mix of broad and niche hashtags
- No more than 2 trending hashtags
- Relevant to the specific topic
- Not spammy or overused
- Return as a comma-separated list only"""
                    }
                ]
            )
            
            hashtags_str = response.choices[0].message.content.strip()
            hashtags = [tag.strip() for tag in hashtags_str.split(',')]
            return hashtags[:8]  # Limit to 8 hashtags
        except Exception as e:
            logger.error(f"Error generating hashtags: {e}")
            return ["#thread", "#tips", "#growth"]
    
    def _analyze_thread_structure(self, blog_title: str, blog_content: str) -> Dict:
        """Analyze and suggest the optimal thread structure"""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at Twitter thread structure and storytelling."
                    },
                    {
                        "role": "user",
                        "content": f"""Analyze the optimal thread structure for a thread about: {blog_title}

Blog content: {blog_content[:500]}...

Provide:
1. Recommended number of tweets (8-15)
2. Key points to cover in order
3. Best storytelling approach (problem-solution, listicle, case study, etc.)
4. Where to place the hook
5. Where to place the CTA

Return in this JSON format:
{{
  "recommended_length": 10,
  "storytelling_approach": "problem-solution",
  "key_points": ["point 1", "point 2"],
  "hook_position": "first_tweet",
  "cta_position": "last_tweet"
}}"""
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error analyzing thread structure: {e}")
            return {
                "recommended_length": 10,
                "storytelling_approach": "problem-solution",
                "key_points": ["Introduction", "Main points", "Conclusion"],
                "hook_position": "first_tweet",
                "cta_position": "last_tweet"
            }
    
    def _generate_engagement_tips(self) -> List[str]:
        """Generate tips for maximizing thread engagement"""
        return [
            "Post your thread between 8 AM - 10 AM or 7 PM - 9 PM for maximum visibility",
            "Reply to every comment in the first hour to boost algorithmic reach",
            "Pin your hook tweet to keep it visible as people scroll through",
            "Add 2-3 relevant threads in the comments as 'related reading'",
            "DM the thread to 10-15 relevant people in your niche",
            "Turn your thread into a blog post for repurposing",
            "Create a graphic summary of the thread for Instagram",
            "Update your thread with new insights over time to keep it relevant"
        ]
    
    def _validate_thread_quality(self, thread_data: Dict) -> int:
        """Validate thread quality and return a score out of 100"""
        score = 0
        max_score = 100
        
        # Hook quality (20 points)
        hook = thread_data.get('hook', '')
        if len(hook) > 50 and len(hook) < 280:
            score += 20
        elif len(hook) > 30:
            score += 10
        
        # Tweet count and quality (40 points)
        tweets = thread_data.get('tweets', [])
        if 8 <= len(tweets) <= 15:
            score += 20
        elif len(tweets) >= 5:
            score += 10
        
        # Check if all tweets are under 280 chars
        valid_tweets = sum(1 for tweet in tweets if tweet.get('character_count', 0) <= 280)
        if valid_tweets == len(tweets):
            score += 20
        elif valid_tweets >= len(tweets) * 0.8:
            score += 10
        
        # CTA quality (15 points)
        cta = thread_data.get('cta', '')
        if len(cta) > 50 and len(cta) < 280:
            score += 15
        elif len(cta) > 30:
            score += 8
        
        # Hashtag quality (15 points)
        hashtags = thread_data.get('hashtags', [])
        if 5 <= len(hashtags) <= 8:
            score += 15
        elif len(hashtags) >= 3:
            score += 8
        
        # Engagement tips (10 points)
        tips = thread_data.get('engagement_tips', [])
        if len(tips) >= 5:
            score += 10
        elif len(tips) >= 3:
            score += 5
        
        return min(score, max_score)
    
    def export_thread(self, thread_data: Dict, output_file: str) -> bool:
        """Export thread data to various formats"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(thread_data, f, indent=2)
            logger.info(f"Thread exported to: {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting thread: {e}")
            return False
    
    def generate_copy_paste_format(self, thread_data: Dict) -> str:
        """Generate a copy-paste friendly format for Twitter"""
        output = []
        
        # Hook
        output.append(f"🧵 THREAD\n\n{thread_data['hook']}\n")
        
        # Tweets
        for tweet in thread_data['tweets']:
            output.append(f"{tweet['number']}/{len(thread_data['tweets'])} {tweet['content']}\n")
        
        # CTA
        output.append(f"\n{thread_data['cta']}")
        
        # Hashtags
        output.append(f"\n\n{' '.join(thread_data['hashtags'])}")
        
        return '\n'.join(output)


def main():
    """Test the Twitter thread generator"""
    generator = TwitterThreadGenerator()
    
    # Example usage
    blog_title = "How to 10x Your Productivity with These 5 Simple Habits"
    blog_content = """
    Productivity isn't about working harder - it's about working smarter. 
    After studying 100+ high performers, I found 5 habits that consistently appear:
    
    1. Time blocking - Schedule your day in focused blocks
    2. The 2-minute rule - If it takes less than 2 minutes, do it now
    3. Morning routine - Start with intention, not reaction
    4. Deep work sessions - Eliminate distractions for focus time
    5. Weekly review - Plan your week before it starts
    
    These habits compound over time. Start with one, master it, then add another.
    """
    
    thread_data = generator.generate_thread(blog_title, blog_content)
    
    print("=== Generated Twitter Thread ===")
    print(generator.generate_copy_paste_format(thread_data))
    
    print("\n=== Thread Quality Score ===")
    print(f"{thread_data['quality_score']}/100")


if __name__ == "__main__":
    main()
