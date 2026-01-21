"""
YouTube Video Analyzer - NLP Analysis Service
==============================================
Multi-provider NLP with fallback.
Providers: Gemini/GPT → Local spaCy/KeyBERT
"""

import asyncio
import re
from typing import Optional, Any
from dataclasses import dataclass
from collections import Counter

from app.core.logger import logger
from app.core.config import settings


@dataclass
class TopicSegment:
    """Topic segment with timing"""
    name: str
    start: float
    end: float
    keywords: list[str]


@dataclass
class EmotionSegment:
    """Emotion detection for a segment"""
    segment: str  # "0-30" format
    emotion: str
    confidence: float


@dataclass
class NLPResult:
    """Complete NLP analysis result"""
    topics: list[TopicSegment]
    keywords: list[str]
    keyphrases: list[str]
    sentiment: str  # positive, neutral, negative
    emotions: list[EmotionSegment]
    summary: str
    provider: str


class NLPProvider:
    """Base class for NLP providers"""
    
    name: str = "base"
    
    async def analyze(self, text: str, segments: list = None) -> Optional[NLPResult]:
        raise NotImplementedError


class GeminiNLPProvider(NLPProvider):
    """
    Google Gemini for NLP analysis
    Uses existing API key from settings
    """
    
    name = "gemini"
    
    async def analyze(self, text: str, segments: list = None) -> Optional[NLPResult]:
        """Analyze text using Gemini"""
        try:
            import google.generativeai as genai
            
            if not settings.GEMINI_API_KEY:
                return None
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-flash-latest")
            
            prompt = f"""Analyze this transcript and return a JSON object with:
1. "topics": array of {{name, keywords}} - main topics discussed
2. "keywords": array of top 20 single keywords
3. "keyphrases": array of top 10 important phrases (2-4 words)
4. "sentiment": "positive" or "neutral" or "negative"
5. "summary": brief summary in 2-3 sentences (max 200 words)

Transcript:
{text[:8000]}

Return ONLY valid JSON, no markdown."""

            loop = asyncio.get_event_loop()
            
            def _generate():
                response = model.generate_content(prompt)
                return response.text
            
            result_text = await loop.run_in_executor(None, _generate)
            
            # Parse JSON from response
            import json
            
            # Clean potential markdown
            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = re.sub(r"```\w*\n?", "", result_text)
                result_text = result_text.strip()
            
            data = json.loads(result_text)
            
            # Build topic segments
            topics = []
            for i, topic in enumerate(data.get("topics", [])):
                topics.append(TopicSegment(
                    name=topic.get("name", f"Topic {i+1}"),
                    start=0,  # Would need segment timing
                    end=0,
                    keywords=topic.get("keywords", [])
                ))
            
            return NLPResult(
                topics=topics,
                keywords=data.get("keywords", [])[:20],
                keyphrases=data.get("keyphrases", [])[:10],
                sentiment=data.get("sentiment", "neutral"),
                emotions=[],  # Gemini doesn't return emotions
                summary=data.get("summary", ""),
                provider=self.name
            )
            
        except Exception as e:
            logger.error(f"Gemini NLP error: {e}")
            return None


