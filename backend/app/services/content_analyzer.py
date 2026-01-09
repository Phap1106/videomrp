import openai
import google.generativeai as genai
from typing import List, Dict, Any, Optional
import json
import asyncio
from pathlib import Path
from loguru import logger
import time

from app.core.config import settings
from app.services.platform_detector import PlatformDetector
from app.ai_prompts import VideoPrompts


class ContentAnalyzer:
    """Analyze video content using AI"""
    
    def __init__(self):
        self.platform_detector = PlatformDetector()
        self.ai_provider = settings.AI_PROVIDER
        
        if self.ai_provider == "openai" and settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        elif self.ai_provider == "gemini" and settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        else:
            logger.warning("No AI API key configured, using mock analysis")
    
    async def analyze_video(
        self, 
        video_path: str, 
        platform: str, 
        video_type: str = "short",
        transcript: Optional[str] = None,
        segments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Analyze video content comprehensively"""
        logger.info(f"Analyzing video: {video_path} for {platform}/{video_type}")
        
        start_time = time.time()
        
        try:
            # Get transcript if not provided
            if not transcript or not segments:
                from app.services.text_detector import TextDetector
                detector = TextDetector()
                transcript, segments = await detector.extract_text(video_path)
            
            # Analyze content with AI
            analysis = await self._analyze_with_ai(transcript, platform, video_type)
            
            # Check copyright
            copyright_check = await self._check_copyright(transcript)
            
            # Generate editing instructions
            editing_instructions = await self._generate_editing_instructions(
                analysis, platform, video_type
            )
            
            # Generate hashtags and titles
            hashtags = await self._generate_hashtags(transcript, platform)
            
            processing_time = time.time() - start_time
            
            result = {
                "transcript": transcript,
                "segments": segments,
                "analysis": analysis,
                "copyright_check": copyright_check,
                "editing_instructions": editing_instructions,
                "hashtags": hashtags,
                "processing_time": processing_time,
                "video_metadata": await self._get_video_metadata(video_path),
            }
            
            logger.info(f"Analysis completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise Exception(f"Video analysis failed: {str(e)}")
    
    async def _analyze_with_ai(self, transcript: str, platform: str, video_type: str) -> Dict[str, Any]:
        """Analyze content using AI"""
        if not self._has_ai_credentials():
            return self._mock_analysis(transcript, platform, video_type)
        
        prompt = VideoPrompts.get_content_analysis_prompt(transcript, platform, video_type)
        
        try:
            if self.ai_provider == "openai":
                return await self._call_openai(prompt)
            elif self.ai_provider == "gemini":
                return await self._call_gemini(prompt)
            else:
                return self._mock_analysis(transcript, platform, video_type)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._mock_analysis(transcript, platform, video_type)
    
    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API"""
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": "You are a video content analysis expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """Call Google Gemini API"""
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = await model.generate_content_async(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 2000,
                }
            )
            
            # Parse JSON from response
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]  # Remove ```json and ```
            elif text.startswith("```"):
                text = text[3:-3]  # Remove ``` and ```
            
            result = json.loads(text)
            return result
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    async def _check_copyright(self, content: str) -> Dict[str, Any]:
        """Check for copyright issues"""
        if not self._has_ai_credentials():
            return self._mock_copyright_check()
        
        prompt = VideoPrompts.get_copyright_avoidance_prompt(content)
        
        try:
            if self.ai_provider == "openai":
                return await self._call_openai(prompt)
            elif self.ai_provider == "gemini":
                return await self._call_gemini(prompt)
            else:
                return self._mock_copyright_check()
        except Exception as e:
            logger.error(f"Copyright check failed: {e}")
            return self._mock_copyright_check()
    
    async def _generate_editing_instructions(
        self, 
        analysis: Dict[str, Any], 
        platform: str, 
        video_type: str
    ) -> Dict[str, Any]:
        """Generate editing instructions"""
        if not self._has_ai_credentials():
            return self._mock_editing_instructions(platform, video_type)
        
        prompt = VideoPrompts.get_editing_instructions_prompt(analysis, platform, video_type)
        
        try:
            if self.ai_provider == "openai":
                return await self._call_openai(prompt)
            elif self.ai_provider == "gemini":
                return await self._call_gemini(prompt)
            else:
                return self._mock_editing_instructions(platform, video_type)
        except Exception as e:
            logger.error(f"Editing instructions generation failed: {e}")
            return self._mock_editing_instructions(platform, video_type)
    
    async def _generate_hashtags(self, content: str, platform: str) -> Dict[str, Any]:
        """Generate hashtags and titles"""
        if not self._has_ai_credentials():
            return self._mock_hashtags(platform)
        
        prompt = VideoPrompts.get_hashtag_generation_prompt(content, platform)
        
        try:
            if self.ai_provider == "openai":
                return await self._call_openai(prompt)
            elif self.ai_provider == "gemini":
                return await self._call_gemini(prompt)
            else:
                return self._mock_hashtags(platform)
        except Exception as e:
            logger.error(f"Hashtag generation failed: {e}")
            return self._mock_hashtags(platform)
    
    async def _get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata"""
        try:
            import subprocess
            import json as json_module
            
            cmd = [
                settings.FFPROBE_PATH,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            metadata = json_module.loads(result.stdout)
            
            video_info = {
                "duration": float(metadata['format'].get('duration', 0)),
                "size": int(metadata['format'].get('size', 0)),
                "bitrate": int(metadata['format'].get('bit_rate', 0)),
                "format": metadata['format'].get('format_name', ''),
            }
            
            # Find video stream
            for stream in metadata.get('streams', []):
                if stream['codec_type'] == 'video':
                    video_info.update({
                        "width": stream.get('width', 0),
                        "height": stream.get('height', 0),
                        "codec": stream.get('codec_name', ''),
                        "fps": eval(stream.get('avg_frame_rate', '0/1')) if 'avg_frame_rate' in stream else 0,
                    })
                    break
            
            return video_info
            
        except Exception as e:
            logger.warning(f"Failed to get video metadata: {e}")
            return {}
    
    def _has_ai_credentials(self) -> bool:
        """Check if AI credentials are available"""
        if self.ai_provider == "openai":
            return bool(settings.OPENAI_API_KEY)
        elif self.ai_provider == "gemini":
            return bool(settings.GEMINI_API_KEY)
        return False
    
    def _mock_analysis(self, transcript: str, platform: str, video_type: str) -> Dict[str, Any]:
        """Mock analysis for testing"""
        return {
            "summary": "This is a mock analysis for testing purposes.",
            "category": "entertainment",
            "mood": "funny",
            "key_moments": [
                {
                    "start": 0,
                    "end": 10,
                    "description": "Opening scene",
                    "importance": "high",
                    "reason": "Hook for viewers"
                }
            ],
            "viral_potential": 75,
            "recommended_duration": 60,
            "editing_style": "fast_paced",
            "hashtag_suggestions": ["#funny", "#viral", "#test"],
            "title_suggestions": ["Test Video Title"],
            "platform_specific_notes": f"Mock analysis for {platform}"
        }
    
    def _mock_copyright_check(self) -> Dict[str, Any]:
        """Mock copyright check"""
        return {
            "copyright_risks": [],
            "safe_to_use_score": 100,
            "required_modifications": []
        }
    
    def _mock_editing_instructions(self, platform: str, video_type: str) -> Dict[str, Any]:
        """Mock editing instructions"""
        return {
            "total_duration_target": 60,
            "aspect_ratio": "9:16" if platform == "tiktok" else "16:9",
            "clips": [
                {
                    "start_time": 0,
                    "end_time": 60,
                    "action": "keep",
                    "reason": "Full video"
                }
            ],
            "platform_specific_settings": {
                "aspect_ratio": "9:16" if platform == "tiktok" else "16:9",
                "max_duration": 60,
                "watermark_removal": True
            }
        }
    
    def _mock_hashtags(self, platform: str) -> Dict[str, Any]:
        """Mock hashtags"""
        return {
            "hashtags": ["#test", "#video", "#edit"],
            "titles": ["Test Video"],
            "description": "Test description"
        }