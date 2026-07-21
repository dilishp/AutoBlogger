"""
Main Blog AI Agent - Orchestrates the entire blog content creation and promotion workflow
"""
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from blogger_client import BloggerClient
from seo_researcher import SEOResearcher, TopicOpportunity
from content_generator import ContentGenerator, BlogPost
from image_generator import ImageGenerator
from internal_linker import InternalLinker
from social_media_generator import SocialMediaGenerator
from blogger_publisher import BloggerPublisher
from digital_product_generator import DigitalProductGenerator
from gumroad_client import GumroadClient
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlogAIAgent:
    """Main AI agent for automated blog content creation and promotion"""
    
    def __init__(self):
        logger.info("Initializing Blog AI Agent...")
        
        # Initialize all components
        self.blogger_client = BloggerClient()
        self.seo_researcher = SEOResearcher()
        self.content_generator = ContentGenerator()
        self.image_generator = ImageGenerator()
        self.internal_linker = InternalLinker()
        self.social_media_generator = SocialMediaGenerator()
        self.blogger_publisher = BloggerPublisher()
        self.digital_product_generator = DigitalProductGenerator()
        self.gumroad_client = GumroadClient()
        
        # Cache for blog content
        self.existing_posts = []
        self.content_index = {}
        
        logger.info("Blog AI Agent initialized successfully")
    
    def run_full_workflow(self, num_topics: int = 1, 
                         generate_images: bool = True,
                         publish_immediately: bool = False) -> Dict:
        """Run the complete blog creation workflow"""
        logger.info("=" * 60)
        logger.info("Starting Full Blog Creation Workflow")
        logger.info("=" * 60)
        
        workflow_result = {
            'start_time': datetime.now().isoformat(),
            'steps_completed': [],
            'posts_created': [],
            'errors': []
        }
        
        try:
            # Step 1: Fetch existing content
            logger.info("Step 1: Fetching existing blog content...")
            self.existing_posts = self.blogger_client.get_all_posts()
            self.content_index = self.internal_linker.build_content_index(self.existing_posts)
            workflow_result['steps_completed'].append('content_fetch')
            logger.info(f"Fetched {len(self.existing_posts)} existing posts")
            
            # Step 2: Analyze content and find opportunities
            logger.info("Step 2: Analyzing content and finding opportunities...")
            content_analysis = self.seo_researcher.analyze_existing_content(self.existing_posts)
            opportunities = self.seo_researcher.discover_topic_opportunities(
                content_analysis, 
                num_opportunities=num_topics
            )
            workflow_result['steps_completed'].append('seo_research')
            logger.info(f"Found {len(opportunities)} topic opportunities")
            
            # Process each opportunity
            for i, opportunity in enumerate(opportunities[:num_topics]):
                logger.info(f"\nProcessing topic {i+1}/{num_topics}: {opportunity.topic}")
                
                post_result = self._process_single_opportunity(
                    opportunity,
                    generate_images,
                    publish_immediately
                )
                
                workflow_result['posts_created'].append(post_result)
            
            workflow_result['end_time'] = datetime.now().isoformat()
            workflow_result['status'] = 'completed'
            
            logger.info("=" * 60)
            logger.info("Workflow Completed Successfully")
            logger.info("=" * 60)
            
            return workflow_result
        
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            workflow_result['errors'].append(str(e))
            workflow_result['status'] = 'failed'
            workflow_result['end_time'] = datetime.now().isoformat()
            return workflow_result
    
    def _process_single_opportunity(self, opportunity: TopicOpportunity,
                                   generate_images: bool,
                                   publish_immediately: bool) -> Dict:
        """Process a single topic opportunity"""
        post_result = {
            'topic': opportunity.topic,
            'title': opportunity.suggested_title,
            'steps': [],
            'success': False
        }
        
        try:
            # Step 1: Generate content
            logger.info("  - Generating blog content...")
            competitor_analysis = self.seo_researcher.analyze_competitors(opportunity.topic)
            blog_post = self.content_generator.generate_blog_post(
                opportunity,
                self.existing_posts,
                competitor_analysis
            )
            post_result['steps'].append('content_generation')
            
            # Step 2: Optimize for SEO
            logger.info("  - Optimizing content for SEO...")
            blog_post = self.content_generator.optimize_content_for_seo(blog_post)
            post_result['steps'].append('seo_optimization')
            
            # Step 3: Generate digital product
            product_result = None
            if self.gumroad_client.enabled:
                logger.info("  - Generating digital product...")
                try:
                    # Determine demand level from opportunity
                    topic_demand = 'medium'
                    if hasattr(opportunity, 'competition') and hasattr(opportunity, 'search_volume'):
                        if opportunity.competition < 30 and opportunity.search_volume > 1000:
                            topic_demand = 'high'
                        elif opportunity.competition < 20 and opportunity.search_volume > 2000:
                            topic_demand = 'very_high'
                        elif opportunity.competition > 70:
                            topic_demand = 'low'
                    
                    product_data = self.digital_product_generator.generate_product(
                        blog_post.title,
                        blog_post.content,
                        blog_post.tags,
                        config.blog_niche,
                        topic_demand
                    )
                    
                    # Save product files
                    saved_product = self.digital_product_generator.save_product_files(
                        product_data,
                        blog_post.title
                    )
                    
                    # Upload to Gumroad
                    gumroad_result = self.gumroad_client.create_product(
                        product_data['title'],
                        product_data['description'],
                        product_data['pricing'],
                        tags=blog_post.tags
                    )
                    
                    if gumroad_result:
                        product_id = gumroad_result.get('product', {}).get('id')
                        product_url = self.gumroad_client.get_product_url(product_id)
                        
                        # Add product link to blog content
                        if product_url:
                            product_cta = f'\n\n<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin: 30px 0;">\n<h3 style="margin: 0 0 10px 0;">🚀 Get the Complete Guide</h3>\n<p style="margin: 0 0 15px 0;">Want the full implementation details, templates, and checklists?</p>\n<a href="{product_url}" style="display: inline-block; background: white; color: #667eea; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Get the Digital Product</a>\n</div>'
                            blog_post.content += product_cta
                            logger.info(f"Added Gumroad product link to blog: {product_url}")
                    
                    product_result = {
                        'success': True,
                        'folder': saved_product.get('folder', ''),
                        'files': saved_product.get('files', {}),
                        'gumroad_url': product_url if gumroad_result else None
                    }
                    post_result['steps'].append('digital_product_generation')
                    post_result['digital_product'] = product_result
                    
                except Exception as e:
                    logger.error(f"Digital product generation failed: {e}")
                    product_result = {'success': False, 'error': str(e)}
            else:
                logger.info("  ℹ Gumroad not configured, skipping digital product generation")
            
            # Step 4: Generate images
            image_paths = []
            if generate_images:
                logger.info("  - Generating images...")
                image_paths = self.image_generator.generate_images(
                    blog_post.image_prompts,
                    use_dalle=True
                )
                post_result['steps'].append('image_generation')
                post_result['images'] = image_paths
                
                if not image_paths:
                    logger.info("  ℹ Image generation failed or not available - will use placeholder images")
                else:
                    logger.info(f"  ✓ Generated {len(image_paths)} images")
            
            # Step 5: Apply internal links
            logger.info("  - Applying internal links...")
            linking_opportunities = self.internal_linker.find_linking_opportunities(
                {'title': blog_post.title, 'content': blog_post.content},
                self.content_index
            )
            
            # Apply links using the InternalLink objects directly
            if linking_opportunities:
                blog_post.content = self.internal_linker.apply_internal_links(
                    blog_post.content,
                    linking_opportunities
                )
                
                # Convert to dict format for storage
                blog_post.internal_links = []
                for link in linking_opportunities:
                    blog_post.internal_links.append({
                        'anchor_text': link.anchor_text,
                        'target_url': link.target_url,
                        'target_title': link.target_title
                    })
                
                logger.info(f"  ✓ Applied {len(blog_post.internal_links)} internal links")
            else:
                blog_post.internal_links = []
                logger.info("  ℹ No internal link opportunities found")
            
            post_result['steps'].append('internal_linking')
            post_result['internal_links'] = len(blog_post.internal_links)
            
            # Step 6: Analyze font style from existing posts
            logger.info("  - Analyzing font style from existing posts...")
            font_style = self.blogger_publisher.analyze_font_style(self.existing_posts)
            logger.info(f"  ✓ Using font style: {font_style}")
            
            # Step 7: Publish to Blogger
            logger.info("  - Publishing to Blogger...")
            publish_result = self.blogger_publisher.publish_blog_post(
                blog_post,
                as_draft=not publish_immediately,
                font_style=font_style,
                image_paths=image_paths,
                content_index=self.content_index
            )
            post_result['steps'].append('publishing')
            post_result['publish_result'] = publish_result
            
            if publish_result['success']:
                # Update blog post with URL
                blog_post_url = publish_result.get('url', '')
                post_result['url'] = blog_post_url
                
                # Step 8: Generate social media posts
                logger.info("  - Generating social media posts...")
                blog_post_dict = {
                    'title': blog_post.title,
                    'content': blog_post.content,
                    'url': blog_post_url
                }
                social_posts = self.social_media_generator.generate_all_platforms(blog_post_dict)
                post_result['steps'].append('social_media_generation')
                post_result['social_posts'] = {
                    platform: {
                        'content': post.content,
                        'hashtags': post.hashtags,
                        'character_count': post.character_count
                    }
                    for platform, post in social_posts.items()
                }
                
                # Save social media posts to files
                logger.info("  - Saving social media posts to files...")
                social_media_dir = self._save_social_media_posts(
                    blog_post.title,
                    blog_post_url,
                    social_posts
                )
                post_result['social_media_dir'] = social_media_dir
                logger.info(f"  ✓ Social media posts saved to: {social_media_dir}")
                
                # Step 8: Generate backlink suggestions and apply them
                logger.info("  - Generating backlink suggestions...")
                backlink_suggestions = self.internal_linker.suggest_backlinks(
                    blog_post_dict,
                    self.content_index
                )
                post_result['steps'].append('backlink_analysis')
                post_result['backlink_suggestions'] = backlink_suggestions
                
                # Step 9: Update old posts with backlinks to new content
                logger.info("  - Adding backlinks from existing posts...")
                updated_posts_count = self.internal_linker.update_old_posts_with_links(
                    blog_post_dict,
                    self.content_index,
                    self.blogger_client
                )
                post_result['steps'].append('backlink_application')
                post_result['backlinks_added'] = updated_posts_count
                logger.info(f"  ✓ Added backlinks from {updated_posts_count} existing posts")
                
                post_result['success'] = True
                logger.info(f"  ✓ Successfully processed: {blog_post.title}")
            else:
                post_result['success'] = False
                post_result['error'] = publish_result.get('error', 'Unknown error')
                logger.error(f"  ✗ Failed to publish: {post_result['error']}")
        
        except Exception as e:
            logger.error(f"  ✗ Error processing opportunity: {e}")
            post_result['success'] = False
            post_result['error'] = str(e)
        
        return post_result
    
    def research_only(self, num_opportunities: int = 10) -> Dict:
        """Run SEO research only without creating content"""
        logger.info("Running SEO research only...")
        
        # Fetch existing content
        self.existing_posts = self.blogger_client.get_all_posts()
        
        # Analyze and find opportunities
        content_analysis = self.seo_researcher.analyze_existing_content(self.existing_posts)
        opportunities = self.seo_researcher.discover_topic_opportunities(
            content_analysis,
            num_opportunities=num_opportunities
        )
        
        # Get trending topics
        trending = self.seo_researcher.get_trending_topics()
        
        return {
            'content_analysis': content_analysis,
            'opportunities': [
                {
                    'topic': opp.topic,
                    'keywords': opp.keywords,
                    'search_volume': opp.search_volume,
                    'difficulty': opp.difficulty,
                    'opportunity_score': opp.opportunity_score,
                    'trend': opp.trend,
                    'suggested_title': opp.suggested_title
                }
                for opp in opportunities
            ],
            'trending_topics': trending
        }
    
    def create_from_topic(self, topic: str, 
                         generate_images: bool = True,
                         publish_immediately: bool = False) -> Dict:
        """Create a blog post from a specific topic"""
        logger.info(f"Creating blog post from topic: {topic}")
        
        # Fetch existing content for context
        self.existing_posts = self.blogger_client.get_all_posts()
        self.content_index = self.internal_linker.build_content_index(self.existing_posts)
        
        # Create opportunity object
        opportunity = TopicOpportunity(
            topic=topic,
            keywords=[],
            search_volume=50,
            difficulty=30,
            opportunity_score=70,
            trend="stable",
            suggested_title=topic,
            content_outline=[]
        )
        
        # Generate keywords for the topic
        existing_keywords = []
        for post in self.existing_posts:
            existing_keywords.extend(post.get('labels', []))
        
        keyword_data = self.seo_researcher.generate_seo_keywords(topic, existing_keywords)
        opportunity.keywords = keyword_data.get('primary_keyword', [topic])
        
        # Process the opportunity
        result = self._process_single_opportunity(
            opportunity,
            generate_images,
            publish_immediately
        )
        
        return result
    
    def _save_social_media_posts(self, blog_title: str, blog_url: str, 
                                social_posts: Dict) -> str:
        """Save social media posts to files organized by blog title"""
        import os
        from pathlib import Path
        
        # Create folder name from blog title (sanitize for filesystem)
        safe_title = "".join(c for c in blog_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        
        # Create directory structure
        social_dir = config.output_dir / "social_media" / safe_title
        social_dir.mkdir(parents=True, exist_ok=True)
        
        # Save each platform's post to a separate file
        for platform, post in social_posts.items():
            filename = f"{platform}_post.txt"
            filepath = social_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {platform.upper()} POST\n")
                f.write(f"# Blog: {blog_title}\n")
                f.write(f"# URL: {blog_url}\n")
                f.write(f"# Character Count: {post.character_count}\n")
                f.write(f"# Hashtags: {', '.join(post.hashtags)}\n")
                f.write("\n" + "="*50 + "\n\n")
                f.write(post.content)
                f.write("\n\n" + "="*50 + "\n")
                f.write(f"\n# Hashtags to use:\n")
                f.write(f"{', '.join(post.hashtags)}\n")
                f.write(f"\n# Direct link to blog post:\n")
                f.write(f"{blog_url}\n")
        
        # Also save a summary file
        summary_file = social_dir / "summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# Social Media Posts Summary\n\n")
            f.write(f"**Blog Title:** {blog_title}\n\n")
            f.write(f"**Blog URL:** {blog_url}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"---\n\n")
            
            for platform, post in social_posts.items():
                f.write(f"## {platform.upper()}\n\n")
                f.write(f"**Character Count:** {post.character_count}\n\n")
                f.write(f"**Hashtags:** {', '.join(post.hashtags)}\n\n")
                f.write(f"**Content:**\n\n```\n{post.content}\n```\n\n")
                f.write(f"---\n\n")
        
        logger.info(f"Social media posts saved to: {social_dir}")
        return str(social_dir)
    
    def generate_social_media_only(self, post_url: str) -> Dict:
        """Generate social media posts for an existing blog post"""
        logger.info(f"Generating social media posts for: {post_url}")
        
        # Extract post ID from URL
        post_id = post_url.split('/')[-1]
        
        # Fetch the post
        post = self.blogger_client.get_post(post_id)
        
        # Generate social media posts
        blog_post_dict = {
            'title': post.get('title', ''),
            'content': post.get('content', ''),
            'url': post.get('url', post_url)
        }
        
        social_posts = self.social_media_generator.generate_all_platforms(blog_post_dict)
        
        return {
            'post_title': post.get('title', ''),
            'post_url': post.get('url', post_url),
            'social_posts': {
                platform: {
                    'content': post.content,
                    'hashtags': post.hashtags,
                    'character_count': post.character_count
                }
                for platform, post in social_posts.items()
            }
        }
    
    def update_internal_links(self, post_url: str) -> Dict:
        """Update internal links for an existing post"""
        logger.info(f"Updating internal links for: {post_url}")
        
        # Fetch all posts
        self.existing_posts = self.blogger_client.get_all_posts()
        self.content_index = self.internal_linker.build_content_index(self.existing_posts)
        
        # Get the specific post
        post_id = post_url.split('/')[-1]
        post = self.blogger_client.get_post(post_id)
        
        # Find linking opportunities
        linking_opportunities = self.internal_linker.find_linking_opportunities(
            post,
            self.content_index
        )
        
        # Apply links
        updated_content = self.internal_linker.apply_internal_links(
            post.get('content', ''),
            linking_opportunities
        )
        
        # Update the post
        result = self.blogger_publisher.update_post(
            post_id,
            BlogPost(
                title=post.get('title', ''),
                content=updated_content,
                meta_description='',
                keywords=post.get('labels', []),
                tags=post.get('labels', []),
                headings={},
                image_prompts=[],
                internal_links=[]
            )
        )
        
        return result
    
    def get_workflow_report(self) -> Dict:
        """Generate a report of recent activity"""
        logger.info("Generating workflow report...")
        
        # Fetch recent posts
        recent_posts = self.blogger_client.get_all_posts()[:10]
        
        return {
            'total_posts': len(self.blogger_client.get_all_posts()),
            'recent_posts': [
                {
                    'title': post.get('title', ''),
                    'url': post.get('url', ''),
                    'published': post.get('published', ''),
                    'labels': post.get('labels', [])
                }
                for post in recent_posts
            ],
            'blog_niche': config.blog_niche,
            'target_audience': config.target_audience
        }


def main():
    """Main entry point for the agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Blog AI Agent')
    parser.add_argument('--mode', choices=['full', 'research', 'topic', 'social', 'links'], 
                       default='full', help='Operation mode')
    parser.add_argument('--topic', type=str, help='Specific topic to create content for')
    parser.add_argument('--url', type=str, help='Post URL for social media or link updates')
    parser.add_argument('--num-topics', type=int, default=1, help='Number of topics to process')
    parser.add_argument('--no-images', action='store_true', help='Skip image generation')
    parser.add_argument('--publish', action='store_true', help='Publish immediately (not as draft)')
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = BlogAIAgent()
    
    # Run based on mode
    if args.mode == 'full':
        result = agent.run_full_workflow(
            num_topics=args.num_topics,
            generate_images=not args.no_images,
            publish_immediately=args.publish
        )
    elif args.mode == 'research':
        result = agent.research_only(num_opportunities=args.num_topics)
    elif args.mode == 'topic' and args.topic:
        result = agent.create_from_topic(
            args.topic,
            generate_images=not args.no_images,
            publish_immediately=args.publish
        )
    elif args.mode == 'social' and args.url:
        result = agent.generate_social_media_only(args.url)
    elif args.mode == 'links' and args.url:
        result = agent.update_internal_links(args.url)
    else:
        logger.error("Invalid arguments for the selected mode")
        return
    
    # Print result
    import json
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
