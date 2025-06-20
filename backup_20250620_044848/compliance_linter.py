
#!/usr/bin/env python3
"""
Compliance Linter for MemoryOS

Static code analysis tool to detect potential compliance bypasses
and enforce universal output compliance across the codebase.

BEHAVIORAL AUTHORITY: AGENT_BIBLE.md, PRODUCT_BIBLE.md
- Scan all Python files for direct output patterns
- Flag functions that bypass compliance middleware
- Generate compliance reports for code review
"""

import os
import re
import ast
import json
import argparse
from typing import List, Dict, Any, Set
from pathlib import Path

class ComplianceLinter:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.violations = []
        self.warnings = []
        
        # Direct output patterns that should be flagged
        self.direct_output_patterns = [
            r'return\s+jsonify\s*\(',
            r'print\s*\(',
            r'logging\.\w+\s*\(',
            r'render_template\s*\(',
            r'redirect\s*\(',
            r'abort\s*\(',
            r'send_file\s*\(',
            r'Response\s*\(',
            r'make_response\s*\('
        ]
        
        # Functions that are allowed to use direct output (exemptions)
        self.exempt_functions = {
            'init_compliance_middleware',
            'init_output_compliance', 
            '_create_audit_log',
            '_log_bypass_to_memory',
            'main',
            '__init__'
        }
        
        # Files that are exempt from compliance checks
        self.exempt_files = {
            'compliance_middleware.py',
            'output_compliance.py',
            'compliance_linter.py',
            'test_*.py'
        }
    
    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Scan a single Python file for compliance violations"""
        violations = []
        warnings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return {
                    "file": file_path,
                    "violations": [{"type": "syntax_error", "message": "Cannot parse file"}],
                    "warnings": []
                }
            
            # Check for direct output patterns
            for line_num, line in enumerate(content.split('\n'), 1):
                for pattern in self.direct_output_patterns:
                    if re.search(pattern, line):
                        # Check if this line is in an exempt function
                        function_name = self._get_function_at_line(tree, line_num)
                        if function_name not in self.exempt_functions:
                            violations.append({
                                "type": "direct_output",
                                "line": line_num,
                                "pattern": pattern,
                                "content": line.strip(),
                                "function": function_name,
                                "message": f"Direct output detected - should use compliance middleware"
                            })
            
            # Check for missing compliance decorators on Flask routes
            route_functions = self._find_flask_routes(tree, content)
            for route_func in route_functions:
                if not self._has_compliance_decorator(tree, route_func['name']):
                    warnings.append({
                        "type": "missing_decorator",
                        "line": route_func['line'],
                        "function": route_func['name'],
                        "message": f"Flask route missing compliance decorator"
                    })
            
            # Check for compliance middleware imports
            if not self._has_compliance_imports(content) and len(violations) > 0:
                warnings.append({
                    "type": "missing_import",
                    "line": 1,
                    "message": "File has output violations but missing compliance imports"
                })
        
        except Exception as e:
            violations.append({
                "type": "scan_error",
                "message": f"Error scanning file: {e}"
            })
        
        return {
            "file": file_path,
            "violations": violations,
            "warnings": warnings
        }
    
    def _get_function_at_line(self, tree: ast.AST, line_num: int) -> str:
        """Get the function name at a specific line number"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'lineno') and node.lineno <= line_num <= (node.end_lineno or node.lineno):
                    return node.name
        return "unknown"
    
    def _find_flask_routes(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """Find Flask route functions"""
        routes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has @app.route decorator
                for decorator in node.decorator_list:
                    if (isinstance(decorator, ast.Attribute) and 
                        isinstance(decorator.value, ast.Name) and
                        decorator.value.id == 'app' and
                        decorator.attr == 'route'):
                        routes.append({
                            "name": node.name,
                            "line": node.lineno
                        })
        return routes
    
    def _has_compliance_decorator(self, tree: ast.AST, function_name: str) -> bool:
        """Check if function has compliance decorator"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        if decorator.id in ['api_output', 'ui_output', 'require_compliance']:
                            return True
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            if decorator.func.id in ['api_output', 'ui_output', 'require_compliance']:
                                return True
        return False
    
    def _has_compliance_imports(self, content: str) -> bool:
        """Check if file imports compliance middleware"""
        imports = [
            'from compliance_middleware import',
            'import compliance_middleware',
            'from output_compliance import'
        ]
        return any(imp in content for imp in imports)
    
    def scan_directory(self, directory: str = None) -> Dict[str, Any]:
        """Scan entire directory for compliance violations"""
        if directory is None:
            directory = self.base_dir
        
        results = {
            "summary": {
                "total_files": 0,
                "files_with_violations": 0,
                "total_violations": 0,
                "total_warnings": 0
            },
            "files": [],
            "compliance_score": 0
        }
        
        # Find all Python files
        python_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    # Skip exempt files
                    if not any(pattern in file for pattern in self.exempt_files):
                        python_files.append(file_path)
        
        # Scan each file
        for file_path in python_files:
            file_result = self.scan_file(file_path)
            results["files"].append(file_result)
            
            results["summary"]["total_files"] += 1
            if file_result["violations"] or file_result["warnings"]:
                results["summary"]["files_with_violations"] += 1
            results["summary"]["total_violations"] += len(file_result["violations"])
            results["summary"]["total_warnings"] += len(file_result["warnings"])
        
        # Calculate compliance score
        total_issues = results["summary"]["total_violations"] + results["summary"]["total_warnings"]
        if results["summary"]["total_files"] > 0:
            compliance_score = max(0, 100 - (total_issues * 10))  # 10 points per issue
            results["compliance_score"] = compliance_score
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable compliance report"""
        report = []
        report.append("=" * 60)
        report.append("MEMORYOS COMPLIANCE LINTER REPORT")
        report.append("=" * 60)
        report.append(f"Compliance Score: {results['compliance_score']}/100")
        report.append("")
        
        summary = results["summary"]
        report.append(f"Files Scanned: {summary['total_files']}")
        report.append(f"Files with Issues: {summary['files_with_violations']}")
        report.append(f"Total Violations: {summary['total_violations']}")
        report.append(f"Total Warnings: {summary['total_warnings']}")
        report.append("")
        
        if summary['total_violations'] > 0:
            report.append("VIOLATIONS (Must Fix):")
            report.append("-" * 30)
            for file_result in results["files"]:
                if file_result["violations"]:
                    report.append(f"\n📄 {file_result['file']}")
                    for violation in file_result["violations"]:
                        report.append(f"  ❌ Line {violation.get('line', 'N/A')}: {violation['message']}")
                        if 'content' in violation:
                            report.append(f"     Code: {violation['content']}")
            report.append("")
        
        if summary['total_warnings'] > 0:
            report.append("WARNINGS (Recommended Fixes):")
            report.append("-" * 30)
            for file_result in results["files"]:
                if file_result["warnings"]:
                    report.append(f"\n📄 {file_result['file']}")
                    for warning in file_result["warnings"]:
                        report.append(f"  ⚠️  Line {warning.get('line', 'N/A')}: {warning['message']}")
        
        report.append("\nRECOMMENDATIONS:")
        report.append("- Use send_user_output() for all user-facing content")
        report.append("- Add @api_output decorator to Flask routes")
        report.append("- Import compliance_middleware in files with direct output")
        report.append("- Review AGENT_BIBLE.md for compliance requirements")
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='MemoryOS Compliance Linter')
    parser.add_argument('--directory', '-d', default='.', help='Directory to scan')
    parser.add_argument('--output', '-o', help='Output file for report')
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text', help='Output format')
    parser.add_argument('--fail-on-violations', action='store_true', help='Exit with error code if violations found')
    
    args = parser.parse_args()
    
    linter = ComplianceLinter(args.directory)
    results = linter.scan_directory(args.directory)
    
    if args.format == 'json':
        output = json.dumps(results, indent=2)
    else:
        output = linter.generate_report(results)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Report saved to {args.output}")
    else:
        print(output)
    
    # Exit with error code if violations found and flag is set
    if args.fail_on_violations and results["summary"]["total_violations"] > 0:
        exit(1)

if __name__ == '__main__':
    main()
