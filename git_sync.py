#!/usr/bin/env python3
"""
GitHub Sync Module for Javlin Memory System
Automatically commits and pushes code changes with intelligent versioning
"""

import os
import json
import subprocess
import datetime
import re
import inspect
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

class GitHubSyncer:
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.memory_file = os.path.join(self.base_dir, 'memory.json')
        self.version_file = os.path.join(self.base_dir, 'version.json')
        self.config_file = os.path.join(self.base_dir, 'config.json')
        self.commit_log_file = os.path.join(self.base_dir, 'commit_log.json')
        self.changelog_file = os.path.join(self.base_dir, 'CHANGELOG.md')

        # Load configuration
        self.config = self.load_config()

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def load_config(self) -> Dict:
        """Load system and personalization configuration"""
        default_config = {
            "git_sync": {
                "enabled": True,
                "auto_push": True,
                "branch": "main",
                "batch_interval": 300,  # 5 minutes
                "max_logs_for_commit": 10,
                "version_bump_strategy": "auto"  # auto, manual, semantic
            },
            "personalization": {
                "commit_format": "standard",  # standard, emoji, formal, custom
                "sign_off": "",
                "delay_commits": False,
                "batch_commits": True,
                "custom_commit_template": ""
            }
        }

        try:
            with open(self.config_file, 'r') as f:
                user_config = json.load(f)

            # Validate config structure
            if not isinstance(user_config, dict):
                self.logger.warning("Invalid config format, using defaults")
                return default_config

            # Merge with defaults
            for section in default_config:
                if section not in user_config:
                    user_config[section] = default_config[section]
                elif isinstance(user_config[section], dict):
                    for key, value in default_config[section].items():
                        if key not in user_config[section]:
                            user_config[section][key] = value
                else:
                    user_config[section] = default_config[section]

            return user_config

        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning(f"Config load error: {e}, using defaults")
            # Create default config file
            try:
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
            except Exception:
                pass
            return default_config

    def load_memory_logs(self, limit: int = None) -> List[Dict]:
        """Load recent memory logs"""
        try:
            with open(self.memory_file, 'r') as f:
                memory = json.load(f)

            # Get recent logs (default to config limit)
            limit = limit or self.config['git_sync']['max_logs_for_commit']
            return memory[-limit:] if memory else []

        except (FileNotFoundError, json.JSONDecodeError):
            self.logger.warning("Could not load memory logs")
            return []

    def load_version_info(self) -> Dict:
        """Load current version information"""
        try:
            with open(self.version_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "version": "v0.1.0",
                "date": datetime.datetime.now().strftime('%Y-%m-%d'),
                "description": "Initial version"
            }

    def determine_version_bump(self, recent_logs: List[Dict]) -> Tuple[str, str]:
        """Determine what type of version bump is needed based on recent changes"""
        major_keywords = ['breaking', 'major', 'incompatible', 'api-change']
        minor_keywords = ['feature', 'enhancement', 'buildlog', 'new', 'add', 'implement']
        patch_keywords = ['fix', 'bugfix', 'patch', 'update', 'refactor']

        has_major = False
        has_minor = False
        has_patch = False

        for log in recent_logs:
            log_text = f"{log.get('topic', '')} {log.get('type', '')} {log.get('output', '')}".lower()
            log_type = log.get('type', '').lower()

            # Check for major changes
            if any(keyword in log_text for keyword in major_keywords):
                has_major = True

            # Check for minor changes (features, enhancements)
            elif log_type in ['feature', 'buildlog', 'enhancement'] or any(keyword in log_text for keyword in minor_keywords):
                has_minor = True

            # Check for patch changes (fixes, small updates)
            elif log_type in ['bugfix', 'fix'] or any(keyword in log_text for keyword in patch_keywords):
                has_patch = True

        # Determine bump type (major > minor > patch)
        if has_major:
            return "major", "Major system changes and breaking updates"
        elif has_minor:
            return "minor", "New features and enhancements"
        elif has_patch:
            return "patch", "Bug fixes and minor improvements"
        else:
            return "patch", "System maintenance and updates"

    def bump_version(self, bump_type: str, description: str) -> str:
        """Bump version number based on semantic versioning"""
        version_info = self.load_version_info()
        current_version = version_info.get('version', 'v0.1.0')

        # Parse current version (remove 'v' prefix if present)
        version_clean = current_version.lstrip('v')
        try:
            major, minor, patch = map(int, version_clean.split('.'))
        except ValueError:
            # Fallback if version format is unexpected
            major, minor, patch = 0, 1, 0

        # Apply version bump
        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        new_version = f"v{major}.{minor}.{patch}"

        # Update version file
        version_info.update({
            "version": new_version,
            "date": datetime.datetime.now().strftime('%Y-%m-%d'),
            "description": description,
            "bump_type": bump_type,
            "auto_bumped": True
        })

        # Archive previous version
        if 'previous_versions' not in version_info:
            version_info['previous_versions'] = []

        version_info['previous_versions'].insert(0, {
            "version": current_version,
            "date": version_info.get('date', ''),
            "description": version_info.get('description', '')
        })

        # Keep only last 10 versions
        version_info['previous_versions'] = version_info['previous_versions'][:10]

        with open(self.version_file, 'w') as f:
            json.dump(version_info, f, indent=2)

        self.logger.info(f"Version bumped from {current_version} to {new_version} ({bump_type})")
        return new_version

    def generate_changelog_entry(self, recent_logs: List[Dict], version: str) -> str:
        """Generate changelog entry from recent memory logs"""
        today = datetime.datetime.now().strftime('%Y-%m-%d')

        changelog_entry = f"\n## [{version}] - {today}\n\n"

        # Group logs by type
        log_groups = {
            'Features': [],
            'Bug Fixes': [],
            'Enhancements': [],
            'Infrastructure': [],
            'System Updates': [],
            'Other': []
        }

        for log in recent_logs:
            log_type = log.get('type', '').lower()
            topic = log.get('topic', '')
            output = log.get('output', '')

            # Categorize log entries
            if log_type in ['feature', 'buildlog']:
                log_groups['Features'].append(f"- {topic}: {output[:100]}...")
            elif log_type in ['bugfix', 'fix']:
                log_groups['Bug Fixes'].append(f"- {topic}: {output[:100]}...")
            elif log_type in ['enhancement', 'improvement']:
                log_groups['Enhancements'].append(f"- {topic}: {output[:100]}...")
            elif log_type in ['systemupdate', 'systemtest']:
                log_groups['System Updates'].append(f"- {topic}: {output[:100]}...")
            elif log.get('category') in ['Infrastructure', 'infrastructure']:
                log_groups['Infrastructure'].append(f"- {topic}: {output[:100]}...")
            else:
                log_groups['Other'].append(f"- {topic}: {output[:100]}...")

        # Build changelog entry
        for group_name, entries in log_groups.items():
            if entries:
                changelog_entry += f"### {group_name}\n"
                changelog_entry += "\n".join(entries[:5])  # Limit to 5 entries per group
                changelog_entry += "\n\n"

        return changelog_entry

    def update_changelog(self, changelog_entry: str):
        """Update or create changelog file"""
        try:
            with open(self.changelog_file, 'r') as f:
                existing_changelog = f.read()
        except FileNotFoundError:
            existing_changelog = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n"

        # Insert new entry after the header
        lines = existing_changelog.split('\n')
        header_end = 2  # After "# Changelog" and description

        # Find where to insert (after header, before first version)
        for i, line in enumerate(lines[header_end:], header_end):
            if line.startswith('## ['):
                header_end = i
                break

        # Insert new changelog entry
        lines.insert(header_end, changelog_entry)

        with open(self.changelog_file, 'w') as f:
            f.write('\n'.join(lines))

        self.logger.info("Changelog updated")

    def generate_commit_message(self, recent_logs: List[Dict], version: str, bump_type: str) -> str:
        """Generate personalized commit message"""
        commit_format = self.config['personalization']['commit_format']
        sign_off = self.config['personalization']['sign_off']
        custom_template = self.config['personalization']['custom_commit_template']

        # Analyze recent changes
        change_types = set()
        key_changes = []

        for log in recent_logs[:5]:  # Focus on top 5 changes
            change_types.add(log.get('type', 'Update'))
            topic = log.get('topic', '')
            if len(topic) < 60:
                key_changes.append(topic)

        # Base commit message
        if custom_template:
            base_msg = custom_template.format(
                version=version,
                bump_type=bump_type,
                changes=', '.join(key_changes[:3])
            )
        else:
            change_summary = ', '.join(key_changes[:3]) if key_changes else "System updates"
            base_msg = f"{version}: {change_summary}"

        # Apply formatting style
        if commit_format == "emoji":
            emoji_map = {
                'major': '🚀',
                'minor': '✨',
                'patch': '🔧',
                'feature': '✨',
                'bugfix': '🐛',
                'enhancement': '⚡'
            }
            emoji = emoji_map.get(bump_type, '📝')
            commit_msg = f"{emoji} {base_msg}"

        elif commit_format == "formal":
            commit_msg = f"Release {version}\n\nChanges:\n" + \
                        '\n'.join([f"- {change}" for change in key_changes[:5]])

        else:  # standard
            commit_msg = base_msg

        # Add sign-off if configured
        if sign_off:
            commit_msg += f"\n\nSigned-off-by: {sign_off}"

        return commit_msg

    def check_git_status(self) -> bool:
        """Check if there are changes to commit"""
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.base_dir)
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            self.logger.error("Failed to check git status")
            return False

    def commit_and_push(self, commit_message: str, version: str) -> bool:
        """Execute git add, commit, and push with proper lock file handling"""
        try:
            # Clear any existing lock files
            lock_files = [
                '.git/index.lock',
                '.git/refs/heads/main.lock',
                '.git/HEAD.lock',
                '.git/config.lock'
            ]

            for lock_file in lock_files:
                lock_path = os.path.join(self.base_dir, lock_file)
                if os.path.exists(lock_path):
                    os.remove(lock_path)
                    self.logger.info(f"Removed lock file: {lock_file}")

            # Wait a moment for file system to clear
            import time
            time.sleep(0.5)

            # Check if there are actually changes to commit
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.base_dir)
            if not result.stdout.strip():
                self.logger.info("No changes to commit")
                return False

            # Add all changes
            subprocess.run(['git', 'add', '.'], check=True, cwd=self.base_dir, timeout=30)

            # Check if there's anything staged
            result = subprocess.run(['git', 'diff', '--cached', '--quiet'], 
                                  capture_output=True, cwd=self.base_dir)
            if result.returncode == 0:
                self.logger.info("No staged changes to commit")
                return False

            # Commit with message
            subprocess.run(['git', 'commit', '-m', commit_message], 
                         check=True, cwd=self.base_dir, timeout=30)

            # Tag the version (skip if already exists)
            try:
                subprocess.run(['git', 'tag', version], check=True, cwd=self.base_dir, timeout=15)
            except subprocess.CalledProcessError:
                self.logger.warning(f"Tag {version} already exists, skipping")

            # Push to main branch
            branch = self.config['git_sync']['branch']
            subprocess.run(['git', 'push', 'origin', branch], check=True, cwd=self.base_dir, timeout=60)

            # Push tags
            try:
                subprocess.run(['git', 'push', 'origin', '--tags'], check=True, cwd=self.base_dir, timeout=30)
            except subprocess.CalledProcessError:
                self.logger.warning("Failed to push tags, but commit was successful")

            self.logger.info(f"Successfully pushed {version} to {branch}")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git operation failed: {e}")
            return False
        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Git operation timed out: {e}")
            return False

    def log_commit_metadata(self, commit_message: str, version: str, recent_logs: List[Dict]):
        """Store commit metadata in commit_log.json"""
        try:
            with open(self.commit_log_file, 'r') as f:
                commit_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            commit_data = {"commits": [], "auto_sync_commits": True}

        # Get commit hash
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True, cwd=self.base_dir)
            commit_hash = result.stdout.strip()
        except subprocess.CalledProcessError:
            commit_hash = "unknown"

        commit_entry = {
            "hash": commit_hash,
            "message": commit_message,
            "version": version,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "auto_generated": True,
            "memory_logs_included": len(recent_logs),
            "files_changed": self.get_changed_files(),
            "sync_method": "auto"
        }

        commit_data["commits"].append(commit_entry)

        with open(self.commit_log_file, 'w') as f:
            json.dump(commit_data, f, indent=2)

        self.logger.info("Commit metadata logged")

    def get_changed_files(self) -> List[str]:
        """Get list of files that were changed in the last commit"""
        try:
            result = subprocess.run(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD'], 
                                  capture_output=True, text=True, cwd=self.base_dir)
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError:
            return []

    def should_auto_sync(self, recent_logs: List[Dict]) -> bool:
        """Determine if auto-sync should be triggered based on recent activity"""
        if not self.config['git_sync']['enabled']:
            return False

        # Check for significant changes that warrant a sync
        significant_types = ['BuildLog', 'Feature', 'BugFix', 'Enhancement', 'SystemUpdate']
        significant_logs = [log for log in recent_logs 
                          if log.get('type') in significant_types and log.get('success', True)]

        # Auto-sync if we have 3+ significant changes or any major changes
        return len(significant_logs) >= 3 or any(
            'major' in log.get('topic', '').lower() or 'breaking' in log.get('output', '').lower()
            for log in recent_logs
        )

    def _load_sync_status(self) -> Dict:
        """Load git sync status and circuit breaker state"""
        status_file = os.path.join(self.base_dir, 'git_sync_status.json')
        try:
            with open(status_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "last_sync_attempt": None,
                "consecutive_failures": 0,
                "circuit_breaker_until": None,
                "last_successful_sync": None,
                "status": "ready"
            }

    def _save_sync_status(self, status: Dict):
        """Save git sync status"""
        status_file = os.path.join(self.base_dir, 'git_sync_status.json')
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)

    def _is_circuit_breaker_active(self) -> bool:
        """Check if circuit breaker is currently blocking sync attempts"""
        status = self._load_sync_status()
        if status.get('circuit_breaker_until'):
            breaker_until = datetime.datetime.fromisoformat(status['circuit_breaker_until'])
            if datetime.datetime.now() < breaker_until:
                return True
            else:
                # Circuit breaker period expired, reset
                status['circuit_breaker_until'] = None
                status['consecutive_failures'] = 0
                self._save_sync_status(status)
        return False

    def _update_sync_status(self, success: bool, message: str = ""):
        """Update sync status and handle circuit breaker logic"""
        status = self._load_sync_status()
        status['last_sync_attempt'] = datetime.datetime.now().isoformat()
        
        if success:
            status['consecutive_failures'] = 0
            status['circuit_breaker_until'] = None
            status['last_successful_sync'] = datetime.datetime.now().isoformat()
            status['status'] = 'success'
        else:
            status['consecutive_failures'] += 1
            status['status'] = 'failed'
            
            # Activate circuit breaker after 3 consecutive failures
            if status['consecutive_failures'] >= 3:
                # Block for 5 minutes
                breaker_until = datetime.datetime.now() + datetime.timedelta(minutes=5)
                status['circuit_breaker_until'] = breaker_until.isoformat()
                self.logger.warning(f"Circuit breaker activated until {breaker_until}")
        
        self._save_sync_status(status)

    def run_auto_sync(self, force: bool = False) -> Dict[str, any]:
        """Run auto-sync with circuit breaker and improved lock handling"""
        import fcntl
        import tempfile
        
        # Check circuit breaker first
        if not force and self._is_circuit_breaker_active():
            status = self._load_sync_status()
            return {
                "status": "blocked", 
                "message": f"Circuit breaker active until {status.get('circuit_breaker_until')}"
            }
        
        # Use file locking to prevent concurrent sync operations
        lock_file_path = os.path.join(tempfile.gettempdir(), 'memoryos_git_sync.lock')
        
        try:
            lock_file = open(lock_file_path, 'w')
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Prevent recursive calls
            if hasattr(self, '_sync_in_progress') and self._sync_in_progress:
                return {"status": "skipped", "message": "Sync already in progress"}

            self._sync_in_progress = True

            # Enhanced lock clearing with timeout
            self._enhanced_lock_clear()

            # Check if sync is needed
            if not force and not self.should_auto_sync(self.load_memory_logs()):
                self._sync_in_progress = False
                return {"status": "skipped", "message": "No sync needed"}

            # Load recent memory logs
            recent_logs = self.load_memory_logs()
            bump_type, bump_description = self.determine_version_bump(recent_logs)

            # Bump version
            new_version = self.bump_version(bump_type, bump_description)

            # Generate changelog
            changelog_entry = self.generate_changelog_entry(recent_logs, new_version)
            self.update_changelog(changelog_entry)

            # Generate commit message
            commit_message = self.generate_commit_message(recent_logs, new_version, bump_type)

            # Commit and push with enhanced error handling
            success = self._safe_commit_and_push(commit_message, new_version)

            # Update circuit breaker status
            self._update_sync_status(success, "Sync completed" if success else "Sync failed")

            if success:
                # Log commit metadata
                self.log_commit_metadata(commit_message, new_version, recent_logs)

                return {
                    "status": "success",
                    "version": new_version,
                    "bump_type": bump_type,
                    "commit_message": commit_message,
                    "logs_processed": len(recent_logs),
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
            else:
                return {"status": "error", "message": "Failed to commit and push changes"}

        except BlockingIOError:
            return {"status": "skipped", "message": "Another sync operation is in progress"}
        except Exception as e:
            self._update_sync_status(False, str(e))
            return {"status": "error", "message": str(e)}
        finally:
            # Always clear the in-progress flag
            if hasattr(self, '_sync_in_progress'):
                self._sync_in_progress = False
            
            # Release file lock
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                os.unlink(lock_file_path)
            except:
                pass

    def _enhanced_lock_clear(self):
        """Enhanced lock clearing with better process management"""
        import time
        import subprocess
        
        # Kill git processes with multiple signals
        try:
            # SIGTERM first (graceful)
            subprocess.run(['pkill', '-TERM', 'git'], capture_output=True, timeout=5)
            time.sleep(2)
            
            # SIGKILL if still running  
            subprocess.run(['pkill', '-KILL', 'git'], capture_output=True, timeout=5)
            time.sleep(1)
            
        except subprocess.TimeoutExpired:
            pass
        
        # Force remove lock files with retry logic
        lock_files = [
            '.git/index.lock',
            '.git/refs/heads/main.lock',
            '.git/HEAD.lock',
            '.git/config.lock',
            '.git/COMMIT_EDITMSG.lock',
            '.git/refs/remotes/origin/main.lock'
        ]
        
        for lock_file in lock_files:
            lock_path = os.path.join(self.base_dir, lock_file)
            for attempt in range(3):  # Try 3 times
                if os.path.exists(lock_path):
                    try:
                        os.remove(lock_path)
                        self.logger.info(f"Removed lock file: {lock_file}")
                        break
                    except (PermissionError, OSError) as e:
                        if attempt < 2:  # Not the last attempt
                            time.sleep(0.5)
                            continue
                        else:
                            self.logger.error(f"Failed to remove {lock_file}: {e}")

    def _safe_commit_and_push(self, commit_message: str, version: str) -> bool:
        """Enhanced commit and push with better error handling"""
        try:
            # Check if there are actually changes
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.base_dir, timeout=15)
            if not result.stdout.strip():
                self.logger.info("No changes to commit")
                return True  # Success - nothing needed

            # Configure git identity
            subprocess.run(['git', 'config', 'user.name', 'MemoryOS'], 
                         cwd=self.base_dir, timeout=10, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'memoryos@javlin.ai'], 
                         cwd=self.base_dir, timeout=10, capture_output=True)

            # Add all changes with timeout
            add_result = subprocess.run(['git', 'add', '.'], 
                                      check=True, cwd=self.base_dir, timeout=30, capture_output=True)

            # Check if there are staged changes
            staged_result = subprocess.run(['git', 'diff', '--cached', '--quiet'], 
                                         capture_output=True, cwd=self.base_dir, timeout=10)
            if staged_result.returncode == 0:
                self.logger.info("No staged changes after add")
                return True  # Success - nothing to commit

            # Commit with timeout
            commit_result = subprocess.run(['git', 'commit', '-m', commit_message], 
                                         check=True, cwd=self.base_dir, timeout=30, capture_output=True)

            # Push with timeout and retry logic
            for attempt in range(2):  # Try push twice
                try:
                    push_result = subprocess.run(['git', 'push', 'origin', 'main'], 
                                               check=True, cwd=self.base_dir, timeout=60, capture_output=True)
                    self.logger.info(f"Successfully pushed {version} to main")
                    return True
                except subprocess.CalledProcessError as e:
                    if attempt == 0:  # First attempt failed, try pull and retry
                        self.logger.warning("Push failed, trying to sync with remote...")
                        try:
                            subprocess.run(['git', 'pull', 'origin', 'main', '--rebase'], 
                                         cwd=self.base_dir, timeout=30, capture_output=True)
                        except:
                            pass  # Continue to retry push
                        continue
                    else:
                        self.logger.error(f"Push failed after retry: {e}")
                        return False

        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Git operation timed out: {e}")
            self._enhanced_lock_clear()  # Clear locks on timeout
            return False
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git operation failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during git operations: {e}")
            return False

        return False

    def _force_clear_git_locks(self):
        """Force clear all git lock files with process checking"""
        import time
        import subprocess
        import psutil
        
        # Kill all git processes using multiple methods for better reliability
        try:
            # Method 1: psutil (most reliable)
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'git' in proc.info['name'] or any('git' in cmd for cmd in (proc.info['cmdline'] or [])):
                        proc.kill()
                        self.logger.info(f"Killed git process: {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            time.sleep(2)
        except ImportError:
            # Fallback methods if psutil not available
            try:
                # Method 2: pkill with force
                subprocess.run(['pkill', '-9', '-f', 'git'], capture_output=True, timeout=5)
                subprocess.run(['pkill', '-9', 'git'], capture_output=True, timeout=5)
                subprocess.run(['killall', '-9', 'git'], capture_output=True, timeout=5)
                time.sleep(3)
            except:
                pass
        
        # Force remove all git lock files with glob patterns
        import glob
        lock_patterns = [
            os.path.join(self.base_dir, '.git', '*.lock'),
            os.path.join(self.base_dir, '.git', 'refs', '**', '*.lock'),
            os.path.join(self.base_dir, '.git', 'objects', '**', '*.lock')
        ]
        
        for pattern in lock_patterns:
            for lock_file in glob.glob(pattern, recursive=True):
                try:
                    os.remove(lock_file)
                    self.logger.info(f"Removed lock file: {lock_file}")
                except Exception as e:
                    self.logger.warning(f"Could not remove {lock_file}: {e}")
        
        # Clear all possible git lock files
        lock_patterns = [
            '.git/index.lock',
            '.git/refs/heads/main.lock',
            '.git/config.lock',
            '.git/HEAD.lock',
            '.git/COMMIT_EDITMSG.lock',
            '.git/refs/remotes/origin/main.lock',
            '.git/refs/heads/*.lock',
            '.git/refs/remotes/origin/*.lock',
            '.git/*.lock'
        ]
        
        # Use shell globbing to clear all lock files
        try:
            subprocess.run(['find', self.base_dir, '-name', '*.lock', '-path', '*/.git/*', '-delete'], 
                         capture_output=True, timeout=10)
            self.logger.info("Cleared all git lock files using find command")
        except:
            pass

        for pattern in lock_patterns:
            lock_path = os.path.join(self.base_dir, pattern)
            max_attempts = 3
            for attempt in range(max_attempts):
                if os.path.exists(lock_path):
                    try:
                        os.remove(lock_path)
                        self.logger.info(f"Removed git lock: {pattern}")
                        break
                    except PermissionError:
                        if attempt < max_attempts - 1:
                            time.sleep(0.5)
                            continue
                        else:
                            self.logger.error(f"Failed to remove lock {pattern} after {max_attempts} attempts")
                    except Exception as e:
                        self.logger.warning(f"Failed to remove lock {pattern}: {e}")
                        break
                else:
                    break

    def _perform_sync_with_timeout(self):
        """Perform git sync with timeout and proper error handling"""
        try:
            # Set git config to avoid interactive prompts
            subprocess.run(['git', 'config', 'user.name', 'MemoryOS'], cwd=self.base_dir, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'memoryos@javlin.ai'], cwd=self.base_dir, capture_output=True)

            # Add all changes with timeout
            result = subprocess.run(['git', 'add', '.'], cwd=self.base_dir, timeout=30, capture_output=True, text=True)
            if result.returncode != 0:
                return {"status": "error", "message": f"Git add failed: {result.stderr}"}

            # Check if there are changes to commit
            status = subprocess.run(['git', 'status', '--porcelain'], cwd=self.base_dir, timeout=15, capture_output=True, text=True)

            if not status.stdout.strip():
                return {"status": "success", "message": "No changes to sync"}

            # Load recent memory logs
            recent_logs = self.load_memory_logs()

            # Generate commit message
            commit_message = self.generate_commit_message(recent_logs, 'version', 'bump_type')

            # Commit changes with timeout
            commit_result = subprocess.run(['git', 'commit', '-m', commit_message], cwd=self.base_dir, timeout=30, capture_output=True, text=True)
            if commit_result.returncode != 0:
                if "nothing to commit" in commit_result.stdout:
                    return {"status": "success", "message": "No changes to commit"}
                return {"status": "error", "message": f"Git commit failed: {commit_result.stderr}"}

            # Push to remote with timeout
            push_result = subprocess.run(['git', 'push', 'origin', 'main'], cwd=self.base_dir, timeout=60, capture_output=True, text=True)
            if push_result.returncode != 0:
                return {"status": "error", "message": f"Git push failed: {push_result.stderr}"}

            return {"status": "success", "message": f"Synced: {commit_message}"}

        except subprocess.TimeoutExpired:
            # Clear locks if timeout occurs
            self._force_clear_git_locks()
            return {"status": "error", "message": "Git operation timed out - locks cleared"}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"Git operation failed: {e.stderr.decode() if e.stderr else str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}

    def log_commit_metadata(self, commit_message: str, version: str, recent_logs: List[Dict]):
        """Store commit metadata in commit_log.json"""
        try:
            with open(self.commit_log_file, 'r') as f:
                commit_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            commit_data = {"commits": [], "auto_sync_commits": True}

        # Get commit hash
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                  capture_output=True, text=True, cwd=self.base_dir)
            commit_hash = result.stdout.strip()
        except subprocess.CalledProcessError:
            commit_hash = "unknown"

        commit_entry = {
            "hash": commit_hash,
            "message": commit_message,
            "version": version,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "auto_generated": True,
            "memory_logs_included": len(recent_logs),
            "files_changed": self.get_changed_files(),
            "sync_method": "auto"
        }

        commit_data["commits"].append(commit_entry)

        with open(self.commit_log_file, 'w') as f:
            json.dump(commit_data, f, indent=2)

        self.logger.info("Commit metadata logged")

    def get_changed_files(self) -> List[str]:
        """Get list of files that were changed in the last commit"""
        try:
            result = subprocess.run(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD'],
                                  capture_output=True, text=True, cwd=self.base_dir)
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError:
            return []

    def should_auto_sync(self, recent_logs: List[Dict]) -> bool:
        """Determine if auto-sync should be triggered based on recent activity"""
        if not self.config['git_sync']['enabled']:
            return False

        # Check for significant changes that warrant a sync
        significant_types = ['BuildLog', 'Feature', 'BugFix', 'Enhancement', 'SystemUpdate']
        significant_logs = [log for log in recent_logs
                          if log.get('type') in significant_types and log.get('success', True)]

        # Auto-sync if we have 3+ significant changes or any major changes
        return len(significant_logs) >= 3 or any(
            'major' in log.get('topic', '').lower() or 'breaking' in log.get('output', '').lower()
            for log in recent_logs
        )


def main():
    """CLI interface for git sync"""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Sync for Javlin Memory System")
    parser.add_argument('--force', action='store_true', help='Force sync even if no significant changes')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be synced without doing it')
    parser.add_argument('--logs', type=int, default=10, help='Number of recent logs to analyze')

    args = parser.parse_args()

    syncer = GitHubSyncer()

    if args.dry_run:
        recent_logs = syncer.load_memory_logs(args.logs)
        bump_type, description = syncer.determine_version_bump(recent_logs)

        print(f"🔍 Dry Run Results:")
        print(f"  Recent logs analyzed: {len(recent_logs)}")
        print(f"  Suggested version bump: {bump_type}")
        print(f"  Bump description: {description}")
        print(f"  Would auto-sync: {syncer.should_auto_sync(recent_logs)}")
        print(f"  Has changes to commit: {syncer.check_git_status()}")
    else:
        result = syncer.run_auto_sync(force=args.force)
        print(f"🚀 Sync Result: {result}")

if __name__ == "__main__":
    main()