# Setup Guide for Blog AI Agent

This guide will walk you through setting up the Blog AI Agent for your Blogger blog at simplifyyourday.blogspot.com.

## Quick Reference: Script Run Variants

### Blog AI Agent (`blog_agent.py`)

```bash
# Full workflow with automatic topic discovery
python blog_agent.py --mode full --num-topics 1

# Full workflow with topics file
python blog_agent.py --mode full --topics-file topics.txt --num-topics 3

# Full workflow with image generation
python blog_agent.py --mode full --num-topics 1 --youtube-video

# Full workflow without images (faster)
python blog_agent.py --mode full --num-topics 1 --no-images

# Full workflow with immediate publishing
python blog_agent.py --mode full --num-topics 1 --publish

# SEO research only (no content creation)
python blog_agent.py --mode research --num-topics 10

# Create content from specific topic
python blog_agent.py --mode topic --topic "Your topic here"

# Generate social media for existing post
python blog_agent.py --mode social --url https://your-blog.com/post-id

# Update internal links for existing post
python blog_agent.py --mode links --url https://your-blog.com/post-id

# Generate YouTube video only (from existing post)
python blog_agent.py --mode youtube-only --url https://your-blog.com/post-id
```

**Available Arguments:**
- `--mode`: Operation mode (full, research, topic, social, links, youtube-only)
- `--topic`: Specific topic to create content for (required for topic mode)
- `--url`: Post URL for social media, link updates, or YouTube video (required for social, links, youtube-only modes)
- `--num-topics`: Number of topics to process (default: 1)
- `--no-images`: Skip image generation (faster execution)
- `--youtube-video`: Generate YouTube video along with blog post
- `--publish`: Publish immediately instead of as draft
- `--topics-file`: Path to text file containing topics (one per line)

---

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

# Model Configuration - Different models for different workflows
# Use gpt-4-turbo-preview for best quality, or gpt-3.5-turbo for cost savings
OPENAI_MODEL_CONTENT=gpt-4-turbo-preview
OPENAI_MODEL_DIGITAL_PRODUCT=gpt-4-turbo-preview
OPENAI_MODEL_SEO=gpt-4-turbo-preview
OPENAI_MODEL_SOCIAL=gpt-4-turbo-preview

# Token Configuration - Optimal tokens for different workflows
# Adjust based on your needs and budget
MAX_TOKENS_CONTENT=2000
MAX_TOKENS_DIGITAL_PRODUCT=4000
MAX_TOKENS_SEO=1500
MAX_TOKENS_SOCIAL=1000

# Topic file configuration
TOPICS_FILE_PATH=topics.txt

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

### Model and Token Configuration

The Blog AI Agent now supports different models and token limits for different workflows to optimize quality and cost:

**Model Configuration:**
- `OPENAI_MODEL_CONTENT`: Model used for blog content generation (default: gpt-4-turbo-preview)
- `OPENAI_MODEL_DIGITAL_PRODUCT`: Model used for digital product generation (default: gpt-4-turbo-preview)
- `OPENAI_MODEL_SEO`: Model used for SEO optimization (default: gpt-4-turbo-preview)
- `OPENAI_MODEL_SOCIAL`: Model used for social media content (default: gpt-4-turbo-preview)

**Token Configuration:**
- `MAX_TOKENS_CONTENT`: Maximum tokens for blog content (default: 2000)
- `MAX_TOKENS_DIGITAL_PRODUCT`: Maximum tokens for digital products (default: 4000)
- `MAX_TOKENS_SEO`: Maximum tokens for SEO tasks (default: 1500)
- `MAX_TOKENS_SOCIAL`: Maximum tokens for social media (default: 1000)

