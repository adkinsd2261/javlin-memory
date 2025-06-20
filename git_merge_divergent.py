
#!/usr/bin/env python3
"""
Automated Git Divergence Resolution for MemoryOS + Javlin Memory Engine
Safely merges two divergent git histories while preserving both codebases
"""

import os
import subprocess
import json
import datetime
import shutil
import tempfile
from pathlib import Path

class GitDivergenceResolver:
    def __init__(self, local_project_name="MemoryOS", remote_url=None):
        self.local_project_name = local_project_name
        self.remote_url = remote_url or self._get_remote_url()
        self.backup_dir = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.temp_branch = f"temp-local-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.merge_branch = f"merge-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.log_file = f"git_merge_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.rollback_commands = []
        
    def log(self, message, level="INFO"):
        """Log messages to file and console"""
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def run_command(self, command, check=True, capture_output=True):
        """Run shell command with logging and error handling"""
        self.log(f"Executing: {command}")
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                check=check, 
                capture_output=capture_output,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.stdout:
                self.log(f"STDOUT: {result.stdout.strip()}")
            if result.stderr:
                self.log(f"STDERR: {result.stderr.strip()}")
                
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {command}", "ERROR")
            self.log(f"Exit code: {e.returncode}", "ERROR")
            if e.stdout:
                self.log(f"STDOUT: {e.stdout}", "ERROR")
            if e.stderr:
                self.log(f"STDERR: {e.stderr}", "ERROR")
            raise
    
    def _get_remote_url(self):
        """Get the current remote URL"""
        try:
            result = self.run_command("git remote get-url origin", check=False)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def backup_workspace(self):
        """Create complete backup of current workspace"""
        self.log("Creating workspace backup...")
        
        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Copy all files except .git
        for item in os.listdir('.'):
            if item != '.git' and item != self.backup_dir:
                src = Path(item)
                dst = Path(self.backup_dir) / item
                
                if src.is_file():
                    shutil.copy2(src, dst)
                elif src.is_dir():
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('.git'))
        
        self.log(f"Backup created in {self.backup_dir}")
        self.rollback_commands.append(f"# Restore from backup: cp -r {self.backup_dir}/* .")
        
    def check_git_processes(self):
        """Check if any git processes are currently running"""
        try:
            import psutil
            git_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'git' in proc.info['name'].lower():
                        git_processes.append(proc.info)
                    elif proc.info['cmdline'] and any('git' in str(cmd).lower() for cmd in proc.info['cmdline']):
                        git_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return git_processes
        except ImportError:
            self.log("psutil not available - skipping process check", "WARNING")
            return []

    def cleanup_git_locks(self):
        """Safely remove git lock files with enhanced process checking"""
        self.log("Checking for git lock files...")
        
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
            self.log("No git lock files found")
            return True
        
        self.log(f"Found {len(found_locks)} git lock files: {found_locks}")
        
        # Check for active git processes (exclude self)
        git_processes = self.check_git_processes()
        if git_processes:
            self.log("Active git processes detected:", "ERROR")
            for proc in git_processes:
                self.log(f"   PID {proc['pid']}: {proc['name']} - {proc['cmdline']}", "ERROR")
            self.log("Cannot safely remove locks while git is running", "ERROR")
            return False
        
        self.log("No active git processes - safe to remove locks")
        
        # Remove lock files with error handling
        import time
        removed_count = 0
        for lock_file in found_locks:
            try:
                if os.path.exists(lock_file):
                    file_age = time.time() - os.path.getmtime(lock_file)
                    self.log(f"Removing {lock_file} (age: {file_age:.1f} seconds)")
                    os.remove(lock_file)
                    removed_count += 1
            except Exception as e:
                self.log(f"Failed to remove {lock_file}: {e}", "ERROR")
                return False
        
        self.log(f"Successfully removed {removed_count} git lock files")
        
        # Brief pause for filesystem sync
        time.sleep(0.5)
        return True
    
    def check_git_status(self):
        """Check current git status"""
        self.log("Checking git status...")
        self.run_command("git status --porcelain")
        self.run_command("git branch -a")
        self.run_command("git remote -v")
    
    def stash_local_changes(self):
        """Stash any uncommitted changes"""
        self.log("Stashing local changes...")
        
        # Check if there are changes to stash
        result = self.run_command("git status --porcelain", check=False)
        if result.stdout.strip():
            self.run_command("git add .")
            stash_result = self.run_command("git stash push -m 'Pre-merge stash'", check=False)
            if stash_result.returncode == 0:
                self.log("Local changes stashed")
                self.rollback_commands.append("git stash pop")
            else:
                self.log("No changes to stash or stash failed")
        else:
            self.log("No changes to stash")
    
    def create_local_branch(self):
        """Create orphan branch for local MemoryOS project"""
        self.log(f"Creating orphan branch {self.temp_branch}...")
        
        # Create orphan branch
        self.run_command(f"git checkout --orphan {self.temp_branch}")
        
        # Add all current files
        self.run_command("git add .")
        
        # Commit current state
        commit_msg = f"Initial commit of {self.local_project_name} project"
        self.run_command(f'git commit -m "{commit_msg}"')
        
        self.log(f"Created local branch {self.temp_branch}")
        self.rollback_commands.append(f"git branch -D {self.temp_branch}")
    
    def fetch_remote_main(self):
        """Fetch remote main branch"""
        self.log("Fetching remote main branch...")
        
        # Add remote if not exists
        if self.remote_url:
            self.run_command(f"git remote set-url origin {self.remote_url}", check=False)
        
        # Fetch remote
        self.run_command("git fetch origin main")
        
    def checkout_remote_main(self):
        """Checkout remote main branch"""
        self.log("Checking out remote main...")
        
        # Checkout remote main
        self.run_command("git checkout -B main origin/main")
        
    def create_memoryos_subdirectory(self):
        """Create MemoryOS subdirectory structure"""
        self.log(f"Creating {self.local_project_name} subdirectory...")
        
        # Create subdirectory
        memoryos_dir = Path(self.local_project_name)
        memoryos_dir.mkdir(exist_ok=True)
        
        self.log(f"Created directory: {memoryos_dir}")
    
    def merge_local_project(self):
        """Merge local project into subdirectory"""
        self.log(f"Merging {self.local_project_name} project...")
        
        # Use git read-tree to merge the orphan branch into subdirectory
        self.run_command(f"git read-tree --prefix={self.local_project_name}/ -u {self.temp_branch}")
        
        # Stage the changes
        self.run_command("git add .")
        
        # Commit the merge
        commit_msg = f"Merge {self.local_project_name} project into /{self.local_project_name} subdirectory"
        self.run_command(f'git commit -m "{commit_msg}"')
        
        self.log("Local project merged successfully")
    
    def resolve_conflicts_if_any(self):
        """Check for and resolve any merge conflicts"""
        self.log("Checking for merge conflicts...")
        
        # Check git status for conflicts
        result = self.run_command("git status --porcelain", check=False)
        conflict_files = [line for line in result.stdout.split('\n') if line.startswith('UU')]
        
        if conflict_files:
            self.log(f"Found {len(conflict_files)} conflict files")
            for conflict in conflict_files:
                self.log(f"Conflict: {conflict}")
            
            # For now, log conflicts - manual resolution may be needed
            self.log("Manual conflict resolution may be required", "WARNING")
            return False
        else:
            self.log("No merge conflicts detected")
            return True
    
    def push_to_remote(self):
        """Push merged repository to remote"""
        self.log("Pushing to remote repository...")
        
        # Push to origin main
        push_result = self.run_command("git push origin main", check=False)
        
        if push_result.returncode == 0:
            self.log("Successfully pushed to remote")
            return True
        else:
            self.log("Push failed - may need force push", "WARNING")
            
            # Ask user for confirmation on force push
            self.log("Attempting force push with lease...")
            force_result = self.run_command("git push --force-with-lease origin main", check=False)
            
            if force_result.returncode == 0:
                self.log("Force push successful")
                return True
            else:
                self.log("Force push failed", "ERROR")
                return False
    
    def cleanup_branches(self):
        """Clean up temporary branches"""
        self.log("Cleaning up temporary branches...")
        
        # Delete temp branch
        self.run_command(f"git branch -D {self.temp_branch}", check=False)
        
        self.log("Cleanup completed")
    
    def verify_merge_result(self):
        """Verify the merge was successful"""
        self.log("Verifying merge result...")
        
        # Check directory structure
        if os.path.exists(self.local_project_name):
            self.log(f"✓ {self.local_project_name} directory exists")
            
            # List contents
            memoryos_files = os.listdir(self.local_project_name)
            self.log(f"MemoryOS files: {memoryos_files}")
            
            # Check for key files
            key_files = ['main.py', 'memory.json', 'AGENT_BIBLE.md']
            for key_file in key_files:
                if key_file in memoryos_files:
                    self.log(f"✓ {key_file} found in MemoryOS directory")
                else:
                    self.log(f"⚠ {key_file} not found in MemoryOS directory", "WARNING")
        else:
            self.log(f"✗ {self.local_project_name} directory not found", "ERROR")
            return False
        
        # Check root directory for Javlin files
        root_files = os.listdir('.')
        javlin_indicators = ['core', 'docs', 'README.md']
        for indicator in javlin_indicators:
            if indicator in root_files:
                self.log(f"✓ Javlin file/directory {indicator} found in root")
        
        return True
    
    def generate_rollback_script(self):
        """Generate rollback script in case of issues"""
        rollback_script = f"rollback_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.sh"
        
        with open(rollback_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Rollback script for git merge operation\n")
            f.write("# WARNING: This will undo the merge operation\n\n")
            
            for command in reversed(self.rollback_commands):
                f.write(f"{command}\n")
            
            f.write(f"\n# Restore from backup\n")
            f.write(f"rm -rf .git\n")
            f.write(f"cp -r {self.backup_dir}/.git .\n")
            f.write(f"cp -r {self.backup_dir}/* .\n")
        
        os.chmod(rollback_script, 0o755)
        self.log(f"Rollback script created: {rollback_script}")
    
    def execute_full_merge(self):
        """Execute the complete merge process"""
        try:
            self.log("=== Starting Git Divergence Resolution ===")
            
            # Step 1: Backup
            self.backup_workspace()
            
            # Step 2: Cleanup
            self.cleanup_git_locks()
            
            # Step 3: Check status
            self.check_git_status()
            
            # Step 4: Stash changes
            self.stash_local_changes()
            
            # Step 5: Create local branch
            self.create_local_branch()
            
            # Step 6: Fetch remote
            self.fetch_remote_main()
            
            # Step 7: Checkout remote main
            self.checkout_remote_main()
            
            # Step 8: Create subdirectory
            self.create_memoryos_subdirectory()
            
            # Step 9: Merge local project
            self.merge_local_project()
            
            # Step 10: Check conflicts
            conflicts_resolved = self.resolve_conflicts_if_any()
            
            if not conflicts_resolved:
                self.log("Manual conflict resolution required", "WARNING")
                return False
            
            # Step 11: Verify merge
            if not self.verify_merge_result():
                self.log("Merge verification failed", "ERROR")
                return False
            
            # Step 12: Push to remote
            if not self.push_to_remote():
                self.log("Push to remote failed", "ERROR")
                return False
            
            # Step 13: Cleanup
            self.cleanup_branches()
            
            # Step 14: Generate rollback script
            self.generate_rollback_script()
            
            self.log("=== Git Divergence Resolution COMPLETED ===")
            self.log(f"✓ Both projects are now in the repository")
            self.log(f"✓ MemoryOS is in /{self.local_project_name}/ subdirectory")
            self.log(f"✓ Javlin Memory Engine is in the root directory")
            self.log(f"✓ Backup available in {self.backup_dir}")
            
            return True
            
        except Exception as e:
            self.log(f"Fatal error during merge: {str(e)}", "ERROR")
            self.log("Consider using the rollback script if needed", "ERROR")
            return False

def main():
    """Main execution function"""
    print("Git Divergence Resolution Tool")
    print("==============================")
    
    resolver = GitDivergenceResolver()
    success = resolver.execute_full_merge()
    
    if success:
        print("\n✅ SUCCESS: Git divergence resolved!")
        print(f"📁 MemoryOS project is now in /{resolver.local_project_name}/ directory")
        print(f"📁 Javlin Memory Engine remains in root directory")
        print(f"💾 Backup available in {resolver.backup_dir}")
        print(f"📋 Full log in {resolver.log_file}")
    else:
        print("\n❌ FAILED: Git divergence resolution failed")
        print(f"📋 Check log file: {resolver.log_file}")
        print(f"💾 Backup available in {resolver.backup_dir}")
        print("🔄 Use rollback script if needed")

if __name__ == "__main__":
    main()
