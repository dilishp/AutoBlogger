"""
YouTube video generation system with engaging scripts and AI-generated visuals
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
from openai import OpenAI
from config import config
from image_generator import ImageGenerator
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VideoScene:
    """Represents a single scene in the video"""
    scene_number: int
    script_text: str
    duration_seconds: float
    image_prompt: str
    image_path: Optional[str] = None
    text_overlay: Optional[str] = None


@dataclass
class YouTubeScript:
    """Represents a complete YouTube video script"""
    title: str
    hook: str
    scenes: List[VideoScene]
    call_to_action: str
    total_duration: float
    tags: List[str]
    description: str


class YouTubeScriptGenerator:
    """Generates engaging YouTube video scripts"""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.openai_api_key)
        self.blog_niche = config.blog_niche
        self.target_audience = config.target_audience
    
    def generate_script_from_blog_post(self, blog_title: str, 
                                       blog_content: str,
                                       target_duration: float = 60.0) -> YouTubeScript:
        """Generate an engaging YouTube script from a blog post"""
        logger.info(f"Generating YouTube script from blog: {blog_title}")
        
        # Calculate number of scenes based on target duration
        avg_scene_duration = 5.0  # 5 seconds per scene
        num_scenes = int(target_duration / avg_scene_duration)
        
        response = self.client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an expert YouTube content creator specializing in {self.blog_niche}.
                    You create highly engaging, retention-focused video scripts that tell a cohesive visual story.
                    
                    Your scripts follow YouTube best practices:
                    - Start with a powerful hook in the first 3 seconds
                    - Create a narrative arc that builds logically from scene to scene
                    - Each scene should visually progress the story forward
                    - Use visual storytelling that viewers can easily follow
                    - Include clear visual transitions between concepts
                    - End with strong call-to-action
                    - Optimize for watch time and engagement
                    
                    CRITICAL: The visual descriptions must form a coherent story that viewers can follow:
                    - Scene 1: Introduction/hook with establishing shot
                    - Scene 2: Problem statement with visual evidence
                    - Scene 3: Solution introduction with clear visual
                    - Scene 4: Step-by-step demonstration
                    - Scene 5: Results/benefits visualization
                    - Scene 6: Conclusion and call-to-action
                    
                    Target audience: {self.target_audience}
                    Video duration: {target_duration} seconds
                    Number of scenes: {num_scenes}
                    
                    IMPORTANT: Always reference the YouTube channel "CatchyBytes by Techy" with URL https://www.youtube.com/@catchybytes71 in the call-to-action and description."""
                },
                {
                    "role": "user",
                    "content": f"""Create an engaging YouTube video script based on this blog post:

Blog Title: {blog_title}
Blog Content: {blog_content[:3000]}

Requirements:
1. Create a catchy, SEO-optimized video title (different from blog title)
2. Write a powerful 3-second hook that grabs attention immediately
3. Create {num_scenes} scenes, each lasting ~{avg_scene_duration} seconds
4. Each scene should have:
   - Script text (what the narrator says - keep it concise for the scene duration)
   - Visual description (detailed, specific, and story-driven - what should be shown on screen)
   - Text overlay (key point to display as text - max 10 words)
5. CRITICAL: Visual descriptions must tell a progressive story:
   - Each scene should logically connect to the next
   - Use visual metaphors and analogies that are easy to understand
   - Include specific visual elements (colors, objects, actions)
   - Make the visual flow intuitive and followable
6. Include a strong call-to-action at the end directing viewers to subscribe to "CatchyBytes by Techy" at https://www.youtube.com/@catchybytes71
7. Generate 5-10 relevant YouTube tags
8. Write a compelling video description (under 5000 characters) that includes the channel name and URL

Script style:
- Conversational and energetic
- Use questions and statements to engage
- Include surprising facts or statistics
- Create emotional connection
- Keep sentences short and punchy
- Match script length to scene duration (approximately {avg_scene_duration} seconds per scene)

Return as JSON with these fields:
- title
- hook
- scenes (array with: script_text, visual_description, text_overlay)
- call_to_action
- tags (array)
- description"""
                }
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        try:
            script_data = json.loads(response.choices[0].message.content)
            
            # Convert to VideoScene objects
            scenes = []
            for i, scene_data in enumerate(script_data['scenes']):
                scene = VideoScene(
                    scene_number=i + 1,
                    script_text=scene_data['script_text'],
                    duration_seconds=avg_scene_duration,
                    image_prompt=scene_data['visual_description'],
                    text_overlay=scene_data.get('text_overlay', '')
                )
                scenes.append(scene)
            
            # Create YouTubeScript object
            youtube_script = YouTubeScript(
                title=script_data['title'],
                hook=script_data['hook'],
                scenes=scenes,
                call_to_action=script_data['call_to_action'],
                total_duration=len(scenes) * avg_scene_duration,
                tags=script_data['tags'],
                description=script_data['description']
            )
            
            logger.info(f"Generated YouTube script with {len(scenes)} scenes")
            return youtube_script
        
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing script response: {e}")
            raise
        except KeyError as e:
            logger.error(f"Missing expected field in script data: {e}")
            raise