**Cost Optimization:**
For cost savings, you can use `gpt-3.5-turbo` for less critical workflows:
```env
OPENAI_MODEL_CONTENT=gpt-3.5-turbo
OPENAI_MODEL_SEO=gpt-3.5-turbo
OPENAI_MODEL_SOCIAL=gpt-3.5-turbo
OPENAI_MODEL_DIGITAL_PRODUCT=gpt-4-turbo-preview  # Keep high quality for products
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

### Using Topics File (Recommended for Specific Topics)

If you have specific topics you want to create content for, you can provide them in a text file:

1. Create a `topics.txt` file with one topic per line:
   ```bash
   # Copy the example file
   cp topics.txt.example topics.txt
   
   # Edit topics.txt with your desired topics
   # Example:
   Practical GitHub Actions caching strategies to speed CI and cut costs
   Building bulletproof TypeScript API clients from OpenAPI with Zod
   Cut CI time in half with incremental Turborepo for TypeScript monorepos
   ```

2. Run the agent with the topics file:
   ```bash
   python blog_agent.py --mode full --topics-file topics.txt --num-topics 3
   ```

3. **Topic Completion Tracking:**
   - When a topic is successfully processed, it will be automatically marked with `[DONE]` in the topics.txt file
   - Completed topics are skipped in subsequent runs
   - You can manually mark topics as done by prefixing them with `[DONE]` or `[COMPLETED]`
   - You can manually mark topics as pending by prefixing them with `[TODO]` or `[PENDING]`
   - Comments (lines starting with `#`) are ignored
   - Empty lines are ignored

   Example topics.txt after processing:
   ```
   # Example topics file
   [DONE] Practical GitHub Actions caching strategies to speed CI and cut costs
   [DONE] Building bulletproof TypeScript API clients from OpenAPI with Zod
   Cut CI time in half with incremental Turborepo for TypeScript monorepos
   ```

4. If the file is empty or doesn't exist, the agent will fall back to automatic topic discovery.

### Using Automatic Topic Discovery

1. Run a test with image generation disabled:
   ```bash
   python blog_agent.py --mode full --num-topics 1 --no-images
   ```

2. This will:
   - Fetch your existing posts
   - Analyze content
   - Find a topic opportunity automatically
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

### Option B: Use Cloudinary for Image Hosting

Since Blogger API doesn't support direct image uploads, you can use Cloudinary to host your AI-generated images:

