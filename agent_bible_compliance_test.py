
#!/usr/bin/env python3
"""
AGENT_BIBLE.md Compliance Test

This script verifies that agent logic and API endpoints comply with AGENT_BIBLE.md principles.
Run this before commits to ensure behavioral compliance.

Usage: python agent_bible_compliance_test.py
"""

import os
import json
import re
import subprocess
import sys
from typing import List, Dict, Tuple

class AgentBibleComplianceChecker:
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.agent_bible_file = os.path.join(base_dir, "AGENT_BIBLE.md")
        self.main_file = os.path.join(base_dir, "main.py")
        self.compliance_issues = []
        
    def check_agent_bible_exists(self) -> bool:
        """Check if AGENT_BIBLE.md exists and is readable"""
        if not os.path.exists(self.agent_bible_file):
            self.compliance_issues.append("CRITICAL: AGENT_BIBLE.md not found")
            return False
        
        try:
            with open(self.agent_bible_file, 'r') as f:
                content = f.read()
                if len(content) < 100:
                    self.compliance_issues.append("WARNING: AGENT_BIBLE.md appears incomplete")
                    return False
        except Exception as e:
            self.compliance_issues.append(f"ERROR: Cannot read AGENT_BIBLE.md: {e}")
            return False
        
        return True
    
    def check_main_py_compliance(self) -> bool:
        """Check if main.py has proper AGENT_BIBLE.md references"""
        if not os.path.exists(self.main_file):
            self.compliance_issues.append("CRITICAL: main.py not found")
            return False
        
        with open(self.main_file, 'r') as f:
            content = f.read()
        
        # Check for docstring reference
        if 'AGENT_BIBLE.md' not in content[:1000]:  # Check first 1000 chars for docstring
            self.compliance_issues.append("FAIL: main.py missing AGENT_BIBLE.md reference in docstring")
        
        # Check for validation function
        if 'validate_confirmation_requirement' not in content:
            self.compliance_issues.append("FAIL: main.py missing validate_confirmation_requirement function")
        
        # Check for compliance checking
        if 'check_agent_bible_compliance' not in content:
            self.compliance_issues.append("FAIL: main.py missing check_agent_bible_compliance function")
        
        # Check for onboarding endpoint
        if '/onboarding' not in content:
            self.compliance_issues.append("FAIL: main.py missing /onboarding endpoint")
        
        return len([issue for issue in self.compliance_issues if 'main.py' in issue]) == 0
    
    def check_readme_compliance(self) -> bool:
        """Check if README.md has proper AGENT_BIBLE.md governance statement"""
        readme_file = os.path.join(self.base_dir, "README.md")
        
        if not os.path.exists(readme_file):
            self.compliance_issues.append("WARNING: README.md not found")
            return False
        
        with open(readme_file, 'r') as f:
            content = f.read()
        
        if 'governed by' not in content.lower() or 'AGENT_BIBLE.md' not in content:
            self.compliance_issues.append("FAIL: README.md missing AGENT_BIBLE.md governance statement")
            return False
        
        return True
    
    def check_endpoint_compliance(self) -> bool:
        """Check if required compliance endpoints exist"""
        with open(self.main_file, 'r') as f:
            content = f.read()
        
        required_endpoints = [
            ('/onboarding', 'Agent capabilities and boundaries explanation'),
            ('/system-health', 'AGENT_BIBLE.md compliance monitoring'),
            ('validate_confirmation_requirement', 'Manual confirmation validation')
        ]
        
        for endpoint, description in required_endpoints:
            if endpoint not in content:
                self.compliance_issues.append(f"FAIL: Missing required endpoint/function: {endpoint} ({description})")
        
        return len([issue for issue in self.compliance_issues if 'Missing required endpoint' in issue]) == 0
    
    def check_api_key_protection(self) -> bool:
        """Check if API key protection follows AGENT_BIBLE.md security requirements"""
        with open(self.main_file, 'r') as f:
            content = f.read()
        
        if 'require_api_key' not in content:
            self.compliance_issues.append("WARNING: API key protection function not found")
            return False
        
        if 'X-API-KEY' not in content:
            self.compliance_issues.append("WARNING: API key header checking may be incomplete")
        
        return True
    
    def run_all_checks(self) -> Dict:
        """Run all compliance checks and return results"""
        print("🔍 Running AGENT_BIBLE.md Compliance Checks...\n")
        
        results = {
            "agent_bible_exists": self.check_agent_bible_exists(),
            "main_py_compliance": self.check_main_py_compliance(),
            "readme_compliance": self.check_readme_compliance(),
            "endpoint_compliance": self.check_endpoint_compliance(),
            "api_key_protection": self.check_api_key_protection(),
            "issues": self.compliance_issues
        }
        
        # Overall compliance
        results["overall_compliant"] = all([
            results["agent_bible_exists"],
            results["main_py_compliance"],
            results["readme_compliance"],
            results["endpoint_compliance"]
        ])
        
        return results
    
    def print_results(self, results: Dict):
        """Print compliance check results"""
        print("📊 COMPLIANCE RESULTS:")
        print(f"{'='*50}")
        
        checks = [
            ("AGENT_BIBLE.md exists", results["agent_bible_exists"]),
            ("main.py compliance", results["main_py_compliance"]),
            ("README.md governance", results["readme_compliance"]),
            ("Required endpoints", results["endpoint_compliance"]),
            ("API key protection", results["api_key_protection"])
        ]
        
        for check_name, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{check_name:<25} {status}")
        
        print(f"{'='*50}")
        
        if results["overall_compliant"]:
            print("🎉 OVERALL: COMPLIANT WITH AGENT_BIBLE.md")
        else:
            print("⚠️  OVERALL: NON-COMPLIANT - SEE ISSUES BELOW")
        
        if results["issues"]:
            print(f"\n🚨 ISSUES FOUND ({len(results['issues'])}):")
            for i, issue in enumerate(results["issues"], 1):
                print(f"{i:2d}. {issue}")
        
        print()

def main():
    """Main compliance check execution"""
    checker = AgentBibleComplianceChecker()
    results = checker.run_all_checks()
    checker.print_results(results)
    
    # Exit with error code if not compliant
    if not results["overall_compliant"]:
        print("💡 FIX ISSUES ABOVE BEFORE COMMITTING")
        sys.exit(1)
    else:
        print("✅ Ready for commit - AGENT_BIBLE.md compliance verified")
        sys.exit(0)

if __name__ == "__main__":
    main()
