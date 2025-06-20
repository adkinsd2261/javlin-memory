
#!/usr/bin/env python3
"""
Automated Git Merge Preparation Script
Safely prepares workspace for merge operations by:
1. Cleaning git locks
2. Verifying safety conditions
3. Optionally launching merge workflow
"""

import sys
import subprocess
import os

def main():
    print("🤖 Automated Git Merge Preparation")
    print("="*50)
    
    # Parse arguments
    force_override = "--force-override" in sys.argv
    auto_merge = "--auto-merge" in sys.argv
    
    if force_override:
        print("⚠️  Force override mode enabled")
    
    # Step 1: Run pre-check with appropriate flags
    cmd = ["python3", "check_git_state.py"]
    if force_override:
        cmd.append("--force-override")
    if auto_merge:
        cmd.append("--auto-proceed")
    
    print("🔍 Running git state pre-check...")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        
        if not auto_merge:
            print("\n" + "="*50)
            print("✅ PREPARATION COMPLETE")
            print("="*50)
            print("Your workspace is now ready for merge operations.")
            print("\nNext steps:")
            print("1. Run: python3 git_merge_divergent.py")
            print("2. Or use: python3 auto_merge_prep.py --auto-merge")
            print("\nFor risky situations, use --force-override")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Pre-check failed with exit code {e.returncode}")
        print("\nTroubleshooting:")
        print("- Check for running git processes")
        print("- Manually remove stale lock files if safe")
        print("- Use --force-override if you're certain it's safe")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("Usage: python3 auto_merge_prep.py [options]")
        print("\nOptions:")
        print("  --force-override    Remove locks even if processes detected")
        print("  --auto-merge        Automatically start merge after prep")
        print("  -h, --help          Show this help")
        sys.exit(0)
    
    main()
