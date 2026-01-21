"""
YouTube Video Analyzer - Stage 4: Policy Evaluator
===================================================
Multi-provider content moderation with fallback.
Providers: OpenAI Moderation (free) → Google Perspective → Local rules
"""

import asyncio
import re
from typing import Optional, Any
from dataclasses import dataclass, field
import httpx

from app.core.logger import logger
from app.core.config import settings


@dataclass
class PolicyCheckResult:
    """Complete policy evaluation result"""
    policy_safe: bool
    risk_level: str  # low, medium, high
    violations: list[str]
    platform_safety: dict[str, dict]
    content_flags: dict[str, bool]
    positive_value: list[str]
    sensitive_topics: list[str]
    reup_safe_score: float
    reasoning: str
    provider: str


class ModerationProvider:
    """Base class for moderation providers"""
    
    name: str = "base"
    
    async def check(self, text: str) -> Optional[dict]:
        raise NotImplementedError


class OpenAIModerationProvider(ModerationProvider):
    """
    OpenAI Moderation API - FREE
    Detects: hate, harassment, self-harm, sexual, violence
    """
    
    name = "openai_moderation"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
    
    async def check(self, text: str) -> Optional[dict]:
        """Check content using OpenAI Moderation API"""
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/moderations",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"input": text[:10000]}  # Limit text length
                )
                
                if response.status_code != 200:
                    logger.error(f"OpenAI Moderation error: {response.status_code}")
                    return None
                
                data = response.json()
                result = data.get("results", [{}])[0]
                
                return {
                    "flagged": result.get("flagged", False),
                    "categories": result.get("categories", {}),
                    "category_scores": result.get("category_scores", {})
                }
                
        except Exception as e:
            logger.error(f"OpenAI Moderation error: {e}")
            return None



class GeminiModerationProvider(ModerationProvider):
    """
    Google Gemini for content moderation
    """
    
    name = "gemini_moderation"
    
    async def check(self, text: str) -> Optional[dict]:
        """Check content using Gemini"""
        try:
            import google.generativeai as genai
            
            if not settings.GEMINI_API_KEY:
                return None
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-flash-latest")
            
            prompt = f"""Analyze this text for content moderation. Check for:
1. Hate speech
2. Violence
3. Sexual content
4. Harassment
5. Self-harm
6. Dangerous content

Text: {text[:8000]}

Return JSON:
{{
    "flagged": boolean,
    "flags": {{
        "hate_speech": boolean,
        "violence": boolean,
        "sexual": boolean,
        "harassment": boolean,
        "self_harm": boolean,
        "dangerous": boolean
    }}
}}"""

            response = await model.generate_content_async(prompt)
            result_text = response.text
            
            # Clean potential markdown
            import re
            if result_text.startswith("```"):
                result_text = re.sub(r"```\w*\n?", "", result_text)
                result_text = result_text.strip()
            
            import json
            data = json.loads(result_text)
            
            flags = data.get("flags", {})
            violations = [k for k, v in flags.items() if v]
            
            return {
                "flagged": data.get("flagged", False),
                "flags": flags,
                "violations": violations,
                "positive_value": []
            }
            
        except Exception as e:
            logger.error(f"Gemini Moderation error: {e}")
            return None


