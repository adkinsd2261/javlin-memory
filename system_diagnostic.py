
import os
import json
import importlib
from datetime import datetime
import logging

class SystemDiagnostic:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.issues = []
        self.warnings = []
        self.recommendations = []

    def run_full_diagnostic(self):
        """Run comprehensive system diagnostic"""
        print("🔍 Running MemoryOS System Diagnostic...")
        
        # Test module imports
        self.test_module_imports()
        
        # Test file integrity
        self.test_file_integrity()
        
        # Test API endpoints
        self.test_api_health()
        
        # Test configuration consistency
        self.test_configuration()
        
        # Generate report
        return self.generate_report()

    def test_module_imports(self):
        """Test all module imports"""
        modules_to_test = [
            'bible_compliance',
            'session_manager', 
            'connection_validator',
            'compliance_middleware',
            'gpt_integration',
            'proactive_founder'
        ]
        
        for module in modules_to_test:
            try:
                importlib.import_module(module)
                print(f"✅ {module} - Import successful")
            except ImportError as e:
                self.issues.append(f"❌ {module} - Import failed: {e}")
                print(f"❌ {module} - Import failed: {e}")

    def test_file_integrity(self):
        """Test critical file integrity"""
        critical_files = [
            'main.py',
            'AGENT_BIBLE.md',
            'config.json',
            'memory.json'
        ]
        
        for file in critical_files:
            file_path = os.path.join(self.base_dir, file)
            if os.path.exists(file_path):
                try:
                    if file.endswith('.json'):
                        with open(file_path, 'r') as f:
                            json.load(f)
                    print(f"✅ {file} - File integrity OK")
                except json.JSONDecodeError:
                    self.issues.append(f"❌ {file} - Invalid JSON format")
            else:
                self.issues.append(f"❌ {file} - File missing")

    def test_api_health(self):
        """Test API endpoint health"""
        import subprocess
        
        endpoints = ['/health', '/memory', '/stats', '/system-health']
        base_url = 'https://memoryos.replit.app'
        
        for endpoint in endpoints:
            try:
                result = subprocess.run(
                    ['curl', '-s', '-f', f'{base_url}{endpoint}'], 
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    print(f"✅ {endpoint} - Endpoint responsive")
                else:
                    self.warnings.append(f"⚠️ {endpoint} - Endpoint issues")
            except Exception as e:
                self.warnings.append(f"⚠️ {endpoint} - Connection test failed: {e}")

    def test_configuration(self):
        """Test configuration consistency"""
        try:
            with open(os.path.join(self.base_dir, 'config.json'), 'r') as f:
                config = json.load(f)
            
            # Check for unused config options
            if 'git_sync' in config and config['git_sync']['enabled']:
                if not os.path.exists(os.path.join(self.base_dir, 'git_integration.py')):
                    self.warnings.append("⚠️ Git sync enabled but git_integration.py missing")
            
            print("✅ Configuration consistency check completed")
            
        except Exception as e:
            self.issues.append(f"❌ Configuration test failed: {e}")

    def generate_report(self):
        """Generate diagnostic report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "issues": len(self.issues),
                "warnings": len(self.warnings),
                "status": "CRITICAL" if self.issues else "WARNING" if self.warnings else "HEALTHY"
            },
            "issues": self.issues,
            "warnings": self.warnings,
            "recommendations": self.get_recommendations()
        }
        
        # Save report
        with open(os.path.join(self.base_dir, 'diagnostic_report.json'), 'w') as f:
            json.dump(report, f, indent=2)
        
        self.print_summary()
        return report

    def get_recommendations(self):
        """Generate recommendations based on findings"""
        recommendations = []
        
        if self.issues:
            recommendations.append("🔧 Fix critical issues before proceeding")
            recommendations.append("📋 Review module imports and dependencies")
        
        if self.warnings:
            recommendations.append("⚠️ Address configuration inconsistencies")
            recommendations.append("🔗 Test API endpoint connectivity")
        
        recommendations.extend([
            "🧹 Clean up duplicate backup directories",
            "📝 Update system documentation",
            "🔍 Run regular diagnostic checks"
        ])
        
        return recommendations

    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "="*50)
        print("📊 MEMORYOS SYSTEM DIAGNOSTIC SUMMARY")
        print("="*50)
        print(f"🔴 Critical Issues: {len(self.issues)}")
        print(f"🟡 Warnings: {len(self.warnings)}")
        
        if self.issues:
            print("\n🔴 CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"  {issue}")
        
        if self.warnings:
            print("\n🟡 WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        print("\n💡 RECOMMENDATIONS:")
        for rec in self.get_recommendations():
            print(f"  {rec}")
        
        print("="*50)

if __name__ == "__main__":
    diagnostic = SystemDiagnostic(os.path.dirname(os.path.abspath(__file__)))
    diagnostic.run_full_diagnostic()
