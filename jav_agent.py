
"""
Jav - Javlin Assistant
A next-generation personal dev assistant that thinks like you
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import subprocess
import re
import glob
from persistent_memory_engine import persistent_memory, AutomationPlaybook

@dataclass
class JavState:
    """Track current state of development work"""
    current_files: List[str]
    active_processes: List[Dict[str, Any]]
    last_test_run: Optional[str]
    last_deploy: Optional[str]
    flow_state: str  # "coding", "testing", "deploying", "stuck", "idle"
    warnings: List[str]
    context: str

class JavAgent:
    """
    Jav - Your personal dev assistant
    Memory-driven, adaptive, respectful learning AI
    """
    
    def __init__(self, memory_api_base: str = "http://0.0.0.0:5000"):
        self.memory_api = memory_api_base
        self.config_dir = Path("jav_config")
        self.config_dir.mkdir(exist_ok=True)
        
        # Load personality and rules
        self.me_config = self.load_me_config()
        self.workflows = self.load_workflows()
        self.user_preferences = self.load_user_preferences()
        self.learned_patterns = self.load_learned_patterns()
        
        # Current state
        self.state = JavState(
            current_files=[],
            active_processes=[],
            last_test_run=None,
            last_deploy=None,
            flow_state="idle",
            warnings=[],
            context="Starting up"
        )
        
        self.logger = logging.getLogger('Jav')
        
    def load_me_config(self) -> Dict[str, Any]:
        """Load personal dev rules and preferences"""
        me_file = self.config_dir / "Me.md"
        if not me_file.exists():
            # Create default Me.md
            self.create_default_me_config()
        
        try:
            with open(me_file, 'r') as f:
                content = f.read()
            
            # Parse Me.md for structured rules
            return {
                "style": "practical, fast, proactive, clear",
                "no_handholding": True,
                "common_patterns": self.extract_patterns(content),
                "preferred_checks": self.extract_checks(content),
                "anti_patterns": self.extract_antipatterns(content)
            }
        except Exception as e:
            self.logger.error(f"Error loading Me.md: {e}")
            return self.get_default_config()
    
    def load_workflows(self) -> Dict[str, str]:
        """Load modular workflow files"""
        workflows = {}
        workflow_files = glob.glob(str(self.config_dir / "*.workflow.md"))
        
        for file_path in workflow_files:
            name = Path(file_path).stem.replace('.workflow', '')
            try:
                with open(file_path, 'r') as f:
                    workflows[name] = f.read()
            except Exception as e:
                self.logger.error(f"Error loading workflow {name}: {e}")
        
        return workflows
    
    def create_default_me_config(self):
        """Create default Me.md with your preferences"""
        me_content = """# Jav - Personal Dev Rules

## My Development Style
- **Practical, fast, proactive, clear** - No hand-holding
- **Show me the problem, give me the fix** - Don't explain why I should care
- **Preempt errors before they happen** - Audit before deploy
- **Keep me in flow** - Minimize context switching

## Common Patterns I Use
- Always run health checks before deploy
- Test endpoints manually with curl
- Check logs for errors after changes
- Git commit frequently with clear messages
- Use bulletproof error handling

## My Anti-Patterns (Flag These!)
- Skipping tests before deploy
- Leaving TODO comments in production code
- Not checking health endpoint after changes
- Silent failures or death loops
- Generic error messages without context

## Preferred Checks
- [ ] Health endpoint returns 200
- [ ] Memory file is valid JSON
- [ ] No syntax errors in Python files
- [ ] All TODOs are addressed or documented
- [ ] Error handling is comprehensive
- [ ] Logs are meaningful and searchable

## Debug Process
1. Check health endpoint first
2. Review recent logs for errors
3. Test the specific failing component
4. Fix root cause, not symptoms
5. Verify fix with health check
6. Document the fix in memory