class LocalRulesProvider(ModerationProvider):
    """
    Local rule-based moderation
    Uses regex patterns and keyword lists
    """
    
    name = "local_rules"
    
    # Sensitive keyword patterns (Vietnamese + English)
    PATTERNS = {
        "hate_speech": [
            r"\b(ghét|căm thù|tiêu diệt|đánh đập)\b",
            r"\b(racist|bigot|nazi|supremacist)\b"
        ],
        "violence": [
            r"\b(giết|đâm|bắn|chém|máu me)\b",
            r"\b(kill|murder|shoot|stab|blood)\b"
        ],
        "sexual": [
            r"\b(sex|porn|xxx|nude)\b",
            r"\b(khiêu dâm|đồi trụy)\b"
        ],
        "misinformation": [
            r"\b(vaccine gây|covid fake|trái đất phẳng)\b",
            r"\b(hoax|conspiracy|fake news)\b"
        ],
        "dangerous": [
            r"\b(tự tử|tự sát|cắt tay)\b",
            r"\b(suicide|self-harm|cutting)\b"
        ]
    }
    
    # Positive content indicators
    POSITIVE_PATTERNS = {
        "education": [r"\b(hướng dẫn|tutorial|learn|dạy|học)\b"],
        "motivation": [r"\b(cảm hứng|động lực|inspire|motivat)\b"],
        "entertainment": [r"\b(vui|hài|funny|comedy|entertainment)\b"],
        "news": [r"\b(tin tức|news|cập nhật|update)\b"]
    }
    
    async def check(self, text: str) -> Optional[dict]:
        """Check content using local rules"""
        text_lower = text.lower()
        
        flags = {}
        violations = []
        
        for category, patterns in self.PATTERNS.items():
            matched = False
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    matched = True
                    violations.append(f"{category}: pattern matched")
                    break
            flags[category] = matched
        
        # Check positive patterns
        positive = []
        for category, patterns in self.POSITIVE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    positive.append(category)
                    break
        
        return {
            "flagged": any(flags.values()),
            "flags": flags,
            "violations": violations,
            "positive_value": positive
        }


