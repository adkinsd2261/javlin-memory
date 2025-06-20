
#!/usr/bin/env python3
"""
Simple Git Manager - Single source of truth for all git operations
Replaces all the competing git systems causing death loops
"""

import os
import subprocess
import time
import fcntl
import tempfile
import json
from datetime import datetime

class SimpleGitManager:
    def __init__(self):
        self.lock_file = '/tmp/memoryos_git.lock'
        
    def _acquire_lock(self):
        """Simple file lock - only one git operation at a time"""
        try:
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            return False
    
    def _release_lock(self):
        """Release the file lock"""
        try:
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
            self.lock_fd.close()
            os.unlink(self.lock_file)
        except:
            pass
    
    def _clear_locks_simple(self):
        """Simple lock clearing - just remove the files"""
        lock_files = [
            '.git/index.lock',
            '.git/refs/heads/main.lock',
            '.git/HEAD.lock'
        ]
        
        for lock_file in lock_files:
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                    print(f"Removed {lock_file}")
                except:
                    pass
    
    def status(self):
        """Check git status"""
        if not self._acquire_lock():
            return {"error": "Git operation in progress"}
        
        try:
            self._clear_locks_simple()
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, timeout=10)
            return {"status": "success", "output": result.stdout.strip()}
        except Exception as e:
            return {"error": str(e)}
        finally:
            self._release_lock()
    
    def commit_and_push(self, message="Auto commit"):
        """Simple commit and push"""
        if not self._acquire_lock():
            return {"error": "Git operation in progress"}
        
        try:
            # Clear locks first
            self._clear_locks_simple()
            time.sleep(1)
            
            # Check for changes
            status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                         capture_output=True, text=True, timeout=10)
            if not status_result.stdout.strip():
                return {"status": "success", "message": "No changes to commit"}
            
            # Simple three-step process
            subprocess.run(['git', 'add', '.'], check=True, timeout=30)
            subprocess.run(['git', 'commit', '-m', message], check=True, timeout=30)
            subprocess.run(['git', 'push', 'origin', 'main'], check=True, timeout=60)
            
            return {"status": "success", "message": "Committed and pushed successfully"}
            
        except subprocess.CalledProcessError as e:
            return {"error": f"Git command failed: {e}"}
        except subprocess.TimeoutExpired:
            return {"error": "Git operation timed out"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            self._release_lock()

# Global instance
git_manager = SimpleGitManager()

if __name__ == "__main__":
    # Test the simple manager
    print("Testing simple git manager...")
    status = git_manager.status()
    print(f"Status: {status}")
    
    if status.get('output'):
        result = git_manager.commit_and_push("🔧 Simple git manager test")
        print(f"Commit result: {result}")
