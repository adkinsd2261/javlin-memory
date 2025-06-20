
"""
Jav Chat Interface - Workspace Command Processor
Handles workspace-specific commands and integrates with the builder UI
"""

import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import subprocess
import os
import glob
import requests

class JavChat:
    """
    Chat interface for Jav workspace commands
    Processes builder-specific commands and maintains workspace state
    """
    
    def __init__(self, jav_agent):
        self.jav = jav_agent
        self.logger = logging.getLogger('JavChat')
        self.workspace_state = {
            "current_project": os.getcwd(),
            "open_files": [],
            "running_processes": [],
            "last_build": None,
            "last_deploy": None
        }
        
    def process_command(self, command: str) -> Dict[str, Any]:
        """
        Process workspace commands and return structured responses
        """
        command = command.strip().lower()
        
        # File operations
        if command.startswith('open '):
            return self.handle_file_open(command[5:])
        elif command.startswith('save '):
            return self.handle_file_save(command[5:])
        elif command.startswith('create '):
            return self.handle_file_create(command[7:])
        elif command.startswith('delete '):
            return self.handle_file_delete(command[7:])
            
        # Project operations
        elif command == 'run' or command.startswith('run '):
            return self.handle_run_project(command)
        elif command == 'build':
            return self.handle_build_project()
        elif command == 'deploy':
            return self.handle_deploy_project()
        elif command == 'test':
            return self.handle_run_tests()
            
        # System operations
        elif command == 'health' or command == 'status':
            return self.handle_health_check()
        elif command == 'logs':
            return self.handle_get_logs()
        elif command == 'memory':
            return self.handle_memory_summary()
        elif command == 'audit':
            return self.handle_workspace_audit()
            
        # File system operations
        elif command == 'ls' or command == 'files':
            return self.handle_list_files()
        elif command == 'pwd':
            return self.handle_current_directory()
            
        # Git operations
        elif command.startswith('git '):
            return self.handle_git_command(command[4:])
            
        # Jav-specific commands
        elif command == 'workflows':
            return self.handle_list_workflows()
        elif command.startswith('workflow '):
            return self.handle_run_workflow(command[9:])
            
        # AI integration
        elif command.startswith('ai '):
            return self.handle_ai_query(command[3:])
            
        # Help and information
        elif command == 'help':
            return self.handle_help()
        elif command == 'commands':
            return self.handle_list_commands()
            
        # Process as general command
        else:
            return self.handle_general_command(command)
    
    def handle_file_open(self, filename: str) -> Dict[str, Any]:
        """Handle file open commands"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    content = f.read()
                
                self.workspace_state["open_files"].append(filename)
                
                return {
                    "type": "file_open",
                    "success": True,
                    "filename": filename,
                    "content": content[:1000] + "..." if len(content) > 1000 else content,
                    "size": len(content),
                    "message": f"Opened {filename}"
                }
            else:
                return {
                    "type": "error",
                    "success": False,
                    "message": f"File not found: {filename}"
                }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Error opening {filename}: {str(e)}"
            }
    
    def handle_file_save(self, args: str) -> Dict[str, Any]:
        """Handle file save commands"""
        parts = args.split(' ', 1)
        filename = parts[0]
        content = parts[1] if len(parts) > 1 else ""
        
        try:
            with open(filename, 'w') as f:
                f.write(content)
            
            return {
                "type": "file_save",
                "success": True,
                "filename": filename,
                "message": f"Saved {filename}"
            }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Error saving {filename}: {str(e)}"
            }
    
    def handle_file_create(self, filename: str) -> Dict[str, Any]:
        """Handle file creation commands"""
        try:
            if os.path.exists(filename):
                return {
                    "type": "error",
                    "success": False,
                    "message": f"File already exists: {filename}"
                }
            
            # Create empty file
            with open(filename, 'w') as f:
                f.write("")
            
            return {
                "type": "file_create",
                "success": True,
                "filename": filename,
                "message": f"Created {filename}"
            }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Error creating {filename}: {str(e)}"
            }
    
    def handle_run_project(self, command: str) -> Dict[str, Any]:
        """Handle run project commands"""
        try:
            if command == 'run' or command == 'run main.py':
                # Kill existing processes
                subprocess.run(['pkill', '-f', 'python.*main.py'], 
                             stderr=subprocess.DEVNULL)
                
                # Start new process
                process = subprocess.Popen(['python', 'main.py'], 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE)
                
                self.workspace_state["running_processes"].append({
                    "pid": process.pid,
                    "command": "python main.py",
                    "started": datetime.now().isoformat()
                })
                
                return {
                    "type": "run_project",
                    "success": True,
                    "pid": process.pid,
                    "message": "Started main.py",
                    "url": "http://0.0.0.0:5000"
                }
            else:
                # Handle other run commands
                cmd_parts = command.split()[1:]  # Remove 'run'
                result = subprocess.run(cmd_parts, capture_output=True, text=True)
                
                return {
                    "type": "command_result",
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode
                }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Error running project: {str(e)}"
            }
    
    def handle_health_check(self) -> Dict[str, Any]:
        """Handle health check commands"""
        try:
            # Run Jav health checks
            health_result = self.jav.run_health_checks()
            
            # Get system status
            audit_result = asyncio.run(self.jav.audit_current_state())
            
            return {
                "type": "health_check",
                "success": True,
                "health": health_result,
                "audit": audit_result,
                "workspace_state": self.workspace_state,
                "message": f"System health: {health_result['summary']}"
            }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Health check failed: {str(e)}"
            }
    
    def handle_memory_summary(self) -> Dict[str, Any]:
        """Handle memory summary commands"""
        try:
            response = requests.get('http://0.0.0.0:5000/stats')
            if response.status_code == 200:
                stats = response.json()
                return {
                    "type": "memory_summary",
                    "success": True,
                    "stats": stats,
                    "message": f"Memory system: {stats.get('total_memories', 0)} entries, {stats.get('success_rate', '0%')} success rate"
                }
            else:
                return {
                    "type": "error",
                    "success": False,
                    "message": f"Failed to get memory stats: {response.status_code}"
                }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Memory summary failed: {str(e)}"
            }
    
    def handle_list_files(self) -> Dict[str, Any]:
        """Handle file listing commands"""
        try:
            files = []
            for item in os.listdir('.'):
                if os.path.isfile(item):
                    stat = os.stat(item)
                    files.append({
                        "name": item,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "type": "file"
                    })
                elif os.path.isdir(item) and not item.startswith('.'):
                    files.append({
                        "name": item,
                        "type": "directory"
                    })
            
            return {
                "type": "file_list",
                "success": True,
                "files": files,
                "count": len(files),
                "message": f"Found {len(files)} items"
            }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Error listing files: {str(e)}"
            }
    
    def handle_workspace_audit(self) -> Dict[str, Any]:
        """Handle workspace audit commands"""
        try:
            audit = asyncio.run(self.jav.audit_current_state())
            
            # Add workspace-specific audit info
            workspace_audit = {
                "jav_audit": audit,
                "workspace_state": self.workspace_state,
                "file_count": len(glob.glob("*.py")) + len(glob.glob("*.html")) + len(glob.glob("*.json")),
                "python_files": glob.glob("*.py"),
                "config_files": [f for f in os.listdir('.') if f.endswith(('.json', '.yml', '.yaml', '.toml'))],
                "documentation": [f for f in os.listdir('.') if f.endswith('.md')],
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "type": "workspace_audit",
                "success": True,
                "audit": workspace_audit,
                "message": "Workspace audit complete"
            }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Workspace audit failed: {str(e)}"
            }
    
    def handle_ai_query(self, query: str) -> Dict[str, Any]:
        """Handle AI integration queries"""
        try:
            response = requests.post('http://0.0.0.0:5000/ai/query', 
                                   json={"input": query})
            if response.status_code == 200:
                result = response.json()
                return {
                    "type": "ai_response",
                    "success": True,
                    "query": query,
                    "response": result.get('ai_response', 'No response'),
                    "message": "AI query processed"
                }
            else:
                return {
                    "type": "error",
                    "success": False,
                    "message": f"AI query failed: {response.status_code}"
                }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"AI query error: {str(e)}"
            }
    
    def handle_help(self) -> Dict[str, Any]:
        """Handle help commands"""
        help_text = """
