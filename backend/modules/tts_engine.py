import torch
import numpy as np
import io
import os
from pathlib import Path

# Fallback TTS engine nếu Valtec không hoạt động
class SimpleTTS:
    def __init__(self):
        print("Initializing SimpleTTS fallback engine")
        self.sample_rate = 16000
        
    def text_to_speech(self, text, output_path=None, language="vi"):
        """
        Simple TTS fallback - tạo audio từ văn bản
        (Trong thực tế, đây là placeholder - sẽ cần tích hợp thư viện TTS thực)
        """
        print(f"Processing text: {text[:50]}...")
        
        # Tạo tone đơn giản (placeholder)
        duration = len(text) * 0.1  # 100ms mỗi ký tự
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Tạo sóng sine với tần số thay đổi
        freq = 220 + np.sin(np.linspace(0, 10, len(t))) * 50
        audio = 0.5 * np.sin(2 * np.pi * freq * t)
        
        # Thêm fade in/out
        fade_samples = int(self.sample_rate * 0.1)
        audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
        audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        if output_path:
            import soundfile as sf
            sf.write(output_path, audio, self.sample_rate)
            return output_path
        
        return audio.tobytes()

class ValtecTTS:
    def __init__(self, use_fallback=False):
        self.use_fallback = use_fallback
        self.fallback_tts = SimpleTTS()
        
        if not use_fallback:
            try:
                self._load_valtec_model()
            except Exception as e:
                print(f"Failed to load Valtec model: {e}")
                print("Using fallback TTS engine")
                self.use_fallback = True
    
    def _load_valtec_model(self):
        """Load Valtec-TTS model"""
        try:
            from transformers import VitsModel, AutoTokenizer
            
            print("Loading Valtec-TTS model...")
            self.model = VitsModel.from_pretrained("valtec-ai/valtec-tts-base")
            self.tokenizer = AutoTokenizer.from_pretrained("valtec-ai/valtec-tts-base")
            
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            
            print(f"Valtec-TTS model loaded successfully on {self.device}")
            self.use_fallback = False
            
        except Exception as e:
            print(f"Error loading Valtec-TTS: {e}")
            raise
    
    def text_to_speech(self, text, output_path=None, language="vi"):
        """Convert text to speech"""
        if self.use_fallback:
            return self.fallback_tts.text_to_speech(text, output_path, language)
        
        try:
            # Tokenize và tạo speech
            inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                output = self.model(**inputs)
            
            # Lấy waveform
            waveform = output.waveform.cpu().numpy().squeeze()
            
            # Normalize
            waveform = waveform / np.max(np.abs(waveform))
            
            if output_path:
                import soundfile as sf
                sf.write(output_path, waveform, self.model.config.sampling_rate)
                return output_path
            
            # Convert to bytes
            import soundfile as sf
            buffer = io.BytesIO()
            sf.write(buffer, waveform, self.model.config.sampling_rate, format='WAV')
            return buffer.getvalue()
            
        except Exception as e:
            print(f"Error in TTS generation: {e}")
            print("Falling back to simple TTS")
            return self.fallback_tts.text_to_speech(text, output_path, language)

# Singleton instance
tts_engine = ValtecTTS(use_fallback=True)  # Tạm dùng fallback