class VideoImageGenerator:
    """Generates images for video scenes"""
    
    def __init__(self):
        self.image_generator = ImageGenerator()
        self.output_dir = config.output_dir / "video_images"
        self.output_dir.mkdir(parents=True, exist_ok=True)


class AudioGenerator:
    """Generates narration audio using text-to-speech"""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.openai_api_key)
        self.output_dir = config.output_dir / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_scene_audio(self, scene: VideoScene, scene_number: int, skip_existing: bool = True) -> str:
        """Generate audio for a single scene"""
        logger.info(f"Generating audio for scene {scene_number}...")
        
        audio_path = self.output_dir / f"scene_{scene_number}_audio.mp3"
        
        # Check if audio already exists
        if skip_existing and audio_path.exists():
            logger.info(f"Scene {scene_number} audio already exists, reusing: {audio_path}")
            return str(audio_path)
        
        try:
            # Use OpenAI's TTS API
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
                input=scene.script_text
            )
            
            # Save audio file
            response.stream_to_file(str(audio_path))
            
            logger.info(f"Scene {scene_number} audio generated: {audio_path}")
            return str(audio_path)
        
        except Exception as e:
            logger.error(f"Scene {scene_number} audio generation failed: {e}")
            raise
    
    def generate_narration_audio(self, script: YouTubeScript) -> str:
        """Generate audio narration for the entire script (legacy method)"""
        logger.info("Generating narration audio...")
        
        # Combine all scene scripts into one continuous narration
        full_narration = script.hook + "\n\n"
        for scene in script.scenes:
            full_narration += scene.script_text + " "
        full_narration += "\n\n" + script.call_to_action
        
        try:
            # Use OpenAI's TTS API
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
                input=full_narration
            )
            
            # Save audio file
            audio_path = self.output_dir / "narration.mp3"
            response.stream_to_file(str(audio_path))
            
            logger.info(f"Audio narration generated: {audio_path}")
            return str(audio_path)
        
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise
    
    def generate_per_scene_audio(self, script: YouTubeScript, hook_audio: str = None, cta_audio: str = None) -> List[str]:
        """Generate separate audio files for each scene for perfect synchronization"""
        logger.info(f"Generating per-scene audio for {len(script.scenes)} scenes...")
        
        audio_paths = []
        
        # Add hook audio if provided
        if hook_audio:
            audio_paths.append(hook_audio)
        
        # Generate audio for each scene
        for i, scene in enumerate(script.scenes):
            scene_audio_path = self.generate_scene_audio(scene, i + 1)
            audio_paths.append(scene_audio_path)
        
        # Add CTA audio if provided
        if cta_audio:
            audio_paths.append(cta_audio)
        
        logger.info(f"Generated {len(audio_paths)} audio files")
        return audio_paths
    
    def normalize_audio(self, audio_path: str, boost_db: float = 3.0) -> str:
        """Normalize audio and boost volume"""
        logger.info(f"Normalizing and boosting audio: {audio_path}")
        
        try:
            import pydub
            from pydub import AudioSegment
            from pydub.effects import normalize
            
            # Load audio
            audio = AudioSegment.from_mp3(audio_path)
            
            # Normalize audio
            audio = normalize(audio)
            
            # Boost volume
            audio = audio + boost_db
            
            # Save normalized audio
            normalized_path = audio_path.replace(".mp3", "_normalized.mp3")
            audio.export(normalized_path, format="mp3")
            
            logger.info(f"Audio normalized and boosted: {normalized_path}")
            return normalized_path
        
        except ImportError as e:
            logger.warning(f"pydub not installed or import failed: {e}, skipping audio normalization")
            return audio_path
        except Exception as e:
            logger.error(f"Audio normalization failed: {e}")
            return audio_path


