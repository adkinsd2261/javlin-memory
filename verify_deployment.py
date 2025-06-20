
"""
Deployment Verification Script
Verifies that the deployed MemoryOS is working correctly
"""

import requests
import json
import time
import sys
from datetime import datetime

class DeploymentVerifier:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.passed = 0
        self.failed = 0
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_emoji = {"INFO": "ℹ️", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}
        print(f"[{timestamp}] {status_emoji.get(status, 'ℹ️')} {message}")
        
    def test_endpoint(self, endpoint, expected_status=200, description=None):
        """Test a single endpoint"""
        if not description:
            description = f"Testing {endpoint}"
            
        try:
            self.log(f"{description}...", "INFO")
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            
            if response.status_code == expected_status:
                self.log(f"{description} - OK (Status: {response.status_code})", "PASS")
                self.passed += 1
                return True, response
            else:
                self.log(f"{description} - FAIL (Expected: {expected_status}, Got: {response.status_code})", "FAIL")
                self.failed += 1
                return False, response
                
        except requests.exceptions.RequestException as e:
            self.log(f"{description} - ERROR: {e}", "FAIL")
            self.failed += 1
            return False, None
    
    def test_health_endpoint(self):
        """Test the bulletproof health endpoint"""
        success, response = self.test_endpoint("/health", description="Health endpoint")
        
        if success and response:
            try:
                data = response.json()
                
                # Verify required fields
                required_fields = ['status', 'timestamp', 'service']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"Health endpoint missing fields: {missing_fields}", "FAIL")
                    self.failed += 1
                    return False
                
                # Check status
                status = data.get('status')
                if status in ['healthy', 'degraded']:
                    self.log(f"Health status: {status}", "PASS")
                    self.passed += 1
                else:
                    self.log(f"Health status concerning: {status}", "WARN")
                
                # Check bulletproof indicator
                if data.get('bulletproof') is True:
                    self.log("Bulletproof health endpoint confirmed", "PASS")
                    self.passed += 1
                
                return True
                
            except json.JSONDecodeError:
                self.log("Health endpoint returned invalid JSON", "FAIL")
                self.failed += 1
                return False
        
        return False
    
    def test_memory_endpoint(self):
        """Test memory retrieval"""
        success, response = self.test_endpoint("/memory", description="Memory endpoint")
        
        if success and response:
            try:
                data = response.json()
                
                if 'memories' in data and 'pagination' in data:
                    memory_count = len(data['memories'])
                    self.log(f"Memory endpoint OK - {memory_count} entries", "PASS")
                    self.passed += 1
                    return True
                else:
                    self.log("Memory endpoint missing required fields", "FAIL")
                    self.failed += 1
                    return False
                    
            except json.JSONDecodeError:
                self.log("Memory endpoint returned invalid JSON", "FAIL")
                self.failed += 1
                return False
        
        return False
    
    def test_stats_endpoint(self):
        """Test stats endpoint"""
        success, response = self.test_endpoint("/stats", description="Stats endpoint")
        
        if success and response:
            try:
                data = response.json()
                
                required_fields = ['total_memories', 'success_rate']
                if all(field in data for field in required_fields):
                    self.log(f"Stats OK - {data.get('total_memories', 0)} total memories", "PASS")
                    self.passed += 1
                    return True
                else:
                    self.log("Stats endpoint missing required fields", "FAIL")
                    self.failed += 1
                    return False
                    
            except json.JSONDecodeError:
                self.log("Stats endpoint returned invalid JSON", "FAIL")
                self.failed += 1
                return False
        
        return False
    
    def test_response_times(self):
        """Test response times are reasonable"""
        endpoints = ['/health', '/memory', '/stats']
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                end_time = time.time()
                
                response_time_ms = (end_time - start_time) * 1000
                
                if response_time_ms < 5000:  # Less than 5 seconds
                    self.log(f"{endpoint} response time: {response_time_ms:.1f}ms - OK", "PASS")
                    self.passed += 1
                else:
                    self.log(f"{endpoint} response time: {response_time_ms:.1f}ms - SLOW", "WARN")
                    
            except Exception as e:
                self.log(f"{endpoint} response time test failed: {e}", "FAIL")
                self.failed += 1
    
    def run_verification(self):
        """Run all verification tests"""
        self.log(f"Starting deployment verification for: {self.base_url}", "INFO")
        self.log("=" * 60, "INFO")
        
        # Test all endpoints
        tests = [
            ("Root endpoint", lambda: self.test_endpoint("/")),
            ("Health endpoint", self.test_health_endpoint),
            ("Memory endpoint", self.test_memory_endpoint),
            ("Stats endpoint", self.test_stats_endpoint),
            ("GPT Status", lambda: self.test_endpoint("/gpt-status")),
            ("Response times", self.test_response_times)
        ]
        
        for test_name, test_func in tests:
            self.log(f"Running {test_name} test...", "INFO")
            try:
                test_func()
            except Exception as e:
                self.log(f"{test_name} test crashed: {e}", "FAIL")
                self.failed += 1
            
            # Small delay between tests
            time.sleep(0.5)
        
        # Summary
        self.log("=" * 60, "INFO")
        self.log("DEPLOYMENT VERIFICATION SUMMARY", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Tests Passed: {self.passed}", "PASS" if self.passed > 0 else "INFO")
        self.log(f"Tests Failed: {self.failed}", "FAIL" if self.failed > 0 else "INFO")
        
        success_rate = (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0
        self.log(f"Success Rate: {success_rate:.1f}%", "PASS" if success_rate >= 80 else "FAIL")
        
        if self.failed == 0:
            self.log("🎉 DEPLOYMENT VERIFICATION PASSED", "PASS")
            self.log("Your MemoryOS deployment is working correctly!", "PASS")
            return True
        else:
            self.log("🚨 DEPLOYMENT VERIFICATION FAILED", "FAIL")
            self.log("Some issues were detected. Please review and fix.", "FAIL")
            return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python verify_deployment.py <base_url>")
        print("Example: python verify_deployment.py https://your-repl-name.replit.app")
        sys.exit(1)
    
    base_url = sys.argv[1]
    verifier = DeploymentVerifier(base_url)
    
    success = verifier.run_verification()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
