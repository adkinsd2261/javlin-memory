
#!/usr/bin/env python3
"""
Infrastructure Audit Module for Javlin Memory System
Tracks system components, detects gaps, and ensures architectural coherence
"""

import os
import json
import re
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import ast
import logging

class InfrastructureAuditor:
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.audit_results = {}
        self.memory_data = []
        self.system_components = {}
        
    def load_memory_data(self) -> List[Dict]:
        """Load memory logs for analysis"""
        try:
            memory_file = os.path.join(self.base_dir, 'memory.json')
            with open(memory_file, 'r') as f:
                self.memory_data = json.load(f)
            return self.memory_data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.warning(f"Could not load memory data: {e}")
            return []
    
    def scan_codebase_components(self) -> Dict[str, Any]:
        """Scan codebase to identify existing components and features"""
        components = {
            "endpoints": [],
            "functions": [],
            "classes": [],
            "files": [],
            "configurations": {},
            "dependencies": []
        }
        
        # Scan main.py for Flask endpoints and functions
        main_py = os.path.join(self.base_dir, 'main.py')
        if os.path.exists(main_py):
            components.update(self._analyze_flask_app(main_py))
        
        # Scan for Python files and their components
        for py_file in Path(self.base_dir).glob("*.py"):
            if py_file.name not in ['main.py']:
                components["files"].append({
                    "name": py_file.name,
                    "size": py_file.stat().st_size,
                    "modified": datetime.datetime.fromtimestamp(py_file.stat().st_mtime).isoformat(),
                    "functions": self._extract_functions(str(py_file)),
                    "classes": self._extract_classes(str(py_file))
                })
        
        # Scan configuration files
        config_files = ['config.json', 'version.json', 'pyproject.toml', '.replit']
        for config_file in config_files:
            config_path = os.path.join(self.base_dir, config_file)
            if os.path.exists(config_path):
                components["configurations"][config_file] = {
                    "exists": True,
                    "size": os.path.getsize(config_path),
                    "modified": datetime.datetime.fromtimestamp(os.path.getmtime(config_path)).isoformat()
                }
        
        self.system_components = components
        return components
    
    def _analyze_flask_app(self, file_path: str) -> Dict[str, List]:
        """Analyze Flask app for endpoints and functions"""
        endpoints = []
        functions = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract Flask routes
            route_pattern = r"@app\.route\(['\"]([^'\"]+)['\"](?:,\s*methods=\[([^\]]+)\])?\)"
            routes = re.findall(route_pattern, content)
            
            for route, methods in routes:
                methods_list = []
                if methods:
                    methods_list = [m.strip().strip('\'"') for m in methods.split(',')]
                endpoints.append({
                    "route": route,
                    "methods": methods_list or ["GET"],
                    "type": "flask_endpoint"
                })
            
            # Extract function definitions
            function_pattern = r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
            function_names = re.findall(function_pattern, content)
            
            for func_name in function_names:
                functions.append({
                    "name": func_name,
                    "file": "main.py",
                    "type": "function"
                })
        
        except Exception as e:
            logging.warning(f"Error analyzing Flask app: {e}")
        
        return {"endpoints": endpoints, "functions": functions}
    
    def _extract_functions(self, file_path: str) -> List[str]:
        """Extract function names from a Python file"""
        functions = []
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            function_pattern = r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
            functions = re.findall(function_pattern, content)
        except Exception as e:
            logging.warning(f"Error extracting functions from {file_path}: {e}")
        
        return functions
    
    def _extract_classes(self, file_path: str) -> List[str]:
        """Extract class names from a Python file"""
        classes = []
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            class_pattern = r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(:]"
            classes = re.findall(class_pattern, content)
        except Exception as e:
            logging.warning(f"Error extracting classes from {file_path}: {e}")
        
        return classes
    
    def detect_unregistered_components(self) -> List[Dict]:
        """Detect components that exist in memory logs but not in codebase"""
        unregistered = []
        
        # Get all registered endpoints
        registered_endpoints = {ep["route"] for ep in self.system_components.get("endpoints", [])}
        
        # Check memory logs for endpoint references
        for memory in self.memory_data:
            input_text = memory.get('input', '')
            output_text = memory.get('output', '')
            topic = memory.get('topic', '')
            
            # Look for endpoint patterns in memory logs
            endpoint_pattern = r'/[a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_-]+)*'
            found_endpoints = re.findall(endpoint_pattern, f"{input_text} {output_text} {topic}")
            
            for endpoint in found_endpoints:
                if endpoint not in registered_endpoints and endpoint not in ['/memory', '/stats', '/digest']:
                    unregistered.append({
                        "type": "endpoint",
                        "component": endpoint,
                        "mentioned_in": memory.get('timestamp', ''),
                        "context": topic,
                        "source": "memory_log"
                    })
        
        # Check for feature mentions that might not be implemented
        feature_keywords = ['endpoint', 'api', 'function', 'module', 'service', 'tool']
        for memory in self.memory_data[-20:]:  # Check recent memories
            if memory.get('type') in ['Feature', 'BuildLog', 'Enhancement']:
                for keyword in feature_keywords:
                    if keyword in memory.get('output', '').lower():
                        # This suggests a feature was built but might not be tracked
                        unregistered.append({
                            "type": "potential_feature",
                            "component": memory.get('topic', ''),
                            "mentioned_in": memory.get('timestamp', ''),
                            "context": memory.get('output', '')[:100],
                            "source": "feature_log"
                        })
        
        return unregistered
    
    def detect_architecture_mismatches(self) -> List[Dict]:
        """Detect potential mismatches between memory logs and actual implementation"""
        mismatches = []
        
        # Check for endpoints mentioned in logs that don't exist
        mentioned_endpoints = set()
        existing_endpoints = {ep["route"] for ep in self.system_components.get("endpoints", [])}
        
        for memory in self.memory_data:
            text = f"{memory.get('input', '')} {memory.get('output', '')}"
            endpoints = re.findall(r'/[a-zA-Z0-9_-]+', text)
            mentioned_endpoints.update(endpoints)
        
        for endpoint in mentioned_endpoints:
            if endpoint not in existing_endpoints and endpoint.startswith('/'):
                mismatches.append({
                    "type": "missing_endpoint",
                    "component": endpoint,
                    "severity": "medium",
                    "description": f"Endpoint {endpoint} mentioned in logs but not found in codebase"
                })
        
        # Check for version mismatches
        try:
            version_file = os.path.join(self.base_dir, 'version.json')
            with open(version_file, 'r') as f:
                version_data = json.load(f)
            
            planned_features = version_data.get('planned_features', [])
            recent_features = [m for m in self.memory_data if m.get('type') == 'Feature']
            
            for feature in planned_features:
                feature_implemented = any(feature.lower() in m.get('topic', '').lower() 
                                        for m in recent_features)
                if not feature_implemented:
                    mismatches.append({
                        "type": "planned_but_not_implemented",
                        "component": feature,
                        "severity": "low",
                        "description": f"Feature '{feature}' planned but no implementation logs found"
                    })
        
        except Exception as e:
            logging.warning(f"Error checking version mismatches: {e}")
        
        return mismatches
    
    def analyze_recent_undocumented_changes(self) -> List[Dict]:
        """Find recent changes from logs that aren't documented in SYSTEM_UPGRADES.md"""
        undocumented = []
        
        try:
            # Load SYSTEM_UPGRADES.md
            upgrades_file = os.path.join(self.base_dir, 'SYSTEM_UPGRADES.md')
            documented_content = ""
            if os.path.exists(upgrades_file):
                with open(upgrades_file, 'r') as f:
                    documented_content = f.read().lower()
            
            # Check recent BuildLog and Feature entries
            recent_logs = [m for m in self.memory_data 
                          if m.get('type') in ['BuildLog', 'Feature', 'SystemUpdate', 'Enhancement']]
            
            for log in recent_logs[-10:]:  # Last 10 significant changes
                topic = log.get('topic', '')
                if topic and topic.lower() not in documented_content:
                    undocumented.append({
                        "timestamp": log.get('timestamp', ''),
                        "topic": topic,
                        "type": log.get('type', ''),
                        "description": log.get('output', '')[:200],
                        "category": log.get('category', ''),
                        "impact": self._assess_change_impact(log)
                    })
        
        except Exception as e:
            logging.warning(f"Error analyzing undocumented changes: {e}")
        
        return undocumented
    
    def _assess_change_impact(self, log: Dict) -> str:
        """Assess the impact level of a change"""
        high_impact_keywords = ['deploy', 'production', 'breaking', 'major', 'critical']
        medium_impact_keywords = ['feature', 'endpoint', 'integration', 'enhancement']
        
        text = f"{log.get('topic', '')} {log.get('output', '')}".lower()
        
        if any(keyword in text for keyword in high_impact_keywords):
            return "high"
        elif any(keyword in text for keyword in medium_impact_keywords):
            return "medium"
        else:
            return "low"
    
    def generate_structural_improvements(self) -> List[Dict]:
        """Generate suggestions for structural improvements"""
        improvements = []
        
        # Check if we have too many functions in main.py
        main_functions = len([f for f in self.system_components.get("functions", []) 
                             if f.get("file") == "main.py"])
        
        if main_functions > 20:
            improvements.append({
                "type": "refactoring",
                "priority": "medium",
                "description": f"main.py has {main_functions} functions. Consider splitting into modules.",
                "suggestion": "Create separate modules for authentication, memory management, and analytics"
            })
        
        # Check for missing error handling patterns
        error_handling_logs = [m for m in self.memory_data 
                              if 'error' in m.get('topic', '').lower() or 'fix' in m.get('type', '').lower()]
        
        if len(error_handling_logs) > 5:
            improvements.append({
                "type": "reliability",
                "priority": "high",
                "description": f"Found {len(error_handling_logs)} error-related logs. Consider implementing centralized error handling.",
                "suggestion": "Add error handling middleware and structured logging"
            })
        
        # Check for testing gaps
        test_files = [f for f in self.system_components.get("files", []) 
                     if 'test' in f.get("name", "").lower()]
        
        if len(test_files) < 2:
            improvements.append({
                "type": "testing",
                "priority": "medium",
                "description": "Limited test coverage detected. Consider adding comprehensive tests.",
                "suggestion": "Implement unit tests for core functions and integration tests for endpoints"
            })
        
        # Check for configuration management
        if not self.system_components.get("configurations", {}).get("config.json", {}).get("exists"):
            improvements.append({
                "type": "configuration",
                "priority": "low",
                "description": "No centralized configuration management detected.",
                "suggestion": "Implement environment-based configuration management"
            })
        
        return improvements
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Run complete infrastructure audit"""
        logging.info("Starting infrastructure audit...")
        
        # Load data
        self.load_memory_data()
        self.scan_codebase_components()
        
        # Run analyses
        unregistered = self.detect_unregistered_components()
        mismatches = self.detect_architecture_mismatches()
        undocumented = self.analyze_recent_undocumented_changes()
        improvements = self.generate_structural_improvements()
        
        # Generate audit report
        audit_report = {
            "audit_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "summary": {
                "total_components": len(self.system_components.get("endpoints", [])) + len(self.system_components.get("files", [])),
                "unregistered_components": len(unregistered),
                "architecture_mismatches": len(mismatches),
                "undocumented_changes": len(undocumented),
                "improvement_suggestions": len(improvements),
                "health_score": self._calculate_health_score(unregistered, mismatches, undocumented)
            },
            "system_components": self.system_components,
            "findings": {
                "unregistered_components": unregistered,
                "architecture_mismatches": mismatches,
                "undocumented_changes": undocumented,
                "structural_improvements": improvements
            },
            "recommendations": self._generate_recommendations(unregistered, mismatches, undocumented, improvements)
        }
        
        self.audit_results = audit_report
        return audit_report
    
    def _calculate_health_score(self, unregistered: List, mismatches: List, undocumented: List) -> int:
        """Calculate overall system health score (0-100)"""
        base_score = 100
        
        # Deduct points for issues
        base_score -= len(unregistered) * 5  # 5 points per unregistered component
        base_score -= len(mismatches) * 10   # 10 points per mismatch
        base_score -= len(undocumented) * 3  # 3 points per undocumented change
        
        return max(0, base_score)
    
    def _generate_recommendations(self, unregistered: List, mismatches: List, 
                                undocumented: List, improvements: List) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if unregistered:
            recommendations.append(f"Register {len(unregistered)} untracked components in system documentation")
        
        if mismatches:
            high_severity = [m for m in mismatches if m.get('severity') == 'high']
            if high_severity:
                recommendations.append(f"Address {len(high_severity)} high-severity architecture mismatches immediately")
        
        if undocumented:
            recent_undocumented = [u for u in undocumented if u.get('impact') in ['high', 'medium']]
            if recent_undocumented:
                recommendations.append(f"Document {len(recent_undocumented)} recent significant changes")
        
        high_priority_improvements = [i for i in improvements if i.get('priority') == 'high']
        if high_priority_improvements:
            recommendations.append(f"Implement {len(high_priority_improvements)} high-priority structural improvements")
        
        if not recommendations:
            recommendations.append("System architecture appears healthy. Continue regular monitoring.")
        
        return recommendations
    
    def save_audit_report(self, format_type: str = "json") -> str:
        """Save audit report to file"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "json":
            filename = f"infrastructure_audit_{timestamp}.json"
            filepath = os.path.join(self.base_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(self.audit_results, f, indent=2)
        
        elif format_type == "markdown":
            filename = f"infrastructure_audit_{timestamp}.md"
            filepath = os.path.join(self.base_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(self._generate_markdown_report())
        
        return filepath
    
    def _generate_markdown_report(self) -> str:
        """Generate markdown version of audit report"""
        if not self.audit_results:
            return "# No audit results available"
        
        summary = self.audit_results.get("summary", {})
        findings = self.audit_results.get("findings", {})
        
        markdown = f"""# Infrastructure Audit Report
        
**Generated:** {self.audit_results.get("audit_timestamp", "Unknown")}
**Health Score:** {summary.get("health_score", 0)}/100

## Summary

- **Total Components:** {summary.get("total_components", 0)}
- **Unregistered Components:** {summary.get("unregistered_components", 0)}
- **Architecture Mismatches:** {summary.get("architecture_mismatches", 0)}
- **Undocumented Changes:** {summary.get("undocumented_changes", 0)}
- **Improvement Suggestions:** {summary.get("improvement_suggestions", 0)}

## Findings

### Unregistered Components
"""
        
        for component in findings.get("unregistered_components", []):
            markdown += f"- **{component.get('component')}** ({component.get('type')}): {component.get('context', '')}\n"
        
        markdown += "\n### Architecture Mismatches\n"
        for mismatch in findings.get("architecture_mismatches", []):
            markdown += f"- **{mismatch.get('component')}** [{mismatch.get('severity')}]: {mismatch.get('description')}\n"
        
        markdown += "\n### Structural Improvements\n"
        for improvement in findings.get("structural_improvements", []):
            markdown += f"- **{improvement.get('type')}** [{improvement.get('priority')}]: {improvement.get('description')}\n"
        
        markdown += "\n## Recommendations\n"
        for rec in self.audit_results.get("recommendations", []):
            markdown += f"- {rec}\n"
        
        return markdown

def main():
    """Run infrastructure audit"""
    auditor = InfrastructureAuditor()
    report = auditor.run_full_audit()
    
    # Save reports
    json_file = auditor.save_audit_report("json")
    md_file = auditor.save_audit_report("markdown")
    
    print(f"📊 Infrastructure Audit Complete")
    print(f"Health Score: {report['summary']['health_score']}/100")
    print(f"Reports saved:")
    print(f"  - JSON: {json_file}")
    print(f"  - Markdown: {md_file}")
    
    return report

if __name__ == "__main__":
    main()