## Deployment Rules
- Never deploy without running tests
- Always check health endpoint post-deploy
- Have rollback plan ready
- Monitor for 5 minutes after deploy
- Log deployment in memory system
"""
        
        with open(self.config_dir / "Me.md", 'w') as f:
            f.write(me_content)
    
    def extract_patterns(self, content: str) -> List[str]:
        """Extract common patterns from Me.md"""
        patterns = []
        lines = content.split('\n')
        in_patterns = False
        
        for line in lines:
            if '## Common Patterns' in line:
                in_patterns = True
                continue
            if in_patterns and line.startswith('##'):
                break
            if in_patterns and line.strip().startswith('-'):
                patterns.append(line.strip('- '))
        
        return patterns
    
    def extract_checks(self, content: str) -> List[str]:
        """Extract preferred checks from Me.md"""
        checks = []
        lines = content.split('\n')
        in_checks = False
        
        for line in lines:
            if '## Preferred Checks' in line:
                in_checks = True
                continue
            if in_checks and line.startswith('##'):
                break
            if in_checks and '[ ]' in line:
                checks.append(line.strip('- [ ] '))
        
        return checks
    
    def extract_antipatterns(self, content: str) -> List[str]:
        """Extract anti-patterns to flag"""
        antipatterns = []
        lines = content.split('\n')
        in_antipatterns = False
        
        for line in lines:
            if '## My Anti-Patterns' in line:
                in_antipatterns = True
                continue
            if in_antipatterns and line.startswith('##'):
                break
            if in_antipatterns and line.strip().startswith('-'):
                antipatterns.append(line.strip('- '))
        
        return antipatterns
    
    def load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences and automation settings"""
        prefs_file = self.config_dir / "user_preferences.json"
        try:
            with open(prefs_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            default_prefs = {
                "automation_level": "suggest_only",  # suggest_only, auto_apply_safe, full_auto
                "never_automate": [],  # List of patterns user never wants automated
                "always_ask": [],      # List of patterns that always need confirmation
                "global_automations": [],  # List of automations to apply across all projects
                "feedback_history": {},    # Track user responses to suggestions
                "suggestion_preferences": {
                    "show_reasoning": True,
                    "show_memory_source": True,
                    "allow_interruptions": False
                }
            }
            self.save_user_preferences(default_prefs)
            return default_prefs
    
    def load_learned_patterns(self) -> Dict[str, Any]:
        """Load patterns learned from user interactions"""
        patterns_file = self.config_dir / "learned_patterns.json"
        try:
            with open(patterns_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "successful_automations": {},
                "rejected_suggestions": {},
                "user_corrections": {},
                "context_adaptations": {},
                "outcome_tracking": {}
            }
    
    def save_user_preferences(self, preferences: Dict[str, Any]):
        """Save user preferences to disk"""
        prefs_file = self.config_dir / "user_preferences.json"
        with open(prefs_file, 'w') as f:
            json.dump(preferences, f, indent=2)
    
    def save_learned_patterns(self, patterns: Dict[str, Any]):
        """Save learned patterns to disk"""
        patterns_file = self.config_dir / "learned_patterns.json"
        with open(patterns_file, 'w') as f:
            json.dump(patterns, f, indent=2)
    
    def get_default_config(self) -> Dict[str, Any]:
        """Default config if Me.md fails to load"""
        return {
            "style": "practical, fast, proactive, clear",
            "no_handholding": True,
            "common_patterns": [
                "Always run health checks before deploy",
                "Test endpoints manually with curl",
                "Check logs for errors after changes"
            ],
            "preferred_checks": [
                "Health endpoint returns 200",
                "Memory file is valid JSON",
                "No syntax errors in Python files"
            ],
            "anti_patterns": [
                "Skipping tests before deploy",
                "Leaving TODO comments in production code",
                "Silent failures or death loops"
            ]
        }
    
    async def audit_current_state(self) -> Dict[str, Any]:
        """Comprehensive audit of current development state"""
        audit = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "flow_state": self.state.flow_state,
            "warnings": [],
            "suggestions": [],
            "health_status": "unknown",
            "files_changed": [],
            "processes": [],
            "next_steps": []
        }
        
        # Check health endpoint
        try:
            import requests
            response = requests.get(f"{self.memory_api}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                audit["health_status"] = health_data.get("status", "unknown")
                if health_data.get("status") != "healthy":
                    audit["warnings"].append(f"Health check returned: {health_data.get('status')}")
            else:
                audit["warnings"].append(f"Health endpoint returned {response.status_code}")
        except Exception as e:
            audit["warnings"].append(f"Health check failed: {str(e)}")
        
        # Check for running processes
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            python_processes = [line for line in result.stdout.split('\n') if 'python' in line and 'main.py' in line]
            audit["processes"] = python_processes
        except Exception as e:
            audit["warnings"].append(f"Process check failed: {str(e)}")
        
        # Check for recent file changes
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
            if result.returncode == 0:
                changed_files = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                audit["files_changed"] = changed_files
                if changed_files:
                    audit["suggestions"].append("You have uncommitted changes - consider committing or stashing")
        except Exception:
            pass
        
        # Check for TODOs in code
        todo_files = self.scan_for_todos()
        if todo_files:
            audit["warnings"].append(f"Found TODOs in {len(todo_files)} files")
            audit["suggestions"].append("Review and address TODO comments before deploy")
        
        # Check for common anti-patterns
        for antipattern in self.me_config.get("anti_patterns", []):
            if "TODO" in antipattern and todo_files:
                audit["warnings"].append(f"Anti-pattern detected: {antipattern}")
        
        # Suggest next steps based on current state
        if audit["health_status"] != "healthy":
            audit["next_steps"].append("Fix health check issues")
        if audit["files_changed"]:
            audit["next_steps"].append("Review and commit changes")
        if not audit["next_steps"]:
            audit["next_steps"].append("System looks good - ready for next task")
        
        return audit
    
    def scan_for_todos(self) -> List[str]:
        """Scan Python files for TODO comments"""
        todo_files = []
        for py_file in glob.glob("*.py"):
            try:
                with open(py_file, 'r') as f:
                    if 'TODO' in f.read().upper():
                        todo_files.append(py_file)
            except Exception:
                continue
        return todo_files
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run comprehensive health checks based on your preferences"""
        checks = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "passed": [],
            "failed": [],
            "warnings": [],
            "summary": "unknown"
        }
        
        # Health endpoint check
        try:
            import requests
            response = requests.get(f"{self.memory_api}/health", timeout=5)
            if response.status_code == 200:
                checks["passed"].append("Health endpoint accessible")
                health_data = response.json()
                if health_data.get("status") == "healthy":
                    checks["passed"].append("System reports healthy status")
                else:
                    checks["failed"].append(f"System status: {health_data.get('status')}")
            else:
                checks["failed"].append(f"Health endpoint returned {response.status_code}")
        except Exception as e:
            checks["failed"].append(f"Health endpoint failed: {str(e)}")
        
        # Memory file check
        try:
            with open('memory.json', 'r') as f:
                json.load(f)
            checks["passed"].append("Memory file is valid JSON")
        except Exception as e:
            checks["failed"].append(f"Memory file invalid: {str(e)}")
        
        # Python syntax check
        for py_file in glob.glob("*.py"):
            try:
                with open(py_file, 'r') as f:
                    compile(f.read(), py_file, 'exec')
                checks["passed"].append(f"Syntax OK: {py_file}")
            except SyntaxError as e:
                checks["failed"].append(f"Syntax error in {py_file}: {str(e)}")
        
        # Port availability check
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 5000))
            if result == 0:
                checks["warnings"].append("Port 5000 is in use")
            else:
                checks["passed"].append("Port 5000 available")
            sock.close()
        except Exception as e:
            checks["warnings"].append(f"Port check failed: {str(e)}")
        
        # Determine overall status
        if checks["failed"]:
            checks["summary"] = "FAILED"
        elif checks["warnings"]:
            checks["summary"] = "WARNING"
        else:
            checks["summary"] = "PASSED"
        
        return checks
    
    def preempt_errors(self, files: List[str]) -> List[str]:
        """Scan files for common error patterns before they cause issues"""
        warnings = []
        
        for file_path in files:
            if not file_path.endswith('.py'):
                continue
                
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for common issues
                if 'app.run(' in content and 'host=' not in content:
                    warnings.append(f"{file_path}: Flask app.run() should specify host='0.0.0.0'")
                
                if 'try:' in content and 'except:' in content:
                    if 'except Exception' not in content:
                        warnings.append(f"{file_path}: Bare except clause - specify exception type")
                
                if 'TODO' in content.upper():
                    warnings.append(f"{file_path}: Contains TODO comments")
                
                if 'print(' in content and 'logging.' not in content:
                    warnings.append(f"{file_path}: Using print() instead of logging")
                
            except Exception as e:
                warnings.append(f"Error scanning {file_path}: {str(e)}")
        
        return warnings
    
    def get_recovery_options(self) -> Dict[str, str]:
        """Get available recovery options"""
        return {
            "restart_service": "pkill -f 'python.*main.py' && python main.py",
            "clear_port": "lsof -ti:5000 | xargs kill -9 2>/dev/null || echo 'Port clear'",
            "check_health": f"curl -s {self.memory_api}/health | python -m json.tool",
            "view_logs": "tail -20 memoryos.log",
            "git_status": "git status --porcelain",
            "rollback_commit": "git reset --hard HEAD~1"
        }
    
    def log_to_memory(self, topic: str, type_: str, input_: str, output: str, 
                     success: bool = True, category: str = "jav") -> bool:
        """Log activities to the memory system"""
        try:
            import requests
            
            data = {
                "topic": topic,
                "type": type_,
                "input": input_,
                "output": output,
                "success": success,
                "category": category,
                "tags": ["jav", "agent", "audit"],
                "context": f"Jav Agent: {self.state.context}"
            }
            
            headers = {"X-API-KEY": os.getenv('JAVLIN_API_KEY', 'default-key-change-me')}
            response = requests.post(f"{self.memory_api}/memory", json=data, headers=headers)
            
            # Also check for persistent memory patterns
            if not success:
                self.analyze_failure_for_patterns(data)
            
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Failed to log to memory: {e}")
            return False
    
    def analyze_failure_for_patterns(self, failure_data: Dict[str, Any]):
        """Analyze failures for cross-project patterns"""
        context = {
            "title": failure_data.get("topic", ""),
            "description": failure_data.get("input", ""),
            "error_type": self.extract_error_type(failure_data.get("output", "")),
            "file_types": self.get_current_file_types(),
            "project_type": self.detect_project_type(),
            "environment": self.get_environment_info()
        }
        
        # Analyze with persistent memory
        analysis = persistent_memory.analyze_situation(context)
        
        if analysis["matching_playbooks"]:
            self.logger.info(f"Found {len(analysis['matching_playbooks'])} potential solutions from past projects")
        
        return analysis
    
    def get_memory_driven_suggestions(self, current_task: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get adaptive suggestions based on memory and user preferences"""
        if context is None:
            context = {
                "title": current_task,
                "description": f"Working on: {current_task}",
                "file_types": self.get_current_file_types(),
                "project_type": self.detect_project_type(),
                "environment": self.get_environment_info()
            }
        
        # Get base analysis from persistent memory
        analysis = persistent_memory.analyze_situation(context)
        suggestions = []
        
        # Filter suggestions based on user preferences and learning
        for match in analysis["matching_playbooks"]:
            playbook = match["playbook"]
            
            # Check if user has rejected this type of suggestion before
            if self._should_skip_suggestion(playbook, context):
                continue
                
            suggestion = {
                "id": f"auto_{playbook.id}_{datetime.now().timestamp()}",
                "type": "automation",
                "title": f"Auto-fix available: {playbook.name}",
                "description": playbook.description,
                "confidence": match["confidence"],
                "playbook_id": playbook.id,
                "memory_source": self._get_memory_source(playbook),
                "reasoning": self._explain_suggestion(playbook, match),
                "controls": {
                    "apply": True,
                    "ignore": True,
                    "never_again": True,
                    "edit_automation": True
                },
                "auto_apply": self._should_auto_apply(playbook, match)
            }
            suggestions.append(suggestion)
        
        # Add context-aware warnings with learned adaptations
        for warning in analysis["preventive_warnings"]:
            if not self._is_warning_suppressed(warning, context):
                suggestions.append({
                    "id": f"warn_{hash(warning)}_{datetime.now().timestamp()}",
                    "type": "warning",
                    "title": "Preventive Warning",
                    "description": warning,
                    "confidence": 0.9,
                    "memory_source": "Past failure patterns",
                    "reasoning": "Similar situation caused issues in previous projects",
                    "controls": {
                        "acknowledge": True,
                        "ignore": True,
                        "never_show_again": True
                    }
                })
        
        # Add learning-based suggestions
        learning_suggestions = self._get_learning_suggestions(context)
        suggestions.extend(learning_suggestions)
        
        return suggestions
    
    def process_user_response(self, suggestion_id: str, response: str, outcome: str = None) -> Dict[str, Any]:
        """Process user response to suggestions and update learning"""
        response_data = {
            "suggestion_id": suggestion_id,
            "response": response,  # "apply", "ignore", "never_again", etc.
            "outcome": outcome,   # "success", "failure", "partial", etc.
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": self.get_current_context()
        }
        
        # Update user preferences based on response
        if response == "never_again":
            pattern_signature = self._extract_pattern_signature(suggestion_id)
            self.user_preferences["never_automate"].append(pattern_signature)
            
        elif response == "always_ask":
            pattern_signature = self._extract_pattern_signature(suggestion_id)
            self.user_preferences["always_ask"].append(pattern_signature)
            
        elif response == "apply" and outcome:
            # Learn from successful applications
            self.learned_patterns["successful_automations"][suggestion_id] = response_data
            
        elif response == "ignore":
            # Track ignored suggestions to improve future relevance
            self.learned_patterns["rejected_suggestions"][suggestion_id] = response_data
        
        # Save updated preferences and patterns
        self.save_user_preferences(self.user_preferences)
        self.save_learned_patterns(self.learned_patterns)
        
        # Log the interaction to memory
        self.log_to_memory(
            topic=f"User Response to Suggestion: {response}",
            type_="UserFeedback",
            input_=f"Suggestion: {suggestion_id}, Response: {response}",
            output=f"Outcome: {outcome}, Learning updated",
            success=True,
            category="learning"
        )
        
        return {
            "status": "processed",
            "message": f"Response '{response}' recorded and learning updated",
            "updated_preferences": bool(response in ["never_again", "always_ask"]),
            "pattern_learned": bool(outcome and response == "apply")
        }
    
    def _should_skip_suggestion(self, playbook, context: Dict[str, Any]) -> bool:
        """Check if suggestion should be skipped based on user preferences"""
        pattern_sig = f"{playbook.id}:{context.get('project_type', 'unknown')}"
        
        # Check never_automate list
        for never_pattern in self.user_preferences["never_automate"]:
            if never_pattern in pattern_sig or pattern_sig in never_pattern:
                return True
                
        # Check if similar suggestions were repeatedly rejected
        rejection_count = sum(1 for suggestion_id, data in 
                            self.learned_patterns["rejected_suggestions"].items()
                            if playbook.name in suggestion_id)
        
        return rejection_count >= 3  # Skip after 3 rejections
    
    def _should_auto_apply(self, playbook, match: Dict[str, Any]) -> bool:
        """Determine if suggestion should auto-apply based on learning"""
        # Never auto-apply if user prefers suggestions only
        if self.user_preferences["automation_level"] == "suggest_only":
            return False
            
        # Check if this type has high success rate
        success_count = sum(1 for data in self.learned_patterns["successful_automations"].values()
                          if playbook.name in data.get("suggestion_id", ""))
        
        total_count = success_count + sum(1 for data in self.learned_patterns["rejected_suggestions"].values()
                                        if playbook.name in data.get("suggestion_id", ""))
        
        if total_count >= 3:  # Enough data to make decision
            success_rate = success_count / total_count
            return success_rate >= 0.8 and match["confidence"] >= 0.9
            
        return False
    
    def _get_memory_source(self, playbook) -> str:
        """Get human-readable memory source for transparency"""
        return f"Learned from project: {playbook.project_origin} on {playbook.created_at[:10]}"
    
    def _explain_suggestion(self, playbook, match: Dict[str, Any]) -> str:
        """Explain why this suggestion is being made"""
        confidence_desc = "high" if match["confidence"] >= 0.8 else "medium" if match["confidence"] >= 0.6 else "low"
        return f"Based on {confidence_desc} confidence match ({match['confidence']:.1%}) with successful solution from {playbook.project_origin}"
    
    def _is_warning_suppressed(self, warning: str, context: Dict[str, Any]) -> bool:
        """Check if warning should be suppressed based on user feedback"""
        warning_hash = str(hash(warning))
        return warning_hash in self.user_preferences.get("suppressed_warnings", [])
    
    def _get_learning_suggestions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate suggestions based on learned patterns"""
        suggestions = []
        
        # Suggest new automations based on repetitive patterns
        for pattern, occurrences in self.learned_patterns.get("context_adaptations", {}).items():
            if len(occurrences) >= 3:  # Pattern seen 3+ times
                suggestions.append({
                    "id": f"learn_{hash(pattern)}_{datetime.now().timestamp()}",
                    "type": "learning",
                    "title": f"Create automation for: {pattern}",
                    "description": f"You've done this {len(occurrences)} times. Want to automate it?",
                    "confidence": 0.8,
                    "memory_source": "Pattern detection from your actions",
                    "reasoning": f"Detected repetitive pattern in your workflow",
                    "controls": {
                        "create_automation": True,
                        "ignore": True,
                        "remind_later": True
                    }
                })
        
        return suggestions
    
    def _extract_pattern_signature(self, suggestion_id: str) -> str:
        """Extract pattern signature for preference matching"""
        # Simple pattern extraction - can be enhanced
        return suggestion_id.split("_")[1] if "_" in suggestion_id else suggestion_id
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current development context"""
        return {
            "flow_state": self.state.flow_state,
            "current_files": self.state.current_files,
            "project_type": self.detect_project_type(),
            "file_types": self.get_current_file_types(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def apply_automation(self, playbook_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Apply an automation playbook"""
        playbook = next((p for p in persistent_memory.playbooks if p.id == playbook_id), None)
        
        if not playbook:
            return {"success": False, "error": "Playbook not found"}
        
        if context is None:
            context = {
                "project_path": os.getcwd(),
                "file_types": self.get_current_file_types(),
                "environment": self.get_environment_info()
            }
        
        result = persistent_memory.apply_playbook(playbook, context)
        
        # Log the automation application
        self.log_to_memory(
            topic=f"Applied automation: {playbook.name}",
            type_="Automation",
            input_=f"Playbook ID: {playbook_id}",
            output=str(result),
            success=result.get("success", False),
            category="automation"
        )
        
        return result
    
    def create_automation_from_solution(self, problem_description: str, 
                                      solution_steps: List[str], 
                                      success: bool) -> AutomationPlaybook:
        """Create a new automation from a successful solution"""
        context = {
            "title": problem_description,
            "description": problem_description,
            "error_type": self.extract_error_type(problem_description),
            "file_types": self.get_current_file_types(),
            "project_type": self.detect_project_type(),
            "environment": self.get_environment_info(),
            "tags": ["user_created", "jav_agent"]
        }
        
        # Convert solution steps to automation format
        automation_steps = []
        for step in solution_steps:
            if step.startswith("run ") or step.startswith("execute "):
                automation_steps.append({
                    "type": "command",
                    "command": step.replace("run ", "").replace("execute ", ""),
                    "description": f"Execute: {step}"
                })
            elif "create file" in step.lower() or "edit file" in step.lower():
                automation_steps.append({
                    "type": "file_edit",
                    "description": step,
                    "manual_review": True
                })
            else:
                automation_steps.append({
                    "type": "manual",
                    "description": step,
                    "requires_human": True
                })
        
        playbook = persistent_memory.create_playbook_from_solution(context, automation_steps, success)
        
        self.log_to_memory(
            topic=f"Created automation playbook: {playbook.name}",
            type_="PlaybookCreation",
            input_=problem_description,
            output=f"Playbook ID: {playbook.id}, Steps: {len(automation_steps)}",
            success=True,
            category="automation"
        )
        
        return playbook
    
    def extract_error_type(self, text: str) -> str:
        """Extract error type from text"""
        import re
        error_patterns = [
            r'(\w*Error)',
            r'(\w*Exception)',
            r'(FAILED|ERROR|CRITICAL)',
            r'(ModuleNotFoundError|ImportError|SyntaxError|NameError)'
        ]
        
        for pattern in error_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Unknown"
    
    def get_current_file_types(self) -> List[str]:
        """Get file types in current directory"""
        file_types = set()
        for file_path in glob.glob("*"):
            if os.path.isfile(file_path):
                ext = os.path.splitext(file_path)[1]
                if ext:
                    file_types.add(ext[1:])  # Remove dot
        return list(file_types)
    
    def detect_project_type(self) -> str:
        """Detect the type of current project"""
        if os.path.exists("package.json"):
            return "nodejs"
        elif os.path.exists("requirements.txt") or os.path.exists("pyproject.toml"):
            return "python"
        elif os.path.exists("Cargo.toml"):
            return "rust"
        elif os.path.exists("go.mod"):
            return "go"
        elif os.path.exists("pom.xml"):
            return "java"
        else:
            return "unknown"
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get current environment information"""
        return {
            "os": os.name,
            "cwd": os.getcwd(),
            "python_version": os.sys.version.split()[0] if hasattr(os, 'sys') else "unknown",
            "has_git": os.path.exists(".git"),
            "has_docker": os.path.exists("Dockerfile"),
            "port_5000_used": self.is_port_in_use(5000)
        }
    
    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0
        except:
            return False

# Global instance
jav = JavAgent()
