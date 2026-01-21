import requests
import time
import os
import json
import logging

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

def run_system_verification():
    """
    Run a full verification of the YouTube Analyzer pipeline.
    """
    logger.info("--- STARTING SYSTEM VERIFICATION (Analyzer Pipeline) ---")

    # Analyzer Test Configuration
    TARGET_URL = "https://www.youtube.com/watch?v=Fj2Jj3d3-1U" # Choose a popular video
    
    logger.info(f"Target Video: {TARGET_URL}")
    
    # 1. Trigger Analysis Job
    payload = {
        "youtube_url": TARGET_URL,
        "min_score_threshold": 7.0
    }
    
    logger.info("Step 1: Triggering Analysis Job...")
    try:
        response = requests.post(f"{BASE_URL}/api/youtube/analyze", json=payload)
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        exit(1)
    
    if response.status_code != 200:
        logger.error(f"Failed to trigger job: {response.text}")
        exit(1)
        
    job_data = response.json()
    job_id = job_data["job_id"]
    logger.info(f"Job triggered successfully! Job ID: {job_id}")
    
    # 2. Poll for Completion
    logger.info("Step 2: Polling for completion...")
    start_time = time.time()
    
    while True:
        try:
            status_resp = requests.get(f"{BASE_URL}/api/youtube/analysis/{job_id}")
            if status_resp.status_code != 200:
                logger.error(f"Error polling status: {status_resp.text}")
                break
                
            status_data = status_resp.json()
            status = status_data["status"]
            progress = status_data.get("progress", 0)
            
            logger.info(f"Status: {status} | Progress: {progress}%")
            
            if status == "completed":
                logger.info("Analysis completed!")
                break
            elif status == "failed":
                logger.error(f"Analysis failed: {status_data.get('error')}")
                exit(1)
                
            if time.time() - start_time > 300: # 5 min timeout
                logger.error("Timeout waiting for analysis")
                exit(1)
                
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)

    # 3. Verify Report
    logger.info("Step 3: Fetching Final Report...")
    try:
        report_resp = requests.get(f"{BASE_URL}/api/youtube/analysis/{job_id}/report")
        
        if report_resp.status_code == 200:
            report = report_resp.json()
            print("\n" + "="*60)
            print(" FINAL REPORT VERIFICATION ")
            print("="*60)
            print(f" Executive Summary : {report.get('executive_summary')}")
            print(f" Policy Risk       : {report.get('policy_status')}")
            print(f" Final Score       : {report.get('score_visualization', {}).get('overall')}")
            print(f" Recommendation    : {report.get('recommendation')}")
            
            insights = report.get('key_insights', [])
            print(f" Key Insights      : {len(insights)} found")
            for idx, insight in enumerate(insights[:3]):
                print(f"  - {insight}")
                
            print("="*60 + "\n")
            logger.info("✅ QA Verification Passed!")
        else:
            logger.error(f"Failed to get report: {report_resp.text}")
            
    except Exception as e:
        logger.error(f"Report fetch error: {e}")

if __name__ == "__main__":
    run_system_verification()
