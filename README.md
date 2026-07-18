# Blog AI Agent

An intelligent AI-powered agent for automated blog content creation, SEO optimization, and social media promotion. Designed specifically for Blogger blogs, this agent handles the entire content workflow from topic discovery to publication and promotion.

## Features

- **SEO Research**: Discovers high-demand, low-competition topics using AI analysis
- **Content Generation**: Creates SEO-optimized blog posts with proper structure and formatting (800-1200 words)
- **Digital Products**: Automatically generates comprehensive digital products for each blog post
- **Gumroad Integration**: Uploads and sells digital products via Gumroad marketplace
- **Image Generation**: Generates custom images using DALL-E or Stability AI
- **Cloudinary Hosting**: Automatically uploads images to Cloudinary for reliable hosting
- **Internal Linking**: Automatically builds internal links between related posts
- **Social Media Posts**: Generates promotional posts for LinkedIn, Facebook, and Twitter
- **Blogger Integration**: Direct publishing to Blogger with draft/publish options
- **Backlink Analysis**: Suggests opportunities for building internal backlinks

## Architecture

The agent consists of several specialized modules:

- `blogger_client.py` - Blogger API integration for content management
- `seo_researcher.py` - SEO topic research and competitor analysis
- `content_generator.py` - AI-powered blog content generation
- `image_generator.py` - Image generation using DALL-E/Stability AI
- `cloudinary_uploader.py` - Cloudinary image hosting integration
- `digital_product_generator.py` - Comprehensive digital product creation
- `gumroad_client.py` - Gumroad API for product sales
- `internal_linker.py` - Internal linking and backlink analysis
- `social_media_generator.py` - Social media post generation
- `blogger_publisher.py` - Content preparation and Blogger publishing
- `blog_agent.py` - Main orchestrator and workflow management

## Installation

### Prerequisites

- Python 3.8 or higher
- Google Cloud Project with Blogger API enabled
- OpenAI API key
- (Optional) Stability AI API key for image generation
- (Optional) Cloudinary account for image hosting
- (Optional) Gumroad account for digital product sales

### Setup Steps

1. **Clone or create the project directory**
   ```bash
   cd C:\Users\dell\CascadeProjects\blog-ai-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   - Copy `.env.example` to `.env`
   - Fill in your API keys and configuration

4. **Set up Google OAuth for Blogger API**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Blogger API v3
   - Create OAuth 2.0 credentials (Desktop application)
   - Download credentials.json and place in `data/` directory

5. **Get your Blog ID**
   - Visit your Blogger blog
   - The blog ID is in the URL: `https://blogger.com/blogID/XXXXXXX`
   - Add it to your `.env` file as `BLOGGER_BLOG_ID`

## Configuration

Edit the `.env` file with your settings:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Blogger Configuration
BLOGGER_API_KEY=your_blogger_api_key_here
BLOGGER_BLOG_ID=your_blog_id_here

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Blog Settings
BLOG_DOMAIN=simplifyyourday.blogspot.com
BLOG_NICHE=productivity/lifestyle
TARGET_AUDIENCE=general_professionals
```

## Usage

### Full Workflow Mode

Run the complete automated workflow:

```bash
python blog_agent.py --mode full --num-topics 1
```

This will:
1. Fetch existing blog content
2. Analyze content and find SEO opportunities
3. Generate blog post content
4. Create images
5. Apply internal links
6. Publish as draft (or publish directly with `--publish`)
7. Generate social media posts
8. Suggest backlink opportunities

### Research Only Mode

Generate topic opportunities without creating content:

```bash
python blog_agent.py --mode research --num-topics 10
```

### Create from Specific Topic

Create content for a specific topic:

```bash
python blog_agent.py --mode topic --topic "Time Management Tips" --publish
```

### Generate Social Media Posts

Generate social media posts for an existing blog post:

```bash
python blog_agent.py --mode social --url https://simplifyyourday.blogspot.com/2024/01/your-post.html
```

### Update Internal Links

Update internal links for an existing post:

```bash
python blog_agent.py --mode links --url https://simplifyyourday.blogspot.com/2024/01/your-post.html
```

### Command Line Options

- `--mode`: Operation mode (full, research, topic, social, links)
- `--topic`: Specific topic for content creation
- `--url`: Post URL for social media or link updates
- `--num-topics`: Number of topics to process (default: 1)
- `--no-images`: Skip image generation
- `--publish`: Publish immediately instead of saving as draft

## Workflow Details

### 1. Content Analysis

The agent fetches all existing blog posts and analyzes:
- Main themes and topics covered
- Content gaps and missing topics
- Audience interests based on content
- Overlapping topics that could be consolidated

### 2. SEO Research

Using AI and SEO principles, the agent:
- Identifies high-demand, low-competition topics
- Estimates search volume and difficulty
- Suggests optimal titles and content outlines
- Generates SEO-friendly keywords
- Analyzes competitor content

### 3. Content Generation

For each topic, the agent:
- Creates comprehensive 1500-2500 word posts
- Structures content with proper headings
- Includes practical examples and advice
- Optimizes for readability and SEO
- Generates meta descriptions and tags

### 4. Image Generation

The agent can:
- Generate custom images using DALL-E
- Create variations of existing images
- Optimize images for web performance
- Generate SEO-friendly alt text
- Upload images to Cloudinary for hosting (when configured)
- Automatically insert Cloudinary URLs into blog posts

**Image Hosting Workflow:**
Since Blogger API doesn't support direct image uploads, the agent uses Cloudinary:
```
OpenAI Images API → Save locally → Upload to Cloudinary → Get secure URL → Insert into Blogger HTML
```

Configure Cloudinary in `.env` to enable actual image hosting:
```bash
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

