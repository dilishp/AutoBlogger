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
    
    # Model Configuration - Different models for different workflows
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    openai_model_content: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL_CONTENT", "gpt-4o"))
    openai_model_digital_product: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL_DIGITAL_PRODUCT", "gpt-4o"))
    openai_model_seo: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL_SEO", "gpt-4o"))
    openai_model_social: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL_SOCIAL", "gpt-4o"))
    
    # Token Configuration - Optimal tokens for different workflows
    max_tokens_content: int = Field(default_factory=lambda: int(os.getenv("MAX_TOKENS_CONTENT", "2000")))
    max_tokens_digital_product: int = Field(default_factory=lambda: int(os.getenv("MAX_TOKENS_DIGITAL_PRODUCT", "4000")))
    max_tokens_seo: int = Field(default_factory=lambda: int(os.getenv("MAX_TOKENS_SEO", "1500")))
    max_tokens_social: int = Field(default_factory=lambda: int(os.getenv("MAX_TOKENS_SOCIAL", "1000")))
    
    # Topic file configuration
    topics_file_path: str = Field(default_factory=lambda: os.getenv("TOPICS_FILE_PATH", "data/topics.txt"))
    
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
