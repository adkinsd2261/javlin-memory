
"""
Persistent Memory Engine - Cross-Project Active Intelligence
Turns every lesson, fix, and pattern into permanent, reusable solutions
"""

import json
import os
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import fnmatch
import difflib

class PatternMatcher:
    """Identifies similar situations across projects"""
    
    def __init__(self):
        self.similarity_threshold = 0.7
        
    def extract_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key features from a problem context"""
        return {
            "error_type": context.get("error_type", ""),
            "file_types": context.get("file_types", []),
            "keywords": self._extract_keywords(context.get("description", "")),
            "stack_trace_signature": self._get_stack_signature(context.get("stack_trace", "")),
            "command_pattern": context.get("command", ""),
            "environment": context.get("environment", {}),
            "project_type": context.get("project_type", "")
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        import re
        # Extract technical terms, error codes, package names
        keywords = re.findall(r'\b(?:[A-Z][a-z]+Error|[a-z]+_[a-z]+|\w+\.\w+|[A-Z]{2,})\b', text)
        return list(set(keywords))
    
    def _get_stack_signature(self, stack_trace: str) -> str:
        """Create a signature from stack trace patterns"""
        if not stack_trace:
            return ""
        # Extract function names and error types
        import re
        functions = re.findall(r'in (\w+)', stack_trace)
        errors = re.findall(r'(\w*Error|\w*Exception)', stack_trace)
        return f"{'+'.join(functions[:3])}|{'+'.join(errors[:2])}"
    
    def calculate_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """Calculate similarity between two feature sets"""
        scores = []
        
        # Error type similarity
        if features1["error_type"] and features2["error_type"]:
            scores.append(1.0 if features1["error_type"] == features2["error_type"] else 0.0)
        
        # Keywords overlap
        keywords1 = set(features1["keywords"])
        keywords2 = set(features2["keywords"])
        if keywords1 or keywords2:
            overlap = len(keywords1.intersection(keywords2))
            total = len(keywords1.union(keywords2))
            scores.append(overlap / total if total > 0 else 0.0)
        
        # Stack trace similarity
        if features1["stack_trace_signature"] and features2["stack_trace_signature"]:
            seq_match = difflib.SequenceMatcher(None, 
                                              features1["stack_trace_signature"],
                                              features2["stack_trace_signature"])
            scores.append(seq_match.ratio())
        
        # File types similarity
        files1 = set(features1["file_types"])
        files2 = set(features2["file_types"])
        if files1 or files2:
            overlap = len(files1.intersection(files2))
            total = len(files1.union(files2))
            scores.append(overlap / total if total > 0 else 0.0)
        
        return sum(scores) / len(scores) if scores else 0.0

class AutomationPlaybook:
    """Represents a reusable automation solution"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.description = data.get("description", "")
        self.trigger_pattern = data.get("trigger_pattern", {})
        self.solution_steps = data.get("solution_steps", [])
        self.auto_apply = data.get("auto_apply", False)
        self.success_rate = data.get("success_rate", 0.0)
        self.usage_count = data.get("usage_count", 0)
        self.created_at = data.get("created_at", "")
        self.last_used = data.get("last_used", "")
        self.tags = data.get("tags", [])
        self.project_origin = data.get("project_origin", "")
        self.retired = data.get("retired", False)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "trigger_pattern": self.trigger_pattern,
            "solution_steps": self.solution_steps,
            "auto_apply": self.auto_apply,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "tags": self.tags,
            "project_origin": self.project_origin,
            "retired": self.retired
        }

