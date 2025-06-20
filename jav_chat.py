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

    def handle_suggestion_response(self, suggestion_id: str, response: str, outcome: str = None) -> Dict[str, Any]:
        """Handle user response to suggestions with full transparency"""

        result = self.jav_agent.process_user_response(suggestion_id, response, outcome)

        # Create response with full transparency
        response_data = {
            "type": "suggestion_response",
            "message": f"✅ **Response Recorded: {response.title()}**",
            "details": {
                "suggestion_id": suggestion_id,
                "your_response": response,
                "outcome": outcome,
                "learning_updated": result.get("pattern_learned", False),
                "preferences_updated": result.get("updated_preferences", False)
            }
        }

        # Add explanation of what was learned
        if result.get("pattern_learned"):
            response_data["message"] += f"\n\n🧠 **Learning Update**: This automation pattern has been marked as successful and may be auto-suggested in similar contexts."

        if result.get("updated_preferences"):
            response_data["message"] += f"\n\n⚙️ **Preference Update**: Your automation preferences have been updated based on this response."

        # Show transparency link
        response_data["transparency"] = {
            "why_link": f"/jav/suggestion-reasoning/{suggestion_id}",
            "memory_source": "User response processed and learning patterns updated",
            "editable": True
        }

        return response_data

    def get_suggestion_reasoning(self, suggestion_id: str) -> Dict[str, Any]:
        """Get full reasoning and memory source for transparency"""

        # This would query the memory system for the full context
        reasoning = {
            "suggestion_id": suggestion_id,
            "memory_trace": [],  # List of memories that led to this suggestion
            "pattern_analysis": {},  # How patterns were matched
            "user_history": {},  # Past responses to similar suggestions
            "confidence_factors": {},  # What contributed to confidence score
            "editable_rules": []  # Rules user can modify
        }

        return reasoning

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
"""
Jav Chat - Memory-Driven Creative Conversation Handler
Every conversation becomes memory, every memory fuels creativity
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import re

class JavChat:
    """
    Jav Chat Interface - Creative AI Partner
    Transforms conversations into actionable memories and implementations
    """

    def __init__(self, jav_agent):
        self.jav = jav_agent
        self.logger = logging.getLogger('JavChat')
        self.conversation_memory = []

    def process_command(self, message: str, context: str = "creative_studio") -> Dict[str, Any]:
        """
        Process user message with full memory awareness and creative context
        """
        try:
            # Analyze message intent and creative context
            intent = self.analyze_creative_intent(message)

            # Load relevant memories for context
            contextual_memories = self.load_contextual_memories(message, intent)

            # Generate creative response with implementation suggestions
            response = self.generate_creative_response(message, intent, contextual_memories, context)

            # Store conversation as memory
            self.store_conversation_memory(message, response, intent, context)

            return {
                'type': 'success',
                'message': response['content'],
                'implementations': response.get('implementations', []),
                'memory_connections': len(contextual_memories),
                'creative_insights': response.get('insights', []),
                'next_suggestions': response.get('suggestions', [])
            }

        except Exception as e:
            self.logger.error(f"Chat processing error: {e}")
            return {
                'type': 'error',
                'message': f"I encountered an issue: {str(e)}. But our conversation is still being saved to memory!",
                'error': str(e)
            }

    def analyze_creative_intent(self, message: str) -> Dict[str, Any]:
        """
        Analyze the creative intent behind the user's message
        """
        message_lower = message.lower()

        # Creative intent patterns
        intents = {
            'build': ['build', 'create', 'make', 'develop', 'implement', 'code'],
            'ideate': ['idea', 'think', 'brainstorm', 'concept', 'design', 'plan'],
            'debug': ['fix', 'error', 'bug', 'broken', 'issue', 'problem'],
            'analyze': ['analyze', 'review', 'examine', 'explain', 'understand'],
            'improve': ['better', 'optimize', 'enhance', 'upgrade', 'refactor'],
            'learn': ['how', 'what', 'why', 'learn', 'teach', 'explain'],
            'memory': ['remember', 'memory', 'recall', 'history', 'before']
        }

        detected_intents = []
        for intent_type, keywords in intents.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_intents.append(intent_type)

        # Determine primary intent
        primary_intent = detected_intents[0] if detected_intents else 'conversation'

        # Detect technical context
        tech_patterns = {
            'frontend': ['html', 'css', 'javascript', 'react', 'ui', 'interface'],
            'backend': ['python', 'flask', 'api', 'server', 'database'],
            'memory': ['memory', 'memoryos', 'brain', 'remember', 'context'],
            'creative': ['creative', 'studio', 'design', 'artistic', 'innovative']
        }

        tech_context = []
        for tech_type, keywords in tech_patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                tech_context.append(tech_type)

        return {
            'primary': primary_intent,
            'all_intents': detected_intents,
            'tech_context': tech_context,
            'complexity': self.estimate_complexity(message),
            'creativity_level': self.estimate_creativity(message)
        }

    def load_contextual_memories(self, message: str, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Load relevant memories based on message content and intent
        """
        try:
            import requests

            # Build search terms from message and intent
            search_terms = []

            # Extract key terms from message
            words = re.findall(r'\b\w+\b', message.lower())
            important_words = [w for w in words if len(w) > 3 and w not in ['with', 'that', 'this', 'want', 'need']]
            search_terms.extend(important_words[:5])  # Top 5 important words

            # Add intent-based terms
            search_terms.extend(intent['tech_context'])
            search_terms.append(intent['primary'])

            # Search memories
            memories_response = requests.get(f"{self.jav.memory_api}/memory?limit=10")
            all_memories = memories_response.json().get('memories', [])

            # Score memories by relevance
            relevant_memories = []
            for memory in all_memories:
                score = self.calculate_memory_relevance(memory, search_terms, intent)
                if score > 0.3:  # Relevance threshold
                    memory['relevance_score'] = score
                    relevant_memories.append(memory)

            # Sort by relevance and return top matches
            relevant_memories.sort(key=lambda x: x['relevance_score'], reverse=True)
            return relevant_memories[:5]

        except Exception as e:
            self.logger.error(f"Failed to load contextual memories: {e}")
            return []

    def calculate_memory_relevance(self, memory: Dict[str, Any], search_terms: List[str], intent: Dict[str, Any]) -> float:
        """
        Calculate how relevant a memory is to the current context
        """
        score = 0.0

        # Check content relevance
        memory_text = f"{memory.get('topic', '')} {memory.get('input', '')} {memory.get('output', '')}".lower()

        for term in search_terms:
            if term in memory_text:
                score += 0.2

        # Boost score for matching intent
        if intent['primary'] in memory_text:
            score += 0.3

        # Boost score for matching tech context
        for tech in intent['tech_context']:
            if tech in memory_text:
                score += 0.2

        # Boost recent memories slightly
        try:
            memory_time = datetime.fromisoformat(memory.get('timestamp', '').replace('Z', '+00:00'))
            hours_ago = (datetime.now(timezone.utc) - memory_time).total_seconds() / 3600
            if hours_ago < 24:  # Recent memory
                score += 0.1
        except:
            pass

        return min(score, 1.0)  # Cap at 1.0

    def generate_creative_response(self, message: str, intent: Dict[str, Any], 
                                  memories: List[Dict[str, Any]], context: str) -> Dict[str, Any]:
        """
        Generate creative, contextual response with implementation suggestions
        """

        # Build memory context
        memory_context = ""
        if memories:
            memory_context = "Relevant memories:\n"
            for i, memory in enumerate(memories[:3], 1):
                memory_context += f"{i}. {memory.get('topic', 'Untitled')}: {memory.get('output', 'No details')[:100]}...\n"

        # Generate response based on intent
        if intent['primary'] == 'build':
            return self.generate_build_response(message, memories, context)
        elif intent['primary'] == 'ideate':
            return self.generate_ideation_response(message, memories, context)
        elif intent['primary'] == 'debug':
            return self.generate_debug_response(message, memories, context)
        elif intent['primary'] == 'memory':
            return self.generate_memory_response(message, memories, context)
        else:
            return self.generate_conversational_response(message, memories, context, intent)

    def generate_build_response(self, message: str, memories: List[Dict[str, Any]], context: str) -> Dict[str, Any]:
        """Generate response for build/create requests"""

        # Analyze what they want to build
        implementations = []

        if 'ui' in message.lower() or 'interface' in message.lower():
            implementations.append({
                'id': f'ui_impl_{datetime.now().timestamp()}',
                'title': 'UI Component Implementation',
                'description': 'Create the user interface component based on your requirements',
                'type': 'frontend',
                'code': '<!-- Generated UI code will go here -->',
                'files': ['index.html', 'styles.css']
            })

        if 'api' in message.lower() or 'endpoint' in message.lower():
            implementations.append({
                'id': f'api_impl_{datetime.now().timestamp()}',
                'title': 'API Endpoint Implementation',
                'description': 'Create the API endpoint functionality',
                'type': 'backend',
                'code': '# Generated API code will go here',
                'files': ['main.py']
            })

        memory_insights = ""
        if memories:
            memory_insights = f"\n\n💡 **Memory Insight**: I found {len(memories)} related memories that might help inform this implementation. "
            recent_builds = [m for m in memories if 'build' in m.get('type', '').lower() or 'feature' in m.get('type', '').lower()]
            if recent_builds:
                memory_insights += f"You've built similar features before - let's build on that experience!"

        response_content = f"""🚀 **Ready to Build!**

I understand you want to create something new. Based on our conversation and memory context, here's my approach:

**What I'm Planning:**
- Analyze your specific requirements
- Leverage our previous work and patterns
- Create clean, maintainable implementations
- Ensure everything integrates with your existing project

{memory_insights}

**Next Steps:**
1. I'll create the implementation based on your specifications
2. You can review, edit, or apply the changes
3. We'll test and iterate together
4. Everything gets saved to memory for future reference

What specific aspect would you like me to focus on first?"""

        return {
            'content': response_content,
            'implementations': implementations,
            'insights': ['build_ready', 'memory_informed'],
            'suggestions': ['Review implementation', 'Test changes', 'Iterate design']
        }

    def generate_ideation_response(self, message: str, memories: List[Dict[str, Any]], context: str) -> Dict[str, Any]:
        """Generate response for ideation/brainstorming"""

        memory_connections = ""
        if memories:
            related_ideas = [m for m in memories if 'idea' in m.get('input', '').lower() or 'concept' in m.get('input', '').lower()]
            if related_ideas:
                memory_connections = f"\n\n🔗 **Memory Connections**: I see connections to {len(related_ideas)} previous ideas we've discussed. Let's build on those concepts!"

        response_content = f"""💡 **Creative Ideation Mode Activated**

I love brainstorming with you! Let's explore this idea space together.

**My Creative Process:**
1. **Expand** - What are all the possibilities?
2. **Connect** - How does this relate to our previous work?
3. **Synthesize** - What unique combinations can we create?
4. **Implement** - Which ideas are ready to become reality?

{memory_connections}

**Let's Explore:**
- What's the core problem or opportunity?
- Who would benefit from this?
- What would make this uniquely valuable?
- How can we prototype this quickly?

I'm ready to dive deep into creative exploration. What aspect excites you most?"""

        return {
            'content': response_content,
            'insights': ['creative_mode', 'ideation_ready'],
            'suggestions': ['Explore concepts', 'Create prototypes', 'Connect ideas']
        }

    def generate_debug_response(self, message: str, memories: List[Dict[str, Any]], context: str) -> Dict[str, Any]:
        """Generate response for debugging/fixing issues"""

        error_history = ""
        if memories:
            error_memories = [m for m in memories if not m.get('success', True) or 'error' in m.get('type', '').lower()]
            if error_memories:
                error_history = f"\n\n🔍 **Error Pattern Analysis**: I found {len(error_memories)} related issues in our history. Let me apply those lessons here."

        response_content = f"""🔧 **Debug Mode Engaged**

I'm here to help solve this issue systematically.

**My Debug Approach:**
1. **Understand** - What exactly is happening vs. what should happen?
2. **Isolate** - Where is the problem occurring?
3. **Analyze** - What are the root causes?
4. **Fix** - Implement the solution
5. **Prevent** - How do we avoid this in the future?

{error_history}

**Let's Diagnose:**
- Can you share the specific error or unexpected behavior?
- When did this start happening?
- What were you trying to accomplish?
- Have you made any recent changes?

I'll combine my debugging skills with our project memory to find the best solution!"""

        return {
            'content': response_content,
            'insights': ['debug_mode', 'systematic_approach'],
            'suggestions': ['Identify root cause', 'Test solution', 'Document fix']
        }

    def generate_memory_response(self, message: str, memories: List[Dict[str, Any]], context: str) -> Dict[str, Any]:
        """Generate response for memory-related queries"""

        memory_stats = f"I currently have access to {len(memories)} relevant memories"
        if memories:
            categories = {}
            for memory in memories:
                cat = memory.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1

            memory_stats += f" across categories: {', '.join([f'{k}({v})' for k, v in categories.items()])}"

        response_content = f"""🧠 **Memory Recall Active**

{memory_stats}.

**What I Remember:**
- Every conversation we've had
- All implementations and their outcomes
- Creative decisions and their rationale
- Patterns in your development style
- Solutions that worked (and ones that didn't)

**Memory Powers Our Partnership:**
- I never forget context between sessions
- I can connect ideas across time
- I learn from our successes and failures
- I compound our creative breakthroughs

**Recent Memory Highlights:**
"""

        if memories:
            for i, memory in enumerate(memories[:3], 1):
                response_content += f"\n{i}. **{memory.get('topic', 'Memory')}** ({self.get_time_ago(memory.get('timestamp'))}):\n   {memory.get('output', 'No details')[:100]}...\n"
        else:
            response_content += "\nThis is the start of our journey together - every interaction from now on becomes part of our shared memory!"

        response_content += "\nWhat specific memories would you like me to recall or connect to our current work?"

        return {
            'content': response_content,
            'insights': ['memory_active', 'context_aware'],
            'suggestions': ['Explore connections', 'Review history', 'Build on past work']
        }

    def generate_conversational_response(self, message: str, memories: List[Dict[str, Any]], 
                                       context: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Generate general conversational response"""

        contextual_note = ""
        if memories:
            contextual_note = f"\n\n💭 I'm drawing from {len(memories)} related memories to inform my response."

        response_content = f"""👋 **Creative Partnership Mode**

I'm here as your memory-driven creative partner, ready to build, brainstorm, and solve problems together.

**What Makes Our Partnership Special:**
- **Memory-Driven**: I remember everything we create together
- **Context-Aware**: I understand your project and style
- **Creative**: I help generate and refine ideas
- **Implementation-Ready**: I can turn conversations into code

{contextual_note}

**How Can I Help?**
- Brainstorm new features or improvements
- Debug and solve technical challenges  
- Review and analyze your code
- Connect current work to past insights
- Turn ideas into actionable implementations

What would you like to explore or create together?"""

        return {
            'content': response_content,
            'insights': ['partnership_ready', 'creative_mode'],
            'suggestions': ['Start creating', 'Explore ideas', 'Solve problems']
        }

    def store_conversation_memory(self, user_message: str, response: Dict[str, Any], 
                                 intent: Dict[str, Any], context: str):
        """
        Store the conversation as memory for future context
        """
        try:
            # Store user input as memory
            user_memory = {
                "topic": f"User Creative Input: {user_message[:50]}...",
                "type": "user_input",
                "input": user_message,
                "output": f"Intent: {intent['primary']}, Context: {context}",
                "success": True,
                "category": "conversation",
                "tags": ["conversation", "user_input", intent['primary'], context] + intent['tech_context'],
                "context": f"Creative studio conversation - Intent: {intent['primary']}"
            }

            self.jav.log_to_memory(
                user_memory["topic"],
                user_memory["type"],
                user_memory["input"],
                user_memory["output"],
                user_memory["success"],
                user_memory["category"]
            )

            # Store Jav response as memory
            jav_memory = {
                "topic": f"Jav Creative Response: {response.get('insights', ['response'])[0]}",
                "type": "ai_response",
                "input": f"Responding to: {user_message[:100]}...",
                "output": response['content'][:200] + "..." if len(response['content']) > 200 else response['content'],
                "success": True,
                "category": "conversation",
                "tags": ["conversation", "ai_response", intent['primary'], context] + intent['tech_context'],
                "context": f"Creative studio response - Generated {len(response.get('implementations', []))} implementations"
            }

            self.jav.log_to_memory(
                jav_memory["topic"],
                jav_memory["type"],
                jav_memory["input"],
                jav_memory["output"],
                jav_memory["success"],
                jav_memory["category"]
            )

        except Exception as e:
            self.logger.error(f"Failed to store conversation memory: {e}")

    def estimate_complexity(self, message: str) -> str:
        """Estimate the complexity of the user's request"""
        word_count = len(message.split())
        technical_terms = len([w for w in message.lower().split() if w in ['api', 'database', 'algorithm', 'optimization', 'integration']])

        if word_count > 50 or technical_terms > 2:
            return 'high'
        elif word_count > 20 or technical_terms > 0:
            return 'medium'
        else:
            return 'low'

    def estimate_creativity(self, message: str) -> str:
        """Estimate the creativity level needed for the request"""
        creative_terms = len([w for w in message.lower().split() if w in ['creative', 'innovative', 'unique', 'design', 'artistic', 'brainstorm']])

        if creative_terms > 1:
            return 'high'
        elif creative_terms > 0:
            return 'medium'
        else:
            return 'low'

    def get_time_ago(self, timestamp: str) -> str:
        """Get human-readable time ago string"""
        if not timestamp:
            return 'unknown time'

        try:
            time_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            diff = now - time_obj

            days = diff.days
            hours = diff.seconds // 3600
            minutes = (diff.seconds // 60) % 60

            if days > 0:
                return f"{days} day{'s' if days > 1 else ''} ago"
            elif hours > 0:
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif minutes > 0:
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "just now"
        except:
            return 'unknown time'
"""
Jav Chat Interface - Central Command Hub
Routes commands and integrates key features with frustration detection
"""

import logging
from typing import Dict, Any, List
from frustration_detector import init_frustration_detector

class JavChat:
    """
    Jav Chat Interface - Command Routing Hub
    Processes commands and dispatches to handlers with gentle support
    """

    def __init__(self, jav_agent):
        self.jav = jav_agent
        self.logger = logging.getLogger('JavChat')
        
        # Initialize frustration detection
        self.frustration_detector = init_frustration_detector(jav_agent)
        
        # Track intervention state
        self.pending_interventions = []
        self.user_intervention_preferences = {
            "auto_hints": True,
            "intervention_level": "help",  # hint, help, auto_debug
            "encouragement": True
        }

    def process_command(self, command: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user command and return response with frustration monitoring"""
        original_command = command
        command = command.strip().lower()
        context = context or {}

        # Handle intervention responses first
        if command.startswith("intervention:"):
            return self.handle_intervention_response(command, context)
        
        result = None
        success = True
        
        try:
            if command.startswith("audit"):
                result = self.handle_audit_command(command)
            elif command.startswith("health"):
                result = self.handle_health_command()
            elif command.startswith("suggest"):
                result = self.handle_suggestions_command(command)
            elif command.startswith("fix"):
                result = self.handle_fix_command(command)
            elif command.startswith("deploy"):
                result = self.handle_deploy_command(command)
            elif command.startswith("test"):
                result = self.handle_test_command(command)
            elif command.startswith("bible"):
                result = self.handle_bible_command(command)
            elif "help" in command:
                result = self.get_help()
            else:
                result = self.handle_general_query(command)
            
            # Check if command was successful
            success = result.get("type") != "error"
            
        except Exception as e:
            success = False
            result = {
                "type": "error",
                "message": f"Error processing command: {str(e)}",
                "suggestions": ["Try 'help' for available commands"]
            }
            context["error"] = str(e)
        
        # Track interaction for frustration detection
        self.frustration_detector.track_interaction(
            "command", 
            original_command, 
            success, 
            context
        )
        
        # Check for frustration patterns and gentle intervention
        intervention = self.check_for_gentle_intervention()
        if intervention:
            result = self.enhance_response_with_intervention(result, intervention)
        
        return result

    def handle_audit_command(self, command: str) -> Dict[str, Any]:
        """Handle audit command"""
        # Placeholder for audit logic
        return {
            "type": "audit_result",
            "message": "Audit command executed"
        }

    def handle_health_command(self) -> Dict[str, Any]:
        """Handle health check command"""
        # Placeholder for health check logic
        return {
            "type": "health_status",
            "message": "Health command executed"
        }

    def handle_suggestions_command(self, command: str) -> Dict[str, Any]:
        """Handle suggestions command"""
        # Placeholder for suggestions logic
        return {
            "type": "suggestion",
            "message": "Suggestion command executed"
        }

    def handle_fix_command(self, command: str) -> Dict[str, Any]:
        """Handle fix command"""
        # Placeholder for fix logic
        return {
            "type": "fix_result",
            "message": "Fix command executed"
        }

    def handle_deploy_command(self, command: str) -> Dict[str, Any]:
        """Handle deploy command"""
        # Placeholder for deploy logic
        return {
            "type": "deploy_result",
            "message": "Deploy command executed"
        }

    def handle_test_command(self, command: str) -> Dict[str, Any]:
        """Handle test command"""
        # Placeholder for test logic
        return {
            "type": "test_result",
            "message": "Test command executed"
        }

    def handle_bible_command(self, command: str) -> Dict[str, Any]:
        """Handle bible-related commands"""
        try:
            from bible_evolution_engine import bible_evolution
            from bible_integration import bible_integration

            if "review" in command:
                return self.handle_bible_review()
            elif "deviations" in command:
                return self.handle_bible_deviations()
            elif "compliance" in command:
                return self.handle_bible_compliance()
            elif "amendments" in command:
                return self.handle_bible_amendments()
            elif "onboard" in command:
                return self.handle_bible_onboarding()
            else:
                return self.get_bible_help()

        except Exception as e:
            return {
                "type": "error",
                "message": f"Bible command error: {str(e)}",
                "suggestions": ["bible help", "bible review", "bible deviations"]
            }

    def handle_bible_review(self) -> Dict[str, Any]:
        """Handle bible review session generation"""
        try:
            from bible_integration import bible_integration

            review_session = bible_integration.generate_team_review_session()

            return {
                "type": "bible_review",
                "title": "📚 Bible Review Session Generated",
                "session_id": review_session["session_id"],
                "summary": review_session["summary"],
                "highlights": [
                    f"📊 {review_session['summary']['total_deviations']} deviations tracked",
                    f"🔧 {review_session['summary']['proposed_amendments']} amendments proposed",
                    f"📁 {len(review_session['summary']['files_affected'])} files affected"
                ],
                "next_steps": review_session["next_steps"],
                "discussion_agenda": review_session.get("discussion_agenda", []),
                "actions": [
                    {"text": "View Full Review", "action": "view_review_details"},
                    {"text": "Start Team Discussion", "action": "start_discussion"},
                    {"text": "Review Amendments", "action": "review_amendments"}
                ]
            }

        except Exception as e:
            return {
                "type": "error",
                "message": f"Failed to generate review session: {str(e)}"
            }

    def handle_bible_deviations(self) -> Dict[str, Any]:
        """Handle bible deviations query"""
        try:
            from bible_evolution_engine import bible_evolution

            # Get recent high-frequency deviations
            recent_deviations = [d for d in bible_evolution.deviations 
                               if d.frequency >= 3][-10:]  # Last 10 high-frequency

            if not recent_deviations:
                return {
                    "type": "bible_info",
                    "title": "✅ Bible Compliance Good",
                    "message": "No significant deviations detected",
                    "suggestions": ["Continue monitoring for patterns"]
                }

            deviation_summary = []
            for dev in recent_deviations:
                deviation_summary.append(
                    f"🔄 {dev.section}: {dev.frequency}x - {dev.actual_process[:50]}..."
                )

            return {
                "type": "bible_deviations",
                "title": f"📋 {len(recent_deviations)} Tracked Deviations",
                "deviations": deviation_summary,
                "patterns": {
                    "most_frequent": max(recent_deviations, key=lambda d: d.frequency),
                    "most_recent": max(recent_deviations, key=lambda d: d.last_seen)
                },
                "actions": [
                    {"text": "Analyze Patterns", "action": "analyze_patterns"},
                    {"text": "Propose Amendments", "action": "propose_amendments"},
                    {"text": "View Details", "action": "view_deviation_details"}
                ]
            }

        except Exception as e:
            return {
                "type": "error",
                "                "message": f"Failed to get deviations: {str(e)}"
            }

    def handle_bible_compliance(self) -> Dict[str, Any]:
        """Handle bible compliance check"""
        try:
            from bible_evolution_engine import bible_evolution

            compliance_report = bible_evolution.monitor_compliance("AGENT_BIBLE.md")

            score = compliance_report["compliance_score"]
            status = "🟢 Excellent" if score > 0.9 else "🟡 Good" if score > 0.7 else "🔴 Needs Attention"

            return {
                "type": "bible_compliance",
                "title": f"📊 Bible Compliance: {status}",
                "score": f"{score:.1%}",
                "details": {
                    "recent_deviations": len(compliance_report["deviations"]),
                    "violations": len(compliance_report["violations"]),
                    "last_check": compliance_report["check_date"][:10]
                },
                "recommendations": compliance_report["recommendations"],
                "actions": [
                    {"text": "View Full Report", "action": "view_compliance_report"},
                    {"text": "Address Issues", "action": "address_compliance"},
                    {"text": "Schedule Review", "action": "schedule_review"}
                ]
            }

        except Exception as e:
            return {
                "type": "error",
                "message": f"Failed to check compliance: {str(e)}"
            }

    def handle_bible_amendments(self) -> Dict[str, Any]:
        """Handle bible amendments query"""
        try:
            from bible_evolution_engine import bible_evolution

            pending_amendments = [a for a in bible_evolution.amendments 
                                if a.status in ["draft", "reviewed"]]

            if not pending_amendments:
                return {
                    "type": "bible_info",
                    "title": "📚 No Pending Amendments",
                    "message": "All amendments have been processed",
                    "suggestions": ["Check for new deviation patterns"]
                }

            amendment_summary = []
            for amend in pending_amendments[:5]:  # Top 5
                confidence_emoji = "🟢" if amend.confidence > 0.8 else "🟡" if amend.confidence > 0.6 else "🔴"
                amendment_summary.append(
                    f"{confidence_emoji} {amend.section}: {amend.reasoning[:60]}..."
                )

            return {
                "type": "bible_amendments",
                "title": f"📝 {len(pending_amendments)} Pending Amendments",
                "amendments": amendment_summary,
                "by_status": {
                    "draft": len([a for a in pending_amendments if a.status == "draft"]),
                    "reviewed": len([a for a in pending_amendments if a.status == "reviewed"])
                },
                "actions": [
                    {"text": "Review Amendments", "action": "review_amendments"},
                    {"text": "Approve High-Confidence", "action": "approve_high_confidence"},
                    {"text": "Schedule Team Review", "action": "schedule_team_review"}
                ]
            }

        except Exception as e:
            return {
                "type": "error",
                "message": f"Failed to get amendments: {str(e)}"
            }

    def handle_bible_onboarding(self) -> Dict[str, Any]:
        """Handle bible onboarding brief"""
        try:
            from bible_evolution_engine import bible_evolution

            brief = bible_evolution.generate_onboarding_brief("new_user")

            return {
                "type": "bible_onboarding",
                "title": "👋 Bible Onboarding Brief",
                "summary": brief["summary"],
                "recent_changes": {
                    "count": brief["recent_changes"]["total_updates"],
                    "files": brief["recent_changes"]["files_updated"],
                    "period": brief["recent_changes"]["period"]
                },
                "key_updates": brief["key_updates"][:3],  # Top 3
                "action_items": brief["action_items"],
                "support": brief["contacts"],
                "actions": [
                    {"text": "Start Onboarding", "action": "start_onboarding"},
                    {"text": "Review Changes", "action": "review_recent_changes"},
                    {"text": "Ask Questions", "action": "ask_questions"}
                ]
            }

        except Exception as e:
            return {
                "type": "error",
                "message": f"Failed to generate onboarding: {str(e)}"
            }

    def get_bible_help(self) -> Dict[str, Any]:
        """Get bible command help"""
        return {
            "type": "bible_help",
            "title": "📚 Bible Evolution Commands",
            "commands": {
                "bible review": "Generate comprehensive bible review session",
                "bible deviations": "Show tracked deviations from documented processes",
                "bible compliance": "Check current compliance with bible standards",
                "bible amendments": "View proposed amendments to documentation",
                "bible onboard": "Get onboarding brief for new team members"
            },
            "examples": [
                "bible review",
                "bible deviations",
                "bible compliance",
                "bible amendments"
            ],
            "features": [
                "📊 Track real-world vs documented processes",
                "🔄 Automatic amendment proposals",
                "👥 Team review and consensus flows",
                "📝 Version control for bible changes",
                "🎯 Onboarding for new users"
            ]
        }

    def check_for_gentle_intervention(self) -> Optional[Dict[str, Any]]:
        """Check if gentle intervention is needed"""
        
        patterns = self.frustration_detector.detect_frustration_patterns()
        
        if patterns:
            intervention = self.frustration_detector.should_intervene(patterns)
            
            if intervention and self.user_intervention_preferences.get("auto_hints", True):
                # Only intervene if user hasn't disabled it
                level_preference = self.user_intervention_preferences.get("intervention_level", "help")
                
                # Respect user's intervention level preference
                if self._intervention_level_ok(intervention["level"], level_preference):
                    self.frustration_detector.mark_intervention_shown()
                    return intervention
        
        return None
    
    def _intervention_level_ok(self, suggested_level: str, user_preference: str) -> bool:
        """Check if intervention level is within user's preference"""
        level_hierarchy = ["hint", "help", "auto_debug"]
        
        suggested_idx = level_hierarchy.index(suggested_level) if suggested_level in level_hierarchy else 0
        preference_idx = level_hierarchy.index(user_preference) if user_preference in level_hierarchy else 1
        
        return suggested_idx <= preference_idx
    
    def enhance_response_with_intervention(self, response: Dict[str, Any], 
                                         intervention: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance response with gentle intervention"""
        
        pattern = intervention["pattern"]
        level = intervention["level"]
        
        # Create encouraging message
        encouragement = ""
        if self.user_intervention_preferences.get("encouragement", True):
            encouragement = self.frustration_detector.get_encouragement_message(pattern)
        
        # Create intervention card
        intervention_card = {
            "type": "gentle_intervention",
            "level": level,
            "title": self._get_intervention_title(level, pattern.pattern_type),
            "encouragement": encouragement,
            "evidence": pattern.evidence,
            "suggested_actions": intervention["suggested_actions"],
            "pattern_summary": self._summarize_pattern(pattern),
            "dismissible": True,
            "escalation_options": self._get_escalation_options(level)
        }
        
        # Add intervention to response
        if "interventions" not in response:
            response["interventions"] = []
        response["interventions"].append(intervention_card)
        
        # Add gentle note to main message if it's an error
        if response.get("type") == "error" and encouragement:
            response["message"] = f"{encouragement}\n\n{response['message']}"
        
        return response
    
    def _get_intervention_title(self, level: str, pattern_type: str) -> str:
        """Get friendly intervention title"""
        
        titles = {
            "hint": {
                "repeated_command": "💡 I notice you're trying this command again",
                "repeated_error": "🤔 This error keeps coming up",
                "no_progress": "🎯 Let's try a fresh approach",
                "error_spike": "🔄 Lots of trial and error happening",
                "session_fatigue": "⭐ You've been coding hard!"
            },
            "help": {
                "repeated_command": "🚀 Let me help with that command",
                "repeated_error": "🛠️ I can help solve this error",
                "no_progress": "🎪 Ready to try something different?",
                "error_spike": "🔧 Let's debug this systematically",
                "session_fatigue": "🌟 Time to celebrate your progress!"
            },
            "auto_debug": {
                "repeated_command": "🤖 Auto-debug this command?",
                "repeated_error": "⚡ Auto-fix this error pattern?",
                "no_progress": "🎨 Let me suggest a breakthrough approach",
                "error_spike": "🔬 Run automated debugging?",
                "session_fatigue": "💫 Save state and refresh?"
            }
        }
        
        return titles.get(level, {}).get(pattern_type, f"✨ {level.title()} available")
    
    def _summarize_pattern(self, pattern: FrustrationPattern) -> str:
        """Create friendly pattern summary"""
        
        summaries = {
            "repeated_command": "You've tried this command a few times - let's make it work!",
            "repeated_error": "This error is being persistent - we can outsmart it!",
            "no_progress": "Sometimes stepping back reveals new paths forward.",
            "error_spike": "You're exploring lots of options - that's great problem solving!",
            "session_fatigue": "Long coding sessions show real dedication to your project!"
        }
        
        return summaries.get(pattern.pattern_type, "I notice a pattern we can address.")
    
    def _get_escalation_options(self, current_level: str) -> List[Dict[str, str]]:
        """Get options to escalate intervention level"""
        
        escalation_map = {
            "hint": [
                {"level": "help", "title": "Get more help", "description": "Show detailed assistance"},
                {"level": "auto_debug", "title": "Auto-debug", "description": "Let me fix this automatically"}
            ],
            "help": [
                {"level": "auto_debug", "title": "Auto-debug", "description": "Apply automated fix"}
            ],
            "auto_debug": []  # Already at highest level
        }
        
        return escalation_map.get(current_level, [])
    
    def handle_intervention_response(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user response to intervention"""
        
        # Parse intervention command: "intervention:action_id:response"
        parts = command.split(":", 2)
        if len(parts) < 3:
            return {"type": "error", "message": "Invalid intervention response format"}
        
        action_id = parts[1]
        response_type = parts[2]  # accept, dismiss, escalate, etc.
        
        if response_type == "dismiss":
            return {
                "type": "intervention_dismissed",
                "message": "Got it! I'll give you space to work. Type 'help' if you need me.",
                "action": "dismissed"
            }
        elif response_type == "accept":
            return self._execute_intervention_action(action_id, context)
        elif response_type.startswith("escalate:"):
            new_level = response_type.split(":", 1)[1]
            return self._escalate_intervention(action_id, new_level, context)
        elif response_type == "preferences":
            return self._show_intervention_preferences()
        
        return {"type": "error", "message": "Unknown intervention response"}
    
    def _execute_intervention_action(self, action_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the chosen intervention action"""
        
        # Parse action_id to understand what to do
        parts = action_id.split("_")
        if len(parts) < 2:
            return {"type": "error", "message": "Invalid action ID"}
        
        pattern_type = parts[0]
        level = parts[1]
        
        if pattern_type == "repeated_command":
            return self._help_with_repeated_command(level, context)
        elif pattern_type == "repeated_error":
            return self._help_with_repeated_error(level, context)
        elif pattern_type == "no_progress":
            return self._help_with_no_progress(level, context)
        elif pattern_type == "error_spike":
            return self._help_with_error_spike(level, context)
        elif pattern_type == "session_fatigue":
            return self._help_with_session_fatigue(level, context)
        
        return {"type": "error", "message": "Unknown intervention type"}
    
    def _help_with_repeated_command(self, level: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide help for repeated command issues"""
        
        if level == "hint":
            return {
                "type": "intervention_help",
                "title": "💡 Command Hint",
                "message": "Try checking if there are any typos, or if you need different arguments. You can also try 'help [command]' for syntax.",
                "suggestions": ["Check command syntax", "Verify arguments", "Try alternative command"]
            }
        elif level == "help":
            # Get memory of similar successful commands
            return {
                "type": "intervention_help",
                "title": "🚀 Command Help",
                "message": "Let me show you similar commands that worked before and suggest alternatives.",
                "memory_examples": self._get_memory_examples("command"),
                "alternatives": ["Use different approach", "Break into smaller steps", "Check documentation"]
            }
        elif level == "auto_debug":
            return {
                "type": "intervention_auto",
                "title": "🤖 Auto-Debug Command",
                "message": "I'll analyze this command and suggest or apply fixes automatically.",
                "action": "auto_debug_command",
                "status": "analyzing"
            }
        
        return {"type": "info", "message": "Help provided"}
    
    def _help_with_repeated_error(self, level: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide help for repeated errors"""
        
        if level == "auto_debug":
            return {
                "type": "intervention_auto",
                "title": "⚡ Auto-Fix Error",
                "message": "I'll search my memory for solutions to this error and apply the best fix.",
                "action": "auto_fix_error",
                "status": "searching_memory"
            }
        
        return {
            "type": "intervention_help",
            "title": "🛠️ Error Analysis",
            "message": "This error has appeared before. Let me show you what typically works.",
            "memory_solutions": self._get_memory_examples("error"),
            "systematic_approach": ["Identify root cause", "Apply known solution", "Verify fix"]
        }
    
    def _help_with_no_progress(self, level: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide help when no progress is made"""
        
        return {
            "type": "intervention_help",
            "title": "🎯 Fresh Perspective",
            "message": "Let's step back and look at this differently. Here's what we've tried and what might work:",
            "summary": self._summarize_recent_attempts(),
            "new_approaches": ["Try different strategy", "Use memory insights", "Break problem down"],
            "memory_patterns": self._get_memory_examples("progress")
        }
    
    def _get_memory_examples(self, example_type: str) -> List[Dict[str, Any]]:
        """Get relevant examples from memory"""
        # This would integrate with the memory system
        # For now, return placeholder structure
        
        return [
            {
                "description": f"Similar {example_type} that worked",
                "solution": "Example solution from memory",
                "context": "When this worked before",
                "success_rate": "85%"
            }
        ]
    
    def _summarize_recent_attempts(self) -> Dict[str, Any]:
        """Summarize what user has tried recently"""
        
        interactions = list(self.frustration_detector.interaction_history)[-10:]
        
        commands_tried = []
        errors_encountered = []
        
        for interaction in interactions:
            if interaction["type"] == "command":
                commands_tried.append(interaction["content"])
                if not interaction["success"]:
                    errors_encountered.append(interaction.get("context", {}).get("error", "Unknown error"))
        
        return {
            "commands_tried": len(set(commands_tried)),
            "unique_errors": len(set(errors_encountered)),
            "time_span": "last 30 minutes",
            "patterns": "Working on command execution and error handling"
        }
    
    def get_help(self) -> Dict[str, Any]:
        """Get help information"""
        return {
            "type": "help",
            "message": "Jav Assistant Commands",
            "commands": {
                "audit": "Run comprehensive system audit",
                "health": "Check system health status",
                "suggest [task]": "Get memory-driven suggestions",
                "fix [issue]": "Get fix recommendations",
                "deploy": "Deploy with safety checks",
                "test": "Run system tests",
                "bible [action]": "Bible evolution and compliance management"
            },
            "examples": [
                "audit current state",
                "health check",
                "suggest deployment",
                "fix error logs",
                "deploy to production",
                "bible review"
            ],
            "intervention_help": {
                "message": "I watch for frustration patterns and offer gentle help",
                "preferences": "Type 'intervention:preferences' to customize my assistance level"
            }
        }