class LocalNLPProvider(NLPProvider):
    """
    Local NLP using KeyBERT and basic analysis
    No API calls, always available
    """
    
    name = "local_nlp"
    
    async def analyze(self, text: str, segments: list = None) -> Optional[NLPResult]:
        """Analyze text using local NLP tools"""
        try:
            loop = asyncio.get_event_loop()
            
            def _analyze():
                # Extract keywords using simple frequency analysis
                keywords = self._extract_keywords(text)
                keyphrases = self._extract_keyphrases(text)
                sentiment = self._analyze_sentiment(text)
                summary = self._generate_summary(text)
                
                return keywords, keyphrases, sentiment, summary
            
            keywords, keyphrases, sentiment, summary = await loop.run_in_executor(
                None, _analyze
            )
            
            return NLPResult(
                topics=[],  # Would need topic modeling
                keywords=keywords,
                keyphrases=keyphrases,
                sentiment=sentiment,
                emotions=[],
                summary=summary,
                provider=self.name
            )
            
        except Exception as e:
            logger.error(f"Local NLP error: {e}")
            return None
    
    def _extract_keywords(self, text: str, n: int = 20) -> list[str]:
        """Extract keywords using frequency analysis"""
        # Simple tokenization
        words = re.findall(r'\b[a-zA-ZÀ-ỹ]{3,}\b', text.lower())
        
        # Remove common stopwords
        stopwords = {
            'the', 'and', 'for', 'that', 'this', 'with', 'are', 'was', 'were',
            'have', 'has', 'had', 'been', 'from', 'they', 'you', 'your',
            'các', 'của', 'cho', 'này', 'được', 'với', 'trong', 'những',
            'khi', 'đã', 'sẽ', 'là', 'có', 'không', 'thì', 'mà', 'như',
            'để', 'một', 'và', 'hay', 'hoặc', 'nếu', 'nhưng', 'vì'
        }
        
        words = [w for w in words if w not in stopwords]
        
        # Count frequency
        freq = Counter(words)
        
        return [word for word, _ in freq.most_common(n)]
    
    def _extract_keyphrases(self, text: str, n: int = 10) -> list[str]:
        """Extract key phrases (bigrams/trigrams)"""
        # Simple bigram extraction
        words = re.findall(r'\b[a-zA-ZÀ-ỹ]{2,}\b', text.lower())
        
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        
        # Count frequency
        freq = Counter(bigrams)
        
        return [phrase for phrase, _ in freq.most_common(n)]
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple rule-based sentiment analysis"""
        text_lower = text.lower()
        
        positive_words = [
            'tốt', 'hay', 'tuyệt', 'xuất sắc', 'thích', 'yêu', 'vui',
            'good', 'great', 'excellent', 'love', 'amazing', 'best'
        ]
        
        negative_words = [
            'xấu', 'tệ', 'ghét', 'chán', 'buồn', 'thất vọng',
            'bad', 'terrible', 'hate', 'boring', 'disappointed', 'worst'
        ]
        
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        if pos_count > neg_count * 1.5:
            return "positive"
        elif neg_count > pos_count * 1.5:
            return "negative"
        return "neutral"
    
    def _generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """Generate basic extractive summary"""
        # Split into sentences
        sentences = re.split(r'[.!?]\s+', text)
        
        if len(sentences) <= max_sentences:
            return text[:500]
        
        # Score sentences by keyword density
        keywords = set(self._extract_keywords(text, 10))
        
        scored = []
        for sent in sentences:
            words = set(re.findall(r'\b[a-zA-ZÀ-ỹ]{3,}\b', sent.lower()))
            score = len(words & keywords)
            scored.append((score, sent))
        
        # Get top sentences
        scored.sort(reverse=True)
        top_sentences = [s for _, s in scored[:max_sentences]]
        
        return ". ".join(top_sentences)[:500]


class NLPService:
    """
    Multi-provider NLP service with fallback.
    
    Priority:
    1. Gemini (accurate, comprehensive)
    2. Local NLP (always available, basic)
    """
    
    def __init__(self):
        self.providers = [
            GeminiNLPProvider(),
            LocalNLPProvider()
        ]
    
    async def analyze(
        self,
        text: str,
        segments: list = None,
        preferred_provider: str = None
    ) -> NLPResult:
        """
        Analyze text with automatic fallback.
        
        Args:
            text: Text to analyze
            segments: Transcript segments with timing
            preferred_provider: Force specific provider
        """
        for provider in self.providers:
            if preferred_provider and provider.name != preferred_provider:
                continue
            
            try:
                logger.info(f"Trying NLP provider: {provider.name}")
                result = await provider.analyze(text, segments)
                
                if result:
                    logger.info(f"NLP completed with {provider.name}")
                    return result
                    
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                continue
        
        # Return empty result if all fail
        return NLPResult(
            topics=[],
            keywords=[],
            keyphrases=[],
            sentiment="neutral",
            emotions=[],
            summary="Unable to generate summary",
            provider="none"
        )


# Singleton instance
nlp_service = NLPService()
