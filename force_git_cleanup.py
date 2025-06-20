
#!/usr/bin/env python3
"""
Force Git Lock Cleanup - Emergency Workaround
Run this manually when git locks are blocking your workflow
"""

import os
import glob
import subprocess

def force_cleanup_git_locks():
    """Forcibly remove all git lock files"""
    try:
        # Specific lock files we've seen in your environment
        specific_locks = [
            '.git/index.lock',
            '.git/config.lock', 
            '.git/gc.pid.lock',
            '.git/HEAD.lock'
        ]
        
        # General patterns for any other locks
        lock_patterns = [
            '.git/refs/heads/*.lock',
            '.git/*.lock',
            '.git/**/*.lock'
        ]
        
        removed_files = []
        
        # Remove specific locks first
        for lock_file in specific_locks:
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                    removed_files.append(lock_file)
                    print(f"✅ Removed: {lock_file}")
                except Exception as e:
                    print(f"❌ Failed to remove {lock_file}: {e}")
        
        # Remove pattern-based locks
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

if __name__ == "__main__":
    print("🔧 Force Git Lock Cleanup")
    print("=" * 40)
    
    # Force cleanup
    print("🧹 Force cleaning lock files...")
    result = force_cleanup_git_locks()
    
    print("\n✅ Cleanup complete!")
    print("Flask app should start successfully now.")
