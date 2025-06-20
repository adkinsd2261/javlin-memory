
#!/usr/bin/env python3
"""
Task Runner for Javlin Memory System
Watches task_queue.json for changes and executes shell commands automatically
"""

import json
import subprocess
import time
import datetime
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_QUEUE_FILE = os.path.join(BASE_DIR, 'task_queue.json')
TASK_OUTPUT_FILE = os.path.join(BASE_DIR, 'task_output.json')

class TaskRunner:
    def __init__(self):
        self.running = True
        self.last_queue_mtime = 0
        self.check_interval = 3  # seconds
        logger.info("Task Runner initialized with file watching")
        print("👀 Watching task_queue.json for new commands...")
    
    def get_queue_file_mtime(self):
        """Get the modification time of task_queue.json"""
        try:
            return os.path.getmtime(TASK_QUEUE_FILE)
        except OSError:
            return 0
    
    def has_queue_changed(self):
        """Check if task_queue.json has been modified since last check"""
        current_mtime = self.get_queue_file_mtime()
        if current_mtime > self.last_queue_mtime:
            self.last_queue_mtime = current_mtime
            return True
        return False
    
    def load_task_queue(self):
        """Load tasks from task_queue.json"""
        try:
            with open(TASK_QUEUE_FILE, 'r') as f:
                tasks = json.load(f)
            return tasks if isinstance(tasks, list) else []
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.debug(f"No valid task queue found: {e}")
            return []
    
    def clear_task_queue(self):
        """Clear the task queue by writing empty array"""
        try:
            with open(TASK_QUEUE_FILE, 'w') as f:
                json.dump([], f, indent=2)
            logger.info("Task queue cleared")
            # Update our tracking time after clearing
            self.last_queue_mtime = self.get_queue_file_mtime()
        except Exception as e:
            logger.error(f"Error clearing task queue: {e}")
    
    def load_task_output(self):
        """Load existing task output"""
        try:
            with open(TASK_OUTPUT_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_task_output(self, outputs):
        """Save task outputs to file"""
        try:
            with open(TASK_OUTPUT_FILE, 'w') as f:
                json.dump(outputs, f, indent=2)
            logger.info(f"Saved {len(outputs)} task outputs")
        except Exception as e:
            logger.error(f"Error saving task output: {e}")
    
    def execute_command(self, command):
        """Execute a single shell command and capture output"""
        # Block Git commands - must be handled manually per AGENT_BIBLE.md
        git_commands = ['git add', 'git commit', 'git push', 'git pull', 'git merge', 'git rebase']
        if any(git_cmd in command.lower() for git_cmd in git_commands):
            logger.warning(f"Git command blocked: {command}")
            return {
                "command": command,
                "timestamp": datetime.datetime.now().isoformat(),
                "execution_time_seconds": 0,
                "return_code": -1,
                "stdout": "",
                "stderr": "Git commands disabled - manual operation required per AGENT_BIBLE.md",
                "success": False,
                "blocked": True,
                "reason": "automated_git_disabled"
            }
        
        logger.info(f"Executing command: {command}")
        
        start_time = datetime.datetime.now()
        
        try:
            # Execute command with timeout
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=BASE_DIR
            )
            
            end_time = datetime.datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Prepare output
            output = {
                "command": command,
                "timestamp": start_time.isoformat(),
                "execution_time_seconds": execution_time,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
            # Log results
            if result.returncode == 0:
                logger.info(f"✅ Command succeeded in {execution_time:.2f}s")
                if result.stdout:
                    logger.info(f"STDOUT: {result.stdout[:200]}{'...' if len(result.stdout) > 200 else ''}")
            else:
                logger.warning(f"❌ Command failed with return code {result.returncode}")
                if result.stderr:
                    logger.warning(f"STDERR: {result.stderr[:200]}{'...' if len(result.stderr) > 200 else ''}")
            
            return output
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Command timed out after 5 minutes")
            return {
                "command": command,
                "timestamp": start_time.isoformat(),
                "execution_time_seconds": 300,
                "return_code": -1,
                "stdout": "",
                "stderr": "Command timed out after 5 minutes",
                "success": False,
                "timeout": True
            }
            
        except Exception as e:
            logger.error(f"💥 Command execution failed: {e}")
            return {
                "command": command,
                "timestamp": start_time.isoformat(),
                "execution_time_seconds": 0,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False,
                "error": str(e)
            }
    
    def process_tasks(self):
        """Process all tasks in the queue"""
        tasks = self.load_task_queue()
        
        if not tasks:
            return False  # No tasks processed
        
        print(f"🔍 Found {len(tasks)} new commands to execute")
        logger.info(f"📋 Found {len(tasks)} tasks to execute")
        
        # Load existing outputs
        all_outputs = self.load_task_output()
        
        # Execute each task
        batch_start = datetime.datetime.now()
        for i, task in enumerate(tasks, 1):
            if isinstance(task, str):
                command = task
            elif isinstance(task, dict):
                command = task.get('command', '')
                if not command:
                    logger.warning(f"Task {i} missing command field")
                    continue
            else:
                logger.warning(f"Task {i} has invalid format: {task}")
                continue
            
            print(f"⚡ [{i}/{len(tasks)}] Executing: {command}")
            logger.info(f"[{i}/{len(tasks)}] Processing: {command}")
            
            # Execute command
            output = self.execute_command(command)
            all_outputs.append(output)
            
            # Brief pause between commands
            if i < len(tasks):
                time.sleep(0.5)
        
        batch_end = datetime.datetime.now()
        batch_time = (batch_end - batch_start).total_seconds()
        
        print(f"✨ Batch completed in {batch_time:.2f}s")
        logger.info(f"✨ Batch completed in {batch_time:.2f}s")
        
        # Save all outputs
        self.save_task_output(all_outputs)
        
        # Clear the task queue
        self.clear_task_queue()
        
        print("👀 Watching task_queue.json for new commands...")
        return True  # Tasks were processed
    
    def run(self):
        """Main loop - watch for file changes and process tasks"""
        logger.info(f"🚀 Task Runner started (checking every {self.check_interval} seconds)")
        print(f"🚀 Task Runner started (checking every {self.check_interval} seconds)")
        print("Press Ctrl+C to stop")
        
        # Initialize last modification time
        self.last_queue_mtime = self.get_queue_file_mtime()
        
        try:
            while self.running:
                # Check if task queue file has changed
                if self.has_queue_changed():
                    logger.info("📄 Task queue file changed, checking for new tasks...")
                    # Process any new tasks
                    tasks_processed = self.process_tasks()
                    if not tasks_processed:
                        print("👀 Watching task_queue.json for new commands...")
                else:
                    # Brief status update every 30 seconds
                    if time.time() % 30 < self.check_interval:
                        logger.debug("Still watching for changes...")
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Task Runner stopped by user")
            logger.info("🛑 Task Runner stopped by user")
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}")
        finally:
            logger.info("Task Runner shutting down")

def main():
    """Run the task runner"""
    runner = TaskRunner()
    runner.run()

if __name__ == "__main__":
    main()
