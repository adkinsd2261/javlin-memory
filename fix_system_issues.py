"""
MemoryOS System Issue Fixer
Automatically detects and fixes common system issues
"""

import os
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class SystemFixer:
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_emoji = {"INFO": "ℹ️", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "FIX": "🔧"}
        print(f"[{timestamp}] {status_emoji.get(status, 'ℹ️')} {message}")
    
    def check_memory_file(self):
        """Check and fix memory.json issues"""
        self.log("Checking memory.json file...", "INFO")
        
        if not os.path.exists('memory.json'):
            self.log("memory.json not found, creating...", "FIX")
            with open('memory.json', 'w') as f:
                json.dump([], f)
            self.fixes_applied.append("Created missing memory.json")
            return True
        
        try:
            with open('memory.json', 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                self.log("memory.json contains invalid data, fixing...", "FIX")
                # Backup corrupted file
                backup_name = f"memory_corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                os.rename('memory.json', backup_name)
                
                # Create fresh file
                with open('memory.json', 'w') as f:
                    json.dump([], f)
                
                self.fixes_applied.append(f"Fixed corrupted memory.json (backup: {backup_name})")
                return True
            
            self.log(f"memory.json is valid with {len(data)} entries", "PASS")
            return True
            
        except json.JSONDecodeError:
            self.log("memory.json has invalid JSON, fixing...", "FIX")
            # Backup corrupted file
            backup_name = f"memory_corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.rename('memory.json', backup_name)
            
            # Create fresh file
            with open('memory.json', 'w') as f:
                json.dump([], f)
            
            self.fixes_applied.append(f"Fixed corrupted JSON (backup: {backup_name})")
            return True
    
    def check_required_files(self):
        """Check for required files"""
        self.log("Checking required files...", "INFO")
        
        required_files = {
            'main.py': 'Main application file',
            'requirements.txt': 'Python dependencies',
            'README.md': 'Documentation'
        }
        
        missing_files = []
        for file, description in required_files.items():
            if not os.path.exists(file):
                missing_files.append(f"{file} ({description})")
        
        if missing_files:
            self.log(f"Missing files: {', '.join(missing_files)}", "WARN")
            self.issues_found.extend(missing_files)
        else:
            self.log("All required files present", "PASS")
        
        return len(missing_files) == 0
    
    def check_port_conflicts(self):
        """Check for port conflicts"""
        self.log("Checking for port conflicts...", "INFO")
        
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 5000))
            sock.close()
            
            if result == 0:
                self.log("Port 5000 is in use, attempting to free it...", "FIX")
                
                # Try to kill processes using port 5000
                try:
                    subprocess.run(['pkill', '-f', 'python.*main.py'], check=False)
                    self.fixes_applied.append("Killed processes using port 5000")
                    self.log("Freed port 5000", "PASS")
                    return True
                except:
                    self.log("Could not free port 5000 automatically", "WARN")
                    self.issues_found.append("Port 5000 conflict")
                    return False
            else:
                self.log("Port 5000 is available", "PASS")
                return True
                
        except Exception as e:
            self.log(f"Port check failed: {e}", "WARN")
            return False
    
    def check_python_syntax(self):
        """Check Python files for syntax errors"""
        self.log("Checking Python syntax...", "INFO")
        
        python_files = ['main.py', 'test_endpoints.py']
        syntax_errors = []
        
        for file in python_files:
            if os.path.exists(file):
                try:
                    with open(file, 'r') as f:
                        compile(f.read(), file, 'exec')
                    self.log(f"{file} syntax OK", "PASS")
                except SyntaxError as e:
                    error_msg = f"{file}: {e}"
                    syntax_errors.append(error_msg)
                    self.log(f"Syntax error in {file}: {e}", "FAIL")
        
        if syntax_errors:
            self.issues_found.extend(syntax_errors)
            return False
        
        return True
    
    def check_dependencies(self):
        """Check if required dependencies are available"""
        self.log("Checking dependencies...", "INFO")
        
        required_modules = ['flask', 'flask_cors', 'requests']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
                self.log(f"{module} available", "PASS")
            except ImportError:
                missing_modules.append(module)
                self.log(f"{module} missing", "FAIL")
        
        if missing_modules:
            self.log("Attempting to install missing dependencies...", "FIX")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_modules, 
                             check=True, capture_output=True)
                self.fixes_applied.append(f"Installed missing modules: {', '.join(missing_modules)}")
                self.log("Dependencies installed successfully", "PASS")
                return True
            except subprocess.CalledProcessError as e:
                self.log(f"Failed to install dependencies: {e}", "FAIL")
                self.issues_found.extend([f"Missing module: {m}" for m in missing_modules])
                return False
        
        return True
    
    def check_logs_directory(self):
        """Ensure logs directory exists"""
        self.log("Checking logs directory...", "INFO")
        
        if not os.path.exists('logs'):
            self.log("Creating logs directory...", "FIX")
            os.makedirs('logs', exist_ok=True)
            self.fixes_applied.append("Created logs directory")
        else:
            self.log("Logs directory exists", "PASS")
        
        return True
    
    def test_basic_functionality(self):
        """Test basic system functionality"""
        self.log("Testing basic functionality...", "INFO")
        
        try:
            # Test memory loading
            sys.path.insert(0, '.')
            from main import load_memory, save_memory
            
            memory = load_memory()
            self.log(f"Memory loading test passed ({len(memory)} entries)", "PASS")
            
            # Test memory saving
            if save_memory(memory):
                self.log("Memory saving test passed", "PASS")
            else:
                self.log("Memory saving test failed", "FAIL")
                self.issues_found.append("Memory saving functionality broken")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Basic functionality test failed: {e}", "FAIL")
            self.issues_found.append(f"Basic functionality error: {e}")
            return False
    
    def run_health_check(self):
        """Run a quick health check"""
        self.log("Running health check...", "INFO")
        
        try:
            import requests
            response = requests.get('http://localhost:5000/health', timeout=5)
            if response.status_code in [200, 503]:
                data = response.json()
                status = data.get('status', 'unknown')
                self.log(f"Health check passed - Status: {status}", "PASS")
                return True
            else:
                self.log(f"Health check failed - Status: {response.status_code}", "FAIL")
                return False
        except requests.exceptions.ConnectionError:
            self.log("Health check failed - Server not running", "WARN")
            return False
        except Exception as e:
            self.log(f"Health check error: {e}", "FAIL")
            return False
    
    def fix_all_issues(self):
        """Run all checks and fixes"""
        self.log("🔧 Starting MemoryOS System Fixer", "INFO")
        self.log("=" * 50, "INFO")
        
        checks = [
            ("Memory File", self.check_memory_file),
            ("Required Files", self.check_required_files),
            ("Port Conflicts", self.check_port_conflicts),
            ("Python Syntax", self.check_python_syntax),
            ("Dependencies", self.check_dependencies),
            ("Logs Directory", self.check_logs_directory),
            ("Basic Functionality", self.test_basic_functionality),
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            self.log(f"Running {check_name} check...", "INFO")
            try:
                if not check_func():
                    all_passed = False
            except Exception as e:
                self.log(f"{check_name} check crashed: {e}", "FAIL")
                all_passed = False
        
        # Try health check if server might be running
        self.run_health_check()
        
        # Summary
        self.log("=" * 50, "INFO")
        self.log("🏁 SYSTEM FIXER SUMMARY", "INFO")
        self.log("=" * 50, "INFO")
        
        if self.fixes_applied:
            self.log("Fixes Applied:", "INFO")
            for fix in self.fixes_applied:
                self.log(f"  • {fix}", "FIX")
        
        if self.issues_found:
            self.log("Issues Found (manual fix needed):", "WARN")
            for issue in self.issues_found:
                self.log(f"  • {issue}", "FAIL")
        
        if all_passed and not self.issues_found:
            self.log("🎉 ALL CHECKS PASSED - System is ready!", "PASS")
        elif self.fixes_applied and not self.issues_found:
            self.log("✅ ISSUES FIXED - System should be working now!", "PASS")
        else:
            self.log("⚠️ SOME ISSUES REMAIN - Manual intervention needed", "WARN")
        
        return all_passed and not self.issues_found

def main():
    fixer = SystemFixer()
    success = fixer.fix_all_issues()
    
    if success:
        print("\n🚀 Ready to start MemoryOS:")
        print("   python main.py")
        print("\n🧪 Or run endpoint tests:")
        print("   python test_endpoints.py")
    else:
        print("\n🔧 Please fix the remaining issues before starting the system")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()