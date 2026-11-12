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
    image_frames: Optional[List[str]] = None


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
        logger.info(f"Blog content length: {len(blog_content)} characters")

        # Use a worked, deterministic example for Fenwick trees. Generic image
        # prompts are unreliable for explaining exact array and tree values.
        if "fenwick" in blog_title.lower() or "binary indexed tree" in blog_title.lower():
            return self._generate_fenwick_tutorial()
        
        # Calculate number of scenes based on target duration
        avg_scene_duration = 7.5  # Allow time to explain and read each scene
        num_scenes = max(1, round(target_duration / avg_scene_duration))
        
        # Use more content for better context (up to 8000 characters)
        content_to_use = blog_content[:8000] if len(blog_content) > 8000 else blog_content
        logger.info(f"Using {len(content_to_use)} characters for script generation")
        
        response = self.client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an expert YouTube content creator specializing in {self.blog_niche}.
                    You create engaging educational videos that explain technical concepts clearly and at a measured pace.
                    
                    Your scripts follow YouTube best practices:
                    - Start with a powerful hook in the first 3 seconds
                    - Create a narrative arc that builds logically from scene to scene
                    - Explain as if the viewer is new to the topic; define technical terms before relying on them
                    - Cover one main idea per scene and connect it clearly to the previous scene
                    - Use a small worked example when the topic supports one; show inputs, each important step, and the result
                    - Keep example values consistent across scenes and make each calculation or state change explicit
                    - Include a practical use case that explains when the concept is useful
                    - Make visuals show the same example evolving step by step, with readable labels and values
                    - Leave enough narration time for a beginner to follow; do not cram multiple operations into one scene
                    - Include clear visual transitions between concepts
                    - End with strong call-to-action
                    - Optimize for watch time and engagement
                    
                    CRITICAL INSTRUCTIONS:
                    - You MUST base the script ENTIRELY on the provided blog post content
                    - Do NOT hallucinate or invent content not in the blog post
                    - The visual descriptions MUST match the actual programming topic of the blog post
                    - The script narration MUST accurately reflect the blog post's technical subject matter
                    - Read the blog content carefully and extract the actual main concept, subtopics, and key points
                    - Create visuals that specifically illustrate the programming concepts discussed in the blog post
                    - Prefer concrete examples and visual diagrams over abstract summaries
                    - For algorithms or data structures, show a small input, how internal state is formed, and how an operation changes it
                    
                    CRITICAL: The visual descriptions must form a coherent story that viewers can follow:
                    - Begin with a relatable problem and state what the viewer will learn
                    - Introduce the concept in plain language and define new terms
                    - Spend most scenes walking through one coherent worked example, including intermediate steps
                    - Explain a practical use case and summarize the key idea before the call-to-action
                    
                    Target audience: {self.target_audience}
                    Video duration: {target_duration} seconds
                    Number of scenes: {num_scenes}
                    
                    IMPORTANT: Always reference the YouTube channel "CatchyBytes by Techy" with URL https://www.youtube.com/@catchybytes71 in the call-to-action and description."""
                },
                {
                    "role": "user",
                    "content": f"""Create an engaging YouTube video script based EXACTLY on this blog post:

Blog Title: {blog_title}

Blog Content (READ CAREFULLY - this is the ONLY source material):
{content_to_use}

CRITICAL REQUIREMENTS:
1. The script MUST be about the actual topic in the blog post above
2. Create a catchy, SEO-optimized video title (different from blog title but same topic)
3. Write a powerful 3-second hook that grabs attention immediately about THIS topic
4. Create {num_scenes} scenes, each lasting about {avg_scene_duration} seconds
5. Each scene should have:
   - Script text (one clear idea, with enough detail to explain it within the scene duration)
   - Visual description (detailed and readable; continue the same example across scenes)
   - Text overlay (key point to display as text - max 10 words)
6. CRITICAL: Visual descriptions MUST tell a progressive story about the blog's actual topic:
   - Each scene should logically connect to the next
   - Use visual metaphors and analogies that are easy to understand
   - Include specific visual elements (colors, objects, actions) relevant to the blog topic
   - Make the visual flow intuitive and followable
7. Include a strong call-to-action at the end directing viewers to subscribe to "CatchyBytes by Techy" at https://www.youtube.com/@catchybytes71
8. Generate 5-10 relevant YouTube tags specific to this blog topic
9. Write a compelling video description (under 5000 characters) that includes the channel name and URL

Script style:
- Conversational, calm, and clearly paced
- Use questions and statements to engage
- Include surprising facts or statistics from the blog
- Create emotional connection
- Use short, complete sentences and brief pauses between steps
- Explain what changed and why; avoid unexplained jumps in calculations or logic
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
            
            # Log the generated script for verification
            logger.info(f"Generated video title: {script_data.get('title', 'N/A')}")
            logger.info(f"Generated hook: {script_data.get('hook', 'N/A')[:100]}...")
            logger.info(f"Number of scenes generated: {len(script_data.get('scenes', []))}")
            
            # Log first few scene scripts to verify topic
            for i, scene in enumerate(script_data.get('scenes', [])[:3]):
                logger.info(f"Scene {i+1} script: {scene.get('script_text', 'N/A')[:100]}...")
            
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

    def _generate_fenwick_tutorial(self) -> YouTubeScript:
        """Build a paced Fenwick-tree walkthrough with a numerically checked example."""
        narration = [
            "Suppose these are daily click counts. We want totals for any prefix of days, even as counts change.",
            "Use one-based positions. The Fenwick array stores partial sums, not copies of the original values.",
            "Each position covers a block ending there. Index two covers positions one and two; index four covers one through four.",
            "Building the tree gives these entries: three stores A two plus A one, which equals three.",
            "Index four stores the first four values: two plus one plus three plus four, which equals ten.",
            "To query the first five days, start at five. Its stored block covers only day five, with value five.",
            "After using BIT five, subtract its one-item block to reach four. BIT four contributes ten; the prefix total is fifteen.",
            "Now increase the original value at index three by two. The value changes from three to five.",
            "Start the update at three. BIT three stores A three, so adding two changes its value from three to five.",
            "Move to four, the next block containing A three. Add two there too: BIT four changes from ten to twelve.",
            "Move to eight, whose block covers the whole array. Add two: BIT eight changes from twenty-four to twenty-six.",
            "Query the first five days again: entry five is still five, and entry four is now twelve. The new total is seventeen.",
            "This is useful for live click or sales counts: update one day's count, then quickly ask for totals through any day.",
        ]
        visual_prompts = [f"FENWICK_STEP_{i + 1}" for i in range(len(narration))]
        overlays = [
            "Daily counts: find prefix totals",
            "Original array and Fenwick array",
            "Each index stores a range",
            "Build: BIT[2] = A[1] + A[2] = 3",
            "BIT[4] = A[1..4] = 10",
            "Query starts at index 5",
            "BIT[5] + BIT[4] = 5 + 10 = 15",
            "Update A[3]: 3 → 5 (add 2)",
            "BIT[3]: 3 → 5",
            "BIT[4]: 10 → 12",
            "BIT[8]: 24 → 26",
            "New prefix total: 5 + 12 = 17",
            "Live clicks, sales, or event counts",
        ]
        scenes = [
            VideoScene(
                scene_number=i + 1,
                script_text=text,
                duration_seconds=8.0,
                image_prompt=visual_prompts[i],
                text_overlay=overlays[i],
            )
            for i, text in enumerate(narration)
        ]
        return YouTubeScript(
            title="Fenwick Tree, Step by Step: Build, Query, and Update",
            hook=narration[0],
            scenes=scenes,
            call_to_action="",
            total_duration=sum(scene.duration_seconds for scene in scenes),
            tags=["Fenwick Tree", "Binary Indexed Tree", "Prefix Sum", "Data Structures", "Algorithms"],
            description=(
                "A worked Fenwick tree example using daily counts [2, 1, 3, 4, 5, 2, 1, 6]. "
                "See how the partial sums are stored, how a prefix query reaches 15, and how adding 2 at index 3 "
                "updates indices 3, 4, and 8 before the prefix becomes 17."
            ),
        )


class VideoImageGenerator:
    """Generates images for video scenes"""
    
    def __init__(self):
        self.image_generator = ImageGenerator()
        self.output_dir = config.output_dir / "video_images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_fenwick_visuals(self, script: YouTubeScript) -> List[str]:
        """Render exact, consistent diagrams for the Fenwick worked example."""
        from PIL import Image, ImageDraw, ImageFont

        width, height = 1280, 720
        values = [2, 1, 3, 4, 5, 2, 1, 6]
        bit = [2, 3, 3, 10, 5, 7, 1, 24]
        ranges = []
        for index in range(1, 9):
            lowbit = index & -index
            ranges.append(f"A[{index - lowbit + 1}..{index}]")

        def font(size: int):
            for name in ("arial.ttf", "DejaVuSans.ttf"):
                try:
                    return ImageFont.truetype(name, size)
                except OSError:
                    pass
            return ImageFont.load_default()

        f_title, f_label, f_value, f_small = font(38), font(22), font(28), font(18)
        paths = []
        for scene_index, scene in enumerate(script.scenes, start=1):
            updated = scene_index >= 8
            current_values = values.copy()
            if updated:
                current_values[2] = 5
            current_bit = bit.copy()
            if scene_index >= 9:
                current_bit[2] = 5
            if scene_index >= 10:
                current_bit[3] = 12
            if scene_index >= 11:
                current_bit[7] = 26

            image = Image.new("RGB", (width, height), (12, 20, 38))
            draw = ImageDraw.Draw(image)
            draw.text((64, 42), "Fenwick Tree: One Example, Step by Step", font=f_title, fill=(245, 248, 255))
            draw.text((66, 105), f"Step {scene_index} of {len(script.scenes)}   |   1-based indices", font=f_label, fill=(164, 184, 210))

            x0, cell_w, cell_h = 64, 144, 96
            draw.text((x0, 168), "ORIGINAL ARRAY A", font=f_label, fill=(111, 205, 255))
            for i, value in enumerate(current_values):
                x = x0 + i * cell_w
                active = (scene_index >= 8 and i == 2)
                fill = (112, 72, 32) if active else (31, 45, 68)
                outline = (255, 184, 77) if active else (78, 103, 137)
                draw.rounded_rectangle((x, 205, x + 112, 205 + cell_h), radius=12, fill=fill, outline=outline, width=3)
                draw.text((x + 42, 214), str(i + 1), font=f_small, fill=(169, 190, 217))
                draw.text((x + 48, 244), str(value), font=f_value, fill=(255, 255, 255))

            if scene_index >= 2:
                draw.text((x0, 346), "FENWICK ARRAY BIT  (each entry stores a block sum)", font=f_label, fill=(122, 235, 173))
                for i, value in enumerate(current_bit):
                    x = x0 + i * cell_w
                    active_indices = set()
                    if scene_index == 4:
                        active_indices = {1}
                    elif scene_index == 5:
                        active_indices = {3}
                    elif scene_index == 6:
                        active_indices = {4}
                    elif scene_index in (7, 12):
                        active_indices = {3, 4}
                    elif scene_index == 9:
                        active_indices = {2}
                    elif scene_index == 10:
                        active_indices = {3}
                    elif scene_index == 11:
                        active_indices = {7}
                    active = i in active_indices
                    fill = (26, 88, 70) if active else (31, 45, 68)
                    outline = (105, 245, 176) if active else (78, 103, 137)
                    draw.rounded_rectangle((x, 383, x + 112, 505), radius=12, fill=fill, outline=outline, width=3)
                    draw.text((x + 47, 391), str(i + 1), font=f_small, fill=(169, 190, 217))
                    draw.text((x + 43, 421), str(value), font=f_value, fill=(255, 255, 255))
                    draw.text((x + 13, 468), ranges[i], font=f_small, fill=(170, 196, 222))

            footer = scene.text_overlay or ""
            draw.rounded_rectangle((64, 560, 1216, 650), radius=14, fill=(22, 34, 56), outline=(58, 79, 111), width=2)
            draw.text((88, 584), footer, font=f_label, fill=(255, 222, 144))

            image_path = self.output_dir / f"fenwick_step_{scene_index:02d}.png"
            image.save(image_path)
            paths.append(str(image_path))

            # Animate the value changing instead of only showing a before/after
            # slide. Each spoken update gets a short count-up in the matching cell.
            animated_cell = None
            animated_values = None
            if scene_index == 8:
                animated_cell, animated_values = ("array", 2), [3, 3, 4, 4, 5, 5, 5, 5]
            elif scene_index == 9:
                animated_cell, animated_values = ("bit", 2), [3, 3, 4, 4, 5, 5, 5, 5]
            elif scene_index == 10:
                animated_cell, animated_values = ("bit", 3), [10, 10, 11, 11, 12, 12, 12, 12]
            elif scene_index == 11:
                animated_cell, animated_values = ("bit", 7), [24, 24, 25, 25, 26, 26, 26, 26]

            if animated_cell:
                row, cell_index = animated_cell
                frame_paths = []
                for frame_number, frame_value in enumerate(animated_values):
                    frame = Image.open(image_path).convert("RGB")
                    frame_draw = ImageDraw.Draw(frame)
                    cell_x = x0 + cell_index * cell_w
                    if row == "array":
                        bounds = (cell_x + 20, 238, cell_x + 94, 281)
                        text_y = 244
                        cell_fill = (112, 72, 32)
                    else:
                        bounds = (cell_x + 20, 415, cell_x + 94, 459)
                        text_y = 421
                        cell_fill = (26, 88, 70)
                    frame_draw.rectangle(bounds, fill=cell_fill)
                    value_text = str(frame_value)
                    text_box = frame_draw.textbbox((0, 0), value_text, font=f_value)
                    text_width = text_box[2] - text_box[0]
                    frame_draw.text((cell_x + (112 - text_width) / 2, text_y), value_text, font=f_value, fill=(255, 255, 255))
                    frame_path = self.output_dir / f"fenwick_step_{scene_index:02d}_frame_{frame_number:02d}.png"
                    frame.save(frame_path)
                    frame_paths.append(str(frame_path))
                script.scenes[scene_index - 1].image_frames = frame_paths
        return paths


class AudioGenerator:
    """Generates narration audio using text-to-speech"""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.openai_api_key)
        self.output_dir = config.output_dir / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_scene_audio(self, scene: VideoScene, scene_number: int, skip_existing: bool = False) -> str:
        """Generate audio for a single scene"""
        logger.info(f"Generating audio for scene {scene_number}...")
        logger.info(f"Scene {scene_number} script text: {scene.script_text[:100]}...")
        
        audio_path = self.output_dir / f"scene_{scene_number}_audio.mp3"
        
        # Check if audio already exists
        if skip_existing and audio_path.exists():
            logger.warning(f"Scene {scene_number} audio already exists, REUSING: {audio_path}")
            logger.warning(f"This may cause mismatch with current script content!")
            return str(audio_path)
        
        try:
            # Use OpenAI's TTS API
            speech_options = {
                "model": "tts-1",
                "voice": "alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
                "input": scene.script_text,
                "speed": 0.9,
            }
            if scene.image_prompt.startswith("FENWICK_STEP_"):
                speech_options["speed"] = 0.85
            response = self.client.audio.speech.create(**speech_options)
            
            # Save audio file
            response.stream_to_file(str(audio_path))
            
            logger.info(f"Scene {scene_number} audio GENERATED: {audio_path}")
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
    
    def normalize_audio(self, audio_path: str, boost_db: float = 0.0) -> str:
        """Normalize audio and boost volume"""
        logger.info(f"Normalizing and boosting audio: {audio_path}")
        
        try:
            import pydub
            from pydub import AudioSegment
            from pydub.effects import normalize
            
            # Load audio
            audio = AudioSegment.from_mp3(audio_path)
            
            # Normalize with headroom, then cap any requested boost so the
            # voice does not clip after normalization.
            audio = normalize(audio, headroom=1.0)
            safe_boost_db = max(0.0, min(boost_db, 0.5))
            if safe_boost_db:
                audio = audio + safe_boost_db
            
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
    
    def generate_scene_images(self, script: YouTubeScript, skip_existing: bool = False) -> YouTubeScript:
        """Generate images for all scenes in the script"""
        logger.info(f"Generating images for {len(script.scenes)} scenes")

        if script.scenes and script.scenes[0].image_prompt.startswith("FENWICK_STEP_"):
            image_paths = self._generate_fenwick_visuals(script)
            for scene, image_path in zip(script.scenes, image_paths):
                scene.image_path = image_path
            logger.info("Generated deterministic Fenwick tree teaching diagrams")
            return script
        
        # Extract image prompts from scenes
        image_prompts = [scene.image_prompt for scene in script.scenes]
        
        # Check if images already exist
        existing_images = list(self.output_dir.glob("image_*.png"))
        if skip_existing and len(existing_images) >= len(script.scenes):
            logger.warning(f"Found {len(existing_images)} existing images, REUSING them")
            logger.warning(f"This may cause mismatch with current script content!")
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
                    if scene.text_overlay and not scene.image_prompt.startswith("FENWICK_STEP_"):
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
                
                # Use frame sequences for Fenwick update steps so changed values
                # visibly count up in the original array and affected BIT cells.
                if scene.image_frames:
                    frame_duration = scene.duration_seconds / len(scene.image_frames)
                    scene_clip = ImageSequenceClip(
                        scene.image_frames,
                        durations=[frame_duration] * len(scene.image_frames),
                    )
                else:
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
                        # Keep the scene visible briefly after narration so the
                        # viewer can read the diagram before the next idea.
                        scene_clip = scene_clip.with_duration(
                            max(scene.duration_seconds, audio_clip.duration + 0.75)
                        )
                    
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
                        normalized = self.audio_generator.normalize_audio(audio_path, boost_db=0.0)
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
    
    test_blog_title = "Understanding Recursion: From Basics to Advanced Patterns"
    test_blog_content = """
    Recursion is a powerful programming technique where a function calls itself to solve problems.
    It's essential for tree traversals, divide-and-conquer algorithms, and many other scenarios.
    
    Key concepts of recursion:
    1. Base case - the condition that stops recursion
    2. Recursive case - the function calling itself with simpler input
    3. Stack management - understanding call stack behavior
    4. Time and space complexity analysis
    
    Common recursion patterns include factorial calculation, Fibonacci sequences, and tree traversals.
    Understanding when to use recursion vs iteration is crucial for writing efficient code.
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
