"""
EOA AI Chatbot Service
Intelligent chatbot for collecting user requirements and generating stories with audio
"""

import uuid
import json
from typing import Optional, List, Dict, Any
from pathlib import Path

from app.core.logger import logger
from app.core.config import settings


# System prompt for EOA chatbot
EOA_SYSTEM_PROMPT = """Bạn là EOA - trợ lý AI thông minh chuyên tạo nội dung audio/video sáng tạo.

NHIỆM VỤ CỦA BẠN:
1. Thu thập thông tin từ người dùng về câu chuyện họ muốn tạo
2. Đưa ra gợi ý và dàn ý câu chuyện
3. Xác nhận các thông số như: độ dài, phong cách, giọng điệu
4. Khi người dùng nhập "@EOA xử lý" thì bạn sẽ tạo câu chuyện hoàn chỉnh

PHONG CÁCH GIAO TIẾP:
- Thân thiện, chuyên nghiệp
- Hỏi từng bước để thu thập thông tin
- Đưa ra gợi ý cụ thể
- Tóm tắt thông tin đã thu thập sau mỗi vài câu hỏi

THÔNG TIN CẦN THU THẬP:
1. Chủ đề/nội dung câu chuyện
2. Phong cách (kịch tính, hài hước, cảm động, giáo dục,...)
3. Độ dài mong muốn (ngắn: 30-60s, vừa: 1-3 phút, dài: 3-5 phút)
4. Đối tượng khán giả (TikTok, YouTube, podcast,...)
5. Giọng điệu (nam/nữ, trẻ/trưởng thành,...)
6. Có muốn thêm nhạc nền không
7. Tốc độ giọng nói

KHI NGƯỜI DÙNG NHẬP "@EOA xử lý":
Trả về JSON với format:
{
    "action": "process",
    "story_outline": "Dàn ý câu chuyện",
    "estimated_duration": 60,
    "style": "dramatic",
    "tone": "engaging",
    "target_audience": "tiktok",
    "voice_gender": "female",
    "speaking_speed": 1.0,
    "add_pauses": true,
    "add_background_music": false
}

LƯU Ý: Luôn ghi nhớ toàn bộ cuộc hội thoại và thông tin đã thu thập."""


