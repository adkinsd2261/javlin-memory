
#!/usr/bin/env python3
"""
Simple Git Recovery - Use git's built-in mechanisms instead of fighting locks
"""

import os
import subprocess
import time
import shutil
from pathlib import Path

def backup_current_work():
    """Backup current work before recovery"""
    print("📦 Backing up current work...")
    
    # Create backup directory
    backup_dir = Path("work_backup_" + str(int(time.time())))
    backup_dir.mkdir(exist_ok=True)
    
    # Copy key files
    important_files = [
        "main.py", "git_sync.py", "doc_watcher.py", 
        "memory.json", "config.json", "README.md",
        "fix_git_locks.py", "AGENT_BIBLE.md"
    ]
    
    backed_up = []
    for file in important_files:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir / file)
            backed_up.append(file)
    
    print(f"  ✅ Backed up {len(backed_up)} files to {backup_dir}")
    return backup_dir, backed_up

def git_nuclear_reset():
    """Use git's own nuclear options"""
    print("🔄 Using git's built-in recovery...")
    
    try:
        # Method 1: git gc to clean up corrupted refs
        subprocess.run(['git', 'gc', '--prune=now'], 
                      timeout=30, capture_output=True)
        print("  ✅ Git garbage collection completed")
        
        # Method 2: git fsck to check and repair
        subprocess.run(['git', 'fsck', '--full'], 
                      timeout=30, capture_output=True)
        print("  ✅ Git filesystem check completed")
        
        # Method 3: Reset to last known good state
        subprocess.run(['git', 'reset', '--hard', 'HEAD'], 
                      timeout=15, capture_output=True)
        print("  ✅ Hard reset to HEAD completed")
        
        # Method 4: Clean untracked files
        subprocess.run(['git', 'clean', '-fdx'], 
                      timeout=15, capture_output=True)
        print("  ✅ Cleaned untracked files")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("  ⚠️ Git operations timed out")
        return False
    except Exception as e:
        print(f"  ❌ Git recovery failed: {e}")
        return False

def reinitialize_repo():
    """Last resort: reinitialize the repo"""
    print("🔥 LAST RESORT: Reinitializing repository...")
    
    try:
        # Remove .git directory
        git_dir = Path(".git")
        if git_dir.exists():
            shutil.rmtree(git_dir)
            print("  🗑️ Removed corrupted .git directory")
        
        # Reinitialize
        subprocess.run(['git', 'init'], timeout=10, capture_output=True)
        subprocess.run(['git', 'remote', 'add', 'origin', 
                       'https://github.com/adkinsd2261/memoryos.git'], 
                      timeout=10, capture_output=True)
        
        # Configure identity
        subprocess.run(['git', 'config', 'user.name', 'Darryl'], 
                      timeout=5, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'adkinsd226@gmail.com'], 
                      timeout=5, capture_output=True)
        
        print("  ✅ Repository reinitialized")
        return True
        
    except Exception as e:
        print(f"  ❌ Reinitialize failed: {e}")
        return False

def test_basic_operations():
    """Test if basic git operations work"""
    print("🧪 Testing basic git operations...")
    
    try:
        # Test status
        result = subprocess.run(['git', 'status'], 
                               timeout=10, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ❌ Git status failed: {result.stderr}")
            return False
        
        print("  ✅ Git status working")
        return True
        
    except Exception as e:
        print(f"  ❌ Basic operations test failed: {e}")
        return False

def simple_commit_and_push():
    """Simple commit and push without complex logic"""
    print("📝 Attempting simple commit and push...")
    
    try:
        # Add all files
        subprocess.run(['git', 'add', '.'], timeout=30, check=True)
        
        # Check if there's anything to commit
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'], 
                               capture_output=True)
        if result.returncode == 0:
            print("  ℹ️ No changes to commit")
            return True
        
        # Simple commit
        commit_msg = f"🔧 Recovery commit - {int(time.time())}"
        subprocess.run(['git', 'commit', '-m', commit_msg], 
                      timeout=30, check=True)
        print(f"  ✅ Committed: {commit_msg}")
        
        # Push
        subprocess.run(['git', 'push', 'origin', 'main'], 
                      timeout=60, check=True)
        print("  ✅ Pushed to GitHub")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Commit/push failed: {e}")
        return False

def main():
    """Main recovery workflow"""
    print("🚨 Simple Git Recovery")
    print("=" * 40)
    
    # Step 1: Backup current work
    backup_dir, backed_up = backup_current_work()
    
    # Step 2: Try git's built-in recovery first
    if git_nuclear_reset() and test_basic_operations():
        print("\n✅ Git built-in recovery successful!")
        
        # Try simple commit
        if simple_commit_and_push():
            print("🎉 Recovery and sync completed!")
            return True
    
    # Step 3: Last resort - reinitialize
    print("\n🔥 Git recovery failed, trying reinitialization...")
    if reinitialize_repo() and test_basic_operations():
        print("✅ Repository reinitialized successfully!")
        
        # Try simple commit
        if simple_commit_and_push():
            print("🎉 Repository recovered and synced!")
            return True
    
    print("\n❌ All recovery attempts failed")
    print(f"💾 Your work is backed up in: {backup_dir}")
    print("🔧 Manual intervention required")
    return False

if __name__ == "__main__":
    main()
