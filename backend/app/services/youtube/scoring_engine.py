"""
YouTube Video Analyzer - Stage 6: Scoring Engine
=================================================
Final score calculation with weighted formula.
"""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class ScoreBreakdown:
    """Individual score component"""
    score: float
    weight: float
    weighted: float
    reasoning: str


@dataclass
class ScoreDeduction:
    """Score deduction with reason"""
    reason: str
    points: float


@dataclass
class FinalScoreResult:
    """Complete scoring result"""
    final_score: float
    grade: str
    breakdown: dict[str, ScoreBreakdown]
    deductions: list[ScoreDeduction]
    explanation: str
    recommendation: str


class ScoringEngine:
    """
    Stage 6: Scoring Engine
    Calculates final score using weighted formula with transparent breakdown.
    """
    
    # Weight configuration
    WEIGHTS = {
        "content_value": 0.25,      # 25%
        "engagement_quality": 0.20,  # 20%
        "trend_alignment": 0.20,     # 20%
        "policy_safety": 0.15,       # 15%
        "reusability": 0.10,         # 10%
        "channel_authority": 0.10    # 10%
    }
    
    # Grade thresholds
    GRADES = {
        9.0: "A",
        8.0: "A-",
        7.0: "B+",
        6.0: "B",
        5.0: "C+",
        4.0: "C",
        3.0: "D",
        0.0: "F"
    }
    
    def calculate(
        self,
        content_data: dict,
        engagement_data: dict,
        trend_data: dict,
        policy_data: dict,
        channel_data: dict
    ) -> FinalScoreResult:
        """
        Calculate final score from all analysis data.
        
        Args:
            content_data: NLP analysis results (keywords, sentiment, summary)
            engagement_data: Engagement metrics and score
            trend_data: Trend alignment results
            policy_data: Policy check results
            channel_data: Channel authority analysis
        """
        breakdown = {}
        deductions = []
        
        # 1. Content Value Score (25%)
        content_score, content_reason = self._score_content(content_data)
        breakdown["content_value"] = ScoreBreakdown(
            score=content_score,
            weight=self.WEIGHTS["content_value"],
            weighted=content_score * self.WEIGHTS["content_value"],
            reasoning=content_reason
        )
        
        # 2. Engagement Quality Score (20%)
        engagement_score = engagement_data.get("engagement_score", 5.0)
        engagement_reason = engagement_data.get("reasoning", "Based on like/comment ratios")
        breakdown["engagement_quality"] = ScoreBreakdown(
            score=engagement_score,
            weight=self.WEIGHTS["engagement_quality"],
            weighted=engagement_score * self.WEIGHTS["engagement_quality"],
            reasoning=engagement_reason
        )
        
        # 3. Trend Alignment Score (20%)
        # Check if trend data exists and has insights
        trend_insights = trend_data.get("trend_insights", [])
        if trend_insights and not trend_data.get("error"):
            # Base it on number of insights and similarity
            trend_score = min(10.0, 5.0 + (len(trend_insights) * 1.5))
            trend_reason = f"High alignment: {len(trend_insights)} trend insights found"
        else:
            trend_score = 5.0
            trend_reason = "Standard alignment (no real-time trend data)"
            
        breakdown["trend_alignment"] = ScoreBreakdown(
            score=trend_score,
            weight=self.WEIGHTS["trend_alignment"],
            weighted=trend_score * self.WEIGHTS["trend_alignment"],
            reasoning=trend_reason
        )
        
        # 4. Policy Safety Score (15%)
        policy_score, policy_reason = self._score_policy(policy_data)
        breakdown["policy_safety"] = ScoreBreakdown(
            score=policy_score,
            weight=self.WEIGHTS["policy_safety"],
            weighted=policy_score * self.WEIGHTS["policy_safety"],
            reasoning=policy_reason
        )
        
        # Add deductions for policy issues
        if policy_data.get("risk_level") == "high":
            deductions.append(ScoreDeduction(
                reason="High policy risk detected",
                points=-2.0
            ))
        elif policy_data.get("risk_level") == "medium":
            deductions.append(ScoreDeduction(
                reason="Medium policy risk",
                points=-0.5
            ))
        
        # 5. Reusability Score (10%)
        reuse_score, reuse_reason = self._score_reusability(content_data, engagement_data)
        breakdown["reusability"] = ScoreBreakdown(
            score=reuse_score,
            weight=self.WEIGHTS["reusability"],
            weighted=reuse_score * self.WEIGHTS["reusability"],
            reasoning=reuse_reason
        )
        
        # 6. Channel Authority Score (10%)
        channel_score = channel_data.get("channel_score", 5.0)
        channel_reason = channel_data.get("reasoning", "Based on channel metrics")
        breakdown["channel_authority"] = ScoreBreakdown(
            score=channel_score,
            weight=self.WEIGHTS["channel_authority"],
            weighted=channel_score * self.WEIGHTS["channel_authority"],
            reasoning=channel_reason
        )
        
        # Calculate base score
        base_score = sum(b.weighted for b in breakdown.values())
        
        # Apply deductions
        total_deduction = sum(d.points for d in deductions)
        final_score = max(0, min(10, base_score + total_deduction))
        final_score = round(final_score, 1)
        
        # Determine grade
        grade = self._get_grade(final_score)
        
        # Generate explanation
        explanation = self._generate_explanation(breakdown, deductions, final_score)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(final_score, breakdown, policy_data)
        
        return FinalScoreResult(
            final_score=final_score,
            grade=grade,
            breakdown={k: vars(v) for k, v in breakdown.items()},
            deductions=[vars(d) for d in deductions],
            explanation=explanation,
            recommendation=recommendation
        )
    
    def _score_content(self, content_data: dict) -> tuple[float, str]:
        """Score content value based on NLP analysis"""
        score = 5.0  # Base score
        reasons = []
        
        # Check sentiment
        sentiment = content_data.get("sentiment", "neutral")
        if sentiment == "positive":
            score += 1.5
            reasons.append("positive sentiment")
        elif sentiment == "negative":
            score -= 1.0
            reasons.append("negative sentiment")
        
        # Check keywords richness
        keywords = content_data.get("keywords", [])
        if len(keywords) >= 15:
            score += 1.0
            reasons.append("rich keywords")
        elif len(keywords) < 5:
            score -= 0.5
            reasons.append("limited keywords")
        
        # Check topic coverage
        topics = content_data.get("topics", [])
        if len(topics) >= 3:
            score += 1.0
            reasons.append("well-structured topics")
        
        # Check summary quality
        summary = content_data.get("summary", "")
        if len(summary) >= 100:
            score += 0.5
            reasons.append("comprehensive content")
        
        score = max(0, min(10, score))
        reasoning = f"Content analysis: {', '.join(reasons) if reasons else 'standard content'}"
        
        return round(score, 1), reasoning
    
    def _score_policy(self, policy_data: dict) -> tuple[float, str]:
        """Score policy safety"""
        if not policy_data.get("policy_safe", True):
            return 0.0, "Policy violation detected"
        
        risk_level = policy_data.get("risk_level", "low")
        
        if risk_level == "low":
            score = 10.0
            reason = "Clean content, no policy concerns"
        elif risk_level == "medium":
            score = 6.0
            reason = f"Some concerns: {', '.join(policy_data.get('sensitive_topics', []))}"
        else:
            score = 3.0
            reason = "High risk content"
        
        return score, reason
    
    def _score_reusability(self, content_data: dict, engagement_data: dict) -> tuple[float, str]:
        """Score how reusable/editable the content is"""
        score = 6.0  # Base score
        reasons = []
        
        # Longer videos are harder to reuse
        duration = engagement_data.get("duration", 300)
        if duration <= 180:  # < 3 min
            score += 2.0
            reasons.append("short format")
        elif duration <= 600:  # < 10 min
            score += 1.0
            reasons.append("medium length")
        elif duration > 1800:  # > 30 min
            score -= 1.5
            reasons.append("long video needs cutting")
        
        # Clear structure is easier to cut
        topics = content_data.get("topics", [])
        if len(topics) >= 2:
            score += 1.0
            reasons.append("clear structure")
        
        score = max(0, min(10, score))
        reasoning = f"Reusability: {', '.join(reasons) if reasons else 'standard'}"
        
        return round(score, 1), reasoning
    
    def _get_grade(self, score: float) -> str:
        """Get letter grade from score"""
        for threshold, grade in sorted(self.GRADES.items(), reverse=True):
            if score >= threshold:
                return grade
        return "F"
    
    def _generate_explanation(
        self,
        breakdown: dict,
        deductions: list,
        final_score: float
    ) -> str:
        """Generate human-readable explanation"""
        parts = []
        
        # Top strengths
        strengths = sorted(
            breakdown.items(),
            key=lambda x: x[1].score,
            reverse=True
        )[:2]
        
        parts.append(f"Video đạt {final_score}/10.")
        
        if strengths:
            strength_names = [self._format_criteria_name(s[0]) for s in strengths]
            parts.append(f"Điểm mạnh: {', '.join(strength_names)}.")
        
        # Deductions
        if deductions:
            deduction_reasons = [d.reason for d in deductions]
            parts.append(f"Điểm trừ: {', '.join(deduction_reasons)}.")
        
        return " ".join(parts)
    
    def _generate_recommendation(
        self,
        score: float,
        breakdown: dict,
        policy_data: dict
    ) -> str:
        """Generate actionable recommendation"""
        if not policy_data.get("policy_safe", True):
            return "NOT RECOMMENDED - Policy violation detected"
        
        if score >= 8.0:
            return "HIGHLY RECOMMENDED for reup. Minimal editing needed."
        elif score >= 6.5:
            return "RECOMMENDED with editing. Consider cutting to shorter segments."
        elif score >= 5.0:
            return "CONSIDER with caution. Significant editing may be needed."
        else:
            return "NOT RECOMMENDED. Score too low for quality reup."
    
    def _format_criteria_name(self, key: str) -> str:
        """Format criteria key to readable name"""
        names = {
            "content_value": "nội dung chất lượng",
            "engagement_quality": "engagement cao",
            "trend_alignment": "phù hợp trend",
            "policy_safety": "nội dung sạch",
            "reusability": "dễ chỉnh sửa",
            "channel_authority": "kênh uy tín"
        }
        return names.get(key, key)


# Singleton instance
scoring_engine = ScoringEngine()
