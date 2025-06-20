
#!/usr/bin/env python3
"""
Pre-check script to analyze current git state before merge
"""

import subprocess
import os
import json
import time
import psutil

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def check_git_processes():
    """Check if any git processes are currently running, excluding self"""
    git_processes = []
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip current process
            if proc.info['pid'] == current_pid:
                continue
                
            # Check for actual git processes (not just scripts checking git)
            if proc.info['name'] and proc.info['name'].lower() == 'git':
                git_processes.append(proc.info)
            elif proc.info['cmdline'] and len(proc.info['cmdline']) > 0:
                # Only flag if the first command is git (not python scripts)
                if proc.info['cmdline'][0].endswith('git') or proc.info['cmdline'][0] == 'git':
                    git_processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return git_processes

def safe_cleanup_git_locks(force_override=False):
    """Safely clean up git lock files if no git processes are running"""
    print("🔒 Checking for git lock files...")
    
    lock_files = [
        '.git/index.lock',
        '.git/HEAD.lock', 
        '.git/config.lock',
        '.git/refs/heads/main.lock',
        '.git/refs/heads/master.lock'
    ]
    
    found_locks = []
    for lock_file in lock_files:
        if os.path.exists(lock_file):
            found_locks.append(lock_file)
    
    if not found_locks:
        print("✅ No git lock files found")
        return True
    
    print(f"⚠️  Found {len(found_locks)} git lock file(s): {found_locks}")
    
    # Check for active git processes
    git_processes = check_git_processes()
    if git_processes and not force_override:
        print("❌ Active git processes detected:")
        for proc in git_processes:
            print(f"   PID {proc['pid']}: {proc['name']} - {proc['cmdline']}")
        print("   Cannot safely remove locks while git is running")
        print("   Use --force-override if you're certain no git operations are active")
        return False
    elif git_processes and force_override:
        print("⚠️  Force override enabled - removing locks despite active processes:")
        for proc in git_processes:
            print(f"   PID {proc['pid']}: {proc['name']} - {proc['cmdline']}")
    else:
        print("✅ No active git processes found - safe to remove locks")
    
    # Remove lock files
    removed_count = 0
    for lock_file in found_locks:
        try:
            # Double-check file still exists and get its age
            if os.path.exists(lock_file):
                file_age = time.time() - os.path.getmtime(lock_file)
                print(f"   Removing {lock_file} (age: {file_age:.1f} seconds)")
                os.remove(lock_file)
                removed_count += 1
        except Exception as e:
            print(f"   ❌ Failed to remove {lock_file}: {e}")
            return False
    
    print(f"✅ Successfully removed {removed_count} git lock file(s)")
    
    # Wait a moment for filesystem to sync
    time.sleep(0.5)
    
    return True

def check_git_state(force_override=False, auto_proceed=False):
    print("🔍 Git State Analysis")
    print("====================")
    
    # First, clean up any stale git locks
    if not safe_cleanup_git_locks(force_override):
        print("❌ Could not safely clean up git locks")
        return False
    
    # Check if we're in a git repo
    stdout, stderr, code = run_command("git rev-parse --is-inside-work-tree")
    if code != 0:
        print("❌ Not in a git repository")
        return False
    
    print("✅ In git repository")
    
    # Check current branch
    stdout, stderr, code = run_command("git branch --show-current")
    print(f"📌 Current branch: {stdout}")
    
    # Check remote
    stdout, stderr, code = run_command("git remote get-url origin")
    if code == 0:
        print(f"🌐 Remote URL: {stdout}")
    else:
        print("⚠️  No remote origin configured")
    
    # Check status
    stdout, stderr, code = run_command("git status --porcelain")
    if stdout:
        status_lines = stdout.split('\n')
        print(f"📝 Uncommitted changes: {len(status_lines)} files")
        print("   Files:")
        for line in status_lines[:5]:  # Show first 5
            print(f"   - {line}")
        if len(status_lines) > 5:
            print(f"   ... and {len(status_lines) - 5} more")
    else:
        print("✅ Working directory clean")
    
    # Check local files
    local_files = []
    for item in os.listdir('.'):
        if item != '.git':
            local_files.append(item)
    
    print(f"📁 Local files ({len(local_files)}):")
    
    # Key MemoryOS files
    memoryos_files = ['main.py', 'memory.json', 'AGENT_BIBLE.md', 'compliance_middleware.py']
    found_memoryos = []
    for f in memoryos_files:
        if f in local_files:
            found_memoryos.append(f)
    
    if found_memoryos:
        print(f"   MemoryOS files found: {found_memoryos}")
    
    # Check for potential Javlin files
    javlin_indicators = ['core', 'docs', 'examples']
    found_javlin = []
    for f in javlin_indicators:
        if f in local_files:
            found_javlin.append(f)
    
    if found_javlin:
        print(f"   Javlin files found: {found_javlin}")
    else:
        print("   No Javlin files detected locally")
    
    # Check git log
    stdout, stderr, code = run_command("git log --oneline -5")
    if code == 0:
        print(f"📚 Recent commits:")
        log_lines = stdout.split('\n')
        for line in log_lines[:3]:
            print(f"   {line}")
    
    # Check for divergence
    stdout, stderr, code = run_command("git fetch origin main && git rev-list --count HEAD..origin/main")
    if code == 0 and stdout.isdigit():
        remote_commits = int(stdout)
        if remote_commits > 0:
            print(f"⚠️  Remote is {remote_commits} commits ahead")
    
    stdout, stderr, code = run_command("git rev-list --count origin/main..HEAD")
    if code == 0 and stdout.isdigit():
        local_commits = int(stdout)
        if local_commits > 0:
            print(f"⚠️  Local is {local_commits} commits ahead")
    
    print("\n🔄 Ready for merge operation")
    
    # Final safety check and summary
    final_git_processes = check_git_processes()
    final_locks = [f for f in ['.git/index.lock', '.git/HEAD.lock', '.git/config.lock', 
                              '.git/refs/heads/main.lock', '.git/refs/heads/master.lock'] 
                   if os.path.exists(f)]
    
    print("\n" + "="*50)
    print("🛡️  FINAL SAFETY SUMMARY")
    print("="*50)
    
    if not final_git_processes and not final_locks:
        print("✅ SAFE TO CONTINUE")
        print("   ▶ No active git processes detected")
        print("   ▶ No git lock files present") 
        print("   ▶ Repository is ready for merge operations")
        
        if auto_proceed:
            print("\n🚀 Auto-proceeding to merge...")
            return "auto_proceed"
        else:
            print("\n💡 Run with --auto-proceed to automatically start merge")
        
        return True
    else:
        print("⚠️  PROCEED WITH CAUTION")
        if final_git_processes:
            print(f"   ▶ {len(final_git_processes)} git process(es) still active")
        if final_locks:
            print(f"   ▶ {len(final_locks)} lock file(s) still present")
        print("   ▶ Manual intervention may be required")
        return False

if __name__ == "__main__":
    import sys
    
    force_override = "--force-override" in sys.argv
    auto_proceed = "--auto-proceed" in sys.argv
    
    if force_override:
        print("⚠️  Force override mode enabled")
    
    result = check_git_state(force_override, auto_proceed)
    
    if result == "auto_proceed":
        print("Starting automated merge workflow...")
        try:
            import subprocess
            subprocess.run(["python3", "git_merge_divergent.py"], check=True)
        except Exception as e:
            print(f"❌ Failed to start merge workflow: {e}")
            sys.exit(1)
    elif result:
        print("\n✅ Pre-check completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Pre-check failed!")
        sys.exit(1)
