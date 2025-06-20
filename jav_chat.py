
"""
Jav Chat Interface
Builder-in-chat with code editor, terminal, and preview panes
"""

import asyncio
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import re

class JavChat:
    """
    Chat interface for Jav with integrated builder capabilities
    """
    
    def __init__(self, jav_agent):
        self.jav = jav_agent
        self.chat_history = []
        self.current_files = {}
        self.terminal_output = []
        self.active_processes = []
        
    def process_command(self, command: str) -> Dict[str, Any]:
        """Process natural language commands"""
        command = command.strip().lower()
        
        # Command routing
        if command.startswith(('@jav', 'jav,', 'jav ')):
            return self.handle_jav_command(command)
        elif command.startswith(('run ', 'execute ', 'cmd ')):
            return self.handle_terminal_command(command)
        elif command.startswith(('edit ', 'open ', 'show ')):
            return self.handle_file_command(command)
        elif command.startswith(('health', 'status', 'check')):
            return self.handle_health_command()
        elif command.startswith(('deploy', 'rollback', 'restart')):
            return self.handle_deployment_command(command)
        else:
            return self.handle_chat_command(command)
    
    def handle_jav_command(self, command: str) -> Dict[str, Any]:
        """Handle direct Jav agent commands"""
        # Remove jav prefix
        clean_command = re.sub(r'^@?jav[,\s]*', '', command, flags=re.IGNORECASE)
        
        if 'audit' in clean_command or 'check' in clean_command:
            return self.run_audit()
        elif 'health' in clean_command:
            return self.run_health_checks()
        elif 'rollback' in clean_command:
            return self.show_rollback_options()
        elif 'logs' in clean_command:
            return self.show_logs()
        elif 'files' in clean_command or 'changes' in clean_command:
            return self.show_file_changes()
        elif 'processes' in clean_command:
            return self.show_processes()
        else:
            return self.show_help()
    
    def handle_terminal_command(self, command: str) -> Dict[str, Any]:
        """Execute terminal commands"""
        # Extract actual command
        cmd = re.sub(r'^(run|execute|cmd)\s+', '', command)
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            
            self.terminal_output.append({
                "command": cmd,
                "output": output,
                "return_code": result.returncode,
                "timestamp": datetime.now().isoformat()
            })
            
            # Log significant commands to memory
            if any(keyword in cmd for keyword in ['deploy', 'test', 'build', 'git']):
                self.jav.log_to_memory(
                    topic=f"Terminal Command: {cmd}",
                    type_="SystemUpdate",
                    input_=cmd,
                    output=output,
                    success=result.returncode == 0,
                    category="terminal"
                )
            
            return {
                "type": "terminal",
                "command": cmd,
                "output": output,
                "success": result.returncode == 0,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "type": "error",
                "message": f"Command timed out: {cmd}"
            }
        except Exception as e:
            return {
                "type": "error",
                "message": f"Command failed: {str(e)}"
            }
    
    def handle_file_command(self, command: str) -> Dict[str, Any]:
        """Handle file operations"""
        # Extract filename
        filename_match = re.search(r'(?:edit|open|show)\s+(\S+)', command)
        if not filename_match:
            return {"type": "error", "message": "Please specify a filename"}
        
        filename = filename_match.group(1)
        
        try:
            if Path(filename).exists():
                with open(filename, 'r') as f:
                    content = f.read()
                
                self.current_files[filename] = {
                    "content": content,
                    "last_modified": datetime.now().isoformat(),
                    "size": len(content)
                }
                
                return {
                    "type": "file",
                    "filename": filename,
                    "content": content,
                    "size": len(content),
                    "lines": len(content.split('\n'))
                }
            else:
                return {
                    "type": "error",
                    "message": f"File not found: {filename}"
                }
                
        except Exception as e:
            return {
                "type": "error",
                "message": f"Error reading file: {str(e)}"
            }
    
    def handle_health_command(self) -> Dict[str, Any]:
        """Handle health check commands"""
        return self.run_health_checks()
    
    def handle_deployment_command(self, command: str) -> Dict[str, Any]:
        """Handle deployment-related commands"""
        if 'deploy' in command:
            return self.run_pre_deploy_checks()
        elif 'rollback' in command:
            return self.show_rollback_options()
        elif 'restart' in command:
            return self.restart_service()
        else:
            return {"type": "error", "message": "Unknown deployment command"}
    
    def handle_chat_command(self, command: str) -> Dict[str, Any]:
        """Handle general chat commands"""
        # Simple pattern matching for common dev questions
        if any(word in command for word in ['error', 'bug', 'broken', 'issue']):
            return self.diagnose_issues()
        elif any(word in command for word in ['next', 'todo', 'should']):
            return self.suggest_next_steps()
        elif any(word in command for word in ['summary', 'status', 'what']):
            return self.get_status_summary()
        else:
            return {
                "type": "chat",
                "message": f"I understand you said: '{command}'. How can I help with your development work?",
                "suggestions": [
                    "Run health checks",
                    "Show file changes",
                    "Check system status",
                    "View recent logs"
                ]
            }
    
    def run_audit(self) -> Dict[str, Any]:
        """Run comprehensive audit"""
        audit_result = asyncio.run(self.jav.audit_current_state())
        
        return {
            "type": "audit",
            "data": audit_result,
            "summary": f"Audit complete: {len(audit_result['warnings'])} warnings, {len(audit_result['suggestions'])} suggestions"
        }
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run health checks"""
        health_result = self.jav.run_health_checks()
        
        return {
            "type": "health",
            "data": health_result,
            "summary": f"Health check {health_result['summary']}: {len(health_result['passed'])} passed, {len(health_result['failed'])} failed"
        }
    
    def show_rollback_options(self) -> Dict[str, Any]:
        """Show available rollback options"""
        recovery_options = self.jav.get_recovery_options()
        
        return {
            "type": "recovery",
            "options": recovery_options,
            "message": "Available recovery options:"
        }
    
    def show_logs(self) -> Dict[str, Any]:
        """Show recent logs"""
        try:
            with open('memoryos.log', 'r') as f:
                lines = f.readlines()
            
            recent_logs = lines[-20:] if len(lines) > 20 else lines
            
            return {
                "type": "logs",
                "logs": recent_logs,
                "total_lines": len(lines)
            }
        except Exception as e:
            return {
                "type": "error",
                "message": f"Error reading logs: {str(e)}"
            }
    
    def show_file_changes(self) -> Dict[str, Any]:
        """Show current file changes"""
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
            if result.returncode == 0:
                changes = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                return {
                    "type": "changes",
                    "files": changes,
                    "count": len(changes)
                }
            else:
                return {"type": "error", "message": "Git status failed"}
        except Exception as e:
            return {"type": "error", "message": f"Error checking changes: {str(e)}"}
    
    def show_processes(self) -> Dict[str, Any]:
        """Show running processes"""
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            python_processes = [line for line in result.stdout.split('\n') if 'python' in line]
            
            return {
                "type": "processes",
                "processes": python_processes,
                "count": len(python_processes)
            }
        except Exception as e:
            return {"type": "error", "message": f"Error checking processes: {str(e)}"}
    
    def run_pre_deploy_checks(self) -> Dict[str, Any]:
        """Run pre-deployment checks"""
        checks = []
        
        # Health check
        health_result = self.jav.run_health_checks()
        checks.append({
            "name": "Health Check",
            "status": health_result["summary"],
            "details": health_result
        })
        
        # File changes check
        file_changes = self.show_file_changes()
        checks.append({
            "name": "Uncommitted Changes",
            "status": "WARNING" if file_changes.get("count", 0) > 0 else "OK",
            "details": file_changes
        })
        
        # TODO check
        todo_files = self.jav.scan_for_todos()
        checks.append({
            "name": "TODO Comments",
            "status": "WARNING" if todo_files else "OK",
            "details": {"files": todo_files, "count": len(todo_files)}
        })
        
        overall_status = "READY" if all(check["status"] in ["OK", "PASSED"] for check in checks) else "CAUTION"
        
        return {
            "type": "pre_deploy",
            "status": overall_status,
            "checks": checks,
            "recommendation": "Proceed with deployment" if overall_status == "READY" else "Review warnings before deploying"
        }
    
    def restart_service(self) -> Dict[str, Any]:
        """Restart the main service"""
        try:
            # Kill existing processes
            subprocess.run(['pkill', '-f', 'python.*main.py'], capture_output=True)
            
            # Start new process
            process = subprocess.Popen(['python', 'main.py'], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
            
            self.active_processes.append({
                "pid": process.pid,
                "command": "python main.py",
                "started": datetime.now().isoformat()
            })
            
            return {
                "type": "restart",
                "message": f"Service restarted with PID {process.pid}",
                "pid": process.pid
            }
        except Exception as e:
            return {
                "type": "error",
                "message": f"Restart failed: {str(e)}"
            }
    
    def diagnose_issues(self) -> Dict[str, Any]:
        """Diagnose current issues"""
        issues = []
        
        # Check health
        health_result = self.jav.run_health_checks()
        if health_result["summary"] != "PASSED":
            issues.extend(health_result["failed"])
        
        # Check logs for errors
        try:
            with open('memoryos.log', 'r') as f:
                log_content = f.read()
            
            error_lines = [line for line in log_content.split('\n') if 'ERROR' in line]
            if error_lines:
                issues.append(f"Found {len(error_lines)} error messages in logs")
        except Exception:
            pass
        
        return {
            "type": "diagnosis",
            "issues": issues,
            "severity": "HIGH" if issues else "LOW",
            "recommendations": self.get_fix_recommendations(issues)
        }
    
    def get_fix_recommendations(self, issues: List[str]) -> List[str]:
        """Get recommendations for fixing issues"""
        recommendations = []
        
        for issue in issues:
            if "health" in issue.lower():
                recommendations.append("Check health endpoint and fix any reported issues")
            elif "port" in issue.lower():
                recommendations.append("Clear port conflicts with: pkill -f 'python.*main.py'")
            elif "memory" in issue.lower():
                recommendations.append("Validate memory.json file for corruption")
            elif "syntax" in issue.lower():
                recommendations.append("Fix Python syntax errors in reported files")
            else:
                recommendations.append(f"Investigate: {issue}")
        
        if not recommendations:
            recommendations.append("No specific issues found - system appears healthy")
        
        return recommendations
    
    def suggest_next_steps(self) -> Dict[str, Any]:
        """Suggest next development steps"""
        audit_result = asyncio.run(self.jav.audit_current_state())
        
        return {
            "type": "suggestions",
            "next_steps": audit_result["next_steps"],
            "context": audit_result["flow_state"],
            "priority": "HIGH" if audit_result["warnings"] else "NORMAL"
        }
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get overall status summary"""
        audit_result = asyncio.run(self.jav.audit_current_state())
        health_result = self.jav.run_health_checks()
        
        return {
            "type": "summary",
            "health": health_result["summary"],
            "warnings": len(audit_result["warnings"]),
            "flow_state": audit_result["flow_state"],
            "files_changed": len(audit_result["files_changed"]),
            "processes": len(audit_result["processes"]),
            "overall": "GOOD" if health_result["summary"] == "PASSED" and not audit_result["warnings"] else "NEEDS_ATTENTION"
        }
    
    def show_help(self) -> Dict[str, Any]:
        """Show help information"""
        return {
            "type": "help",
            "commands": {
                "Health & Status": [
                    "@jav health - Run health checks",
                    "@jav audit - Full system audit",
                    "@jav status - System summary"
                ],
                "File Operations": [
                    "edit filename.py - Open file for editing",
                    "show filename.py - View file content",
                    "@jav files - Show changed files"
                ],
                "Terminal": [
                    "run command - Execute terminal command",
                    "@jav logs - Show recent logs",
                    "@jav processes - Show running processes"
                ],
                "Deployment": [
                    "@jav deploy - Pre-deployment checks",
                    "@jav rollback - Show rollback options",
                    "@jav restart - Restart service"
                ]
            },
            "message": "Jav is ready to help with your development workflow"
        }