Without Cloudinary, the agent uses placeholder images.

### 5. Digital Products

The agent automatically creates comprehensive digital products for each blog post:

**Product Components:**
- Comprehensive guide (3000-5000 words)
- Implementation checklist
- Code templates and snippets
- Marketing copy
- Gumroad product listing

**Workflow:**
```
Blog Topic → Short Blog Content → Digital Product → Gumroad Upload → Product Link in Blog
```

**Configure Gumroad in `.env`:**
```bash
GUMROAD_ACCESS_TOKEN=your_gumroad_access_token
ENABLE_DIGITAL_PRODUCTS=true
DEFAULT_PRODUCT_PRICE=9.99
```

**Product Folder Structure:**
```
output/digital_products/
├── {blog_title_safe}/
│   ├── product_content.md
│   ├── product_description.txt
│   ├── checklist.txt
│   ├── templates.json
│   ├── marketing_copy.txt
│   └── product_metadata.json
```

### 6. Internal Linking

Automatically:
- Finds relevant existing posts to link to
- Generates appropriate anchor text
- Applies links naturally within content
- Suggests backlink opportunities from old posts
- Ensures minimum 3 internal links per blog post

### 7. Social Media Promotion

Generates platform-specific posts:
- **LinkedIn**: Professional, engaging posts with clear CTAs
- **Facebook**: Friendly, shareable posts with engagement questions
- **Twitter**: Concise tweets under 280 characters
- **Twitter Threads**: Multi-tweet threads for complex topics

### 8. Publishing

Options for publishing:
- Save as draft for review
- Publish immediately
- Schedule for future publication (as draft with metadata)

## API Integration

### Blogger API

The agent uses OAuth 2.0 to authenticate with Blogger:
- First run will open browser for OAuth consent
- Credentials are saved for subsequent runs
- Supports full CRUD operations on posts

### OpenAI API

Used for:
- Content generation
- SEO research
- Keyword generation
- Social media post creation
- Image generation (DALL-E)

### Optional Integrations

- **Stability AI**: Alternative image generation
- **Semrush/Ahrefs**: Advanced SEO metrics (requires API keys)
- **Social Media APIs**: Direct posting to platforms (requires API keys)

## Output Files

The agent creates several output files:

- `data/token.json` - OAuth credentials (auto-generated)
- `data/credentials.json` - Google OAuth credentials (you provide)
- `output/images/` - Generated images
- `output/post_*_metadata.json` - Post metadata and tracking
- `output/scheduled_*.json` - Scheduled post information

## Best Practices

1. **Review Drafts**: Always review generated content before publishing
2. **Customize Prompts**: Adjust AI prompts in code for your specific niche
3. **Monitor Costs**: Track OpenAI API usage for image generation
4. **Internal Links**: Review suggested internal links for relevance
5. **SEO Keywords**: Verify keywords match your target audience
6. **Social Media**: Customize posts for your brand voice

## Troubleshooting

### OAuth Authentication Issues

If OAuth fails:
- Delete `data/token.json` and re-authenticate
- Ensure `credentials.json` is in the `data/` directory
- Check that Blogger API is enabled in Google Cloud Console

### Blogger API Errors

Common issues:
- Invalid Blog ID: Verify your blog ID in `.env`
- Insufficient permissions: Ensure OAuth scope includes Blogger
- Rate limiting: Wait a few minutes between operations

### OpenAI API Errors

Common issues:
- Invalid API key: Check your `.env` file
- Rate limits: Upgrade your OpenAI plan if needed
- Model availability: Ensure model name is correct in config

### Image Generation Issues

If image generation fails:
- Check API key is valid
- Verify sufficient credits/usage
- Try alternative image generation service
- Use `--no-images` flag to skip

## Advanced Usage

### Custom Content Generation

Modify the `ContentGenerator` class to:
- Adjust word count targets
- Change tone and style
- Add custom formatting
- Include specific sections

### Custom SEO Research

Extend the `SEOResearcher` class to:
- Integrate with SEO tools APIs
- Add custom keyword research
- Implement competitor tracking
- Add trend analysis

### Custom Social Media Posts

Modify the `SocialMediaGenerator` class to:
- Add platform-specific formatting
- Include brand-specific elements
- Add custom hashtags
- Adjust post length limits

## Contributing

To extend the agent:

1. Add new modules following the existing pattern
2. Update the main `BlogAIAgent` class to integrate
3. Add configuration options to `config.py`
4. Update this README with new features

## License

This project is provided as-is for personal and commercial use.

## Support

For issues or questions:
- Check the troubleshooting section
- Review logs for detailed error messages
- Verify all API keys and configurations
- Ensure all dependencies are installed

## Roadmap

Potential future enhancements:
- Direct social media posting via APIs
- Advanced SEO metrics integration
- A/B testing for content
- Analytics and performance tracking
- Multi-language support
- Video content generation
- Podcast generation from blog posts
