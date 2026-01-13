"""
Highlight Extractor Service
Extracts the best moments from long videos using AI analysis
"""

import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any

from app.core.logger import logger
from app.core.config import settings
from app.utils.ffmpeg_ops import ffmpeg_ops


class HighlightExtractor:
    """Extract highlights from long videos"""
    
    def __init__(self):
        self.ai_provider = getattr(settings, "AI_PROVIDER", "auto")
        self._openai_client = None
        self._gemini_client = None
    
    def _get_openai_client(self):
        """Get or create OpenAI client"""
        if self._openai_client is None:
            try:
                from openai import AsyncOpenAI
                self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to init OpenAI client: {e}")
        return self._openai_client
    
    def _get_gemini_client(self):
        """Get or create Gemini client"""
        if self._gemini_client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GOOGLE_API_KEY)
                self._gemini_client = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                logger.error(f"Failed to init Gemini client: {e}")
        return self._gemini_client
    
    async def analyze_transcript_for_highlights(
        self,
        transcript: str,
        segments: List[Dict],
        target_duration: int = 60,
        num_highlights: int = 5,
        style: str = "engaging",
        ai_provider: Optional[str] = None
    ) -> List[Dict]:
        """
        Analyze transcript and extract highlight segments
        
        Returns list of: {"start": float, "end": float, "score": float, "reason": str}
        """
        try:
            provider = ai_provider or self.ai_provider
            
            # Build prompt
            prompt = f"""Phân tích đoạn transcript sau và tìm {num_highlights} đoạn hay nhất cho video {style}.

TRANSCRIPT VỚI TIMESTAMPS:
{self._format_transcript_with_timestamps(segments)}

YÊU CẦU:
1. Tìm {num_highlights} đoạn hay nhất (engaging, dramatic, funny, or informative)
2. Mỗi đoạn nên dài khoảng {target_duration // num_highlights} giây
3. Tổng thời lượng tất cả đoạn khoảng {target_duration} giây
4. Ưu tiên đoạn có content viral potential

PHONG CÁCH: {style}
- engaging: Đoạn hấp dẫn, lôi cuốn
- informative: Đoạn có thông tin giá trị
- dramatic: Đoạn kịch tính, cảm xúc
- funny: Đoạn hài hước, vui nhộn

TRẢ VỀ JSON ARRAY (KHÔNG CÓ TEXT NGOÀI):
[
    {{"start": 0.0, "end": 15.0, "score": 0.95, "reason": "Mở đầu hấp dẫn"}},
    {{"start": 45.5, "end": 58.0, "score": 0.88, "reason": "Twist bất ngờ"}}
]

CHỈ TRẢ VỀ JSON ARRAY, KHÔNG CÓ GÌ KHÁC."""

            # Call AI
            result = await self._call_ai(prompt, provider)
            
            # Parse result
            highlights = self._parse_highlights(result)
            
            # Sort by score
            highlights.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            return highlights[:num_highlights]
            
        except Exception as e:
            logger.error(f"Highlight analysis error: {e}")
            # Return fallback highlight selection
            return self._fallback_highlights(segments, target_duration, num_highlights)
    
    def _format_transcript_with_timestamps(self, segments: List[Dict]) -> str:
        """Format transcript segments with timestamps"""
        lines = []
        for seg in segments:
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            text = seg.get("text", "")
            lines.append(f"[{start:.1f}s - {end:.1f}s]: {text}")
        return "\n".join(lines)
    
    async def _call_ai(self, prompt: str, provider: str) -> str:
        """Call AI provider"""
        if provider == "auto":
            if settings.OPENAI_API_KEY:
                provider = "openai"
            elif settings.GOOGLE_API_KEY:
                provider = "gemini"
            else:
                return "[]"
        
        try:
            if provider == "openai":
                client = self._get_openai_client()
                if client:
                    response = await client.chat.completions.create(
                        model=settings.OPENAI_MODEL or "gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7
                    )
                    return response.choices[0].message.content
            elif provider == "gemini":
                client = self._get_gemini_client()
                if client:
                    response = await client.generate_content_async(prompt)
                    return response.text
        except Exception as e:
            logger.error(f"AI call failed: {e}")
        
        return "[]"
    
    def _parse_highlights(self, result: str) -> List[Dict]:
        """Parse AI response to highlights list"""
        import json
        
        try:
            # Find JSON array in response
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                json_str = result[start:end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to parse highlights: {e}")
        
        return []
    
    def _fallback_highlights(
        self, 
        segments: List[Dict], 
        target_duration: int,
        num_highlights: int
    ) -> List[Dict]:
        """Fallback: select evenly spaced segments"""
        if not segments:
            return []
        
        total_duration = segments[-1].get("end", 60) if segments else 60
        segment_duration = target_duration / num_highlights
        
        highlights = []
        step = total_duration / num_highlights
        
        for i in range(num_highlights):
            start = i * step
            end = min(start + segment_duration, total_duration)
            highlights.append({
                "start": start,
                "end": end,
                "score": 0.5,
                "reason": f"Đoạn {i+1} (tự động chọn)"
            })
        
        return highlights
    
    async def extract_highlights(
        self,
        video_path: Path,
        transcript_segments: List[Dict],
        target_duration: int = 60,
        num_highlights: int = 5,
        style: str = "engaging",
        output_path: Optional[Path] = None,
        ai_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full highlight extraction pipeline:
        1. Analyze transcript for best moments
        2. Extract video segments
        3. Concatenate into final highlight video
        """
        try:
            job_id = str(uuid.uuid4())[:8]
            
            # Analyze transcript
            logger.info(f"Analyzing transcript for highlights...")
            highlights = await self.analyze_transcript_for_highlights(
                transcript="",  # Will use segments
                segments=transcript_segments,
                target_duration=target_duration,
                num_highlights=num_highlights,
                style=style,
                ai_provider=ai_provider
            )
            
            if not highlights:
                raise ValueError("No highlights found")
            
            # Extract segments
            logger.info(f"Extracting {len(highlights)} highlight segments...")
            temp_dir = Path(settings.TEMP_DIR) / f"highlights_{job_id}"
            segment_paths = await ffmpeg_ops.extract_segments(
                video_path=video_path,
                segments=highlights,
                output_dir=temp_dir
            )
            
            # Concatenate segments
            logger.info("Concatenating highlight segments...")
            output_path = output_path or Path(settings.PROCESSED_DIR) / f"highlights_{job_id}.mp4"
            final_video = await ffmpeg_ops.concatenate_videos(
                video_paths=segment_paths,
                output_path=output_path
            )
            
            # Cleanup temp segments
            for seg_path in segment_paths:
                try:
                    seg_path.unlink()
                except:
                    pass
            try:
                temp_dir.rmdir()
            except:
                pass
            
            # Get final video info
            video_info = await ffmpeg_ops.get_video_info(final_video)
            
            return {
                "success": True,
                "job_id": job_id,
                "output_path": str(final_video),
                "output_url": f"/api/videos/highlights/{job_id}",
                "duration": video_info.get("duration", 0),
                "highlights": highlights,
                "num_highlights": len(highlights),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Highlight extraction error: {e}")
            return {
                "success": False,
                "job_id": job_id if 'job_id' in locals() else None,
                "output_path": None,
                "highlights": [],
                "error": str(e)
            }


# Global instance
highlight_extractor = HighlightExtractor()