1. **Create a Cloudinary Account**
   - Sign up at [cloudinary.com](https://cloudinary.com)
   - Get your free account (includes generous free tier)

2. **Get Cloudinary Credentials**
   - Go to Dashboard → Settings → API Security
   - Copy your Cloud Name, API Key, and API Secret

3. **Configure Environment Variables**
   Add to your `.env` file:
   ```bash
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   ```

4. **Create Upload Preset (Optional)**
   - Go to Settings → Upload → Upload Presets
   - Create an unsigned upload preset for easier uploads
   - Or use signed uploads (default, more secure)

**Workflow:**
```
OpenAI Images API → Save locally → Upload to Cloudinary → Get secure URL → Insert into Blogger HTML
```

The agent will automatically:
- Generate images using OpenAI
- Upload them to Cloudinary
- Use the Cloudinary URLs in your blog posts
- Fall back to placeholders if Cloudinary is not configured

## Step 10: Enable YouTube Video Generation (Optional)

The Blog AI Agent can automatically generate YouTube videos from your blog posts with AI-generated visuals and synchronized narration.

### 10.1 Install Video Processing Dependencies

YouTube video generation requires additional Python packages:

```bash
pip install moviepy numpy pydub
```

**Note**: pydub may require additional system dependencies:
- **Windows**: No additional dependencies needed
- **Linux**: Install ffmpeg: `sudo apt-get install ffmpeg`
- **Mac**: Install ffmpeg: `brew install ffmpeg`

### 10.2 How YouTube Video Generation Works

The system creates engaging YouTube videos through:

1. **Script Generation**: Creates a story-driven script with visual descriptions for each scene
2. **Scene Images**: Generates AI images for each scene using DALL-E
3. **Per-Scene Audio**: Generates synchronized narration for each scene using OpenAI's TTS
4. **Video Composition**: Stitches images and audio into a synchronized video
5. **Text Overlays**: Adds key points as text overlays on each scene

**Key Features**:
- Story-like visual flow that viewers can easily follow
- Perfect audio synchronization with individual scenes
- Audio normalization and volume boosting
- SEO-optimized titles, descriptions, and tags
- Configurable video duration (default 60 seconds)

### 10.3 Generate YouTube Videos

Run the agent with the `--youtube-video` flag:

```bash
# Generate blog post with YouTube video
python blog_agent.py --mode full --num-topics 1 --youtube-video

# Generate from specific topic with video
python blog_agent.py --mode topic --topic "Your topic here" --youtube-video

# Generate video without images (faster, uses placeholders)
python blog_agent.py --mode full --num-topics 1 --youtube-video --no-images
```

### 10.4 Video Output

Videos are saved to: `output/videos/`

Each video includes:
- **Video file**: MP4 format with H.264 video codec and AAC audio codec
- **Metadata**: Title, description, tags, duration, scene count
- **Audio files**: Individual scene audio files in `output/audio/`
- **Scene images**: Generated images in `output/images/`

### 10.5 Customization

Adjust video generation parameters in `youtube_video_generator.py`:

- **Target duration**: Change `target_duration` parameter (default 60 seconds)
- **Voice style**: Modify `voice` parameter in AudioGenerator (options: alloy, echo, fable, onyx, nova, shimmer)
- **Audio boost**: Adjust `boost_db` in normalize_audio (default 3dB)
- **Scene duration**: Modify `avg_scene_duration` in script generation (default 5 seconds)

### 10.6 Troubleshooting Video Generation

**Problem**: "No module named 'moviepy'" or similar import errors

**Solution**:
```bash
pip install moviepy numpy pydub --upgrade
```

**Problem**: Audio normalization fails (pydub import error)

**Solution**: This is optional - the system will skip normalization and continue with standard audio. To fix:
- Install ffmpeg system dependency (see 10.1)
- Or disable normalization by setting `normalize_audio=False` in the code

**Problem**: Video generation takes too long

**Solution**:
- Reduce target duration (e.g., 30 seconds instead of 60)
- Use fewer scenes by adjusting scene duration
- Disable audio normalization if not critical

**Problem**: Generated video has no audio

**Solution**:
- Check OpenAI API key has access to TTS API
- Verify audio files are generated in `output/audio/`
- Check logs for audio generation errors

### 10.7 Generate YouTube Video Only (Skip Other Steps)

If you already have a published blog post and want to generate a YouTube video without running the full workflow, use the `youtube-only` mode:

```bash
python blog_agent.py --mode youtube-only --url "https://your-blog-post-url"
```

**What this mode does:**
- Fetches the existing blog post from the provided URL
- Generates a YouTube video from the blog content
- Skips all other steps (content generation, SEO research, image generation, social media, etc.)
- Saves the video to `output/videos/`

**Example:**
```bash
python blog_agent.py --mode youtube-only --url "https://simplifyyourday.blogspot.com/2024/01/your-post-id"
```

**Use cases:**
- Generate videos for existing posts that were created without videos
- Re-generate videos with updated settings
- Create videos for manually written posts
- Test video generation without affecting blog content

### 10.8 Best Practices for YouTube Videos

1. **Start Short**: Begin with 30-second videos to test the workflow
2. **Review Scripts**: The AI generates scripts - review them for your niche
3. **Customize Voice**: Try different voice options (alloy, echo, fable, onyx, nova, shimmer)
4. **Monitor Costs**: Video generation uses OpenAI API for both images and audio
5. **Quality Check**: Review generated videos before uploading to YouTube
6. **SEO Optimization**: Use the generated titles, descriptions, and tags for YouTube SEO

## Step 11: Schedule Regular Runs

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
