
#!/usr/bin/env python3
"""
Complete Replit Merge Workflow
Coordinates cleanup, timing, and merge operations for Replit environment
"""

import os
import subprocess
import time
import json
from datetime import datetime

class ReplitMergeWorkflow:
    def __init__(self):
        self.workflow_log = f"replit_merge_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message):
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        with open(self.workflow_log, 'a') as f:
            f.write(log_entry + '\n')
    
    def check_replit_readiness(self):
        """Check if Replit workspace is ready for git operations"""
        self.log("🔍 Checking Replit workspace readiness...")
        
        # Check if we're in Replit
        if not os.path.exists('/home/runner'):
            self.log("❌ Not in Replit environment")
            return False
            
        # Check for active Replit processes that might interfere
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout
            
            interfering_processes = []
            for line in processes.split('\n'):
                if any(proc in line.lower() for proc in ['replit-runtime', 'git', 'autosave']):
                    if 'python' not in line.lower():  # Exclude our own scripts
                        interfering_processes.append(line.strip())
            
            if interfering_processes:
                self.log(f"⚠️ Found {len(interfering_processes)} potentially interfering processes")
                for proc in interfering_processes[:3]:  # Show first 3
                    self.log(f"   {proc}")
            else:
                self.log("✅ No interfering processes detected")
                
        except Exception as e:
            self.log(f"⚠️ Could not check processes: {e}")
            
        return True
    
    def wait_for_quiet_period(self, max_wait=60):
        """Wait for a quiet period with minimal file system activity"""
        self.log("⏳ Waiting for quiet period...")
        
        start_time = time.time()
        quiet_duration = 0
        required_quiet = 10  # 10 seconds of quiet
        
        while time.time() - start_time < max_wait:
            # Check for recent file modifications in .git
            recent_activity = False
            try:
                for root, dirs, files in os.walk('.git'):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if time.time() - os.path.getmtime(file_path) < 5:
                            recent_activity = True
                            break
                    if recent_activity:
                        break
            except:
                pass
                
            if recent_activity:
                quiet_duration = 0
                self.log("   Activity detected, resetting quiet timer...")
                time.sleep(2)
            else:
                quiet_duration += 2
                if quiet_duration >= required_quiet:
                    self.log(f"✅ Quiet period achieved ({quiet_duration}s)")
                    return True
                time.sleep(2)
        
        self.log(f"⚠️ Timeout waiting for quiet period (waited {max_wait}s)")
        return False
    
    def execute_cleanup_with_retries(self, max_retries=3):
        """Execute git cleanup with multiple retries and different strategies"""
        self.log("🧹 Starting git cleanup with retries...")
        
        strategies = [
            ('standard', ['python3', 'replit_git_force_cleanup.py', '--force']),
            ('nuclear', ['python3', 'replit_git_force_cleanup.py', '--nuclear']),
            ('manual', self._manual_cleanup)
        ]
        
        for attempt in range(max_retries):
            self.log(f"🔄 Cleanup attempt {attempt + 1}/{max_retries}")
            
            for strategy_name, strategy in strategies:
                self.log(f"   Trying {strategy_name} strategy...")
                
                try:
                    if callable(strategy):
                        success = strategy()
                    else:
                        result = subprocess.run(strategy, timeout=120)
                        success = result.returncode == 0
                    
                    if success:
                        self.log(f"✅ {strategy_name} strategy succeeded")
                        return True
                    else:
                        self.log(f"❌ {strategy_name} strategy failed")
                        
                except Exception as e:
                    self.log(f"❌ {strategy_name} strategy error: {e}")
                
                time.sleep(5)  # Brief pause between strategies
            
            if attempt < max_retries - 1:
                self.log("⏳ Waiting before next attempt...")
                time.sleep(10)
        
        self.log("❌ All cleanup strategies failed")
        return False
    
    def _manual_cleanup(self):
        """Manual cleanup as last resort"""
        self.log("🔧 Executing manual cleanup...")
        
        try:
            # Force remove common lock files
            lock_files = [
                '.git/index.lock',
                '.git/config.lock', 
                '.git/HEAD.lock',
                '.git/gc.pid.lock'
            ]
            
            removed = 0
            for lock_file in lock_files:
                if os.path.exists(lock_file):
                    try:
                        os.remove(lock_file)
                        removed += 1
                        self.log(f"   Removed {lock_file}")
                    except:
                        try:
                            subprocess.run(['rm', '-f', lock_file])
                            removed += 1
                            self.log(f"   Force removed {lock_file}")
                        except:
                            self.log(f"   Failed to remove {lock_file}")
            
            self.log(f"Manual cleanup removed {removed} files")
            return removed > 0
            
        except Exception as e:
            self.log(f"Manual cleanup failed: {e}")
            return False
    
    def verify_git_state(self):
        """Verify git repository is in good state for merge"""
        self.log("🔍 Verifying git repository state...")
        
        checks = [
            ('Git repo check', ['git', 'rev-parse', '--is-inside-work-tree']),
            ('Status check', ['git', 'status', '--porcelain']),
            ('Branch check', ['git', 'branch', '--show-current']),
            ('Remote check', ['git', 'remote', '-v'])
        ]
        
        all_passed = True
        for check_name, command in checks:
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    self.log(f"   ✅ {check_name} passed")
                else:
                    self.log(f"   ❌ {check_name} failed: {result.stderr}")
                    all_passed = False
            except Exception as e:
                self.log(f"   ❌ {check_name} error: {e}")
                all_passed = False
        
        return all_passed
    
    def execute_merge(self):
        """Execute the actual merge process"""
        self.log("🔄 Starting merge process...")
        
        try:
            result = subprocess.run(['python3', 'auto_merge_prep.py', '--auto-merge'], 
                                  timeout=300, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ Merge completed successfully")
                self.log("STDOUT:")
                for line in result.stdout.split('\n')[:10]:  # First 10 lines
                    if line.strip():
                        self.log(f"   {line}")
                return True
            else:
                self.log("❌ Merge failed")
                self.log("STDERR:")
                for line in result.stderr.split('\n')[:10]:
                    if line.strip():
                        self.log(f"   {line}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("❌ Merge timed out after 5 minutes")
            return False
        except Exception as e:
            self.log(f"❌ Merge error: {e}")
            return False
    
    def run_complete_workflow(self):
        """Run the complete merge workflow"""
        self.log("🚀 STARTING REPLIT MERGE WORKFLOW")
        self.log("=" * 50)
        
        steps = [
            ("Check Replit readiness", self.check_replit_readiness),
            ("Wait for quiet period", lambda: self.wait_for_quiet_period(60)),
            ("Execute cleanup", self.execute_cleanup_with_retries),
            ("Verify git state", self.verify_git_state),
            ("Execute merge", self.execute_merge)
        ]
        
        for step_name, step_func in steps:
            self.log(f"📋 Step: {step_name}")
            
            try:
                if not step_func():
                    self.log(f"❌ Step failed: {step_name}")
                    self.log("🛑 Workflow stopped")
                    return False
                else:
                    self.log(f"✅ Step completed: {step_name}")
            except Exception as e:
                self.log(f"❌ Step error in {step_name}: {e}")
                self.log("🛑 Workflow stopped")
                return False
            
            time.sleep(2)  # Brief pause between steps
        
        self.log("🎉 WORKFLOW COMPLETED SUCCESSFULLY")
        self.log(f"📄 Full log available in: {self.workflow_log}")
        return True

def main():
    import sys
    
    workflow = ReplitMergeWorkflow()
    
    if '--help' in sys.argv:
        print("Replit Merge Workflow")
        print("Usage: python3 replit_merge_workflow.py [--auto]")
        print("  --auto : Run complete workflow automatically")
        return
    
    if '--auto' in sys.argv:
        success = workflow.run_complete_workflow()
        exit(0 if success else 1)
    else:
        print("Replit Merge Workflow - Interactive Mode")
        print("Run with --auto to execute complete workflow")
        print("Or use individual steps:")
        print("  python3 replit_git_force_cleanup.py --force")
        print("  python3 check_git_state.py")
        print("  python3 auto_merge_prep.py --auto-merge")

if __name__ == "__main__":
    main()