class EOAChatbot:
    """EOA AI Chatbot for intelligent story generation"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.ai_provider: str = getattr(settings, "AI_PROVIDER", "auto")
        
        # Initialize AI clients lazily
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
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """Get existing session or create new one"""
        if session_id and session_id in self.sessions:
            return session_id
        
        new_id = session_id or str(uuid.uuid4())
        self.sessions[new_id] = {
            "id": new_id,
            "messages": [],
            "collected_info": {},
            "ready_to_process": False,
        }
        return new_id
    
    def _build_conversation_context(self, session_id: str, new_message: str) -> List[Dict]:
        """Build conversation context for AI"""
        session = self.sessions.get(session_id, {})
        messages = session.get("messages", [])
        
        # Start with system prompt
        context = [{"role": "system", "content": EOA_SYSTEM_PROMPT}]
        
        # Add conversation history
        for msg in messages:
            context.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # Add new user message
        context.append({"role": "user", "content": new_message})
        
        return context
    
    def _extract_collected_info(self, response_text: str, current_info: Dict) -> Dict:
        """Extract structured info from AI response"""
        # Try to parse JSON if response contains it
        try:
            if '"action"' in response_text and '"process"' in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = response_text[start:end]
                    parsed = json.loads(json_str)
                    return {**current_info, **parsed}
        except:
            pass
        
        # Extract info from natural language (basic extraction)
        info = current_info.copy()
        
        lower_text = response_text.lower()
        
        # Detect style
        if "kịch tính" in lower_text or "dramatic" in lower_text:
            info["style"] = "dramatic"
        elif "hài hước" in lower_text or "humorous" in lower_text:
            info["style"] = "humorous"
        elif "cảm động" in lower_text or "emotional" in lower_text:
            info["style"] = "emotional"
        
        # Detect duration preference
        if "ngắn" in lower_text or "30 giây" in lower_text:
            info["estimated_duration"] = 30
        elif "1 phút" in lower_text or "60 giây" in lower_text:
            info["estimated_duration"] = 60
        elif "2 phút" in lower_text:
            info["estimated_duration"] = 120
        elif "3 phút" in lower_text:
            info["estimated_duration"] = 180
        
        return info
    
    def _check_ready_to_process(self, message: str) -> bool:
        """Check if user wants to process"""
        triggers = ["@eoa xử lý", "@eoa process", "@eoa tạo", "xử lý ngay", "tạo ngay"]
        lower_msg = message.lower().strip()
        return any(trigger in lower_msg for trigger in triggers)
    
    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        ai_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process chat message and return response"""
        try:
            # Get or create session
            session_id = self.get_or_create_session(session_id)
            session = self.sessions[session_id]
            
            # Restore history if provided
            if conversation_history:
                session["messages"] = [
                    {"role": m.get("role", "user"), "content": m.get("content", "")}
                    for m in conversation_history
                ]
            
            # Check if user wants to process
            ready_to_process = self._check_ready_to_process(message)
            
            # Build context
            context = self._build_conversation_context(session_id, message)
            
            # Add instruction to return JSON if ready to process
            if ready_to_process:
                context.append({
                    "role": "system",
                    "content": "Người dùng muốn xử lý. Hãy tóm tắt thông tin đã thu thập và trả về JSON config như hướng dẫn."
                })
            
            # Call AI
            provider = ai_provider or self.ai_provider
            response_text = await self._call_ai(context, provider)
            
            # Save messages
            session["messages"].append({"role": "user", "content": message})
            session["messages"].append({"role": "assistant", "content": response_text})
            
            # Extract collected info
            session["collected_info"] = self._extract_collected_info(
                response_text, 
                session.get("collected_info", {})
            )
            
            # Check if ready
            session["ready_to_process"] = ready_to_process or session["collected_info"].get("action") == "process"
            
            # Generate suggestions
            suggestions = self._generate_suggestions(session["collected_info"])
            
            return {
                "success": True,
                "message": response_text,
                "session_id": session_id,
                "suggestions": suggestions,
                "collected_info": session["collected_info"],
                "ready_to_process": session["ready_to_process"],
                "action_required": "process" if session["ready_to_process"] else None
            }
            
        except Exception as e:
            logger.error(f"EOA chat error: {e}")
            return {
                "success": False,
                "message": f"Xin lỗi, tôi gặp lỗi: {str(e)}. Vui lòng thử lại.",
                "session_id": session_id,
                "suggestions": [],
                "collected_info": {},
                "ready_to_process": False,
                "action_required": None
            }
    
    async def _call_ai(self, messages: List[Dict], provider: str = "auto") -> str:
        """Call AI provider"""
        # Auto-select provider
        if provider == "auto":
            if settings.OPENAI_API_KEY:
                provider = "openai"
            elif settings.GOOGLE_API_KEY:
                provider = "gemini"
            else:
                return self._mock_response(messages)
        
        try:
            if provider == "openai":
                return await self._call_openai(messages)
            elif provider == "gemini":
                return await self._call_gemini(messages)
            else:
                return self._mock_response(messages)
        except Exception as e:
            logger.error(f"AI call failed: {e}")
            return self._mock_response(messages)
    
    async def _call_openai(self, messages: List[Dict]) -> str:
        """Call OpenAI API"""
        client = self._get_openai_client()
        if not client:
            return self._mock_response(messages)
        
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL or "gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    
    async def _call_gemini(self, messages: List[Dict]) -> str:
        """Call Gemini API"""
        client = self._get_gemini_client()
        if not client:
            return self._mock_response(messages)
        
        # Convert to Gemini format
        prompt = "\n\n".join([
            f"{m['role'].upper()}: {m['content']}" 
            for m in messages
        ])
        
        response = await client.generate_content_async(prompt)
        return response.text
    
    def _mock_response(self, messages: List[Dict]) -> str:
        """Generate mock response for testing"""
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "").lower()
                break
        
        if "@eoa xử lý" in last_user_msg or "@eoa process" in last_user_msg:
            return """Tuyệt vời! Tôi đã thu thập đủ thông tin. Đây là cấu hình câu chuyện của bạn:

{
    "action": "process",
    "story_outline": "Câu chuyện kể về cuộc sống thường ngày với những tình huống bất ngờ và cảm xúc",
    "estimated_duration": 60,
    "style": "dramatic",
    "tone": "engaging",
    "target_audience": "tiktok",
    "voice_gender": "female",
    "speaking_speed": 1.0,
    "add_pauses": true,
    "add_background_music": false
}

Bấm nút "Tạo Audio" để EOA bắt đầu xử lý!"""
        
        return """Chào bạn! Tôi là EOA, trợ lý AI giúp bạn tạo nội dung audio sáng tạo. 🎙️

Tôi đã ghi nhận yêu cầu của bạn. Để tạo được câu chuyện phù hợp nhất, hãy cho tôi biết thêm:

1. **Phong cách câu chuyện** bạn muốn là gì? (Kịch tính, hài hước, cảm động,...)
2. **Độ dài mong muốn**? (30 giây, 1 phút, 2 phút,...)
3. **Đối tượng khán giả**? (TikTok, YouTube, Podcast,...)

💡 Khi đã sẵn sàng, hãy nhập **"@EOA xử lý"** để tôi tạo câu chuyện cho bạn!"""
    
    def _generate_suggestions(self, collected_info: Dict) -> List[str]:
        """Generate suggestions based on collected info"""
        suggestions = []
        
        if not collected_info.get("style"):
            suggestions.append("Chọn phong cách: Kịch tính / Hài hước / Cảm động")
        
        if not collected_info.get("estimated_duration"):
            suggestions.append("Chọn độ dài: 30 giây / 1 phút / 2 phút")
        
        if not collected_info.get("target_audience"):
            suggestions.append("Chọn nền tảng: TikTok / YouTube / Podcast")
        
        if collected_info.get("action") != "process":
            suggestions.append("Nhập '@EOA xử lý' khi sẵn sàng tạo audio")
        
        return suggestions
    
    async def process_and_generate(
        self,
        session_id: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        add_pauses: bool = True,
        ai_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate story and convert to audio"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "Session not found",
                    "story_text": "",
                    "audio_path": None
                }
            
            collected_info = session.get("collected_info", {})
            messages = session.get("messages", [])
            
            # Generate full story using AI
            story_text = await self._generate_story(messages, collected_info, ai_provider)
            
            # Generate audio using TTS
            from app.services.ai.tts_provider import get_tts_provider
            
            tts = await get_tts_provider(ai_provider or settings.TTS_PROVIDER)
            
            # Add natural pauses if requested
            if add_pauses:
                story_text = self._add_natural_pauses(story_text)
            
            output_path = Path(settings.PROCESSED_DIR) / f"eoa_audio_{session_id}.mp3"
            audio_path, _ = await tts.synthesize(
                text=story_text,
                voice=voice,
                speed=speed,
                output_path=output_path
            )
            
            # Calculate duration (approximate: ~150 words per minute)
            word_count = len(story_text.split())
            duration = (word_count / 150) * 60 / speed
            
            return {
                "success": True,
                "story_text": story_text,
                "audio_path": str(audio_path),
                "audio_url": f"/api/eoa/download/{session_id}",
                "duration": duration,
                "word_count": word_count,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"EOA process error: {e}")
            return {
                "success": False,
                "story_text": "",
                "audio_path": None,
                "error": str(e)
            }
    
    async def _generate_story(
        self, 
        messages: List[Dict], 
        config: Dict,
        ai_provider: Optional[str] = None
    ) -> str:
        """Generate full story based on conversation"""
        
        style = config.get("style", "dramatic")
        duration = config.get("estimated_duration", 60)
        outline = config.get("story_outline", "")
        
        # Calculate approximate word count from duration
        words_per_second = 2.5  # Average speaking rate
        target_words = int(duration * words_per_second)
        
        # Get professional conversational prompt
        from app.ai_prompts import VideoPrompts
        
        prompt = VideoPrompts.get_conversational_narration_prompt(
            topic=outline or "Video audio content",
            duration=duration,
            tone=style
        )
        
        prompt += f"\n\nTHÔNG TIN BỔ SUNG TỪ NGƯỜI DÙNG:\n- Dàn ý: {outline}\n- Phong cách: {style}\n- Yêu cầu đặc biệt: Phải là một cuộc hội thoại/lời thoại hấp dẫn."

        context = [
            {"role": "system", "content": "Bạn là chuyên gia viết kịch bản audio/video sáng tạo."}
        ]
        
        # Add relevant conversation history
        for msg in messages[-6:]:  # Last 6 messages for context
            context.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        context.append({"role": "user", "content": prompt})
        
        return await self._call_ai(context, ai_provider or self.ai_provider)
    
    def _add_natural_pauses(self, text: str) -> str:
        """Add natural pauses to text for TTS"""
        # Add pauses after sentences
        text = text.replace(". ", "... ")
        text = text.replace("! ", "!... ")
        text = text.replace("? ", "?... ")
        
        # Add shorter pauses after commas
        text = text.replace(", ", ",.. ")
        
        return text
    
    def clear_session(self, session_id: str):
        """Clear a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]


# Singleton instance
eoa_chatbot = EOAChatbot()
