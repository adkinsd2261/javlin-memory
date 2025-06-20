
#!/usr/bin/env python3
"""
Comprehensive Git Lock Fix
Addresses persistent INDEX_LOCKED issues with multiple strategies
"""

import os
import subprocess
import time
import glob
import signal
import psutil
from pathlib import Path

def kill_all_git_processes():
    """Kill all git processes using multiple methods"""
    print("🔥 Killing all git processes...")
    
    # Method 1: psutil (most reliable)
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'git' in proc.info['name'].lower():
                proc.kill()
                killed_count += 1
                print(f"  Killed git process: {proc.info['pid']}")
            elif proc.info['cmdline']:
                for cmd_part in proc.info['cmdline']:
                    if 'git' in str(cmd_part).lower():
                        proc.kill() 
                        killed_count += 1
                        print(f"  Killed git process: {proc.info['pid']}")
                        break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    print(f"  Killed {killed_count} git processes")
    time.sleep(3)  # Wait for processes to die

def remove_all_lock_files():
    """Remove all possible git lock files"""
    print("🔒 Removing all git lock files...")
    
    lock_patterns = [
        '.git/**/*.lock',
        '.git/*.lock', 
        '.git/refs/**/*.lock',
        '.git/objects/**/*.lock'
    ]
    
    removed_count = 0
    for pattern in lock_patterns:
        for lock_file in glob.glob(pattern, recursive=True):
            try:
                os.remove(lock_file)
                print(f"  Removed: {lock_file}")
                removed_count += 1
            except Exception as e:
                print(f"  Failed to remove {lock_file}: {e}")
    
    # Specific common lock files
    specific_locks = [
        '.git/index.lock',
        '.git/refs/heads/main.lock', 
        '.git/HEAD.lock',
        '.git/config.lock',
        '.git/COMMIT_EDITMSG.lock',
        '.git/refs/remotes/origin/main.lock'
    ]
    
    for lock_file in specific_locks:
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                print(f"  Removed: {lock_file}")
                removed_count += 1
            except Exception as e:
                print(f"  Failed to remove {lock_file}: {e}")
    
    print(f"  Removed {removed_count} lock files")

def reset_git_state():
    """Reset git to a clean state"""
    print("🔄 Resetting git state...")
    
    try:
        # Reset any ongoing operations
        subprocess.run(['git', 'reset', '--hard', 'HEAD'], 
                      capture_output=True, timeout=10)
        print("  Git reset completed")
        
        # Clean untracked files
        subprocess.run(['git', 'clean', '-fd'], 
                      capture_output=True, timeout=10)
        print("  Cleaned untracked files")
        
        # Abort any ongoing merge/rebase
        subprocess.run(['git', 'merge', '--abort'], 
                      capture_output=True, timeout=5)
        subprocess.run(['git', 'rebase', '--abort'], 
                      capture_output=True, timeout=5)
        
    except subprocess.TimeoutExpired:
        print("  ⚠️ Git reset timed out")
    except Exception as e:
        print(f"  ⚠️ Git reset failed: {e}")

def configure_git():
    """Configure git identity"""
    print("⚙️ Configuring git identity...")
    
    try:
        subprocess.run(['git', 'config', 'user.name', 'Darryl'], 
                      timeout=5, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'adkinsd226@gmail.com'], 
                      timeout=5, capture_output=True)
        print("  Git identity configured")
    except Exception as e:
        print(f"  ⚠️ Git config failed: {e}")

def test_git_operations():
    """Test basic git operations"""
    print("🧪 Testing git operations...")
    
    try:
        # Test status
        result = subprocess.run(['git', 'status', '--porcelain'], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("  ✅ Git status working")
            if result.stdout.strip():
                print(f"    Changes detected: {len(result.stdout.strip().split())} files")
            else:
                print("    No changes detected")
        else:
            print(f"  ❌ Git status failed: {result.stderr}")
            return False
            
        # Test add (dry run)
        result = subprocess.run(['git', 'add', '--dry-run', '.'], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("  ✅ Git add test working")
        else:
            print(f"  ❌ Git add test failed: {result.stderr}")
            return False
            
        return True
        
    except subprocess.TimeoutExpired:
        print("  ❌ Git operations timed out")
        return False
    except Exception as e:
        print(f"  ❌ Git test failed: {e}")
        return False

def main():
    """Run comprehensive git lock fix"""
    print("🚀 Starting comprehensive git lock fix...")
    print("=" * 50)
    
    # Step 1: Kill all git processes
    kill_all_git_processes()
    
    # Step 2: Remove all lock files
    remove_all_lock_files()
    
    # Step 3: Reset git state
    reset_git_state()
    
    # Step 4: Configure git
    configure_git()
    
    # Step 5: Test git operations
    success = test_git_operations()
    
    print("=" * 50)
    if success:
        print("✅ Git lock fix completed successfully!")
        print("🚀 Ready to push to GitHub")
    else:
        print("❌ Git operations still failing")
        print("🔧 Manual intervention may be required")
    
    return success

if __name__ == "__main__":
    main()
