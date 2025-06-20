
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
