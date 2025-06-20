
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
    """Check if any actual git processes are currently running, excluding harmless processes"""
    git_processes = []
    current_pid = os.getpid()
    current_script_name = os.path.basename(__file__)
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip current process and parent processes
            if proc.info['pid'] == current_pid:
                continue
                
            # Only flag actual git binary processes, not scripts
            if proc.info['name'] and proc.info['name'].lower() == 'git':
                # Exclude git processes that are just doing safe read operations
                cmdline_str = ' '.join(proc.info.get('cmdline', []))
                safe_git_ops = ['git status', 'git log', 'git show', 'git diff', 'git rev-parse', 'git branch']
                
                if not any(safe_op in cmdline_str for safe_op in safe_git_ops):
                    git_processes.append(proc.info)
            elif proc.info['cmdline'] and len(proc.info['cmdline']) > 0:
                # Only flag if it's actually the git binary (not python scripts using git)
                first_cmd = proc.info['cmdline'][0]
                if (first_cmd == 'git' or first_cmd.endswith('/git')) and 'python' not in first_cmd:
                    # Exclude safe operations
                    cmdline_str = ' '.join(proc.info['cmdline'])
                    safe_git_ops = ['git status', 'git log', 'git show', 'git diff', 'git rev-parse', 'git branch']
                    
                    if not any(safe_op in cmdline_str for safe_op in safe_git_ops):
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
        '.git/refs/heads/master.lock',
        '.git/refs/remotes/origin/main.lock'
    ]
    
    found_locks = []
    for lock_file in lock_files:
        if os.path.exists(lock_file):
            found_locks.append(lock_file)
    
    if not found_locks:
        print("✅ No git lock files found")
        return True
    
    print(f"⚠️  Found {len(found_locks)} git lock file(s): {found_locks}")
    
    # Check lock file ages - if very old, likely stale
    stale_locks = []
    for lock_file in found_locks:
        if os.path.exists(lock_file):
            file_age = time.time() - os.path.getmtime(lock_file)
            if file_age > 300:  # 5 minutes
                stale_locks.append(lock_file)
                print(f"   Detected stale lock: {lock_file} (age: {file_age:.1f} seconds)")
    
    # Check for active git processes
    git_processes = check_git_processes()
    
    # If we have stale locks and no harmful git processes, auto-cleanup
    if stale_locks and not git_processes:
        print("✅ Stale locks detected with no active git processes - auto-cleaning")
        force_override = True
    
    if git_processes and not force_override:
        print("❌ Active git processes detected:")
        for proc in git_processes:
            print(f"   PID {proc['pid']}: {proc['name']} - {proc['cmdline']}")
        print("   Cannot safely remove locks while git is running")
        print("   Use --force-override if you're certain no git operations are active")
        print("   Or use --replit-safe for Replit environment cleanup")
        return False
    elif git_processes and force_override:
        print("⚠️  Force override enabled - removing locks despite active processes:")
        for proc in git_processes:
            print(f"   PID {proc['pid']}: {proc['name']} - {proc['cmdline']}")
    else:
        print("✅ No active git processes found - safe to remove locks")
    
    # Remove lock files with enhanced error handling
    removed_count = 0
    for lock_file in found_locks:
        try:
            if os.path.exists(lock_file):
                file_age = time.time() - os.path.getmtime(lock_file)
                print(f"   Removing {lock_file} (age: {file_age:.1f} seconds)")
                
                # Try to remove with proper permissions
                os.chmod(lock_file, 0o666)
                os.remove(lock_file)
                removed_count += 1
        except PermissionError:
            print(f"   ⚠️  Permission denied for {lock_file} - trying alternative method")
            try:
                # Alternative removal method for Replit
                subprocess.run(['rm', '-f', lock_file], check=True)
                removed_count += 1
                print(f"   ✅ Removed {lock_file} via rm command")
            except Exception as e:
                print(f"   ❌ Failed to remove {lock_file}: {e}")
                return False
        except Exception as e:
            print(f"   ❌ Failed to remove {lock_file}: {e}")
            return False
    
    print(f"✅ Successfully removed {removed_count} git lock file(s)")
    
    # Wait for filesystem sync
    time.sleep(1.0)
    
    # Verify locks are gone
    remaining_locks = [f for f in lock_files if os.path.exists(f)]
    if remaining_locks:
        print(f"⚠️  {len(remaining_locks)} lock file(s) still remain: {remaining_locks}")
        return False
    
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
    replit_safe = "--replit-safe" in sys.argv
    manual_cleanup = "--manual-cleanup" in sys.argv
    
    if force_override:
        print("⚠️  Force override mode enabled")
    if replit_safe:
        print("🔧 Replit-safe mode enabled - enhanced cleanup for Replit environment")
        force_override = True
    
    # Manual cleanup mode
    if manual_cleanup:
        print("🧹 Manual cleanup mode - removing all git locks")
        success = safe_cleanup_git_locks(force_override=True)
        if success:
            print("✅ Manual cleanup completed successfully!")
        else:
            print("❌ Manual cleanup failed!")
        sys.exit(0 if success else 1)
    
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
        print("\n🔧 Try these options:")
        print("   python3 check_git_state.py --replit-safe")
        print("   python3 check_git_state.py --manual-cleanup")
        print("   python3 check_git_state.py --force-override")
        sys.exit(1)