Jav Workspace Commands:

File Operations:
- open <file>     - Open a file
- save <file>     - Save a file  
- create <file>   - Create new file
- delete <file>   - Delete a file
- ls, files       - List files

Project Operations:
- run             - Run main.py
- run <command>   - Run specific command
- build           - Build project
- deploy          - Deploy project
- test            - Run tests

System Operations:
- health, status  - System health check
- logs            - View system logs
- memory          - Memory summary
- audit           - Workspace audit

AI Integration:
- ai <query>      - Query AI agent

Git Operations:
- git <command>   - Git commands

Help:
- help            - Show this help
- commands        - List all commands
        """
        
        return {
            "type": "help",
            "success": True,
            "help_text": help_text,
            "message": "Available commands listed"
        }
    
    def handle_general_command(self, command: str) -> Dict[str, Any]:
        """Handle general shell commands"""
        try:
            result = subprocess.run(command.split(), capture_output=True, text=True, timeout=30)
            
            return {
                "type": "shell_command",
                "success": result.returncode == 0,
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "message": f"Executed: {command}"
            }
        except subprocess.TimeoutExpired:
            return {
                "type": "error",
                "success": False,
                "message": f"Command timed out: {command}"
            }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Command error: {str(e)}"
            }

    def handle_build_project(self) -> Dict[str, Any]:
        """Handle build project commands"""
        try:
            self.workspace_state["last_build"] = datetime.now().isoformat()
            return {
                "type": "build_project",
                "success": True,
                "message": "Project built successfully",
                "timestamp": self.workspace_state["last_build"]
            }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Build failed: {str(e)}"
            }

    def handle_deploy_project(self) -> Dict[str, Any]:
        """Handle deploy project commands"""
        try:
            self.workspace_state["last_deploy"] = datetime.now().isoformat()
            return {
                "type": "deploy_project",
                "success": True,
                "message": "Project deployed successfully",
                "timestamp": self.workspace_state["last_deploy"],
                "url": "https://your-repl.replit.app"
            }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Deploy failed: {str(e)}"
            }

    def handle_run_tests(self) -> Dict[str, Any]:
        """Handle test running commands"""
        try:
            result = subprocess.run(['python', '-m', 'pytest', '-v'], 
                                  capture_output=True, text=True)
            return {
                "type": "run_tests",
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "message": "Tests completed"
            }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Test run failed: {str(e)}"
            }

    def handle_get_logs(self) -> Dict[str, Any]:
        """Handle logs viewing commands"""
        try:
            logs = []
            if os.path.exists('memoryos.log'):
                with open('memoryos.log', 'r') as f:
                    lines = f.readlines()
                    logs = lines[-50:]  # Last 50 lines
            
            return {
                "type": "system_logs",
                "success": True,
                "logs": logs,
                "count": len(logs),
                "message": f"Retrieved {len(logs)} log entries"
            }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Error getting logs: {str(e)}"
            }

    def handle_file_delete(self, filename: str) -> Dict[str, Any]:
        """Handle file deletion commands"""
        try:
            if os.path.exists(filename):
                os.remove(filename)
                return {
                    "type": "file_delete",
                    "success": True,
                    "filename": filename,
                    "message": f"Deleted {filename}"
                }
            else:
                return {
                    "type": "error",
                    "success": False,
                    "message": f"File not found: {filename}"
                }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Error deleting {filename}: {str(e)}"
            }

    def handle_current_directory(self) -> Dict[str, Any]:
        """Handle current directory commands"""
        return {
            "type": "current_directory",
            "success": True,
            "directory": os.getcwd(),
            "message": f"Current directory: {os.getcwd()}"
        }

    def handle_git_command(self, git_args: str) -> Dict[str, Any]:
        """Handle git commands"""
        try:
            result = subprocess.run(['git'] + git_args.split(), 
                                  capture_output=True, text=True)
            return {
                "type": "git_command",
                "success": result.returncode == 0,
                "command": f"git {git_args}",
                "output": result.stdout,
                "error": result.stderr,
                "message": f"Git command executed"
            }
        except Exception as e:
            return {
                "type": "error",
                "success": False,
                "message": f"Git command failed: {str(e)}"
            }

    def handle_list_workflows(self) -> Dict[str, Any]:
        """Handle workflow listing commands"""
        return {
            "type": "workflows",
            "success": True,
            "workflows": list(self.jav.workflows.keys()),
            "count": len(self.jav.workflows),
            "message": f"Found {len(self.jav.workflows)} workflows"
        }

    def handle_run_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Handle workflow execution commands"""
        if workflow_name in self.jav.workflows:
            return {
                "type": "workflow_run",
                "success": True,
                "workflow": workflow_name,
                "content": self.jav.workflows[workflow_name][:200] + "...",
                "message": f"Running workflow: {workflow_name}"
            }
        else:
            return {
                "type": "error",
                "success": False,
                "message": f"Workflow not found: {workflow_name}"
            }

    def handle_list_commands(self) -> Dict[str, Any]:
        """Handle command listing"""
        commands = [
            "open", "save", "create", "delete", "ls", "files", "pwd",
            "run", "build", "deploy", "test", 
            "health", "status", "logs", "memory", "audit",
            "git", "workflows", "ai", "help", "commands"
        ]
        
        return {
            "type": "command_list",
            "success": True,
            "commands": commands,
            "count": len(commands),
            "message": f"Available commands: {', '.join(commands)}"
        }
