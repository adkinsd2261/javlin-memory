"""
Simple System Check - Alternative to fix_system_issues.py
Minimal system checker that avoids problematic imports
"""

import os
import json
from datetime import datetime

def check_memory_file():
    """Check and fix memory.json issues"""
    print("🔍 Checking memory.json file...")
    
    if not os.path.exists('memory.json'):
        print("📝 Creating memory.json file...")
        with open('memory.json', 'w') as f:
            json.dump([], f)
        print("✅ Created memory.json")
        return True
    
    try:
        with open('memory.json', 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("🔧 Fixing corrupted memory.json...")
            backup_name = f"memory_corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.rename('memory.json', backup_name)
            
            with open('memory.json', 'w') as f:
                json.dump([], f)
            
            print(f"✅ Fixed corrupted memory.json (backup: {backup_name})")
            return True
        
        print(f"✅ memory.json is valid with {len(data)} entries")
        return True
        
    except json.JSONDecodeError:
        print("🔧 Fixing corrupted JSON...")
        backup_name = f"memory_corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.rename('memory.json', backup_name)
        
        with open('memory.json', 'w') as f:
            json.dump([], f)
        
        print(f"✅ Fixed corrupted JSON (backup: {backup_name})")
        return True

def check_logs_directory():
    """Ensure logs directory exists"""
    print("🔍 Checking logs directory...")
    
    if not os.path.exists('logs'):
        print("📁 Creating logs directory...")
        os.makedirs('logs', exist_ok=True)
        print("✅ Created logs directory")
    else:
        print("✅ Logs directory exists")
    
    return True

def main():
    print("🔧 Simple System Check Starting...")
    print("=" * 40)
    
    checks = [
        ("Memory File", check_memory_file),
        ("Logs Directory", check_logs_directory),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
            all_passed = False
    
    print("=" * 40)
    if all_passed:
        print("🎉 Basic system checks passed!")
        print("\n🚀 Ready to start:")
        print("   Backend: python main.py")
        print("   Frontend: npm run dev")
    else:
        print("⚠️ Some issues found - please check manually")

if __name__ == "__main__":
    main()