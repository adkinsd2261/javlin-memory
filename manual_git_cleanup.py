
#!/usr/bin/env python3
"""
Manual Git Lock Cleanup for Replit
Quick workaround for persistent git lock issues
"""

import os
import subprocess
import time

def force_cleanup_git_locks():
    """Force cleanup of all git lock files"""
    print("🧹 Force cleaning all git lock files...")
    
    lock_patterns = [
        '.git/*.lock',
        '.git/refs/heads/*.lock', 
        '.git/refs/remotes/origin/*.lock'
    ]
    
    cleaned = 0
    
    # Method 1: Direct file removal
    lock_files = [
        '.git/index.lock',
        '.git/HEAD.lock',
        '.git/config.lock',
        '.git/refs/heads/main.lock',
        '.git/refs/heads/master.lock',
        '.git/refs/remotes/origin/main.lock'
    ]
    
    for lock_file in lock_files:
        if os.path.exists(lock_file):
            try:
                print(f"   Removing {lock_file}")
                os.chmod(lock_file, 0o666)
                os.remove(lock_file)
                cleaned += 1
            except Exception as e:
                print(f"   Direct removal failed: {e}")
                try:
                    subprocess.run(['rm', '-f', lock_file], check=True)
                    print(f"   ✅ Removed via rm: {lock_file}")
                    cleaned += 1
                except Exception as e2:
                    print(f"   ❌ All methods failed for {lock_file}: {e2}")
    
    # Method 2: Shell command cleanup
    try:
        result = subprocess.run(['find', '.git', '-name', '*.lock', '-delete'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ find command cleanup successful")
        else:
            print(f"   find command output: {result.stderr}")
    except Exception as e:
        print(f"   find command failed: {e}")
    
    print(f"✅ Cleanup completed - {cleaned} files removed")
    
    # Wait and verify
    time.sleep(1)
    
    remaining = [f for f in lock_files if os.path.exists(f)]
    if remaining:
        print(f"⚠️  {len(remaining)} lock files still remain: {remaining}")
        return False
    else:
        print("✅ All lock files successfully removed")
        return True

def reset_git_state():
    """Reset git to a clean state"""
    print("🔄 Resetting git to clean state...")
    
    commands = [
        "git reset --hard",
        "git clean -fd", 
        "git status"
    ]
    
    for cmd in commands:
        try:
            print(f"   Running: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {cmd} successful")
                if result.stdout.strip():
                    print(f"      {result.stdout.strip()}")
            else:
                print(f"   ⚠️  {cmd} returned code {result.returncode}")
                if result.stderr.strip():
                    print(f"      {result.stderr.strip()}")
        except Exception as e:
            print(f"   ❌ {cmd} failed: {e}")

if __name__ == "__main__":
    import sys
    
    print("🔧 Manual Git Cleanup Tool for Replit")
    print("=" * 40)
    
    if "--reset" in sys.argv:
        reset_git_state()
    
    success = force_cleanup_git_locks()
    
    if success:
        print("\n✅ Ready to proceed with git operations")
        print("You can now run:")
        print("   python3 check_git_state.py")
        print("   python3 auto_merge_prep.py")
    else:
        print("\n❌ Some lock files could not be removed")
        print("You may need to:")
        print("   1. Check for running git processes: ps aux | grep git")
        print("   2. Kill any hung git processes")
        print("   3. Restart your Replit workspace")
