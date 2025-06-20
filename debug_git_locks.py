
#!/usr/bin/env python3
"""
Debug Git Lock Issues
Helps diagnose persistent git lock problems
"""

import os
import subprocess
import glob
import json
import time
from datetime import datetime

def check_git_processes():
    """Check for running git processes"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        git_processes = [line for line in result.stdout.split('\n') if 'git' in line.lower() and 'grep' not in line]
        return git_processes
    except:
        return []

def check_lock_files():
    """Check for all git lock files"""
    lock_files = []
    patterns = [
        '.git/*.lock',
        '.git/**/*.lock',
        '.git/refs/**/*.lock'
    ]
    
    for pattern in patterns:
        lock_files.extend(glob.glob(pattern, recursive=True))
    
    return lock_files

def check_git_status():
    """Check git repository status"""
    try:
        # Basic status
        status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        
        # Check if repo is in a weird state
        branch = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True)
        
        # Check for merge conflicts
        conflicts = subprocess.run(['git', 'diff', '--name-only', '--diff-filter=U'], capture_output=True, text=True)
        
        return {
            'status': status.stdout.strip(),
            'branch': branch.stdout.strip(),
            'conflicts': conflicts.stdout.strip(),
            'return_codes': {
                'status': status.returncode,
                'branch': branch.returncode,
                'conflicts': conflicts.returncode
            }
        }
    except Exception as e:
        return {'error': str(e)}

def force_clear_everything():
    """Nuclear option - clear everything"""
    print("🧨 NUCLEAR OPTION: Clearing all git locks and processes...")
    
    # Kill processes
    os.system("pkill -9 -f git 2>/dev/null || true")
    os.system("pkill -9 git 2>/dev/null || true") 
    os.system("killall -9 git 2>/dev/null || true")
    
    time.sleep(3)
    
    # Remove all lock files
    os.system("find .git -name '*.lock' -type f -delete 2>/dev/null || true")
    os.system("find . -name '*.lock' -path '*/.git/*' -delete 2>/dev/null || true")
    
    # Reset git state
    os.system("git reset --hard HEAD 2>/dev/null || true")
    
    print("✅ Nuclear clear completed")

def main():
    print("🔍 Git Lock Debugging Tool")
    print("=" * 40)
    
    # Check processes
    print("\n📊 Git Processes:")
    processes = check_git_processes()
    if processes:
        for proc in processes:
            print(f"  {proc}")
    else:
        print("  ✅ No git processes found")
    
    # Check lock files
    print("\n🔒 Lock Files:")
    locks = check_lock_files()
    if locks:
        for lock in locks:
            print(f"  📝 {lock}")
    else:
        print("  ✅ No lock files found")
    
    # Check git status
    print("\n📋 Git Status:")
    git_info = check_git_status()
    for key, value in git_info.items():
        print(f"  {key}: {value}")
    
    # Save debug info
    debug_info = {
        'timestamp': datetime.now().isoformat(),
        'processes': processes,
        'lock_files': locks,
        'git_status': git_info
    }
    
    with open('git_debug.json', 'w') as f:
        json.dump(debug_info, f, indent=2)
    
    print(f"\n💾 Debug info saved to git_debug.json")
    
    # Ask if user wants nuclear option
    if locks or processes:
        response = input("\n🧨 Found issues. Run nuclear clear? (y/N): ")
        if response.lower() == 'y':
            force_clear_everything()

if __name__ == "__main__":
    main()
