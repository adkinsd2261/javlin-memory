
#!/usr/bin/env python3
"""
Pre-check script to analyze current git state before merge
"""

import subprocess
import os
import json

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def check_git_state():
    print("🔍 Git State Analysis")
    print("====================")
    
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
    return True

if __name__ == "__main__":
    check_git_state()
