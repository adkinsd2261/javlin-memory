
#!/usr/bin/env python3
"""
Force Git Lock Cleanup - Emergency Workaround
Run this manually when git locks are blocking your workflow
"""

import os
import glob
import subprocess
import time

def force_cleanup_git_locks():
    """Forcibly remove all git lock files"""
    try:
        # Find all git lock files
        lock_patterns = [
            '.git/index.lock',
            '.git/config.lock', 
            '.git/HEAD.lock',
            '.git/refs/heads/*.lock',
            '.git/*.lock',
            '.git/**/*.lock'
        ]
        
        removed_files = []
        
        for pattern in lock_patterns:
            lock_files = glob.glob(pattern, recursive=True)
            for lock_file in lock_files:
                if os.path.exists(lock_file):
                    try:
                        os.remove(lock_file)
                        removed_files.append(lock_file)
                        print(f"✅ Removed: {lock_file}")
                    except Exception as e:
                        print(f"❌ Failed to remove {lock_file}: {e}")
        
        if removed_files:
            print(f"\n🧹 Cleaned up {len(removed_files)} lock files")
        else:
            print("✨ No lock files found")
            
        return {"success": True, "removed_files": removed_files}
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return {"success": False, "error": str(e)}

def check_git_processes():
    """Check for any running git processes"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        git_processes = [line for line in result.stdout.split('\n') if 'git' in line.lower() and 'grep' not in line]
        
        if git_processes:
            print("⚠️  Found git processes:")
            for proc in git_processes:
                print(f"  {proc}")
        else:
            print("✅ No git processes running")
            
        return git_processes
        
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        return []

if __name__ == "__main__":
    print("🔧 Force Git Lock Cleanup")
    print("=" * 40)
    
    # Check processes first
    git_procs = check_git_processes()
    
    # Force cleanup regardless
    print("\n🧹 Force cleaning lock files...")
    result = force_cleanup_git_locks()
    
    print("\n✅ Cleanup complete!")
    print("You can now try starting your Flask app again.")