class VideoImageGenerator:
    """Generates images for video scenes"""
    
    def __init__(self):
        self.image_generator = ImageGenerator()
        self.output_dir = config.output_dir / "video_images"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_scene_images(self, script: YouTubeScript, skip_existing: bool = True) -> YouTubeScript:
        """Generate images for all scenes in the script"""
        logger.info(f"Generating images for {len(script.scenes)} scenes")
        
        # Extract image prompts from scenes
        image_prompts = [scene.image_prompt for scene in script.scenes]
        
        # Check if images already exist
        existing_images = list(self.output_dir.glob("image_*.png"))
        if skip_existing and len(existing_images) >= len(script.scenes):
            logger.info(f"Found {len(existing_images)} existing images, reusing them")
            for i, scene in enumerate(script.scenes):
                if i < len(existing_images):
                    scene.image_path = str(existing_images[i])
                    logger.info(f"Scene {i+1}: Reusing existing image at {existing_images[i]}")
            return script
        
        # Generate images using existing image generator
        image_paths = self.image_generator.generate_images(
            prompts=image_prompts,
            upload_to_cloudinary=False  # Keep local for video processing
        )
        
        # Assign images to scenes
        for i, scene in enumerate(script.scenes):
            if i < len(image_paths):
                scene.image_path = image_paths[i]
                logger.info(f"Scene {i+1}: Generated image at {image_paths[i]}")
            else:
                logger.warning(f"Scene {i+1}: No image generated")
        
        logger.info(f"Generated {len(image_paths)} scene images")
        return script