class PersistentMemoryEngine:
    """Cross-project persistent memory and automation engine"""
    
    def __init__(self, global_memory_path: str = None):
        self.global_memory_path = global_memory_path or os.path.expanduser("~/.jav_global_memory")
        self.ensure_global_memory_structure()
        
        self.pattern_matcher = PatternMatcher()
        self.logger = logging.getLogger('PersistentMemory')
        
        # Load existing data
        self.playbooks = self.load_playbooks()
        self.project_registry = self.load_project_registry()
        self.cross_project_patterns = self.load_cross_project_patterns()
        
    def ensure_global_memory_structure(self):
        """Ensure global memory directory structure exists"""
        Path(self.global_memory_path).mkdir(parents=True, exist_ok=True)
        
        subdirs = ["playbooks", "patterns", "projects", "automations", "shared"]
        for subdir in subdirs:
            Path(self.global_memory_path, subdir).mkdir(exist_ok=True)
    
    def load_playbooks(self) -> List[AutomationPlaybook]:
        """Load all automation playbooks"""
        playbooks = []
        playbooks_dir = Path(self.global_memory_path, "playbooks")
        
        for playbook_file in playbooks_dir.glob("*.json"):
            try:
                with open(playbook_file, 'r') as f:
                    data = json.load(f)
                    playbooks.append(AutomationPlaybook(data))
            except Exception as e:
                self.logger.error(f"Error loading playbook {playbook_file}: {e}")
        
        return playbooks
    
    def load_project_registry(self) -> Dict[str, Any]:
        """Load project registry"""
        registry_file = Path(self.global_memory_path, "projects", "registry.json")
        try:
            with open(registry_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"projects": {}, "last_updated": ""}
    
    def load_cross_project_patterns(self) -> List[Dict[str, Any]]:
        """Load cross-project patterns"""
        patterns_file = Path(self.global_memory_path, "patterns", "cross_project.json")
        try:
            with open(patterns_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def register_current_project(self, project_path: str, project_info: Dict[str, Any]):
        """Register current project in global registry"""
        project_id = self._generate_project_id(project_path)
        
        self.project_registry["projects"][project_id] = {
            "path": project_path,
            "name": project_info.get("name", os.path.basename(project_path)),
            "type": project_info.get("type", "unknown"),
            "technologies": project_info.get("technologies", []),
            "last_active": datetime.now(timezone.utc).isoformat(),
            "memory_count": project_info.get("memory_count", 0),
            "success_patterns": project_info.get("success_patterns", [])
        }
        
        self._save_project_registry()
    
    def analyze_situation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current situation and find matching patterns/solutions"""
        current_features = self.pattern_matcher.extract_features(context)
        
        # Find matching playbooks
        matching_playbooks = []
        for playbook in self.playbooks:
            if playbook.retired:
                continue
                
            pattern_features = self.pattern_matcher.extract_features(playbook.trigger_pattern)
            similarity = self.pattern_matcher.calculate_similarity(current_features, pattern_features)
            
            if similarity >= self.pattern_matcher.similarity_threshold:
                matching_playbooks.append({
                    "playbook": playbook,
                    "similarity": similarity,
                    "confidence": self._calculate_confidence(playbook, similarity)
                })
        
        # Sort by confidence
        matching_playbooks.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Find cross-project patterns
        similar_situations = self._find_similar_cross_project_situations(current_features)
        
        return {
            "matching_playbooks": matching_playbooks[:5],  # Top 5 matches
            "similar_situations": similar_situations[:3],  # Top 3 similar situations
            "recommendations": self._generate_recommendations(matching_playbooks, similar_situations),
            "preventive_warnings": self._check_preventive_warnings(current_features)
        }
    
    def create_playbook_from_solution(self, problem_context: Dict[str, Any], 
                                    solution_steps: List[Dict[str, Any]], 
                                    success: bool) -> AutomationPlaybook:
        """Create a new automation playbook from a successful solution"""
        playbook_id = self._generate_playbook_id(problem_context)
        
        playbook_data = {
            "id": playbook_id,
            "name": f"Auto-fix: {problem_context.get('title', 'Unknown Issue')}",
            "description": problem_context.get('description', ''),
            "trigger_pattern": self.pattern_matcher.extract_features(problem_context),
            "solution_steps": solution_steps,
            "auto_apply": False,  # Manual approval by default
            "success_rate": 1.0 if success else 0.0,
            "usage_count": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used": datetime.now(timezone.utc).isoformat(),
            "tags": problem_context.get('tags', []),
            "project_origin": os.getcwd(),
            "retired": False
        }
        
        playbook = AutomationPlaybook(playbook_data)
        self.playbooks.append(playbook)
        self._save_playbook(playbook)
        
        return playbook
    
    def apply_playbook(self, playbook: AutomationPlaybook, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply an automation playbook"""
        try:
            results = []
            
            for step in playbook.solution_steps:
                step_result = self._execute_solution_step(step, context)
                results.append(step_result)
                
                if not step_result.get("success", False):
                    break
            
            success = all(result.get("success", False) for result in results)
            
            # Update playbook stats
            playbook.usage_count += 1
            playbook.last_used = datetime.now(timezone.utc).isoformat()
            
            if success:
                playbook.success_rate = (playbook.success_rate * (playbook.usage_count - 1) + 1.0) / playbook.usage_count
            else:
                playbook.success_rate = (playbook.success_rate * (playbook.usage_count - 1) + 0.0) / playbook.usage_count
            
            self._save_playbook(playbook)
            
            return {
                "success": success,
                "results": results,
                "playbook_id": playbook.id,
                "message": "Playbook applied successfully" if success else "Playbook application failed"
            }
            
        except Exception as e:
            self.logger.error(f"Error applying playbook {playbook.id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "playbook_id": playbook.id
            }
    
    def update_playbook_auto_apply(self, playbook_id: str, auto_apply: bool):
        """Update auto-apply setting for a playbook"""
        for playbook in self.playbooks:
            if playbook.id == playbook_id:
                playbook.auto_apply = auto_apply
                self._save_playbook(playbook)
                break
    
    def retire_playbook(self, playbook_id: str, reason: str = ""):
        """Retire an outdated playbook"""
        for playbook in self.playbooks:
            if playbook.id == playbook_id:
                playbook.retired = True
                playbook.tags.append(f"retired:{reason}")
                self._save_playbook(playbook)
                break
    
    def get_cross_project_insights(self) -> Dict[str, Any]:
        """Get insights across all projects"""
        insights = {
            "total_projects": len(self.project_registry["projects"]),
            "total_playbooks": len([p for p in self.playbooks if not p.retired]),
            "success_patterns": self._analyze_success_patterns(),
            "common_pitfalls": self._analyze_common_pitfalls(),
            "automation_opportunities": self._find_automation_opportunities(),
            "knowledge_gaps": self._identify_knowledge_gaps()
        }
        
        return insights
    
    def sync_with_team(self, team_id: str, sync_config: Dict[str, Any]):
        """Sync automations with team members (future feature)"""
        # Implementation for team sharing
        shared_dir = Path(self.global_memory_path, "shared", team_id)
        shared_dir.mkdir(exist_ok=True)
        
        # Export selected playbooks for sharing
        shareable_playbooks = [
            p for p in self.playbooks 
            if not p.retired and "shareable" in p.tags
        ]
        
        shared_file = shared_dir / "shared_playbooks.json"
        with open(shared_file, 'w') as f:
            json.dump([p.to_dict() for p in shareable_playbooks], f, indent=2)
        
        return {
            "shared_playbooks": len(shareable_playbooks),
            "sync_location": str(shared_file)
        }
    
    def _generate_project_id(self, project_path: str) -> str:
        """Generate unique project ID"""
        return hashlib.md5(project_path.encode()).hexdigest()[:12]
    
    def _generate_playbook_id(self, context: Dict[str, Any]) -> str:
        """Generate unique playbook ID"""
        content = f"{context.get('title', '')}{context.get('error_type', '')}{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _calculate_confidence(self, playbook: AutomationPlaybook, similarity: float) -> float:
        """Calculate confidence score for playbook application"""
        base_confidence = similarity
        success_boost = playbook.success_rate * 0.3
        usage_boost = min(playbook.usage_count / 10.0, 0.2)
        
        return min(base_confidence + success_boost + usage_boost, 1.0)
    
    def _find_similar_cross_project_situations(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar situations across other projects"""
        similar = []
        
        for pattern in self.cross_project_patterns:
            pattern_features = pattern.get("features", {})
            similarity = self.pattern_matcher.calculate_similarity(features, pattern_features)
            
            if similarity >= 0.6:  # Lower threshold for cross-project insights
                similar.append({
                    "pattern": pattern,
                    "similarity": similarity,
                    "project": pattern.get("project_name", "Unknown"),
                    "solution_summary": pattern.get("solution_summary", "")
                })
        
        return sorted(similar, key=lambda x: x["similarity"], reverse=True)
    
    def _generate_recommendations(self, matching_playbooks: List[Dict[str, Any]], 
                                similar_situations: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if matching_playbooks:
            best_match = matching_playbooks[0]
            if best_match["confidence"] > 0.8:
                recommendations.append(f"🎯 High-confidence auto-fix available: {best_match['playbook'].name}")
            else:
                recommendations.append(f"💡 Similar issue solved before: {best_match['playbook'].name}")
        
        if similar_situations:
            recommendations.append(f"🔍 Similar pattern found in {similar_situations[0]['project']}")
        
        if not matching_playbooks and not similar_situations:
            recommendations.append("🆕 New pattern detected - consider creating playbook after resolution")
        
        return recommendations
    
    def _check_preventive_warnings(self, features: Dict[str, Any]) -> List[str]:
        """Check for preventive warnings based on past failures"""
        warnings = []
        
        # Check for patterns that led to failures in the past
        for pattern in self.cross_project_patterns:
            if pattern.get("outcome") == "failure":
                pattern_features = pattern.get("features", {})
                similarity = self.pattern_matcher.calculate_similarity(features, pattern_features)
                
                if similarity > 0.7:
                    warnings.append(f"⚠️ Similar situation caused issues in {pattern.get('project_name', 'another project')}: {pattern.get('failure_reason', 'Unknown')}")
        
        return warnings
    
    def _execute_solution_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single solution step"""
        step_type = step.get("type", "")
        
        if step_type == "command":
            return self._execute_command_step(step, context)
        elif step_type == "file_edit":
            return self._execute_file_edit_step(step, context)
        elif step_type == "config_change":
            return self._execute_config_change_step(step, context)
        else:
            return {"success": False, "error": f"Unknown step type: {step_type}"}
    
    def _execute_command_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command step"""
        import subprocess
        
        try:
            command = step.get("command", "")
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_file_edit_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a file edit step"""
        try:
            file_path = step.get("file_path", "")
            operation = step.get("operation", "")
            content = step.get("content", "")
            
            if operation == "create":
                with open(file_path, 'w') as f:
                    f.write(content)
            elif operation == "append":
                with open(file_path, 'a') as f:
                    f.write(content)
            elif operation == "replace":
                with open(file_path, 'w') as f:
                    f.write(content)
            
            return {"success": True, "file_path": file_path, "operation": operation}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_config_change_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a configuration change step"""
        try:
            config_file = step.get("config_file", "")
            key = step.get("key", "")
            value = step.get("value", "")
            
            # Simple JSON config update
            if config_file.endswith('.json'):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Support nested keys with dot notation
                keys = key.split('.')
                current = config
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
                
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
            
            return {"success": True, "config_file": config_file, "key": key, "value": value}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _save_playbook(self, playbook: AutomationPlaybook):
        """Save playbook to disk"""
        playbooks_dir = Path(self.global_memory_path, "playbooks")
        playbook_file = playbooks_dir / f"{playbook.id}.json"
        
        with open(playbook_file, 'w') as f:
            json.dump(playbook.to_dict(), f, indent=2)
    
    def _save_project_registry(self):
        """Save project registry to disk"""
        registry_file = Path(self.global_memory_path, "projects", "registry.json")
        self.project_registry["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        with open(registry_file, 'w') as f:
            json.dump(self.project_registry, f, indent=2)
    
    def _analyze_success_patterns(self) -> List[Dict[str, Any]]:
        """Analyze patterns that lead to success"""
        # Implementation for success pattern analysis
        return []
    
    def _analyze_common_pitfalls(self) -> List[Dict[str, Any]]:
        """Analyze common pitfalls across projects"""
        # Implementation for pitfall analysis
        return []
    
    def _find_automation_opportunities(self) -> List[Dict[str, Any]]:
        """Find opportunities for new automations"""
        # Implementation for automation opportunity detection
        return []
    
    def _identify_knowledge_gaps(self) -> List[Dict[str, Any]]:
        """Identify areas where more knowledge/automation is needed"""
        # Implementation for knowledge gap analysis
        return []

# Global instance
persistent_memory = PersistentMemoryEngine()
