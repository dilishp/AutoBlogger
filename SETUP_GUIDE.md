# Setup Guide for Blog AI Agent

This guide will walk you through setting up the Blog AI Agent for your Blogger blog at simplifyyourday.blogspot.com.

## Step 1: Google Cloud Console Setup

### 1.1 Create/Select Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account (the one that owns your Blogger blog)
3. Create a new project or select an existing one
4. Note the Project ID for later reference

### 1.2 Enable Blogger API

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Blogger API"
3. Click on "Blogger API v3"
4. Click "Enable"

### 1.3 Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Desktop application" as the application type
4. Give it a name (e.g., "Blog AI Agent")
5. Click "Create"
6. Download the JSON file
7. Rename it to `credentials.json`
8. Place it in the `data/` directory of the project

### 1.4 Get Blogger API Key

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API key"
3. Copy the API key
4. Add it to your `.env` file as `BLOGGER_API_KEY`

## Step 2: Get Your Blogger Blog ID

1. Visit your blog: https://simplifyyourday.blogspot.com/
2. Go to Blogger dashboard
3. Click on "Settings" for your blog
4. The Blog ID is listed under "Blog ID" (format: long number)
5. Add it to your `.env` file as `BLOGGER_BLOG_ID`

Alternative method:
- The Blog ID is also in the URL when editing a post:
- `https://blogger.com/blog/post/edit/XXXXXXX?postID=YYYYYYYY`
- XXXXXXX is your Blog ID

## Step 3: OpenAI API Setup

### 3.1 Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign in or create an account
3. Go to "API Keys" section
4. Click "Create new secret key"
5. Copy the API key
6. Add it to your `.env` file as `OPENAI_API_KEY`

### 3.2 Choose OpenAI Model

The agent uses GPT-4 by default for best results. You can change this in `.env`:
- `gpt-4-turbo-preview` (recommended, best quality)
- `gpt-4` (older but still good)
- `gpt-3.5-turbo` (faster, cheaper, lower quality)

Add to `.env`:
```env
OPENAI_MODEL=gpt-4-turbo-preview
```

## Step 4: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual values:

```env
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-actual-openai-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Blogger API Configuration
BLOGGER_API_KEY=your-blogger-api-key-here
BLOGGER_BLOG_ID=1234567890123456789

# Google OAuth Credentials
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here

# Blog Configuration
BLOG_DOMAIN=simplifyyourday.blogspot.com
BLOG_NICHE=productivity/lifestyle
TARGET_AUDIENCE=general_professionals
```

## Step 5: Install Python Dependencies

