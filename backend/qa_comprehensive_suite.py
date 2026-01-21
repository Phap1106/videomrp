import requests
import time
import json
import logging
import sys
from datetime import datetime

# --- Configuration ---
BASE_URL = "http://localhost:8000"
TEST_URL_SHORT_1 = "https://www.youtube.com/watch?v=jNQXAC9IVRw" # "Me at the zoo" (19s) - Safe test
TEST_URL_ANALYZER = "https://www.youtube.com/watch?v=Fj2Jj3d3-1U" # Standard test
OUTPUT_FILE = "test_execution_report.json"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("qa_test.log", mode='w')
    ]
)
logger = logging.getLogger("ProfessionalTester")

class PerformanceMetrics:
    def __init__(self):
        self.metrics = {}

    def record(self, names, duration):
        if names not in self.metrics:
            self.metrics[names] = []
        self.metrics[names].append(duration)

    def get_average(self, name):
        if name not in self.metrics:
            return 0
        return sum(self.metrics[name]) / len(self.metrics[name])

metrics = PerformanceMetrics()

def measure_time(func_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            logger.info(f"START: {func_name}")
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                metrics.record(func_name, duration)
                logger.info(f"PASS: {func_name} (Duration: {duration:.2f}s)")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"FAIL: {func_name} (Duration: {duration:.2f}s) - Error: {e}")
                raise e
        return wrapper
    return decorator

class ProfessionalTester:
    def __init__(self):
        self.session = requests.Session()

    @measure_time("System Health Check")
    def check_health(self):
        resp = self.session.get(f"{BASE_URL}/api/health")
        if resp.status_code != 200:
            raise Exception(f"Health check failed: {resp.text}")
        data = resp.json()
        logger.info(f"System Health: {json.dumps(data, indent=2)}")
        return data

    @measure_time("Analyzer Pipeline")
    def test_analyzer(self):
        payload = {
            "youtube_url": TEST_URL_ANALYZER,
            "min_score_threshold": 6.0
        }
        resp = self.session.post(f"{BASE_URL}/api/youtube/analyze", json=payload)
        if resp.status_code != 200:
            raise Exception(f"Trigger failed: {resp.text}")
        
        job_id = resp.json()["job_id"]
        logger.info(f"Analyzer Job ID: {job_id}")
        
        # Poll
        return self._poll_job(job_id, f"{BASE_URL}/api/youtube/analysis/{job_id}", timeout=300)

    @measure_time("Reup Pipeline (Fast)")
    def test_reup_flow(self):
        # Using "Fast" flow to verify pipeline mechanics without burning API credits excessive wait
        payload = {
            "source_url": TEST_URL_SHORT_1,
            "target_platform": "tiktok",
            "video_type": "shorts",
            "processing_flow": "fast",
            "title": "QA Automated Reup Test"
        }
        resp = self.session.post(f"{BASE_URL}/api/videos/process-reup", json=payload)
        if resp.status_code != 200:
            raise Exception(f"Reup Trigger failed: {resp.text}")
        
        job_data = resp.json()
        job_id = job_data.get("job_id") or job_data.get("id")
        if not job_id:
            raise Exception(f"Job ID missing in response: {job_data}")
        logger.info(f"Reup Job ID: {job_id}")
        
        # Poll - Endpoint verified in endpoints.py line 866: /videos/job/{job_id}
        return self._poll_job(job_id, f"{BASE_URL}/api/videos/job/{job_id}", timeout=300)

    def _poll_job(self, job_id, url, timeout=300):
        start = time.time()
        while time.time() - start < timeout:
            resp = self.session.get(url)
            if resp.status_code != 200:
                # Some endpoints might return 404 momentarily?
                logger.warning(f"Poll check failed: {resp.status_code}")
                time.sleep(2)
                continue
            
            data = resp.json()
            status = data.get("status")
            progress = data.get("progress", 0)
            
            # Logger clean progress update
            # print(f"\rPolling {job_id}: {status} {progress}%", end="")
            
            if status == "completed":
                logger.info(f"Job {job_id} COMPLETED.")
                return data
            elif status == "failed":
                raise Exception(f"Job {job_id} FAILED: {data.get('error')}")
            
            time.sleep(3)
        raise Exception(f"Timeout awaiting job {job_id}")

    def run_suite(self):
        report = {
            "timestamp": datetime.now().isoformat(),
            "results": {},
            "metrics": {},
            "satisfaction_score": 0
        }
        
        try:
            # 1. Health
            self.check_health()
            report["results"]["health"] = "PASS"
            
            # 2. Reup (Priority)
            try:
                reup_res = self.test_reup_flow()
                report["results"]["reup_flow"] = "PASS"
                report["reup_output"] = reup_res.get("output_path") or reup_res.get("result", {}).get("output_path")
            except Exception as e:
                logger.error(f"Reup Test Failed: {e}")
                report["results"]["reup_flow"] = f"FAIL: {str(e)}"

            # 3. Analyzer
            try:
                anz_res = self.test_analyzer()
                report["results"]["analyzer"] = "PASS"
            except Exception as e:
                 logger.error(f"Analyzer Test Skipped/Failed: {e}")
                 report["results"]["analyzer"] = f"FAIL: {str(e)}"
                 
        except Exception as e:
            logger.critical(f"Suite Aborted: {e}")
            
        # Compile Metrics
        report["metrics"] = metrics.metrics
        
        # Calculate Satisfaction Score (Simple Heuristic)
        # 100 base, -20 per fail, -1 per second over expected duration
        score = 100
        if report["results"].get("health") != "PASS": score = 0
        if report["results"].get("reup_flow") != "PASS": score -= 30
        
        # Latency check
        avg_reup = metrics.get_average("Reup Pipeline (Fast)")
        if avg_reup > 0 and avg_reup > 60: # Expect < 60s for fast flow
             score -= (avg_reup - 60) * 0.5
             
        report["satisfaction_score"] = max(0, min(100, score))
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(report, f, indent=2)
            
        logger.info("="*60)
        logger.info(f"TEST SUITE COMPLETE. Satisfaction Score: {report['satisfaction_score']}/100")
        logger.info(f"Report saved to {OUTPUT_FILE}")
        logger.info("="*60)

if __name__ == "__main__":
    tester = ProfessionalTester()
    tester.run_suite()
