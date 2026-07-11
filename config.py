"""
Configuration management for Blog AI Agent
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
from pydantic import Field, BaseModel

# Load environment variables
load_dotenv()

class Config(BaseModel):
    """Application configuration"""
    
    # OpenAI Configuration
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"))
    
    # Blogger Configuration
    blogger_api_key: str = Field(default_factory=lambda: os.getenv("BLOGGER_API_KEY", ""))
    blogger_blog_id: str = Field(default_factory=lambda: os.getenv("BLOGGER_BLOG_ID", ""))
    
    # Google OAuth
    google_client_id: str = Field(default_factory=lambda: os.getenv("GOOGLE_CLIENT_ID", ""))
    google_client_secret: str = Field(default_factory=lambda: os.getenv("GOOGLE_CLIENT_SECRET", ""))
    
    # SEO Tools
    semrush_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("SEMRUSH_API_KEY"))
    ahrefs_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("AHREFS_API_KEY"))
    
    # Social Media
    linkedin_access_token: Optional[str] = Field(default_factory=lambda: os.getenv("LINKEDIN_ACCESS_TOKEN"))
    twitter_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("TWITTER_API_KEY"))
    twitter_api_secret: Optional[str] = Field(default_factory=lambda: os.getenv("TWITTER_API_SECRET"))
    twitter_access_token: Optional[str] = Field(default_factory=lambda: os.getenv("TWITTER_ACCESS_TOKEN"))
    twitter_access_secret: Optional[str] = Field(default_factory=lambda: os.getenv("TWITTER_ACCESS_SECRET"))
    facebook_page_access_token: Optional[str] = Field(default_factory=lambda: os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN"))
    
    # Image Generation
    stability_ai_key: Optional[str] = Field(default_factory=lambda: os.getenv("STABILITY_AI_KEY"))
    
    # Blog Configuration
    blog_domain: str = Field(default_factory=lambda: os.getenv("BLOG_DOMAIN", ""))
    blog_niche: str = Field(default_factory=lambda: os.getenv("BLOG_NICHE", "technology"))
    target_audience: str = Field(default_factory=lambda: os.getenv("TARGET_AUDIENCE", "general"))
    
    # Project Paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent / "data")
    output_dir: Path = Field(default_factory=lambda: Path(__file__).parent / "output")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

# Global config instance
config = Config()