1. Ensure you have Python 3.8 or higher installed:
   ```bash
   python --version
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Step 6: First Run - Authentication

1. Run the agent in research mode to test authentication:
   ```bash
   python blog_agent.py --mode research --num-topics 5
   ```

2. On first run, a browser window will open:
   - Sign in with your Google account
   - Grant permissions to access your Blogger blog
   - The browser will redirect to a localhost URL (this is expected)
   - The script will save the token automatically

3. If successful, you'll see:
   - "Successfully authenticated with Blogger API"
   - SEO research results

## Step 7: Test Full Workflow

1. Run a test with image generation disabled:
   ```bash
   python blog_agent.py --mode full --num-topics 1 --no-images
   ```

2. This will:
   - Fetch your existing posts
   - Analyze content
   - Find a topic opportunity
   - Generate blog post content
   - Apply internal links
   - Publish as draft
   - Generate social media posts

3. Check your Blogger dashboard for the new draft post

## Step 8: Review and Customize

### 8.1 Review Generated Content

1. Go to your Blogger dashboard
2. Find the draft post
3. Review the content for quality and accuracy
4. Make any manual edits if needed
5. Publish when satisfied

### 8.2 Customize for Your Niche

Edit `config.py` to adjust:
- Blog niche and target audience
- Content generation parameters
- Image generation settings

### 8.3 Adjust AI Prompts

For better results, customize prompts in:
- `content_generator.py` - Content generation prompts
- `seo_researcher.py` - SEO research prompts
- `social_media_generator.py` - Social media prompts

## Step 9: Enable Image Generation (Optional)

### Option A: Use DALL-E (OpenAI)

No additional setup needed - uses your existing OpenAI API key.

Run with images:
```bash
python blog_agent.py --mode full --num-topics 1
```

### Option B: Use Stability AI

1. Get a Stability AI API key from [Stability AI](https://platform.stability.ai/)
2. Add to `.env`:
   ```env
   STABILITY_AI_KEY=your-stability-ai-key-here
   ```

## Step 10: Schedule Regular Runs

### Windows Task Scheduler

1. Open Task Scheduler
2. Create a new task
3. Set trigger (e.g., daily at 9 AM)
4. Set action to run:
   ```
   python C:\Users\dell\CascadeProjects\blog-ai-agent\blog_agent.py --mode full --num-topics 1
   ```
5. Configure to run with your Python environment

### Alternative: Cron (Linux/Mac)

Add to crontab:
```bash
0 9 * * * cd /path/to/blog-ai-agent && /usr/bin/python3 blog_agent.py --mode full --num-topics 1
```

## Rerunning with a Specific Topic

If a post creation failed and you want to retry with the same topic:

### Method 1: Use the Topic Directly

```bash
python blog_agent.py --mode full --topic "Your specific topic here"
```

### Method 2: Use Saved Research Results

The agent saves research results in `output/research/`. To reuse a previously researched topic:

1. Find the research file in `output/research/`
2. Copy the topic from the saved file
3. Run with that topic:
```bash
python blog_agent.py --mode full --topic "Practical GitHub Actions caching strategies to speed CI and cut costs"
```

### Method 3: Continue from Draft

If a draft was created but publishing failed:

1. Check your Blogger drafts for the incomplete post
2. Manually publish from Blogger dashboard, OR
3. Delete the draft and rerun the agent to create a fresh post

### Common Scenarios

**Post creation failed during internal linking:**
```bash
python blog_agent.py --mode full --topic "Your topic here"
```

**Image generation failed but content was created:**
```bash
python blog_agent.py --mode full --topic "Your topic here" --no-images
```

**Social media generation failed:**
```bash
python blog_agent.py --mode social-only --url "https://your-blog-post-url"
```

## Troubleshooting

### Authentication Issues

**Problem**: OAuth fails or token expires

**Solution**:
```bash
# Delete the token file
rm data/token.json

# Run again to re-authenticate
python blog_agent.py --mode research --num-topics 1
```

### Blogger API Errors

**Problem**: "Invalid blog ID" or "Permission denied"

**Solution**:
- Verify BLOGGER_BLOG_ID in `.env`
- Ensure you're using the correct Google account
- Check that Blogger API is enabled in Google Cloud Console
- Re-authenticate by deleting `data/token.json`

### OpenAI API Errors

**Problem**: "Invalid API key" or rate limits

**Solution**:
- Verify OPENAI_API_KEY in `.env`
- Check your OpenAI billing status
- Consider switching to `gpt-3.5-turbo` for lower costs
- Monitor usage at [OpenAI Platform](https://platform.openai.com/usage)

### Module Import Errors

**Problem**: "Module not found" errors

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Ensure you're using the correct Python environment
python --version
which python  # Linux/Mac
where python  # Windows
```

## Best Practices

1. **Start with Research Mode**: Use `--mode research` to understand opportunities before creating content
2. **Review Drafts**: Always review generated content before publishing
3. **Monitor Costs**: Track OpenAI API usage, especially for image generation
4. **Customize Prompts**: Adjust AI prompts for your specific niche and voice
5. **Test Incrementally**: Start with `--no-images` to test content generation first
6. **Backup Content**: The agent creates drafts, but keep backups of important content
7. **Regular Updates**: Periodically update dependencies and review generated content quality

## Next Steps

After setup is complete:

1. Run research mode to understand content opportunities
2. Create your first AI-generated blog post
3. Review and refine the generated content
4. Customize prompts for your specific niche
5. Set up a regular content creation schedule
6. Monitor performance and adjust as needed

## Support

For issues:
1. Check the main README.md
2. Review logs for detailed error messages
3. Verify all API keys and configurations
4. Ensure all dependencies are correctly installed

## Security Notes

- Never commit `.env` file to version control
- Keep API keys secure and rotate them periodically
- Use read-only API keys when possible
- Regularly review OAuth permissions in Google Cloud Console
