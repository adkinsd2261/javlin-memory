
#!/usr/bin/env python3
"""
Clean Git Manager - Single source of truth for git operations
No competing systems, no death loops, just simple git operations
"""

import os
import subprocess
import time
import json
from datetime import datetime

class GitManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
    def status(self):
        """Check git status"""
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, timeout=10)
            return {"status": "success", "changes": result.stdout.strip()}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def commit_and_push(self, message="Auto commit"):
        """Simple commit and push - no lock fighting"""
        try:
            # Check for changes
            status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                         capture_output=True, text=True, timeout=10)
            if not status_result.stdout.strip():
                return {"status": "success", "message": "No changes to commit"}
            
            # Add all changes
            subprocess.run(['git', 'add', '.'], check=True, timeout=30)
            
            # Commit
            subprocess.run(['git', 'commit', '-m', message], check=True, timeout=30)
            
            # Push
            subprocess.run(['git', 'push', 'origin', 'main'], check=True, timeout=60)
            
            return {"status": "success", "message": "Committed and pushed successfully"}
            
        except subprocess.CalledProcessError as e:
            return {"status": "error", "error": f"Git command failed: {e}"}
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Git operation timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Global instance
git_manager = GitManager()

if __name__ == "__main__":
    print("Testing git manager...")
    status = git_manager.status()
    print(f"Status: {status}")
    
    if status.get('changes'):
        result = git_manager.commit_and_push("🔧 Fresh start with clean git manager")
        print(f"Commit result: {result}")
