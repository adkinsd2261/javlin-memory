
#!/usr/bin/env python3
"""
Ultra-Simple Git Manager
One function: commit and push. No locks, no complexity, no death loops.
"""

import subprocess
import os
from datetime import datetime

class GitManager:
    def __init__(self):
        self.repo_dir = os.path.dirname(os.path.abspath(__file__))
        
    def commit_and_push(self, message="Auto commit"):
        """Ultra-simple: add, commit, push. That's it."""
        try:
            # Step 1: Add everything
            result = subprocess.run(['git', 'add', '.'], 
                                  cwd=self.repo_dir, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30)
            
            # Step 2: Check if there's anything to commit
            status = subprocess.run(['git', 'status', '--porcelain'], 
                                  cwd=self.repo_dir,
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            if not status.stdout.strip():
                return {"status": "success", "message": "No changes to commit"}
            
            # Step 3: Commit
            subprocess.run(['git', 'commit', '-m', message], 
                         cwd=self.repo_dir,
                         check=True, 
                         timeout=30)
            
            # Step 4: Push
            subprocess.run(['git', 'push', 'origin', 'main'], 
                         cwd=self.repo_dir,
                         check=True, 
                         timeout=60)
            
            return {"status": "success", "message": "Successfully committed and pushed"}
            
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Git operation timed out"}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "error": f"Git command failed: {e.stderr if e.stderr else str(e)}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Single global instance
git_manager = GitManager()

if __name__ == "__main__":
    result = git_manager.commit_and_push("🧹 Clean git manager rebuild")
    print(f"Result: {result}")