class PolicyEvaluator:
    """
    Multi-provider policy evaluation service.
    
    Priority:
    1. OpenAI Moderation (free, comprehensive)
    2. Gemini Moderation (backup)
    3. Local rules (fallback, always available)
    """
    
    PLATFORM_POLICIES = {
        "youtube": {
            "blocked_categories": ["hate", "harassment", "sexual", "violence"],
            "restricted_topics": ["politics", "health", "gambling"]
        },
        "tiktok": {
            "blocked_categories": ["hate", "harassment", "sexual", "violence", "dangerous"],
            "restricted_topics": ["politics", "medical", "gambling", "alcohol"]
        },
        "facebook": {
            "blocked_categories": ["hate", "harassment", "sexual", "violence"],
            "restricted_topics": ["politics", "health", "adult"]
        }
    }
    
    def __init__(self):
        self.providers = [
            OpenAIModerationProvider(),
            GeminiModerationProvider(),
            LocalRulesProvider()
        ]
    
    async def evaluate(
        self,
        text: str,
        keywords: list[str] = None,
        include_platforms: list[str] = None
    ) -> PolicyCheckResult:
        """
        Evaluate content against platform policies.
        
        Args:
            text: Content text to evaluate
            keywords: Extracted keywords from content
            include_platforms: Specific platforms to check
        """
        platforms = include_platforms or ["youtube", "tiktok", "facebook"]
        
        # Get moderation results from providers
        moderation_result = await self._get_moderation(text)
        
        # Evaluate against each platform
        platform_safety = {}
        all_violations = []
        
        for platform in platforms:
            safety = self._check_platform(platform, moderation_result)
            platform_safety[platform] = safety
            all_violations.extend(safety.get("issues", []))
        
        # Determine overall risk level
        risk_level = self._calculate_risk_level(moderation_result, all_violations)
        
        # Check for positive value
        positive_value = moderation_result.get("positive_value", [])
        
        # Identify sensitive topics
        sensitive_topics = self._identify_sensitive_topics(text, keywords or [])
        
        # Calculate reup safety score
        reup_score = self._calculate_reup_score(
            risk_level, 
            len(all_violations),
            len(positive_value)
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            risk_level,
            all_violations,
            positive_value,
            sensitive_topics
        )
        
        return PolicyCheckResult(
            policy_safe=risk_level == "low",
            risk_level=risk_level,
            violations=list(set(all_violations)),
            platform_safety=platform_safety,
            content_flags=moderation_result.get("flags", {}),
            positive_value=positive_value,
            sensitive_topics=sensitive_topics,
            reup_safe_score=reup_score,
            reasoning=reasoning,
            provider=moderation_result.get("provider", "unknown")
        )
    
    async def _get_moderation(self, text: str) -> dict:
        """Get moderation result from available providers"""
        for provider in self.providers:
            try:
                result = await provider.check(text)
                if result:
                    result["provider"] = provider.name
                    
                    # Normalize OpenAI format to our format
                    if provider.name == "openai_moderation":
                        result = self._normalize_openai(result)
                    
                    return result
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                continue
        
        # All providers failed, return safe default
        return {
            "flagged": False,
            "flags": {},
            "violations": [],
            "positive_value": [],
            "provider": "none"
        }
    
    def _normalize_openai(self, result: dict) -> dict:
        """Normalize OpenAI result to our format"""
        categories = result.get("categories", {})
        scores = result.get("category_scores", {})
        
        flags = {
            "hate_speech": categories.get("hate", False) or categories.get("hate/threatening", False),
            "violence": categories.get("violence", False) or categories.get("violence/graphic", False),
            "sexual": categories.get("sexual", False) or categories.get("sexual/minors", False),
            "harassment": categories.get("harassment", False) or categories.get("harassment/threatening", False),
            "self_harm": categories.get("self-harm", False),
            "dangerous": categories.get("self-harm/intent", False) or categories.get("self-harm/instructions", False)
        }
        
        violations = [k for k, v in flags.items() if v]
        
        return {
            "flagged": result.get("flagged", False),
            "flags": flags,
            "violations": violations,
            "positive_value": [],
            "provider": result.get("provider"),
            "scores": scores
        }
    
    def _check_platform(self, platform: str, moderation: dict) -> dict:
        """Check content against specific platform policy"""
        policy = self.PLATFORM_POLICIES.get(platform, {})
        blocked = policy.get("blocked_categories", [])
        
        flags = moderation.get("flags", {})
        issues = []
        
        for category in blocked:
            if flags.get(category) or flags.get(f"{category}_speech"):
                issues.append(f"{category} content detected")
        
        return {
            "safe": len(issues) == 0,
            "issues": issues
        }
    
    def _calculate_risk_level(self, moderation: dict, violations: list) -> str:
        """Calculate overall risk level"""
        if moderation.get("flagged") or len(violations) > 2:
            return "high"
        elif len(violations) > 0:
            return "medium"
        return "low"
    
    def _identify_sensitive_topics(self, text: str, keywords: list) -> list:
        """Identify potentially sensitive topics"""
        text_lower = text.lower()
        topics = []
        
        sensitive_patterns = {
            "politics": r"\b(chính trị|bầu cử|đảng|politics|election|government)\b",
            "health": r"\b(bệnh|thuốc|điều trị|vaccine|covid|health|medicine)\b",
            "religion": r"\b(tôn giáo|đạo|chùa|nhà thờ|religion|church|temple)\b",
            "finance": r"\b(đầu tư|chứng khoán|bitcoin|crypto|invest|trading)\b"
        }
        
        for topic, pattern in sensitive_patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                topics.append(topic)
        
        return topics
    
    def _calculate_reup_score(
        self,
        risk_level: str,
        violation_count: int,
        positive_count: int
    ) -> float:
        """Calculate reup safety score (0-10)"""
        base_score = {
            "low": 9.0,
            "medium": 6.0,
            "high": 2.0
        }.get(risk_level, 5.0)
        
        # Deduct for violations
        score = base_score - (violation_count * 0.5)
        
        # Bonus for positive content
        score += min(positive_count * 0.3, 1.0)
        
        return round(max(0, min(10, score)), 1)
    
    def _generate_reasoning(
        self,
        risk_level: str,
        violations: list,
        positive: list,
        sensitive: list
    ) -> str:
        """Generate human-readable reasoning"""
        parts = []
        
        if risk_level == "low":
            parts.append("Nội dung an toàn, không phát hiện vi phạm policy.")
        elif risk_level == "medium":
            parts.append("Nội dung có một số cảnh báo nhẹ.")
        else:
            parts.append("Nội dung có rủi ro cao.")
        
        if violations:
            parts.append(f"Vi phạm phát hiện: {', '.join(violations[:3])}.")
        
        if positive:
            parts.append(f"Giá trị tích cực: {', '.join(positive)}.")
        
        if sensitive:
            parts.append(f"Chủ đề nhạy cảm: {', '.join(sensitive)}.")
        
        return " ".join(parts)


# Singleton instance
policy_evaluator = PolicyEvaluator()
