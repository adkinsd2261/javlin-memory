
#!/usr/bin/env python3
"""
GitHub Sync Connection Test
Validates all components needed for GitHub sync
"""

import os
import json
import subprocess
import requests
import sys
from pathlib import Path

def test_git_config():
    """Test git configuration"""
    print("🔧 Testing Git Configuration...")
    
    try:
        # Check git user
        user_name = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True)
        user_email = subprocess.run(['git', 'config', 'user.email'], capture_output=True, text=True)
        
        print(f"  ✅ Git user: {user_name.stdout.strip()}")
        print(f"  ✅ Git email: {user_email.stdout.strip()}")
        
        # Check remote
        remote = subprocess.run(['git', 'remote', 'get-url', 'origin'], capture_output=True, text=True)
        if remote.returncode == 0:
            print(f"  ✅ Remote URL: {remote.stdout.strip()}")
        else:
            print("  ❌ No remote configured")
            return False
            
        return True
    except Exception as e:
        print(f"  ❌ Git config error: {e}")
        return False

def test_git_status():
    """Test git status and lock files"""
    print("\n📊 Testing Git Status...")
    
    try:
        # Check for lock files
        lock_files = ['.git/index.lock', '.git/refs/heads/main.lock']
        for lock_file in lock_files:
            if os.path.exists(lock_file):
                print(f"  ⚠️  Lock file exists: {lock_file}")
                os.remove(lock_file)
                print(f"  🧹 Removed: {lock_file}")
        
        # Check git status
        status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if status.stdout.strip():
            print(f"  📝 Changes detected: {len(status.stdout.strip().split())} files")
        else:
            print("  ✅ Working directory clean")
            
        return True
    except Exception as e:
        print(f"  ❌ Git status error: {e}")
        return False

def test_config_files():
    """Test configuration files"""
    print("\n⚙️  Testing Configuration Files...")
    
    config_files = {
        'config.json': 'Main configuration',
        'git_sync.py': 'Git sync module',
        'main.py': 'Flask application'
    }
    
    all_good = True
    for file_path, description in config_files.items():
        if os.path.exists(file_path):
            print(f"  ✅ {description}: {file_path}")
            
            # Validate JSON files
            if file_path.endswith('.json'):
                try:
                    with open(file_path, 'r') as f:
                        json.load(f)
                    print(f"    ✅ Valid JSON structure")
                except json.JSONDecodeError as e:
                    print(f"    ❌ Invalid JSON: {e}")
                    all_good = False
        else:
            print(f"  ❌ Missing: {file_path}")
            all_good = False
    
    return all_good

def test_flask_endpoints():
    """Test Flask endpoints"""
    print("\n🌐 Testing Flask Endpoints...")
    
    base_url = "http://127.0.0.1:5000"
    endpoints = [
        '/health',
        '/system-health', 
        '/memory',
        '/git-sync'
    ]
    
    all_good = True
    for endpoint in endpoints:
        try:
            if endpoint == '/git-sync':
                response = requests.post(f"{base_url}{endpoint}?force=true", timeout=5)
            else:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code < 500:
                print(f"  ✅ {endpoint}: {response.status_code}")
            else:
                print(f"  ❌ {endpoint}: {response.status_code}")
                all_good = False
        except requests.RequestException as e:
            print(f"  ❌ {endpoint}: Connection failed - {e}")
            all_good = False
    
    return all_good

def test_git_sync_module():
    """Test git sync module directly"""
    print("\n🔄 Testing Git Sync Module...")
    
    try:
        from git_sync import GitHubSyncer
        
        syncer = GitHubSyncer()
        print("  ✅ GitHubSyncer imported successfully")
        
        # Test configuration loading
        config = syncer.config
        print(f"  ✅ Config loaded: {config.get('git_sync', {}).get('enabled', False)}")
        
        # Test status check
        has_changes = syncer.check_git_status()
        print(f"  📊 Has changes to commit: {has_changes}")
        
        return True
    except Exception as e:
        print(f"  ❌ Git sync module error: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 GitHub Sync Deep Audit\n")
    
    tests = [
        test_git_config,
        test_git_status,
        test_config_files,
        test_flask_endpoints,
        test_git_sync_module
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*50)
    print("📋 Test Summary:")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! GitHub sync should work correctly.")
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
