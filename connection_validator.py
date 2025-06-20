
"""
Connection Validation Utility for MemoryOS

This module provides comprehensive connection validation for the connection-first 
confirmation system, ensuring all agent confirmations are backed by fresh backend checks.

BEHAVIORAL AUTHORITY: AGENT_BIBLE.md
- All "live" or "complete" claims require fresh connection validation
- Stale or lost connections block agent confirmations
- Every connection check is logged for audit compliance
"""

import os
import json
import datetime
import logging
import requests
from typing import Dict, List, Optional, Any

class ConnectionValidator:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.cache_file = os.path.join(base_dir, 'connection_cache.json')
        self.connection_log_file = os.path.join(base_dir, 'connection_audit.json')
        self.cache_duration = 60  # seconds
        
    def validate_fresh_connection(self, action_type: str, require_endpoints: List[str] = None) -> Dict[str, Any]:
        """Perform comprehensive fresh connection validation"""
        try:
            current_time = datetime.datetime.now(datetime.timezone.utc)
            
            validation_result = {
                'timestamp': current_time.isoformat(),
                'action_type': action_type,
                'validation_passed': False,
                'connection_fresh': False,
                'endpoints_validated': [],
                'failed_endpoints': [],
                'overall_health_score': 0,
                'confirmation_allowed': False,
                'cache_used': False,
                'validation_details': {}
            }
            
            # Define endpoints to test based on action type
            if require_endpoints is None:
                require_endpoints = self._get_required_endpoints(action_type)
            
            # Test each required endpoint
            endpoint_results = []
            successful_checks = 0
            
            for endpoint in require_endpoints:
                endpoint_result = self._test_endpoint(endpoint)
                endpoint_results.append(endpoint_result)
                
                if endpoint_result['status'] == 'success':
                    successful_checks += 1
                    validation_result['endpoints_validated'].append(endpoint)
                else:
                    validation_result['failed_endpoints'].append({
                        'endpoint': endpoint,
                        'error': endpoint_result.get('error', 'Unknown failure')
                    })
            
            # Calculate health score
            validation_result['overall_health_score'] = (successful_checks / len(require_endpoints)) * 100
            validation_result['connection_fresh'] = True  # Always fresh since we just tested
            validation_result['validation_passed'] = successful_checks >= len(require_endpoints) * 0.66  # 66% success rate
            validation_result['confirmation_allowed'] = validation_result['validation_passed']
            
            validation_result['validation_details'] = {
                'total_endpoints': len(require_endpoints),
                'successful_checks': successful_checks,
                'success_rate': f"{(successful_checks / len(require_endpoints)) * 100:.1f}%",
                'endpoint_results': endpoint_results
            }
            
            # Log this validation
            self._log_validation(validation_result)
            
            # Cache successful results
            if validation_result['validation_passed']:
                self._cache_validation(validation_result)
            
            return validation_result
            
        except Exception as e:
            logging.error(f"Connection validation error: {e}")
            return {
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'action_type': action_type,
                'validation_passed': False,
                'connection_fresh': False,
                'confirmation_allowed': False,
                'error': str(e)
            }
    
    def _get_required_endpoints(self, action_type: str) -> List[str]:
        """Get required endpoints based on action type"""
        endpoint_map = {
            'live_claim': ['/health', '/system-health', '/memory'],
            'deployment': ['/health', '/system-health', '/'],
            'feature_activation': ['/health', '/system-health', '/stats'],
            'system_change': ['/health', '/memory', '/stats'],
            'file_check': ['/health', '/'],
            'api_check': ['/health', '/memory', '/stats', '/system-health'],
            'session_operation': ['/health', '/memory'],
            'general': ['/health', '/']
        }
        
        return endpoint_map.get(action_type, endpoint_map['general'])
    
    def _test_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """Test individual endpoint connectivity"""
        try:
            url = f"http://127.0.0.1:80{endpoint}"
            start_time = datetime.datetime.now()
            
            response = requests.get(url, timeout=5)
            response_time = (datetime.datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                'endpoint': endpoint,
                'status': 'success' if response.status_code < 400 else 'failed',
                'status_code': response.status_code,
                'response_time_ms': response_time,
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            
            # Additional validation for specific endpoints
            if endpoint == '/health' and response.status_code == 200:
                try:
                    health_data = response.json()
                    result['health_score'] = health_data.get('connection_health_score', 0)
                    result['agent_ready'] = health_data.get('agent_confirmation_ready', False)
                except:
                    result['health_validation'] = 'invalid_json'
            
            return result
            
        except requests.RequestException as e:
            return {
                'endpoint': endpoint,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
    
    def _cache_validation(self, validation_result: Dict[str, Any]):
        """Cache successful validation results"""
        try:
            cache_data = {
                'validation_result': validation_result,
                'cached_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'expires_at': (datetime.datetime.now(datetime.timezone.utc) + 
                             datetime.timedelta(seconds=self.cache_duration)).isoformat()
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            logging.warning(f"Could not cache validation: {e}")
    
    def _log_validation(self, validation_result: Dict[str, Any]):
        """Log validation for audit trail"""
        try:
            # Load existing log
            try:
                with open(self.connection_log_file, 'r') as f:
                    log_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                log_data = {'validation_log': []}
            
            # Add new entry
            log_entry = {
                'timestamp': validation_result['timestamp'],
                'action_type': validation_result['action_type'],
                'validation_passed': validation_result['validation_passed'],
                'health_score': validation_result['overall_health_score'],
                'endpoints_tested': len(validation_result.get('endpoints_validated', [])) + len(validation_result.get('failed_endpoints', [])),
                'confirmation_allowed': validation_result['confirmation_allowed']
            }
            
            log_data['validation_log'].append(log_entry)
            
            # Keep only last 100 entries
            if len(log_data['validation_log']) > 100:
                log_data['validation_log'] = log_data['validation_log'][-100:]
            
            with open(self.connection_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error logging connection validation: {e}")
    
    def get_cached_validation(self, action_type: str) -> Optional[Dict[str, Any]]:
        """Get cached validation if still valid"""
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            expires_at = datetime.datetime.fromisoformat(cache_data['expires_at'].replace('Z', '+00:00'))
            current_time = datetime.datetime.now(datetime.timezone.utc)
            
            if current_time < expires_at:
                cached_result = cache_data['validation_result']
                cached_result['cache_used'] = True
                cached_result['cache_age_seconds'] = (current_time - datetime.datetime.fromisoformat(cache_data['cached_at'].replace('Z', '+00:00'))).total_seconds()
                return cached_result
            
            return None
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None
    
    def force_fresh_validation(self, action_type: str, require_endpoints: List[str] = None) -> Dict[str, Any]:
        """Force fresh validation regardless of cache"""
        # Clear cache first
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
        except:
            pass
        
        return self.validate_fresh_connection(action_type, require_endpoints)