class VideoComposer:
    """Composes images into a video with transitions and text overlays"""
    
    def __init__(self):
        self.output_dir = config.output_dir / "videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def compose_video(self, script: YouTubeScript, 
                     scene_audio_paths: Optional[List[str]] = None,
                     output_filename: str = "youtube_video.mp4",
                     add_transitions: bool = True,
                     add_text_overlays: bool = True) -> str:
        """Compose images into a video file with per-scene audio synchronization"""
        logger.info("Composing video from scenes...")
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np
            from moviepy import ImageSequenceClip
            
            # Collect image paths
            image_paths = []
            for scene in script.scenes:
                if scene.image_path and Path(scene.image_path).exists():
                    image_paths.append(scene.image_path)
                else:
                    logger.warning(f"Missing image for scene {scene.scene_number}, skipping")
            
            if not image_paths:
                raise ValueError("No valid images found for video composition")
            
            logger.info(f"Found {len(image_paths)} images for composition")
            
            # Calculate duration per image
            durations = [scene.duration_seconds for scene in script.scenes if scene.image_path]
            
            # Add text overlays to images if enabled
            if add_text_overlays:
                logger.info("Adding text overlays...")
                clips_with_text = []
                
                for i, (img_path, scene) in enumerate(zip(image_paths, script.scenes)):
                    if scene.text_overlay:
                        # Load image
                        img = Image.open(img_path)
                        
                        # Create text overlay
                        draw = ImageDraw.Draw(img)
                        
                        # Try to use a default font, fallback to basic
                        try:
                            font = ImageFont.truetype("arial.ttf", 40)
                        except:
                            font = ImageFont.load_default()
                        
                        # Get text bounding box
                        bbox = draw.textbbox((0, 0), scene.text_overlay, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        
                        # Calculate position (bottom center)
                        img_width, img_height = img.size
                        x = (img_width - text_width) // 2
                        y = img_height - text_height - 50
                        
                        # Add text with shadow for readability
                        draw.text((x + 2, y + 2), scene.text_overlay, font=font, fill=(0, 0, 0))
                        draw.text((x, y), scene.text_overlay, font=font, fill=(255, 255, 255))
                        
                        # Save modified image
                        temp_path = self.output_dir / f"scene_{i}_with_text.png"
                        img.save(temp_path)
                        clips_with_text.append(str(temp_path))
                    else:
                        clips_with_text.append(img_path)
                
                image_paths = clips_with_text
            
            # Create video clips for each scene with synchronized audio
            from moviepy import ImageSequenceClip, AudioFileClip
            
            scene_clips = []
            
            for i, (img_path, scene) in enumerate(zip(image_paths, script.scenes)):
                # Get audio for this scene if available
                scene_audio_path = None
                if scene_audio_paths and i < len(scene_audio_paths):
                    scene_audio_path = scene_audio_paths[i]
                
                # Create video clip for this scene
                scene_clip = ImageSequenceClip([img_path], durations=[scene.duration_seconds])
                scene_clip = scene_clip.with_fps(24)
                
                # Add audio to this scene if available
                if scene_audio_path and Path(scene_audio_path).exists():
                    logger.info(f"Adding audio to scene {i+1}: {scene_audio_path}")
                    audio_clip = AudioFileClip(scene_audio_path)
                    
                    # Adjust scene duration to match audio duration
                    if audio_clip.duration > scene.duration_seconds:
                        # Extend scene to match audio
                        scene_clip = scene_clip.with_duration(audio_clip.duration)
                    elif scene_clip.duration > audio_clip.duration:
                        # Trim scene to match audio
                        scene_clip = scene_clip.subclipped(0, audio_clip.duration)
                    
                    scene_clip = scene_clip.with_audio(audio_clip)
                    logger.info(f"Scene {i+1} audio synced (duration: {audio_clip.duration:.2f}s)")
                else:
                    logger.warning(f"No audio for scene {i+1}, using default duration")
                
                scene_clips.append(scene_clip)
            
            # Concatenate all scene clips
            if scene_clips:
                from moviepy import concatenate_videoclips
                clip = concatenate_videoclips(scene_clips)
                logger.info(f"Concatenated {len(scene_clips)} scenes")
            else:
                raise ValueError("No scene clips created")
            
            # Write video file
            output_path = self.output_dir / output_filename
            
            # Sanitize filename for Windows (remove invalid characters)
            import re
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', output_filename)
            output_path = self.output_dir / safe_filename
            
            logger.info(f"Writing video to: {output_path}")
            clip.write_videofile(str(output_path), codec='libx264', audio_codec='aac', fps=24)
            
            # Verify video file was created and has content
            if output_path.exists():
                file_size = output_path.stat().st_size
                logger.info(f"Video file created with size: {file_size} bytes")
                if file_size == 0:
                    raise ValueError("Video file was created but has 0 bytes - composition failed")
            else:
                raise ValueError(".Video file was not created")
            
            logger.info(f"Video successfully created: {output_path}")
            return str(output_path)
        
        except ImportError as e:
            logger.error(f"Missing required library: {e}")
            logger.error("Please install moviepy: pip install moviepy")
            raise
        except Exception as e:
            logger.error(f"Video composition failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise


class YouTubeVideoGenerator:
    """Main orchestrator for YouTube video generation"""
    
    def __init__(self):
        self.script_generator = YouTubeScriptGenerator()
        self.image_generator = VideoImageGenerator()
        self.audio_generator = AudioGenerator()
        self.video_composer = VideoComposer()
    
    def generate_video(self, blog_title: str, 
                      blog_content: str,
                      target_duration: float = 60.0,
                      output_filename: str = "youtube_video.mp4",
                      add_audio: bool = True,
                      normalize_audio: bool = True) -> Dict[str, any]:
        """Generate complete YouTube video from blog post"""
        logger.info(f"Starting YouTube video generation for: {blog_title}")
        
        try:
            # Step 1: Generate script
            logger.info("Step 1: Generating engaging script...")
            script = self.script_generator.generate_script_from_blog_post(
                blog_title, blog_content, target_duration
            )
            
            # Step 2: Generate scene images
            logger.info("Step 2: Generating scene images...")
            script = self.image_generator.generate_scene_images(script)
            
            # Step 3: Generate per-scene audio narration
            scene_audio_paths = None
            if add_audio:
                logger.info("Step 3: Generating per-scene audio narration...")
                scene_audio_paths = self.audio_generator.generate_per_scene_audio(script)
                
                # Normalize audio if requested
                if normalize_audio:
                    logger.info("Step 3.5: Normalizing and boosting audio...")
                    normalized_paths = []
                    for audio_path in scene_audio_paths:
                        normalized = self.audio_generator.normalize_audio(audio_path, boost_db=3.0)
                        normalized_paths.append(normalized)
                    scene_audio_paths = normalized_paths
            
            # Step 4: Compose video with synchronized audio
            logger.info("Step 4: Composing video with synchronized audio...")
            video_path = self.video_composer.compose_video(
                script, scene_audio_paths=scene_audio_paths, output_filename=output_filename,
                add_transitions=True,
                add_text_overlays=True
            )
            
            # Return metadata
            metadata = {
                'video_path': video_path,
                'title': script.title,
                'description': script.description,
                'tags': script.tags,
                'duration': script.total_duration,
                'num_scenes': len(script.scenes),
                'hook': script.hook,
                'call_to_action': script.call_to_action
            }
            
            logger.info("YouTube video generation completed successfully!")
            return metadata
        
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise


if __name__ == "__main__":
    # Test the video generator
    generator = YouTubeVideoGenerator()
    
    test_blog_title = "How to Speed Up TypeScript Builds in Monorepos"
    test_blog_content = """
    TypeScript build times can become a major bottleneck in large monorepos. 
    This guide shows you practical techniques to reduce build times by up to 70%.
    
    Key strategies include:
    1. Using project references for incremental builds
    2. Configuring proper tsconfig paths
    3. Leveraging build caching
    4. Optimizing dependency management
    
    These techniques have been tested on monorepos with 50+ projects.
    """
    
    try:
        metadata = generator.generate_video(
            blog_title=test_blog_title,
            blog_content=test_blog_content,
            target_duration=30.0,
            output_filename="test_video_improved.mp4",
            add_audio=True,
            normalize_audio=True
        )
        
        print("\n" + "="*50)
        print("VIDEO GENERATION COMPLETED")
        print("="*50)
        print(f"Video Path: {metadata['video_path']}")
        print(f"Title: {metadata['title']}")
        print(f"Duration: {metadata['duration']} seconds")
        print(f"Scenes: {metadata['num_scenes']}")
        print(f"Tags: {', '.join(metadata['tags'])}")
        print("="*50)
    
    except Exception as e:
        print(f"Error: {e}")
