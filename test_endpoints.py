"""
MemoryOS Endpoint Testing Script
Comprehensive testing of all API endpoints with detailed reporting
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List

class EndpointTester:
    def __init__(self, base_url: str = "http://0.0.0.0:5000"):
        self.base_url = base_url.rstrip('/')
        self.api_key = "default-key-change-me"  # Default API key
        self.results = []
        self.passed = 0
        self.failed = 0
        
    def log(self, message: str, status: str = "INFO"):
        """Log test results with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_emoji = {
            "INFO": "ℹ️",
            "PASS": "✅", 
            "FAIL": "❌",
            "WARN": "⚠️",
            "TEST": "🧪"
        }
        print(f"[{timestamp}] {status_emoji.get(status, 'ℹ️')} {message}")
        
        self.results.append({
            "timestamp": timestamp,
            "status": status,
            "message": message
        })
    
    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, 
                     headers: Dict = None, expected_status: int = 200,
                     description: str = None) -> Dict[str, Any]:
        """Test a single endpoint and return detailed results"""
        
        if not description:
            description = f"{method} {endpoint}"
            
        self.log(f"Testing {description}...", "TEST")
        
        try:
            url = f"{self.base_url}{endpoint}"
            start_time = time.time()
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_time_ms": round(response_time, 2),
                "response_data": response_data,
                "success": response.status_code == expected_status,
                "description": description
            }
            
            if result["success"]:
                self.log(f"{description} - PASS (Status: {response.status_code}, Time: {response_time:.1f}ms)", "PASS")
                self.passed += 1
            else:
                self.log(f"{description} - FAIL (Expected: {expected_status}, Got: {response.status_code})", "FAIL")
                self.failed += 1
                
            return result
            
        except requests.exceptions.ConnectionError:
            self.log(f"{description} - FAIL (Connection refused - is server running?)", "FAIL")
            self.failed += 1
            return {
                "endpoint": endpoint,
                "method": method,
                "error": "Connection refused",
                "success": False,
                "description": description
            }
            
        except Exception as e:
            self.log(f"{description} - ERROR ({str(e)})", "FAIL")
            self.failed += 1
            return {
                "endpoint": endpoint,
                "method": method,
                "error": str(e),
                "success": False,
                "description": description
            }
    
    def test_health_endpoint(self):
        """Test health endpoint thoroughly"""
        self.log("=== TESTING HEALTH ENDPOINT ===", "INFO")
        
        result = self.test_endpoint("GET", "/health", description="Health check")
        
        if result.get("success"):
            data = result.get("response_data", {})
            
            # Check required fields
            required_fields = ["status", "timestamp", "service", "checks", "metrics"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log(f"Health endpoint missing fields: {missing_fields}", "FAIL")
                self.failed += 1
            else:
                self.log("Health endpoint has all required fields", "PASS")
                self.passed += 1
            
            # Check status values
            status = data.get("status")
            if status in ["healthy", "degraded", "unhealthy"]:
                self.log(f"Health status is valid: {status}", "PASS")
                self.passed += 1
            else:
                self.log(f"Health status is invalid: {status}", "FAIL")
                self.failed += 1
            
            # Check bulletproof indicator
            if data.get("bulletproof") is True:
                self.log("Bulletproof health endpoint confirmed", "PASS")
                self.passed += 1
            else:
                self.log("Bulletproof indicator missing", "WARN")
        
        return result
    
    def test_memory_endpoints(self):
        """Test memory GET and POST endpoints"""
        self.log("=== TESTING MEMORY ENDPOINTS ===", "INFO")
        
        # Test GET /memory
        get_result = self.test_endpoint("GET", "/memory", description="Get memories")
        
        if get_result.get("success"):
            data = get_result.get("response_data", {})
            
            # Check structure
            if "memories" in data and "pagination" in data:
                self.log("Memory GET endpoint has correct structure", "PASS")
                self.passed += 1
                
                memory_count = len(data["memories"])
                self.log(f"Retrieved {memory_count} memory entries", "INFO")
            else:
                self.log("Memory GET endpoint missing required fields", "FAIL")
                self.failed += 1
        
        # Test POST /memory (with API key)
        test_memory = {
            "topic": "Test Memory Entry",
            "type": "SystemTest",
            "input": "Testing memory creation via API",
            "output": "Memory entry created successfully",
            "success": True,
            "category": "test"
        }
        
        headers = {"X-API-KEY": self.api_key}
        post_result = self.test_endpoint(
            "POST", "/memory", 
            data=test_memory, 
            headers=headers,
            expected_status=201,
            description="Create memory entry"
        )
        
        # Test POST without API key (should fail)
        self.test_endpoint(
            "POST", "/memory",
            data=test_memory,
            expected_status=401,
            description="Create memory without API key (should fail)"
        )
        
        # Test POST with invalid data
        invalid_memory = {"invalid": "data"}
        self.test_endpoint(
            "POST", "/memory",
            data=invalid_memory,
            headers=headers,
            expected_status=400,
            description="Create invalid memory entry (should fail)"
        )
        
        return get_result, post_result
    
    def test_stats_endpoint(self):
        """Test statistics endpoint"""
        self.log("=== TESTING STATS ENDPOINT ===", "INFO")
        
        result = self.test_endpoint("GET", "/stats", description="Get statistics")
        
        if result.get("success"):
            data = result.get("response_data", {})
            
            # Check required fields
            required_fields = ["total_memories", "success_rate", "categories", "types"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log(f"Stats endpoint missing fields: {missing_fields}", "FAIL")
                self.failed += 1
            else:
                self.log("Stats endpoint has all required fields", "PASS")
                self.passed += 1
                
                # Log some stats
                total = data.get("total_memories", 0)
                success_rate = data.get("success_rate", "0%")
                self.log(f"Total memories: {total}, Success rate: {success_rate}", "INFO")
        
        return result
    
    def test_gpt_status_endpoint(self):
        """Test GPT status endpoint"""
        self.log("=== TESTING GPT STATUS ENDPOINT ===", "INFO")
        
        result = self.test_endpoint("GET", "/gpt-status", description="GPT status check")
        
        if result.get("success"):
            data = result.get("response_data", {})
            
            # Check required fields
            required_fields = ["system_status", "memory_count", "api_accessible", "timestamp"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log(f"GPT status endpoint missing fields: {missing_fields}", "FAIL")
                self.failed += 1
            else:
                self.log("GPT status endpoint has all required fields", "PASS")
                self.passed += 1
        
        return result
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        self.log("=== TESTING ROOT ENDPOINT ===", "INFO")
        
        result = self.test_endpoint("GET", "/", description="Root endpoint")
        return result
    
    def test_error_handling(self):
        """Test error handling"""
        self.log("=== TESTING ERROR HANDLING ===", "INFO")
        
        # Test 404
        self.test_endpoint(
            "GET", "/nonexistent",
            expected_status=404,
            description="404 error handling"
        )
        
        # Test invalid JSON
        try:
            response = requests.post(
                f"{self.base_url}/memory",
                data="invalid json",
                headers={"Content-Type": "application/json", "X-API-KEY": self.api_key},
                timeout=10
            )
            if response.status_code == 400:
                self.log("Invalid JSON handling - PASS", "PASS")
                self.passed += 1
            else:
                self.log(f"Invalid JSON handling - FAIL (Status: {response.status_code})", "FAIL")
                self.failed += 1
        except Exception as e:
            self.log(f"Invalid JSON test error: {e}", "FAIL")
            self.failed += 1
    
    def test_performance(self):
        """Test endpoint performance"""
        self.log("=== TESTING PERFORMANCE ===", "INFO")
        
        endpoints = ["/health", "/memory", "/stats", "/gpt-status"]
        
        for endpoint in endpoints:
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                if response_time < 1000:  # Less than 1 second
                    self.log(f"{endpoint} response time: {response_time:.1f}ms - GOOD", "PASS")
                    self.passed += 1
                elif response_time < 5000:  # Less than 5 seconds
                    self.log(f"{endpoint} response time: {response_time:.1f}ms - ACCEPTABLE", "WARN")
                else:
                    self.log(f"{endpoint} response time: {response_time:.1f}ms - SLOW", "FAIL")
                    self.failed += 1
                    
            except Exception as e:
                self.log(f"{endpoint} performance test failed: {e}", "FAIL")
                self.failed += 1
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        self.log("🚀 Starting MemoryOS Endpoint Testing", "INFO")
        self.log("=" * 60, "INFO")
        
        # Test all endpoints
        self.test_root_endpoint()
        self.test_health_endpoint()
        self.test_memory_endpoints()
        self.test_stats_endpoint()
        self.test_gpt_status_endpoint()
        self.test_error_handling()
        self.test_performance()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        self.log("=" * 60, "INFO")
        self.log("🏁 TEST SUMMARY", "INFO")
        self.log("=" * 60, "INFO")
        
        total_tests = self.passed + self.failed
        success_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"Total Tests: {total_tests}", "INFO")
        self.log(f"Passed: {self.passed}", "PASS" if self.passed > 0 else "INFO")
        self.log(f"Failed: {self.failed}", "FAIL" if self.failed > 0 else "INFO")
        self.log(f"Success Rate: {success_rate:.1f}%", "PASS" if success_rate >= 80 else "FAIL")
        
        if self.failed == 0:
            self.log("🎉 ALL TESTS PASSED - System is working correctly!", "PASS")
        else:
            self.log("🚨 SOME TESTS FAILED - Check the issues above", "FAIL")
            
        # Save detailed results
        self.save_test_results()
    
    def save_test_results(self):
        """Save test results to file"""
        try:
            results = {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tests": self.passed + self.failed,
                    "passed": self.passed,
                    "failed": self.failed,
                    "success_rate": f"{(self.passed / (self.passed + self.failed) * 100):.1f}%" if (self.passed + self.failed) > 0 else "0%"
                },
                "detailed_results": self.results
            }
            
            with open("test_results.json", "w") as f:
                json.dump(results, f, indent=2)
                
            self.log("Test results saved to test_results.json", "INFO")
            
        except Exception as e:
            self.log(f"Failed to save test results: {e}", "WARN")

def main():
    """Main testing function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://0.0.0.0:5000"
    
    print(f"🧪 MemoryOS Endpoint Tester")
    print(f"Testing server at: {base_url}")
    print("=" * 60)
    
    tester = EndpointTester(base_url)
    tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if tester.failed == 0 else 1)

if __name__ == "__main__":
    main()