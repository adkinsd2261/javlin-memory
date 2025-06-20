
#!/usr/bin/env python3
"""
Ultimate Git Recovery - Progressive strategy with death loop prevention
"""

import os
import subprocess
import time
import json
import psutil
import glob
from datetime import datetime, timedelta
from pathlib import Path

class UltimateGitRecovery:
    def __init__(self):
        self.recovery_log = "git_recovery_log.json"
        self.max_attempts_per_hour = 3
        self.strategies = [
            "gentle_recovery",
            "aggressive_lock_clear", 
            "nuclear_reset",
            "repo_reinit"
        ]
        
    def load_recovery_history(self):
        """Load recent recovery attempts to prevent death loops"""
        try:
            with open(self.recovery_log, 'r') as f:
                history = json.load(f)
            
            # Filter to last hour only
            cutoff = datetime.now() - timedelta(hours=1)
            recent = [
                attempt for attempt in history 
                if datetime.fromisoformat(attempt['timestamp']) > cutoff
            ]
            return recent
        except:
            return []
    
    def log_recovery_attempt(self, strategy, success, message):
        """Log recovery attempt with timestamp"""
        try:
            history = self.load_recovery_history()
        except:
            history = []
            
        history.append({
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy,
            "success": success,
            "message": message
        })
        
        # Keep only last 20 attempts
        history = history[-20:]
        
        with open(self.recovery_log, 'w') as f:
            json.dump(history, f, indent=2)
    
    def should_abort_recovery(self):
        """Check if we should abort to prevent death loops"""
        history = self.load_recovery_history()
        
        if len(history) >= self.max_attempts_per_hour:
            print(f"🛑 ABORT: {len(history)} recovery attempts in last hour - preventing death loop")
            print("   Manual intervention required or wait 1 hour")
            return True
            
        # Check if same strategy failed 3 times recently
        strategy_failures = {}
        for attempt in history[-6:]:  # Last 6 attempts
            if not attempt['success']:
                strategy = attempt['strategy']
                strategy_failures[strategy] = strategy_failures.get(strategy, 0) + 1
                
        for strategy, failures in strategy_failures.items():
            if failures >= 3:
                print(f"🛑 ABORT: Strategy '{strategy}' failed {failures} times - death loop detected")
                return True
                
        return False
    
    def gentle_recovery(self):
        """Try gentle git recovery first"""
        print("🕊️ Attempting gentle recovery...")
        
        try:
            # Just remove specific lock files
            lock_files = ['.git/index.lock', '.git/refs/heads/main.lock', '.git/HEAD.lock']
            removed = 0
            
            for lock_file in lock_files:
                if os.path.exists(lock_file):
                    os.remove(lock_file)
                    removed += 1
                    
            if removed > 0:
                print(f"   Removed {removed} lock files")
                
            # Test basic git operation
            result = subprocess.run(['git', 'status'], capture_output=True, timeout=10)
            if result.returncode == 0:
                return True, "Gentle recovery successful"
            else:
                return False, f"Git status failed: {result.stderr.decode()}"
                
        except Exception as e:
            return False, f"Gentle recovery failed: {str(e)}"
    
    def aggressive_lock_clear(self):
        """More aggressive lock clearing"""
        print("⚡ Attempting aggressive lock clearing...")
        
        try:
            # Kill git processes
            killed = 0
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'git' in proc.info['name'].lower():
                        proc.kill()
                        killed += 1
                except:
                    pass
                    
            if killed > 0:
                print(f"   Killed {killed} git processes")
                time.sleep(3)
            
            # Remove all lock files
            lock_count = 0
            for lock_file in glob.glob('.git/**/*.lock', recursive=True):
                try:
                    os.remove(lock_file)
                    lock_count += 1
                except:
                    pass
                    
            print(f"   Removed {lock_count} lock files")
            
            # Test git
            result = subprocess.run(['git', 'status'], capture_output=True, timeout=15)
            if result.returncode == 0:
                return True, "Aggressive clearing successful"
            else:
                return False, f"Git still failing: {result.stderr.decode()}"
                
        except Exception as e:
            return False, f"Aggressive clearing failed: {str(e)}"
    
    def nuclear_reset(self):
        """Nuclear option - reset everything"""
        print("💥 Attempting nuclear reset...")
        
        try:
            # Force kill everything
            os.system("pkill -9 git 2>/dev/null || true")
            time.sleep(2)
            
            # Remove all locks
            os.system("find .git -name '*.lock' -delete 2>/dev/null || true")
            
            # Hard reset
            result = subprocess.run(['git', 'reset', '--hard', 'HEAD'], 
                                  capture_output=True, timeout=20)
            
            # Clean untracked files
            subprocess.run(['git', 'clean', '-fdx'], capture_output=True, timeout=15)
            
            # Test
            test_result = subprocess.run(['git', 'status'], capture_output=True, timeout=10)
            if test_result.returncode == 0:
                return True, "Nuclear reset successful"
            else:
                return False, f"Nuclear reset failed: {test_result.stderr.decode()}"
                
        except Exception as e:
            return False, f"Nuclear reset failed: {str(e)}"
    
    def repo_reinit(self):
        """Last resort - reinitialize repository"""
        print("🔥 Last resort: Repository reinitialization...")
        
        try:
            # Create backup
            backup_dir = f"backup_{int(time.time())}"
            important_files = ["main.py", "memory.json", "README.md", "AGENT_BIBLE.md"]
            
            os.makedirs(backup_dir, exist_ok=True)
            for file in important_files:
                if os.path.exists(file):
                    subprocess.run(['cp', file, f"{backup_dir}/"])
                    
            print(f"   Created backup in {backup_dir}")
            
            # Remove .git directory
            subprocess.run(['rm', '-rf', '.git'], timeout=10)
            print("   Removed corrupted .git directory")
            
            # Reinitialize
            subprocess.run(['git', 'init'], timeout=10)
            subprocess.run(['git', 'remote', 'add', 'origin', 
                           'https://github.com/adkinsd2261/memoryos.git'], timeout=10)
            
            # Configure
            subprocess.run(['git', 'config', 'user.name', 'Darryl'], timeout=5)
            subprocess.run(['git', 'config', 'user.email', 'adkinsd226@gmail.com'], timeout=5)
            
            print("   Repository reinitialized")
            
            # Test
            result = subprocess.run(['git', 'status'], capture_output=True, timeout=10)
            if result.returncode == 0:
                return True, f"Repository reinitialized successfully, backup in {backup_dir}"
            else:
                return False, "Reinitialization failed"
                
        except Exception as e:
            return False, f"Repository reinitialization failed: {str(e)}"
    
    def execute_recovery(self):
        """Execute progressive recovery with death loop prevention"""
        print("🚨 Ultimate Git Recovery Starting")
        print("=" * 50)
        
        # Check for death loop conditions
        if self.should_abort_recovery():
            print("\n❌ Recovery aborted to prevent death loop")
            print("💡 Suggested actions:")
            print("   1. Wait 1 hour for automatic reset")
            print("   2. Manual git operations in shell")
            print("   3. Contact support if persistent")
            return False
        
        # Try each strategy progressively
        for strategy in self.strategies:
            print(f"\n🔄 Trying strategy: {strategy}")
            
            strategy_method = getattr(self, strategy)
            success, message = strategy_method()
            
            # Log the attempt
            self.log_recovery_attempt(strategy, success, message)
            
            if success:
                print(f"✅ SUCCESS: {message}")
                
                # Try a simple commit to verify it works
                if self.test_commit():
                    print("🎉 Git operations fully restored!")
                    return True
                else:
                    print("⚠️ Git operations partially restored")
                    continue
            else:
                print(f"❌ FAILED: {message}")
        
        print("\n💥 All recovery strategies failed")
        print("🔧 Manual intervention required")
        return False
    
    def test_commit(self):
        """Test if we can actually commit and push"""
        try:
            # Create a test file
            with open('git_recovery_test.txt', 'w') as f:
                f.write(f"Recovery test: {datetime.now().isoformat()}")
            
            # Try to commit
            subprocess.run(['git', 'add', 'git_recovery_test.txt'], 
                          check=True, timeout=15)
            subprocess.run(['git', 'commit', '-m', 'Test commit after recovery'], 
                          check=True, timeout=15)
            
            # Clean up test file
            os.remove('git_recovery_test.txt')
            
            print("   ✅ Test commit successful")
            return True
            
        except Exception as e:
            print(f"   ❌ Test commit failed: {e}")
            return False

def main():
    recovery = UltimateGitRecovery()
    recovery.execute_recovery()

if __name__ == "__main__":
    main()
