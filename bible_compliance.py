
"""
Bible Compliance System for MemoryOS

This module enforces AGENT_BIBLE.md, MEMORY_BIBLE.md, and PRODUCT_BIBLE.md compliance
for all agent actions, confirmations, logs, and user-facing outputs.

BEHAVIORAL AUTHORITY: All .md bible files
- Parse bible documents as live policy objects on startup
- All agent actions must comply with bible rules
- Any claim of "live" requires API or explicit user confirmation
- Block or delay outputs if confirmation not obtained
"""

import os
import json
import datetime
import logging
import re
from functools import wraps
from typing import Dict, List, Optional, Any, Callable
import requests

class BibleCompliance:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.bible_policies = {}
        self.compliance_cache = {}
        self.load_bible_policies()
        
    def load_bible_policies(self):
        """Load and parse all bible documents as live policy objects"""
        bible_files = [
            'AGENT_BIBLE.md',
            'MEMORY_BIBLE.md', 
            'PRODUCT_BIBLE.md',
            'SECURITY_BIBLE.md',
            'PRIVACY_POLICY.md'
        ]
        
        for bible_file in bible_files:
            bible_path = os.path.join(self.base_dir, bible_file)
            if os.path.exists(bible_path):
                try:
                    with open(bible_path, 'r') as f:
                        content = f.read()
                    
                    self.bible_policies[bible_file] = {
                        'content': content,
                        'last_updated': os.path.getmtime(bible_path),
                        'policies': self._extract_policies(content, bible_file),
                        'compliance_rules': self._extract_compliance_rules(content, bible_file)
                    }
                    
                    logging.info(f"Loaded bible policies from {bible_file}")
                    
                except Exception as e:
                    logging.error(f"Error loading {bible_file}: {e}")
                    self.bible_policies[bible_file] = {
                        'content': '',
                        'last_updated': 0,
                        'policies': [],
                        'compliance_rules': [],
                        'error': str(e)
                    }
            else:
                logging.warning(f"Bible file not found: {bible_file}")
                self.bible_policies[bible_file] = {
                    'content': '',
                    'last_updated': 0,
                    'policies': [],
                    'compliance_rules': [],
                    'missing': True
                }
    
    def _extract_policies(self, content: str, bible_file: str) -> List[Dict[str, Any]]:
        """Extract policy rules from bible content"""
        policies = []
        
        if bible_file == 'AGENT_BIBLE.md':
            # Extract agent behavior rules
            if 'cannot execute commands' in content.lower():
                policies.append({
                    'type': 'execution_boundary',
                    'rule': 'Agent cannot execute commands unless triggered by Replit Assistant or human operator',
                    'enforcement': 'block_autonomous_execution'
                })
            
            if 'manual confirmation' in content.lower():
                policies.append({
                    'type': 'confirmation_requirement', 
                    'rule': 'Manual confirmation required for any "live" feature claims',
                    'enforcement': 'require_confirmation'
                })
                
            if 'never claim' in content.lower() and 'live' in content.lower():
                policies.append({
                    'type': 'live_claim_restriction',
                    'rule': 'Never claim state or feature is "live" unless validated by endpoint or human confirmation',
                    'enforcement': 'validate_live_claims'
                })
        
        elif bible_file == 'MEMORY_BIBLE.md':
            # Extract memory schema rules
            policies.append({
                'type': 'memory_schema',
                'rule': 'All memory entries must follow standardized schema',
                'enforcement': 'validate_schema'
            })
        
        elif bible_file == 'SECURITY_BIBLE.md':
            # Extract security policies
            if 'principle of least privilege' in content.lower():
                policies.append({
                    'type': 'access_control',
                    'rule': 'Principle of least privilege for all endpoints and agent actions',
                    'enforcement': 'restrict_access'
                })
        
        return policies
    
    def _extract_compliance_rules(self, content: str, bible_file: str) -> List[Dict[str, Any]]:
        """Extract specific compliance rules and requirements"""
        rules = []
        
        # Look for specific patterns that indicate compliance requirements
        patterns = {
            'confirmation_required': r'confirmation required|must.*confirm|require.*confirmation',
            'manual_intervention': r'manual.*required|human.*required|operator.*required',
            'api_validation': r'endpoint.*validation|api.*check|observable.*endpoint',
            'security_compliance': r'security.*compliance|secure.*handling|access.*control',
            'data_handling': r'data.*rights|privacy.*compliance|user.*data'
        }
        
        for rule_type, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                rules.append({
                    'type': rule_type,
                    'matches': len(matches),
                    'enforcement_level': 'strict' if 'must' in ' '.join(matches).lower() else 'warning'
                })
        
        return rules
    
    def requires_confirmation(self, action_type: str = 'general'):
        """Decorator to enforce confirmation requirements per AGENT_BIBLE.md"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Check if action requires confirmation
                confirmation_required = self._check_confirmation_requirement(action_type, kwargs)
                
                if confirmation_required['required']:
                    # Check if confirmation already provided
                    confirmation_status = kwargs.get('confirmation_status', {})
                    
                    if not confirmation_status.get('confirmed', False):
                        return {
                            'status': '⚠️ Manual confirmation required',
                            'message': confirmation_required['reason'],
                            'bible_compliance': False,
                            'confirmation_required': True,
                            'action_blocked': True,
                            'next_steps': confirmation_required['next_steps']
                        }
                
                # Add confirmation tracking to result
                result = func(*args, **kwargs)
                if isinstance(result, dict):
                    result['bible_compliance'] = True
                    result['confirmation_status'] = confirmation_status
                
                return result
            return wrapper
        return decorator
    
    def _check_confirmation_requirement(self, action_type: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Check if action requires confirmation per bible policies with connection-first validation"""
        
        # FIRST: Always check connection for any confirmation request
        connection_validation = self.require_fresh_connection_check(action_type)
        
        if connection_validation['confirmation_blocked']:
            return {
                'required': True,
                'reason': f'Connection-first validation failed: {connection_validation["block_reason"]}',
                'next_steps': [
                    'Verify backend connection via GET /health',
                    'Check system status via GET /system-health', 
                    'Ensure fresh connection before confirmation',
                    'Reconnect if connection is stale or lost'
                ],
                'connection_blocked': True,
                'connection_status': connection_validation
            }
        
        # Check for "live" claims
        output_text = kwargs.get('output', '')
        if any(word in output_text.lower() for word in ['live', 'deployed', 'running', 'active', 'complete', 'working', 'ready']):
            return {
                'required': True,
                'reason': 'AGENT_BIBLE.md: Cannot claim "live" status without fresh endpoint validation',
                'next_steps': [
                    'Perform fresh connection check via GET /health',
                    'Verify specific feature via targeted endpoint',
                    'Get human confirmation if automated validation fails',
                    'Check system health for comprehensive status'
                ],
                'connection_status': connection_validation
            }
        
        # Check high-risk actions
        high_risk_actions = ['deployment', 'feature_activation', 'system_change', 'endpoint_creation', 'file_modification', 'api_change']
        if action_type in high_risk_actions:
            return {
                'required': True,
                'reason': f'AGENT_BIBLE.md: {action_type} requires fresh connection validation and manual confirmation',
                'next_steps': [
                    'Perform fresh connection check via GET /health',
                    'Human operator approval required',
                    'System validation via relevant endpoints',
                    'Endpoint verification for changed functionality'
                ],
                'connection_status': connection_validation
            }
        
        # Any system state changes require connection validation
        state_change_actions = ['session_save', 'session_load', 'memory_add', 'config_update']
        if action_type in state_change_actions:
            return {
                'required': True,
                'reason': f'System state change requires fresh connection validation',
                'next_steps': [
                    'Verify connection via GET /health',
                    'Confirm system health via GET /system-health',
                    'Validate state change was successful'
                ],
                'connection_status': connection_validation
            }
        
        return {
            'required': False, 
            'reason': '', 
            'next_steps': [],
            'connection_status': connection_validation
        }
    
    def validate_memory_entry(self, memory_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Validate memory entry against MEMORY_BIBLE.md schema"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'compliance_score': 100
        }
        
        # Required fields check
        required_fields = ['topic', 'type', 'input', 'output', 'score', 'maxScore', 'success', 'category', 'reviewed']
        missing_fields = [field for field in required_fields if field not in memory_entry]
        
        if missing_fields:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Missing required fields: {missing_fields}")
            validation_result['compliance_score'] -= 20
        
        # Add confirmation tracking
        if 'confirmed' not in memory_entry:
            memory_entry['confirmed'] = False
            memory_entry['confirmation_method'] = 'none'
            memory_entry['confirmation_required'] = True
            validation_result['warnings'].append("Memory entry missing confirmation status")
            validation_result['compliance_score'] -= 10
        
        # Add Replit connection confirmation
        if 'replit_connection_confirmed' not in memory_entry:
            memory_entry['replit_connection_confirmed'] = False
            validation_result['warnings'].append("Replit connection status not confirmed")
            validation_result['compliance_score'] -= 5
        
        return validation_result
    
    def check_replit_connection(self, require_fresh: bool = True) -> Dict[str, Any]:
        """Validate real-time connection to Replit backend with fresh check requirements"""
        try:
            current_time = datetime.datetime.now(datetime.timezone.utc)
            
            # Check cache if fresh check not required
            if not require_fresh:
                cache_file = os.path.join(self.base_dir, 'connection_cache.json')
                try:
                    with open(cache_file, 'r') as f:
                        cached_result = json.load(f)
                    
                    cache_time = datetime.datetime.fromisoformat(cached_result['timestamp'].replace('Z', '+00:00'))
                    if (current_time - cache_time).total_seconds() < 3600:  # Cache valid for 1 hour
                        cached_result['from_cache'] = True
                        return cached_result
                except (FileNotFoundError, json.JSONDecodeError, KeyError):
                    pass
            
            # Perform fresh connection checks
            local_checks = [
                'http://127.0.0.1:80/',
                'http://127.0.0.1:80/memory',
                'http://127.0.0.1:80/stats'
            ]
            
            connection_status = {
                'connected': False,
                'checks_passed': 0,
                'total_checks': len(local_checks),
                'timestamp': current_time.isoformat(),
                'fresh_check': True,
                'from_cache': False,
                'details': [],
                'validation_level': 'comprehensive'
            }
            
            for endpoint in local_checks:
                try:
                    response = requests.get(endpoint, timeout=3)
                    if response.status_code == 200:
                        connection_status['checks_passed'] += 1
                        connection_status['details'].append({
                            'endpoint': endpoint,
                            'status': 'success',
                            'response_code': response.status_code,
                            'response_time_ms': response.elapsed.total_seconds() * 1000
                        })
                    else:
                        connection_status['details'].append({
                            'endpoint': endpoint,
                            'status': 'failed',
                            'response_code': response.status_code
                        })
                except Exception as e:
                    connection_status['details'].append({
                        'endpoint': endpoint,
                        'status': 'error',
                        'error': str(e)
                    })
            
            connection_status['connected'] = connection_status['checks_passed'] >= 2  # At least 2 of 3 must pass
            connection_status['connection_quality'] = (connection_status['checks_passed'] / connection_status['total_checks']) * 100
            
            # Cache the result
            cache_file = os.path.join(self.base_dir, 'connection_cache.json')
            try:
                with open(cache_file, 'w') as f:
                    json.dump(connection_status, f, indent=2)
            except Exception as e:
                logging.warning(f"Could not cache connection result: {e}")
            
            return connection_status
            
        except Exception as e:
            return {
                'connected': False,
                'checks_passed': 0,
                'total_checks': 0,
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'fresh_check': True,
                'from_cache': False,
                'error': str(e),
                'validation_level': 'error'
            }
    
    def require_fresh_connection_check(self, action_type: str = 'general') -> Dict[str, Any]:
        """Require fresh connection check before agent confirmations"""
        try:
            connection_status = self.check_replit_connection(require_fresh=True)
            
            validation_result = {
                'connection_valid': connection_status['connected'],
                'fresh_check_performed': connection_status.get('fresh_check', False),
                'connection_quality': connection_status.get('connection_quality', 0),
                'timestamp': connection_status['timestamp'],
                'action_type': action_type,
                'confirmation_blocked': False,
                'reconnection_required': False
            }
            
            # Determine if confirmation should be blocked
            if not connection_status['connected']:
                validation_result['confirmation_blocked'] = True
                validation_result['reconnection_required'] = True
                validation_result['block_reason'] = 'Backend connection lost or unavailable'
            
            elif connection_status.get('connection_quality', 0) < 66:  # Less than 2/3 checks passed
                validation_result['confirmation_blocked'] = True
                validation_result['block_reason'] = 'Connection quality degraded - require full validation'
            
            elif connection_status.get('from_cache', False):
                validation_result['confirmation_blocked'] = True  
                validation_result['block_reason'] = 'Stale connection data - fresh check required'
            
            return validation_result
            
        except Exception as e:
            return {
                'connection_valid': False,
                'fresh_check_performed': False,
                'connection_quality': 0,
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'action_type': action_type,
                'confirmation_blocked': True,
                'reconnection_required': True,
                'error': str(e),
                'block_reason': 'Connection validation failed with error'
            }
    
    def run_compliance_audit(self) -> Dict[str, Any]:
        """Run comprehensive compliance audit against all bible policies"""
        audit_result = {
            'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'overall_compliance': True,
            'compliance_score': 100,
            'bible_status': {},
            'violations': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check each bible file status
        for bible_file, policies in self.bible_policies.items():
            if policies.get('missing'):
                audit_result['violations'].append(f"{bible_file} is missing - behavioral guidelines undefined")
                audit_result['compliance_score'] -= 20
                audit_result['overall_compliance'] = False
            elif policies.get('error'):
                audit_result['warnings'].append(f"{bible_file} has loading errors: {policies['error']}")
                audit_result['compliance_score'] -= 10
            else:
                audit_result['bible_status'][bible_file] = {
                    'loaded': True,
                    'policies_count': len(policies['policies']),
                    'compliance_rules': len(policies['compliance_rules']),
                    'last_updated': datetime.datetime.fromtimestamp(policies['last_updated']).isoformat()
                }
        
        # Check memory entries for compliance
        try:
            memory_file = os.path.join(self.base_dir, 'memory.json')
            with open(memory_file, 'r') as f:
                memories = json.load(f)
            
            unconfirmed_memories = [m for m in memories if not m.get('confirmed', False)]
            if unconfirmed_memories:
                audit_result['warnings'].append(f"{len(unconfirmed_memories)} memory entries lack confirmation")
                audit_result['compliance_score'] -= min(len(unconfirmed_memories), 20)
            
            live_claims = [m for m in memories if any(word in m.get('output', '').lower() 
                                                    for word in ['live', 'deployed', 'active']) 
                          and not m.get('confirmed', False)]
            if live_claims:
                audit_result['violations'].append(f"{len(live_claims)} unconfirmed 'live' claims found")
                audit_result['compliance_score'] -= 30
                audit_result['overall_compliance'] = False
                
        except Exception as e:
            audit_result['warnings'].append(f"Could not audit memory entries: {e}")
        
        # Check Replit connection
        connection_status = self.check_replit_connection()
        if not connection_status['connected']:
            audit_result['warnings'].append("Replit connection could not be confirmed")
            audit_result['compliance_score'] -= 10
        
        # Generate recommendations
        if audit_result['compliance_score'] < 100:
            audit_result['recommendations'].extend([
                "Review and confirm all unconfirmed memory entries",
                "Validate 'live' claims with endpoint checks",
                "Ensure all bible documents are present and readable",
                "Verify Replit connection status"
            ])
        
        return audit_result

# Create global compliance instance
bible_compliance = None

def init_bible_compliance(base_dir: str):
    """Initialize global bible compliance instance"""
    global bible_compliance
    bible_compliance = BibleCompliance(base_dir)
    return bible_compliance

def requires_confirmation(action_type: str = 'general'):
    """Global decorator for confirmation requirements"""
    if bible_compliance:
        return bible_compliance.requires_confirmation(action_type)
    else:
        # Fallback if compliance not initialized
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                if isinstance(result, dict):
                    result['bible_compliance'] = False
                    result['warning'] = 'Bible compliance not initialized'
                return result
            return wrapper
        return decorator
