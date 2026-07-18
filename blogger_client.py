"""
Blogger API client for fetching and publishing blog content
"""
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/blogger']


class BloggerClient:
    """Client for interacting with Blogger API"""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google OAuth"""
        token_path = config.data_dir / 'token.json'
        credentials_path = config.data_dir / 'credentials.json'
        
        # Check if we have existing valid credentials
        if token_path.exists():
            self.credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        
        # If credentials are invalid or missing, get new ones
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                try:
                    self.credentials.refresh(Request())
                except Exception as e:
                    logger.warning(f"Token refresh failed: {e}")
                    logger.info("Deleting expired token and re-authenticating...")
                    # Delete expired token file
                    if token_path.exists():
                        token_path.unlink()
                    self.credentials = None
            
            # If still no valid credentials, perform full authentication
            if not self.credentials or not self.credentials.valid:
                if not credentials_path.exists():
                    raise FileNotFoundError(
                        "credentials.json not found. Please download it from Google Cloud Console "
                        "and place it in the data directory."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), SCOPES
                )
                self.credentials = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(token_path, 'w') as token:
                token.write(self.credentials.to_json())
        
        # Build the service
        self.service = build('blogger', 'v3', credentials=self.credentials)
        logger.info("Successfully authenticated with Blogger API")
    
    def get_blog_info(self) -> Dict:
        """Get blog information"""
        try:
            blog = self.service.blogs().get(blogId=config.blogger_blog_id).execute()
            return blog
        except HttpError as e:
            logger.error(f"Error fetching blog info: {e}")
            raise
    
    def get_all_posts(self, fetch_bodies: bool = True) -> List[Dict]:
        """Fetch all blog posts"""
        posts = []
        page_token = None
        
        try:
            while True:
                response = self.service.posts().list(
                    blogId=config.blogger_blog_id,
                    fetchBodies=fetch_bodies,
                    pageToken=page_token,
                    maxResults=50
                ).execute()
                
                posts.extend(response.get('items', []))
                page_token = response.get('nextPageToken')
                
                if not page_token:
                    break
            
            logger.info(f"Fetched {len(posts)} posts from blog")
            return posts
        
        except HttpError as e:
            logger.error(f"Error fetching posts: {e}")
            raise
    
    def get_post(self, post_id: str) -> Dict:
        """Get a specific post by ID"""
        try:
            post = self.service.posts().get(
                blogId=config.blogger_blog_id,
                postId=post_id
            ).execute()
            return post
        except HttpError as e:
            logger.error(f"Error fetching post {post_id}: {e}")
            raise
    
    def create_post(self, title: str, content: str, 
                   labels: Optional[List[str]] = None,
                   is_draft: bool = False,
                   search_description: Optional[str] = None) -> Dict:
        """Create a new blog post"""
        try:
            body = {
                'title': title,
                'content': content,
                'labels': labels or []
            }
            
            # Add search description if provided
            if search_description:
                body['searchDescription'] = search_description
            
            post = self.service.posts().insert(
                blogId=config.blogger_blog_id,
                body=body,
                isDraft=is_draft
            ).execute()
            
            logger.info(f"Created post: {title} (ID: {post['id']})")
            return post
        
        except HttpError as e:
            logger.error(f"Error creating post: {e}")
            raise
    
    def update_post(self, post_id: str, title: str, content: str,
                   labels: Optional[List[str]] = None) -> Dict:
        """Update an existing blog post"""
        try:
            body = {
                'title': title,
                'content': content,
                'labels': labels or []
            }
            
            post = self.service.posts().update(
                blogId=config.blogger_blog_id,
                postId=post_id,
                body=body
            ).execute()
            
            logger.info(f"Updated post: {title} (ID: {post['id']})")
            return post
        
        except HttpError as e:
            logger.error(f"Error updating post: {e}")
            raise
    
    def publish_post(self, post_id: str) -> Dict:
        """Publish a draft post"""
        try:
            post = self.service.posts().publish(
                blogId=config.blogger_blog_id,
                postId=post_id
            ).execute()
            
            logger.info(f"Published post (ID: {post['id']})")
            return post
        
        except HttpError as e:
            logger.error(f"Error publishing post: {e}")
            raise
    
    def delete_post(self, post_id: str):
        """Delete a blog post"""
        try:
            self.service.posts().delete(
                blogId=config.blogger_blog_id,
                postId=post_id
            ).execute()
            logger.info(f"Deleted post (ID: {post_id})")
        
        except HttpError as e:
            logger.error(f"Error deleting post: {e}")
            raise
    
    def search_posts(self, query: str) -> List[Dict]:
        """Search posts by query"""
        try:
            response = self.service.posts().search(
                blogId=config.blogger_blog_id,
                q=query
            ).execute()
            
            posts = response.get('items', [])
            logger.info(f"Found {len(posts)} posts matching '{query}'")
            return posts
        
        except HttpError as e:
            logger.error(f"Error searching posts: {e}")
            raise
    
    def get_post_comments(self, post_id: str) -> List[Dict]:
        """Get comments for a specific post"""
        try:
            response = self.service.comments().list(
                blogId=config.blogger_blog_id,
                postId=post_id
            ).execute()
            
            comments = response.get('items', [])
            logger.info(f"Fetched {len(comments)} comments for post {post_id}")
            return comments
        
        except HttpError as e:
            logger.error(f"Error fetching comments: {e}")
            raise
    
    def get_blog_by_url(self, blog_url: str) -> Dict:
        """Get blog information by URL"""
        try:
            blog = self.service.blogs().getByUrl(url=blog_url).execute()
            return blog
        except HttpError as e:
            logger.error(f"Error fetching blog by URL: {e}")
            raise
