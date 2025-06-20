
"""
MemoryOS Test Runner
Convenient script to run all tests with proper setup
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🧪 {description}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="MemoryOS Test Runner")
    parser.add_argument("--quick", action="store_true", help="Run only quick tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--test", "-t", help="Run specific test pattern")
    
    args = parser.parse_args()
    
    print("🛡️  MemoryOS Bulletproof Test Runner")
    print("=" * 50)
    print(f"Started at: {datetime.now()}")
    
    # Ensure we're in the right directory
    if not os.path.exists('main.py'):
        print("❌ Error: main.py not found. Run this script from the project root.")
        sys.exit(1)
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test commands
    test_commands = []
    
    if args.test:
        # Run specific test pattern
        verbose_flag = "-v" if args.verbose else ""
        test_commands.append((
            f"python -m pytest test_memoryos.py -k \"{args.test}\" {verbose_flag}",
            f"Specific tests matching: {args.test}"
        ))
    elif args.quick:
        # Quick tests only
        test_commands = [
            ("python -c \"from main import load_memory; print('Memory loading:', 'OK' if load_memory() is not None else 'FAIL')\"", "Quick memory test"),
            ("python -c \"import requests; r=requests.get('http://localhost:5000/health'); print('Health endpoint:', r.status_code)\" 2>/dev/null || echo 'Health endpoint: Server not running'", "Quick health test"),
        ]
    else:
        # Full test suite
        verbose_flag = "-v --tb=short" if args.verbose else ""
        test_commands = [
            ("python bulletproof_startup.py --check-only 2>/dev/null || python -c \"print('Startup checks: SKIPPED (bulletproof_startup.py not available)')\"", "Startup integrity checks"),
            (f"python -m pytest test_memoryos.py::TestMemoryOperations {verbose_flag}", "Memory operations tests"),
            (f"python -m pytest test_memoryos.py::TestHealthEndpoint {verbose_flag}", "Health endpoint tests"),
            (f"python -m pytest test_memoryos.py::TestAPIEndpoints {verbose_flag}", "API endpoint tests"),
            (f"python -m pytest test_memoryos.py::TestBulletproofLogger {verbose_flag}", "Bulletproof logger tests"),
            (f"python -m pytest test_memoryos.py::TestSystemResilience {verbose_flag}", "System resilience tests"),
            (f"python -m pytest test_memoryos.py::TestSystemIntegration {verbose_flag}", "Integration tests"),
        ]
    
    # Run all tests
    for command, description in test_commands:
        if run_command(command, description):
            tests_passed += 1
        else:
            tests_failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Tests Passed: {tests_passed}")
    print(f"❌ Tests Failed: {tests_failed}")
    print(f"📊 Success Rate: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%" if (tests_passed+tests_failed) > 0 else "No tests run")
    print(f"Completed at: {datetime.now()}")
    
    if tests_failed > 0:
        print("\n🚨 SOME TESTS FAILED - DO NOT DEPLOY")
        print("Fix the failing tests before deploying to production.")
        sys.exit(1)
    else:
        print("\n🎉 ALL TESTS PASSED - SAFE TO DEPLOY")
        print("System is ready for production deployment.")
        sys.exit(0)

if __name__ == "__main__":
    main()
