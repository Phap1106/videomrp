"""
Stage 10: Reporting & Dashboard
Aggregates all results and produces a final summary report.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.logger import logger
from app.services.ai.story_generator import get_story_generator

class ReportGenerator:
    """
    Synthesizes all analysis stages into a final report.
    """

    async def generate_final_report(self, all_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate results from all 10 stages and produce an executive summary.
        """
        try:
            logger.info("Generating final analysis report")
            
            # Extract scores and data
            metadata = all_data.get("ingestion", {})
            quality_data = all_data.get("policy", {})
            scoring_data = all_data.get("scoring", {})
            trend_data = all_data.get("trends", {})
            rec_data = all_data.get("recommendations", {})
            
            # Generate executive summary via AI
            summary = await self._generate_executive_summary(all_data)
            
            report = {
                "metadata": {
                    "video_id": metadata.get("id"),
                    "title": metadata.get("title"),
                    "channel": metadata.get("channel_title"),
                    "analysis_date": datetime.now().isoformat()
                },
                "executive_summary": summary.get("text", "Analysis complete."),
                "viral_potential_breakdown": summary.get("potential", {}),
                "key_takeaways": summary.get("takeaways", []),
                "action_plan": summary.get("action_plan", []),
                "overall_score": scoring_data.get("overall_score", 0),
                "detailed_data": all_data, # Include original data for the frontend if needed
                "status": "COMPLETED"
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "overall_score": 0,
                "timestamp": datetime.now().isoformat()
            }

    async def _generate_executive_summary(self, all_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call AI to synthesize the whole analysis into a bite-sized summary"""
        try:
            generator = await get_story_generator()
            
            # Create a compressed context for the AI
            context = {
                "title": all_data.get("ingestion", {}).get("title"),
                "score": all_data.get("scoring", {}).get("overall_score"),
                "policy_issues": all_data.get("policy", {}).get("issues", []),
                "trending_niche": all_data.get("trends", {}).get("trend_insights", [])[:2],
                "top_recommendation": all_data.get("recommendations", {}).get("title_variants", [None])[0]
            }
            
            prompt = f"""
            ACT AS A SENIOR PRODUCT MANAGER AT YOUTUBE.
            You have analyzed a video with the following data:
            {json.dumps(context, indent=2)}
            
            TASK:
            1. Write a 2-sentence Executive Summary of the video's quality and potential.
            2. Break down "Viral Potential" into: Hooks (1-10), Visuals (1-10), Trend Timing (1-10).
            3. List 3 Key Takeaways.
            4. Provide a 3-step immediate Action Plan.
            
            RETURN JSON ONLY:
            {{
                "text": "...",
                "potential": {{
                    "hooks": 8,
                    "visuals": 7,
                    "trend_timing": 9
                }},
                "takeaways": ["...", "...", "..."],
                "action_plan": ["Step 1", "Step 2", "Step 3"]
            }}
            """
            
            response = await generator.generate_story(
                prompt=prompt,
                max_length=1000,
                style="json"
            )
            
            # Extract JSON
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
                
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"AI report summary failed: {e}")
            return {
                "text": "Video analysis completed with an overall score of " + str(all_data.get("scoring", {}).get("overall_score", 0)),
                "potential": {"hooks": 5, "visuals": 5, "trend_timing": 5},
                "takeaways": ["Check the detailed data for more info"],
                "action_plan": ["Follow general optimization best practices"]
            }

report_generator = ReportGenerator()