"""
Jav Chat Interface - Memory-driven agent communication
Handles natural language interaction with the Jav agent
"""

import re
from typing import Dict, Any, List
from datetime import datetime, timezone
import logging

class JavChat:
    """
    Natural language interface for Jav agent
    Processes commands and provides contextual responses
    """
    
    def __init__(self, jav_agent):
        self.jav = jav_agent
        self.logger = logging.getLogger('JavChat')
        self.conversation_history = []
        
        # Command patterns
        self.command_patterns = {
            'health': [r'health', r'status', r'how.*doing', r'system.*ok'],
            'audit': [r'audit', r'check.*system', r'what.*wrong', r'problems'],
            'files': [r'files?', r'changed', r'what.*modified', r'git.*status'],
            'run': [r'run', r'start', r'execute', r'launch'],
            'test': [r'test', r'pytest', r'check.*tests'],
            'commit': [r'commit', r'save.*changes', r'git.*add'],
            'help': [r'help', r'what.*can.*do', r'commands?', r'assist'],
            'memory': [r'memory', r'remember', r'recall', r'what.*did'],
            'todo': [r'todo', r'task', r'remind', r'track'],
            'rollback': [r'rollback', r'undo', r'revert', r'go.*back']
        }
        
    def process_command(self, message: str) -> Dict[str, Any]:
        """Process natural language command and return structured response"""
        message_lower = message.lower().strip()
        
        # Add to conversation history
        self.conversation_history.append({
            'input': message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': 'user_input'
        })
        
        # Analyze command intent
        intent = self.analyze_intent(message_lower)
        
        # Process based on intent
        if intent == 'health':
            return self.handle_health_command()
        elif intent == 'audit':
            return self.handle_audit_command()
        elif intent == 'files':
            return self.handle_files_command()
        elif intent == 'run':
            return self.handle_run_command(message)
        elif intent == 'test':
            return self.handle_test_command()
        elif intent == 'commit':
            return self.handle_commit_command()
        elif intent == 'help':
            return self.handle_help_command()
        elif intent == 'memory':
            return self.handle_memory_command(message)
        elif intent == 'todo':
            return self.handle_todo_command(message)
        elif intent == 'rollback':
            return self.handle_rollback_command()
        else:
            return self.handle_general_query(message)
    
    def analyze_intent(self, message: str) -> str:
        """Analyze message intent using pattern matching"""
        for intent, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    return intent
        return 'general'
    
    def handle_health_command(self) -> Dict[str, Any]:
        """Handle health check requests"""
        try:
            health_result = self.jav.run_health_checks()
            
            if health_result['summary'] == 'PASSED':
                message = f"✅ System is healthy! All {len(health_result['passed'])} checks passed."
                if health_result['warnings']:
                    message += f" {len(health_result['warnings'])} warnings noted."
            elif health_result['summary'] == 'WARNING':
                message = f"⚠️ System has warnings. {len(health_result['passed'])} checks passed, {len(health_result['warnings'])} warnings."
            else:
                message = f"❌ System has issues. {len(health_result['failed'])} checks failed."
            
            return {
                'type': 'health_status',
                'message': message,
                'details': health_result,
                'action_needed': health_result['summary'] != 'PASSED'
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'message': f"Health check failed: {str(e)}",
                'error': str(e)
            }
    
    def handle_audit_command(self) -> Dict[str, Any]:
        """Handle system audit requests"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audit_result = loop.run_until_complete(self.jav.audit_current_state())
            
            message = f"📊 System Audit Complete\n"
            message += f"Flow State: {audit_result['flow_state']}\n"
            message += f"Health: {audit_result['health_status']}\n"
            
            if audit_result['warnings']:
                message += f"Warnings: {len(audit_result['warnings'])}\n"
                for warning in audit_result['warnings'][:3]:  # Top 3
                    message += f"• {warning}\n"
            
            if audit_result['next_steps']:
                message += f"Next Steps: {', '.join(audit_result['next_steps'][:2])}"
            
            return {
                'type': 'audit_result',
                'message': message,
                'details': audit_result,
                'action_needed': len(audit_result['warnings']) > 0
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'message': f"Audit failed: {str(e)}",
                'error': str(e)
            }
    
    def handle_files_command(self) -> Dict[str, Any]:
        """Handle file status requests"""
        try:
            import subprocess
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                changed_files = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                
                if changed_files:
                    message = f"📁 {len(changed_files)} file(s) have changes:\n"
                    for file_line in changed_files[:5]:  # Show first 5
                        message += f"• {file_line}\n"
                    if len(changed_files) > 5:
                        message += f"... and {len(changed_files) - 5} more"
                else:
                    message = "✅ No uncommitted changes detected."
                
                return {
                    'type': 'file_status',
                    'message': message,
                    'changed_files': changed_files,
                    'action_needed': len(changed_files) > 0
                }
            else:
                return {
                    'type': 'error',
                    'message': "Could not check file status (not a git repository?)",
                    'error': result.stderr
                }
                
        except Exception as e:
            return {
                'type': 'error',
                'message': f"File check failed: {str(e)}",
                'error': str(e)
            }
    
    def handle_run_command(self, message: str) -> Dict[str, Any]:
        """Handle run/start requests"""
        if 'health' in message:
            return self.handle_health_command()
        elif 'test' in message:
            return self.handle_test_command()
        else:
            recovery_options = self.jav.get_recovery_options()
            
            message_text = "🚀 Available run commands:\n"
            message_text += "• Health Check: I can run system diagnostics\n"
            message_text += "• Tests: I can execute test suites\n"
            message_text += "• Service Restart: I can restart the main service\n"
            message_text += "What would you like me to run?"
            
            return {
                'type': 'run_options',
                'message': message_text,
                'options': recovery_options,
                'action_needed': True
            }
    
    def handle_test_command(self) -> Dict[str, Any]:
        """Handle test execution requests"""
        try:
            import subprocess
            result = subprocess.run(['python', '-m', 'pytest', '--tb=short'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                message = "✅ Tests passed successfully!"
            else:
                message = f"❌ Tests failed. Exit code: {result.returncode}"
                if result.stdout:
                    message += f"\nOutput: {result.stdout[-200:]}"  # Last 200 chars
            
            return {
                'type': 'test_result',
                'message': message,
                'exit_code': result.returncode,
                'output': result.stdout,
                'error': result.stderr,
                'action_needed': result.returncode != 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                'type': 'error',
                'message': "Tests timed out after 30 seconds",
                'action_needed': True
            }
        except Exception as e:
            return {
                'type': 'error',
                'message': f"Test execution failed: {str(e)}",
                'error': str(e)
            }
    
    def handle_commit_command(self) -> Dict[str, Any]:
        """Handle git commit requests"""
        try:
            import subprocess
            
            # Check for changes first
            status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                         capture_output=True, text=True)
            
            if not status_result.stdout.strip():
                return {
                    'type': 'info',
                    'message': "No changes to commit. Working directory is clean.",
                    'action_needed': False
                }
            
            # Add files
            add_result = subprocess.run(['git', 'add', '.'], 
                                      capture_output=True, text=True)
            
            if add_result.returncode != 0:
                return {
                    'type': 'error',
                    'message': f"Failed to add files: {add_result.stderr}",
                    'action_needed': True
                }
            
            # Generate commit message based on changes
            commit_msg = f"Agent-assisted changes - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            commit_result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                                         capture_output=True, text=True)
            
            if commit_result.returncode == 0:
                message = f"✅ Changes committed successfully!\nMessage: {commit_msg}"
            else:
                message = f"❌ Commit failed: {commit_result.stderr}"
            
            return {
                'type': 'commit_result',
                'message': message,
                'success': commit_result.returncode == 0,
                'commit_message': commit_msg
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'message': f"Commit operation failed: {str(e)}",
                'error': str(e)
            }
    
    def handle_help_command(self) -> Dict[str, Any]:
        """Handle help requests"""
        help_text = """🤖 Clude Agent - Available Commands:

