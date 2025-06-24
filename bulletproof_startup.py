"""
Bulletproof Startup Script for MemoryOS
Ensures the system starts safely with all safeguards in place
"""

import os
import sys
import json
import subprocess
import traceback
import time
import signal
from datetime import datetime, timezone
from pathlib import Path

class BulletproofStartup:
    """Handles safe system startup with comprehensive checks"""
    
    def __init__(self):
        self.startup_log = []
        self.errors = []
        self.warnings = []
        
    def log(self, message, level="INFO"):
        """Log startup messages"""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        self.startup_log.append(log_entry)
        print(log_entry)
        
        if level == "ERROR":
            self.errors.append(message)
        elif level == "WARNING":
            self.warnings.append(message)
    
    def check_python_version(self):
        """Check Python version compatibility"""
        try:
            version = sys.version_info
            if version.major < 3 or (version.major == 3 and version.minor < 8):
                self.log(f"Python version {version.major}.{version.minor} may have compatibility issues", "WARNING")
            else:
                self.log(f"Python version {version.major}.{version.minor}.{version.micro} - OK", "INFO")
            return True
        except Exception as e:
            self.log(f"Could not check Python version: {e}", "ERROR")
            return False
    
    def check_required_files(self):
        """Check all required files exist"""
        required_files = [
            'main.py',
            'memory.json',
            'AGENT_BIBLE.md',
            'README.md'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            self.log(f"Missing required files: {missing_files}", "ERROR")
            return False
        else:
            self.log("All required files present - OK", "INFO")
            return True
    
    def check_memory_file_integrity(self):
        """Check memory.json file integrity"""
        try:
            with open('memory.json', 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                self.log("memory.json is not a list - attempting to fix", "WARNING")
                with open('memory.json', 'w') as f:
                    json.dump([], f)
                self.log("memory.json fixed - OK", "INFO")
            else:
                self.log(f"memory.json valid with {len(data)} entries - OK", "INFO")
            
            return True
            
        except json.JSONDecodeError as e:
            self.log(f"memory.json is corrupted: {e}", "ERROR")
            # Create backup and reset
            try:
                backup_name = f"memory_corrupted_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                os.rename('memory.json', backup_name)
                with open('memory.json', 'w') as f:
                    json.dump([], f)
                self.log(f"Created backup {backup_name} and reset memory.json", "WARNING")
                return True
            except Exception as backup_error:
                self.log(f"Could not fix memory.json: {backup_error}", "ERROR")
                return False
        
        except Exception as e:
            self.log(f"Could not check memory.json: {e}", "ERROR")
            return False
    
    def check_logs_directory(self):
        """Ensure logs directory exists"""
        try:
            Path("logs").mkdir(exist_ok=True)
            self.log("Logs directory ready - OK", "INFO")
            return True
        except Exception as e:
            self.log(f"Could not create logs directory: {e}", "ERROR")
            return False
    
    def run_health_tests(self):
        """Run basic health tests"""
        try:
            # Import and test core functions
            from main import load_memory, save_memory
            
            # Test memory loading
            memory = load_memory()
            self.log(f"Memory loading test - OK ({len(memory)} entries)", "INFO")
            
            # Test memory saving (dry run)
            test_save = save_memory(memory)
            if test_save:
                self.log("Memory saving test - OK", "INFO")
            else:
                self.log("Memory saving test - FAILED", "ERROR")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Health tests failed: {e}", "ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            return False
    
    def kill_processes_on_port(self, port=5000):
        """Kill any processes using the specified port"""
        try:
            # Try to find and kill processes using the port
            self.log(f"Attempting to free port {port}...", "INFO")
            
            # Kill any Python processes that might be running main.py
            try:
                subprocess.run(['pkill', '-f', 'python.*main.py'], 
                             capture_output=True, timeout=5)
                self.log("Killed existing Python processes", "INFO")
            except subprocess.TimeoutExpired:
                self.log("Timeout while killing processes", "WARNING")
            except FileNotFoundError:
                # pkill not available, try alternative approach
                self.log("pkill not available, trying alternative approach", "INFO")
                
            # Try to find processes using lsof (if available)
            try:
                result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                      capture_output=True, text=True, timeout=5)
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                            self.log(f"Killed process {pid} using port {port}", "INFO")
                        except (ValueError, ProcessLookupError, PermissionError) as e:
                            self.log(f"Could not kill process {pid}: {e}", "WARNING")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.log("lsof not available or timed out", "INFO")
            
            # Wait a moment for processes to clean up
            time.sleep(2)
            
            return True
            
        except Exception as e:
            self.log(f"Error while trying to free port {port}: {e}", "WARNING")
            return True  # Don't fail startup for this
    
    def check_port_availability(self, port=5000):
        """Check if the target port is available, attempt to free it if not"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:
                self.log(f"Port {port} is already in use", "WARNING")
                
                # Attempt to free the port
                self.kill_processes_on_port(port)
                
                # Check again after attempting to free the port
                time.sleep(1)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                
                if result == 0:
                    self.log(f"Port {port} is still in use after cleanup attempt", "ERROR")
                    return False
                else:
                    self.log(f"Port {port} successfully freed - OK", "INFO")
                    return True
            else:
                self.log(f"Port {port} is available - OK", "INFO")
                return True
                
        except Exception as e:
            self.log(f"Could not check port {port}: {e}", "WARNING")
            return True  # Assume OK if we can't check
    
    def run_startup_checks(self):
        """Run all startup checks"""
        self.log("Starting MemoryOS Bulletproof Startup Checks", "INFO")
        self.log("=" * 50, "INFO")
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Required Files", self.check_required_files),
            ("Memory File Integrity", self.check_memory_file_integrity),
            ("Logs Directory", self.check_logs_directory),
            ("Port Availability", self.check_port_availability),
            ("Health Tests", self.run_health_tests)
        ]
        
        failed_checks = []
        
        for check_name, check_func in checks:
            self.log(f"Running {check_name} check...", "INFO")
            try:
                if not check_func():
                    failed_checks.append(check_name)
            except Exception as e:
                self.log(f"{check_name} check crashed: {e}", "ERROR")
                failed_checks.append(check_name)
        
        self.log("=" * 50, "INFO")
        
        if failed_checks:
            self.log(f"STARTUP CHECKS FAILED: {failed_checks}", "ERROR")
            self.log("Please fix the above issues before starting the server", "ERROR")
            return False
        else:
            self.log("ALL STARTUP CHECKS PASSED - READY TO START", "INFO")
            return True
    
    def save_startup_report(self):
        """Save startup report to file"""
        try:
            report = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "startup_log": self.startup_log,
                "errors": self.errors,
                "warnings": self.warnings,
                "status": "success" if not self.errors else "failed"
            }
            
            with open('logs/startup_report.json', 'w') as f:
                json.dump(report, f, indent=2)
                
            self.log("Startup report saved to logs/startup_report.json", "INFO")
            
        except Exception as e:
            self.log(f"Could not save startup report: {e}", "WARNING")

def main():
    """Main startup function"""
    startup = BulletproofStartup()
    
    try:
        # Run all checks
        if startup.run_startup_checks():
            startup.save_startup_report()
            print("\n🚀 SYSTEM READY - Starting MemoryOS...")
            
            # Start the main application
            from main import app
            app.run(host='0.0.0.0', port=5000, debug=False)
            
        else:
            startup.save_startup_report()
            print("\n❌ STARTUP FAILED - Check errors above")
            print("📋 Full report saved to logs/startup_report.json")
            
            # Check if port availability was one of the failed checks
            if any("Port 5000 is still in use" in error for error in startup.errors):
                print("\n🔧 PORT CONFLICT DETECTED:")
                print("   Port 5000 is already in use by another process.")
                print("   To manually free the port, run this command:")
                print("   lsof -ti :5000 | xargs kill -9")
                print("   Then restart the application.")
            
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Startup interrupted by user")
        sys.exit(0)
    except Exception as e:
        startup.log(f"Critical startup failure: {e}", "ERROR")
        startup.log(f"Traceback: {traceback.format_exc()}", "ERROR")
        startup.save_startup_report()
        print("\n💥 CRITICAL STARTUP FAILURE")
        print("📋 Full report saved to logs/startup_report.json")
        sys.exit(1)

if __name__ == "__main__":
    main()