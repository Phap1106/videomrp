import os
import json
import logging
import tempfile
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    import google.generativeai as genai
    import openai
    from deepgram import Deepgram
    from valtec_tts import TTS as ValtecTTS
except ImportError as e:
    logging.warning(f"Some AI libraries not installed: {e}")

from config import Config

logger = logging.getLogger(__name__)

class AIEnhancer:
    """AI enhancement services for videos"""
    
    def __init__(self):
        # Initialize AI services
        self.setup_services()
    
    def setup_services(self):
        """Setup AI service connections"""
        # Deepgram for speech-to-text
        self.deepgram = None
        if Config.DEEPGRAM_API_KEY:
            try:
                self.deepgram = Deepgram(Config.DEEPGRAM_API_KEY)
                logger.info("Deepgram initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Deepgram: {str(e)}")
        
        # Google Gemini
        self.gemini = None
        if Config.GEMINI_API_KEY:
            try:
                genai.configure(api_key=Config.GEMINI_API_KEY)
                self.gemini = genai
                logger.info("Gemini initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {str(e)}")
        
        # OpenAI
        self.openai_client = None
        if Config.OPENAI_API_KEY:
            try:
                openai.api_key = Config.OPENAI_API_KEY
                self.openai_client = openai
                logger.info("OpenAI initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {str(e)}")
        
        # Valtec TTS (Vietnamese Text-to-Speech)
        self.valtec_tts = None
        try:
            self.valtec_tts = ValtecTTS()
            logger.info("Valtec TTS initialized")
        except Exception as e:
            logger.warning(f"Valtec TTS not available: {str(e)}")
    
    def check_services(self) -> Dict[str, bool]:
        """Check which AI services are available"""
        return {
            'deepgram': self.deepgram is not None,
            'gemini': self.gemini is not None,
            'openai': self.openai_client is not None,
            'valtec_tts': self.valtec_tts is not None
        }
    
    def generate_subtitles(self, video_path: str, language: str = 'vi') -> List[Dict]:
        """Generate subtitles from video audio"""
        try:
            if not self.deepgram:
                logger.warning("Deepgram not configured")
                return []
            
            # Extract audio first
            from modules.video_processor import VideoProcessor
            processor = VideoProcessor(video_path)
            audio_path = processor.extract_audio(video_path)
            
            if not audio_path or not os.path.exists(audio_path):
                logger.error("Failed to extract audio")
                return []
            
            # Transcribe with Deepgram
            with open(audio_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Set transcription options
            options = {
                'punctuate': True,
                'diarize': True,
                'numerals': True,
                'paragraphs': True,
                'language': language,
                'model': 'general',
            }
            
            # Make API request
            response = self.deepgram.transcription.sync_prerecorded(
                {'buffer': audio_data, 'mimetype': 'audio/mp3'},
                options
            )
            
            # Parse response
            subtitles = []
            if 'results' in response:
                transcript = response['results']['channels'][0]['alternatives'][0]
                
                if 'paragraphs' in transcript:
                    for para in transcript['paragraphs']['paragraphs']:
                        subtitles.append({
                            'start': para['start'],
                            'end': para['end'],
                            'text': para['sentences'][0]['text']
                        })
                elif 'words' in transcript:
                    # Group words into sentences
                    current_sentence = []
                    current_start = None
                    
                    for word in transcript['words']:
                        if not current_start:
                            current_start = word['start']
                        
                        current_sentence.append(word['word'])
                        
                        # End sentence at punctuation or after 5 words
                        if word.get('punctuated_word', '').endswith(('.', '!', '?')) or len(current_sentence) >= 5:
                            subtitles.append({
                                'start': current_start,
                                'end': word['end'],
                                'text': ' '.join(current_sentence)
                            })
                            current_sentence = []
                            current_start = None
            
            # Clean up audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            logger.info(f"Generated {len(subtitles)} subtitle segments")
            return subtitles
            
        except Exception as e:
            logger.error(f"Error generating subtitles: {str(e)}")
            return []
    
    def generate_voiceover(self, text: str, speaker: str = None, 
                          speed: float = 1.0) -> Optional[str]:
        """Generate voiceover audio using Valtec TTS"""
        try:
            if not self.valtec_tts:
                logger.warning("Valtec TTS not available")
                return None
            
            if speaker is None:
                speaker = Config.VALTEC_DEFAULT_SPEAKER
            
            # Check if speaker is valid
            available_speakers = ['NF', 'SF', 'NM1', 'SM', 'NM2']
            if speaker not in available_speakers:
                logger.warning(f"Speaker {speaker} not available, using {available_speakers[0]}")
                speaker = available_speakers[0]
            
            # Generate audio file
            output_path = str(Config.TEMP_FOLDER / f"voiceover_{speaker}_{hash(text)}.wav")
            
            # Use Valtec TTS
            self.valtec_tts.speak(
                text,
                speaker=speaker,
                speed=speed,
                output_path=output_path
            )
            
            logger.info(f"Voiceover generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating voiceover: {str(e)}")
            return None
    
    def analyze_video_content(self, video_path: str) -> Dict[str, Any]:
        """Analyze video content using AI"""
        try:
            # Extract key frames for analysis
            key_frames = self.extract_key_frames(video_path, num_frames=5)
            
            analysis = {
                'key_moments': [],
                'sentiment': 'neutral',
                'topics': [],
                'description': '',
                'hashtags': []
            }
            
            # Use Gemini if available
            if self.gemini:
                analysis.update(self._analyze_with_gemini(key_frames))
            # Fallback to OpenAI
            elif self.openai_client:
                analysis.update(self._analyze_with_openai(key_frames))
            
            logger.info(f"Video analysis completed: {len(analysis['topics'])} topics found")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing video content: {str(e)}")
            return {
                'key_moments': [],
                'sentiment': 'neutral',
                'topics': [],
                'description': 'Analysis failed',
                'hashtags': []
            }
    
    def extract_key_frames(self, video_path: str, num_frames: int = 5) -> List[str]:
        """Extract key frames from video for analysis"""
        try:
            import cv2
            import tempfile
            
            key_frames = []
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames == 0:
                logger.warning("Video has no frames")
                return []
            
            # Extract frames at regular intervals
            interval = max(1, total_frames // num_frames)
            
            for i in range(num_frames):
                frame_idx = i * interval
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if ret:
                    # Save frame as temp file
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                        cv2.imwrite(temp_file.name, frame)
                        key_frames.append(temp_file.name)
            
            cap.release()
            logger.info(f"Extracted {len(key_frames)} key frames")
            return key_frames
            
        except Exception as e:
            logger.error(f"Error extracting key frames: {str(e)}")
            return []
    
    def _analyze_with_gemini(self, image_paths: List[str]) -> Dict[str, Any]:
        """Analyze images with Gemini"""
        try:
            model = self.gemini.GenerativeModel('gemini-pro-vision')
            
            # Prepare prompt
            prompt = """
            Analyze these video frames and provide:
            1. Key moments/timestamps for highlights
            2. Overall sentiment (positive/negative/neutral)
            3. Main topics/activities
            4. Brief description
            5. Relevant hashtags (5-10)
            
            Respond in JSON format.
            """
            
            # Prepare images
            images = []
            for img_path in image_paths:
                if os.path.exists(img_path):
                    img = self.gemini.upload_file(img_path)
                    images.append(img)
            
            # Generate content
            response = model.generate_content([prompt] + images)
            
            # Parse response
            try:
                # Extract JSON from response
                text = response.text.strip()
                if text.startswith('```json'):
                    text = text[7:-3]  # Remove markdown code blocks
                elif text.startswith('```'):
                    text = text[3:-3]
                
                analysis = json.loads(text)
                return analysis
            except json.JSONDecodeError:
                # Fallback to simple parsing
                return {
                    'description': response.text[:200],
                    'hashtags': ['#video', '#content', '#ai']
                }
                
        except Exception as e:
            logger.error(f"Gemini analysis error: {str(e)}")
            return {}
    
    def _analyze_with_openai(self, image_paths: List[str]) -> Dict[str, Any]:
        """Analyze images with OpenAI"""
        try:
            # For now, use text-only analysis
            # In production, use vision capabilities
            
            prompt = """
            Analyze a video based on these descriptions:
            - It contains various scenes
            - May have people, objects, activities
            
            Provide analysis in JSON format with:
            - key_moments: list of interesting timestamps
            - sentiment: overall sentiment
            - topics: main topics
            - description: brief description
            - hashtags: relevant hashtags
            """
            
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a video content analyzer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            text = response.choices[0].message.content
            try:
                return json.loads(text)
            except:
                return {
                    'description': text[:200],
                    'hashtags': ['#ai', '#video', '#content']
                }
                
        except Exception as e:
            logger.error(f"OpenAI analysis error: {str(e)}")
            return {}
    
    def generate_title_description(self, video_path: str, 
                                  platform: str = 'tiktok') -> Dict[str, str]:
        """Generate title and description for video"""
        try:
            analysis = self.analyze_video_content(video_path)
            
            title = analysis.get('description', 'Interesting Video')[:60]
            description = analysis.get('description', 'Check out this video!')[:500]
            
            # Add hashtags
            hashtags = ' '.join(analysis.get('hashtags', ['#video', '#content'])[:5])
            description += f"\n\n{hashtags}"
            
            # Platform-specific formatting
            if platform == 'tiktok':
                # TikTok prefers shorter descriptions with trending hashtags
                title = title[:30]
                description = description[:150]
            
            return {
                'title': title,
                'description': description,
                'hashtags': hashtags
            }
            
        except Exception as e:
            logger.error(f"Error generating title/description: {str(e)}")
            return {
                'title': 'Awesome Video',
                'description': 'Check out this amazing content! #video #content',
                'hashtags': '#video #content'
            }
    
    def enhance_script(self, script: str, style: str = 'engaging') -> str:
        """Enhance script/text using AI"""
        try:
            if self.gemini:
                model = self.gemini.GenerativeModel('gemini-pro')
                prompt = f"Make this script more {style} and engaging:\n\n{script}"
                
                response = model.generate_content(prompt)
                return response.text
            
            elif self.openai_client:
                response = self.openai_client.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"You are a script writer who makes content {style}."},
                        {"role": "user", "content": f"Improve this script:\n\n{script}"}
                    ],
                    temperature=0.8,
                    max_tokens=1000
                )
                return response.choices[0].message.content
            
            return script  # Return original if no AI available
            
        except Exception as e:
            logger.error(f"Error enhancing script: {str(e)}")
            return script