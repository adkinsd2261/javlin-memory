
"""
Output Compliance System for MemoryOS

This module implements post-processing and confirmation enforcement to prevent
agent "action language" without backend validation per AGENT_BIBLE.md and PRODUCT_BIBLE.md.

BEHAVIORAL AUTHORITY: AGENT_BIBLE.md, PRODUCT_BIBLE.md
- Block any implied confirmation without verifiable backend results
- Enforce confirmation requirements for all agent outputs
- Log GPT drift violations as BuildLogs
- Surface pending actions in UI/session logs
"""

import os
import json
import datetime
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from functools import wraps
import requests

class OutputCompliance:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.memory_file = os.path.join(base_dir, 'memory.json')
        self.drift_log_file = os.path.join(base_dir, 'gpt_drift_log.json')
        self.pending_actions_file = os.path.join(base_dir, 'pending_actions.json')
        
        # Action language patterns that require confirmation
        self.action_patterns = [
            # First-person action language
            r"\bi'll\s+\w+|\bi\s+am\s+\w+ing|\bi\s+will\s+\w+|\bi\s+have\s+\w+ed",
            r"\bi'm\s+\w+ing|\bi've\s+\w+ed|\bi\s+can\s+now\s+\w+",
            
            # Completion claims
            r"\bcomplete\b|\bfinished\b|\bdone\b|\bready\b|\blive\b|\bactive\b",
            r"\bdeployed\b|\brunning\b|\bworking\b|\bsuccessful\b|\bimplemented\b",
            
            # Action statements
            r"\bstep\s+complete\b|\btask\s+finished\b|\bfeature\s+is\s+\w+",
            r"\bhas\s+been\s+\w+ed\b|\bnow\s+\w+ing\b|\bcurrently\s+\w+ing\b",
            
            # Status claims
            r"\bis\s+now\s+\w+|\bshould\s+now\s+work\b|\bwill\s+now\s+\w+",
            r"\benabled\b|\bactivated\b|\bexecuted\b|\bprocessed\b"
        ]
        
        # Allowed confirmation sources
        self.valid_confirmation_sources = [
            'api_endpoint_check',
            'backend_validation',
            'human_confirmation',
            'system_verification',
            'connection_validation'
        ]
        
    def post_process_output(self, output_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Post-process agent output to detect and block action language without confirmation
        
        Returns: {
            'processed_output': str,
            'compliance_status': str,
            'blocked': bool,
            'violations': List[str],
            'pending_confirmation': bool
        }
        """
        if not output_text:
            return {
                'processed_output': output_text,
                'compliance_status': 'valid',
                'blocked': False,
                'violations': [],
                'pending_confirmation': False
            }
        
        context = context or {}
        violations = []
        blocked = False
        pending_confirmation = False
        
        # Check for action language patterns
        detected_patterns = self._detect_action_language(output_text)
        
        if detected_patterns:
            # Check if confirmation is provided
            confirmation_status = context.get('confirmation_status', {})
            confirmed = confirmation_status.get('confirmed', False)
            confirmation_method = confirmation_status.get('confirmation_method', 'none')
            
            if not confirmed or confirmation_method not in self.valid_confirmation_sources:
                # Block the output and require confirmation
                violations.extend([f"Action language detected: {pattern}" for pattern in detected_patterns])
                blocked = True
                pending_confirmation = True
                
                # Log GPT drift violation
                self._log_gpt_drift_violation(output_text, detected_patterns, context)
                
                # Add to pending actions
                self._add_pending_action(output_text, detected_patterns, context)
                
                # Replace output with compliance message
                processed_output = self._generate_compliance_message(output_text, detected_patterns)
            else:
                # Confirmation provided, allow output with confirmation note
                processed_output = self._add_confirmation_note(output_text, confirmation_status)
        else:
            processed_output = output_text
        
        return {
            'processed_output': processed_output,
            'compliance_status': 'blocked' if blocked else 'valid',
            'blocked': blocked,
            'violations': violations,
            'pending_confirmation': pending_confirmation,
            'detected_patterns': detected_patterns
        }
    
    def _detect_action_language(self, text: str) -> List[str]:
        """Detect action language patterns in text"""
        detected = []
        text_lower = text.lower()
        
        for pattern in self.action_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                detected.extend(matches)
        
        return list(set(detected))  # Remove duplicates
    
    def _generate_compliance_message(self, original_output: str, detected_patterns: List[str]) -> str:
        """Generate compliance-safe message for blocked outputs"""
        return f"""⚠️ **Awaiting backend confirmation. Action not yet complete.**

**AGENT_BIBLE.md Compliance:** The agent attempted to use action language without verified backend confirmation.

**Detected patterns:** {', '.join(detected_patterns)}

**Next steps:**
1. Verify via API endpoint check (GET /health, /system-health)
2. Confirm specific functionality via targeted endpoints
3. Get human operator confirmation if automated validation fails

**Original message blocked for compliance.**

Per AGENT_BIBLE.md: No feature, file, or status should be presented as complete until verified."""
    
    def _add_confirmation_note(self, output_text: str, confirmation_status: Dict[str, Any]) -> str:
        """Add confirmation note to validated outputs"""
        method = confirmation_status.get('confirmation_method', 'unknown')
        timestamp = confirmation_status.get('timestamp', datetime.datetime.now(datetime.timezone.utc).isoformat())
        
        return f"""{output_text}

✅ **Backend Confirmed** (Method: {method}, Time: {timestamp[:19]})"""
    
    def _log_gpt_drift_violation(self, output_text: str, detected_patterns: List[str], context: Dict[str, Any]):
        """Log GPT drift violation as BuildLog per requirements"""
        try:
            # Create GPT drift BuildLog entry
            drift_memory = {
                "topic": "GPT Drift Violation - Unconfirmed Action Language",
                "type": "BuildLog",
                "input": f"Agent attempted action language without backend confirmation: {detected_patterns}",
                "output": f"Blocked agent output containing: {', '.join(detected_patterns)}. Original: {output_text[:100]}...",
                "score": 0,
                "maxScore": 25,
                "success": False,
                "category": "compliance",
                "tags": ["gpt_drift", "compliance", "action_language", "blocked"],
                "context": "Agent compliance violation - attempted unconfirmed action language per AGENT_BIBLE.md",
                "related_to": [],
                "reviewed": False,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "auto_generated": True,
                "confirmed": True,
                "confirmation_method": "compliance_system",
                "confirmation_required": False,
                "replit_connection_confirmed": True,
                "drift_violation": {
                    "detected_patterns": detected_patterns,
                    "original_output": output_text,
                    "context": context,
                    "violation_type": "action_language_without_confirmation"
                }
            }
            
            # Save to memory
            try:
                with open(self.memory_file, 'r') as f:
                    memory = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                memory = []
            
            memory.append(drift_memory)
            
            with open(self.memory_file, 'w') as f:
                json.dump(memory, f, indent=2)
                
            # Also save to dedicated drift log
            try:
                with open(self.drift_log_file, 'r') as f:
                    drift_log = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                drift_log = {'violations': []}
            
            drift_log['violations'].append({
                'timestamp': drift_memory['timestamp'],
                'patterns': detected_patterns,
                'output_snippet': output_text[:200],
                'context': context
            })
            
            # Keep only last 100 violations
            if len(drift_log['violations']) > 100:
                drift_log['violations'] = drift_log['violations'][-100:]
            
            with open(self.drift_log_file, 'w') as f:
                json.dump(drift_log, f, indent=2)
                
            logging.warning(f"GPT drift violation logged: {detected_patterns}")
            
        except Exception as e:
            logging.error(f"Error logging GPT drift violation: {e}")
    
    def _add_pending_action(self, output_text: str, detected_patterns: List[str], context: Dict[str, Any]):
        """Add action to pending confirmations list"""
        try:
            try:
                with open(self.pending_actions_file, 'r') as f:
                    pending_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pending_data = {'pending_actions': []}
            
            pending_action = {
                'id': len(pending_data['pending_actions']) + 1,
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'detected_patterns': detected_patterns,
                'original_output': output_text,
                'context': context,
                'status': 'pending_confirmation',
                'confirmation_methods_available': [
                    'GET /health - Check system health',
                    'GET /system-health - Comprehensive status',
                    'Manual operator confirmation',
                    'Specific endpoint validation'
                ]
            }
            
            pending_data['pending_actions'].append(pending_action)
            
            # Keep only last 50 pending actions
            if len(pending_data['pending_actions']) > 50:
                pending_data['pending_actions'] = pending_data['pending_actions'][-50:]
            
            with open(self.pending_actions_file, 'w') as f:
                json.dump(pending_data, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error adding pending action: {e}")
    
    def get_pending_actions(self) -> List[Dict[str, Any]]:
        """Get list of pending actions awaiting confirmation"""
        try:
            with open(self.pending_actions_file, 'r') as f:
                pending_data = json.load(f)
            return pending_data.get('pending_actions', [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def get_drift_violations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent GPT drift violations"""
        try:
            with open(self.drift_log_file, 'r') as f:
                drift_log = json.load(f)
            violations = drift_log.get('violations', [])
            return violations[-limit:] if violations else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def clear_pending_action(self, action_id: int, confirmation_method: str, operator: str = 'system'):
        """Clear a pending action with confirmation"""
        try:
            with open(self.pending_actions_file, 'r') as f:
                pending_data = json.load(f)
            
            # Find and update the action
            for action in pending_data['pending_actions']:
                if action['id'] == action_id:
                    action['status'] = 'confirmed'
                    action['confirmation_method'] = confirmation_method
                    action['confirmed_by'] = operator
                    action['confirmed_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    break
            
            with open(self.pending_actions_file, 'w') as f:
                json.dump(pending_data, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error clearing pending action: {e}")

# Decorator for output compliance
def require_output_compliance(base_dir: str):
    """Decorator to enforce output compliance on agent functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Apply compliance to result if it's a dict with output
            if isinstance(result, dict):
                output_compliance = OutputCompliance(base_dir)
                
                # Check various output fields
                output_fields = ['output', 'message', 'result', 'status']
                for field in output_fields:
                    if field in result and isinstance(result[field], str):
                        compliance_result = output_compliance.post_process_output(
                            result[field], 
                            result.get('context', {})
                        )
                        
                        if compliance_result['blocked']:
                            # Replace with compliance message
                            result[field] = compliance_result['processed_output']
                            result['compliance_blocked'] = True
                            result['compliance_violations'] = compliance_result['violations']
                            result['pending_confirmation'] = True
                            
                            # Override success status
                            result['success'] = False
                            break
                        else:
                            result[field] = compliance_result['processed_output']
                            result['compliance_validated'] = True
            
            return result
        return wrapper
    return decorator

# Global compliance instance
output_compliance = None

def init_output_compliance(base_dir: str):
    """Initialize global output compliance instance"""
    global output_compliance
    output_compliance = OutputCompliance(base_dir)
    return output_compliance
