
#!/usr/bin/env python3
"""
Git Coordinator - Single point of control for all git operations
Prevents the death loop by ensuring only one git operation at a time
"""

import os
import subprocess
import time
import fcntl
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path

class GitCoordinator:
    def __init__(self):
        self.lock_file = os.path.join(tempfile.gettempdir(), 'memoryos_git_coordinator.lock')
        self.status_file = 'git_coordinator_status.json'
        
    def _load_status(self):
        """Load coordinator status"""
        try:
            with open(self.status_file, 'r') as f:
                return json.load(f)
        except:
            return {
                "last_operation": None,
                "consecutive_failures": 0,
                "blocked_until": None,
                "status": "ready"
            }
    
    def _save_status(self, status):
        """Save coordinator status"""
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def _is_blocked(self):
        """Check if operations are temporarily blocked"""
        status = self._load_status()
        if status.get('blocked_until'):
            blocked_until = datetime.fromisoformat(status['blocked_until'])
            if datetime.now() < blocked_until:
                return True, f"Blocked until {blocked_until.strftime('%H:%M:%S')}"
            else:
                # Unblock
                status['blocked_until'] = None
                status['consecutive_failures'] = 0
                self._save_status(status)
        return False, ""
    
    def _simple_clear_locks(self):
        """Aggressive lock clearing - force remove all git locks"""
        lock_files = [
            '.git/index.lock',
            '.git/refs/heads/main.lock', 
            '.git/HEAD.lock',
            '.git/config.lock',
            '.git/COMMIT_EDITMSG.lock'
        ]
        
        # Kill any git processes first
        try:
            subprocess.run(['pkill', '-9', 'git'], capture_output=True, timeout=5)
            time.sleep(1)
        except:
            pass
        
        removed = 0
        for lock_file in lock_files:
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                    removed += 1
                    print(f"Removed lock file: {lock_file}")
                except Exception as e:
                    print(f"Failed to remove {lock_file}: {e}")
        
        return removed
    
    def execute_git_operation(self, operation_name, operation_func, *args, **kwargs):
        """Execute git operation with coordination"""
        
        # Check if blocked
        blocked, reason = self._is_blocked()
        if blocked:
            return {"status": "blocked", "message": reason}
        
        # Try to acquire lock
        try:
            with open(self.lock_file, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                status = self._load_status()
                
                try:
                    # Always clear locks before operations - be aggressive
                    print(f"🔧 Clearing git locks before {operation_name}")
                    cleared = self._simple_clear_locks()
                    if cleared > 0:
                        print(f"   Cleared {cleared} lock files")
                        time.sleep(2)  # Longer pause after clearing
                    
                    # Execute the operation
                    result = operation_func(*args, **kwargs)
                    
                    # Update status on success
                    status['last_operation'] = {
                        "name": operation_name,
                        "timestamp": datetime.now().isoformat(),
                        "success": True
                    }
                    status['consecutive_failures'] = 0
                    status['status'] = 'success'
                    self._save_status(status)
                    
                    return {"status": "success", "result": result}
                    
                except Exception as e:
                    # Update status on failure
                    status['consecutive_failures'] += 1
                    status['last_operation'] = {
                        "name": operation_name,
                        "timestamp": datetime.now().isoformat(),
                        "success": False,
                        "error": str(e)
                    }
                    
                    # Block for increasing durations
                    if status['consecutive_failures'] >= 3:
                        block_minutes = min(status['consecutive_failures'] * 2, 15)
                        blocked_until = datetime.now() + timedelta(minutes=block_minutes)
                        status['blocked_until'] = blocked_until.isoformat()
                        status['status'] = 'blocked'
                    else:
                        status['status'] = 'failed'
                    
                    self._save_status(status)
                    return {"status": "error", "message": str(e)}
                
        except BlockingIOError:
            return {"status": "skipped", "message": "Another git operation in progress"}

# Global coordinator instance
git_coordinator = GitCoordinator()

def coordinated_git_add_commit_push(message="Auto commit"):
    """Coordinated git add, commit, push"""
    def operation():
        # Check for changes
        result = subprocess.run(['git', 'status', '--porcelain'], 
                               capture_output=True, text=True, timeout=10)
        if not result.stdout.strip():
            return "No changes to commit"
        
        # Add files
        subprocess.run(['git', 'add', '.'], check=True, timeout=30)
        
        # Commit
        subprocess.run(['git', 'commit', '-m', message], check=True, timeout=30)
        
        # Push
        subprocess.run(['git', 'push', 'origin', 'main'], check=True, timeout=60)
        
        return "Successfully committed and pushed"
    
    return git_coordinator.execute_git_operation("add_commit_push", operation)

def coordinated_git_status():
    """Coordinated git status check"""
    def operation():
        result = subprocess.run(['git', 'status', '--porcelain'], 
                               capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    
    return git_coordinator.execute_git_operation("status", operation)

if __name__ == "__main__":
    # Test the coordinator
    print("🎯 Git Coordinator Test")
    print("=" * 30)
    
    # Check status
    status_result = coordinated_git_status()
    print(f"Status check: {status_result}")
    
    # Try commit if there are changes
    if status_result.get('status') == 'success' and status_result.get('result'):
        commit_result = coordinated_git_add_commit_push("🔧 Coordinated commit - breaking death loop")
        print(f"Commit result: {commit_result}")
    else:
        print("No changes to commit")