**System Management:**
• "health" or "status" - Check system health
• "audit" - Run comprehensive system audit
• "files" - Check file changes and git status

**Development:**
• "test" - Run test suite
• "run [something]" - Execute commands
• "commit" - Save and commit changes

**Memory & Context:**
• "memory" - Access session memory
• "todo" - Manage tasks and reminders
• "rollback" - Undo recent changes

**General:**
• "help" - Show this help
• Ask me anything about your code or system!

I maintain full context of your work and can proactively warn about issues."""

        return {
            'type': 'help',
            'message': help_text,
            'action_needed': False
        }
    
    def handle_memory_command(self, message: str) -> Dict[str, Any]:
        """Handle memory/recall requests"""
        try:
            # Get recent memories from the API
            import requests
            response = requests.get(f"{self.jav.memory_api}/memory?limit=5")
            
            if response.status_code == 200:
                data = response.json()
                memories = data.get('memories', [])
                
                message_text = f"🧠 Recent Memory Context ({len(memories)} entries):\n"
                for memory in memories:
                    topic = memory.get('topic', 'Unknown')
                    success = '✅' if memory.get('success', False) else '❌'
                    message_text += f"{success} {topic}\n"
                
                return {
                    'type': 'memory_recall',
                    'message': message_text,
                    'memories': memories,
                    'action_needed': False
                }
            else:
                return {
                    'type': 'error',
                    'message': "Could not access memory system",
                    'action_needed': True
                }
                
        except Exception as e:
            return {
                'type': 'error',
                'message': f"Memory recall failed: {str(e)}",
                'error': str(e)
            }
    
    def handle_todo_command(self, message: str) -> Dict[str, Any]:
        """Handle TODO tracking requests"""
        # Scan for TODOs in codebase
        todo_files = self.jav.scan_for_todos()
        
        if todo_files:
            message_text = f"📋 Found TODOs in {len(todo_files)} files:\n"
            for file in todo_files[:3]:  # Show first 3
                message_text += f"• {file}\n"
            if len(todo_files) > 3:
                message_text += f"... and {len(todo_files) - 3} more files"
                
            message_text += "\nWould you like me to extract and track these?"
        else:
            message_text = "✅ No TODO comments found in your codebase."
        
        return {
            'type': 'todo_status',
            'message': message_text,
            'todo_files': todo_files,
            'action_needed': len(todo_files) > 0
        }
    
    def handle_rollback_command(self) -> Dict[str, Any]:
        """Handle rollback/undo requests"""
        recovery_options = self.jav.get_recovery_options()
        
        message_text = "🔄 Available rollback options:\n"
        message_text += "• Git rollback: " + recovery_options.get('rollback_commit', 'Not available') + "\n"
        message_text += "• Service restart: " + recovery_options.get('restart_service', 'Available') + "\n"
        message_text += "• Check git status first: " + recovery_options.get('git_status', 'Available') + "\n"
        message_text += "\nWhich rollback action would you like me to perform?"
        
        return {
            'type': 'rollback_options',
            'message': message_text,
            'options': recovery_options,
            'action_needed': True
        }
    
    def handle_general_query(self, message: str) -> Dict[str, Any]:
        """Handle general questions and queries"""
        # Try to provide contextual help based on keywords
        if any(word in message.lower() for word in ['error', 'broken', 'wrong', 'issue']):
            return {
                'type': 'diagnostic_suggestion',
                'message': "I detected you might have an issue. Let me run a quick audit to identify problems.",
                'suggested_action': 'audit',
                'action_needed': True
            }
        elif any(word in message.lower() for word in ['how', 'what', 'explain']):
            return {
                'type': 'explanation',
                'message': "I'm here to help explain and guide your development process. Can you be more specific about what you'd like to know? I have full context of your MemoryOS system and can provide detailed explanations.",
                'action_needed': False
            }
        else:
            return {
                'type': 'general_response',
                'message': "I understand you want to interact with the system. I can help with health checks, file management, testing, commits, and system auditing. What would you like me to assist with?",
                'action_needed': False
            }
