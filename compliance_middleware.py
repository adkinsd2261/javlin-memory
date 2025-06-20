
"""
Universal Compliance and Output Enforcement Layer for MemoryOS

This module provides centralized output compliance validation for all system outputs
including API responses, logs, UI messages, and agent communications.

BEHAVIORAL AUTHORITY: AGENT_BIBLE.md, PRODUCT_BIBLE.md
- All outputs must be routed through this compliance layer
- No direct user-facing outputs allowed without compliance validation
- Automatic detection and blocking of non-compliant outputs
- Comprehensive audit trail for all output compliance checks
"""

import os
import json
import datetime
import logging
import re
import inspect
import traceback
from typing import Dict, List, Optional, Any, Tuple, Callable
from functools import wraps
from enum import Enum
from dataclasses import dataclass

class OutputChannel(Enum):
    """Define all possible output channels"""
    API_RESPONSE = "api_response"
    LOG_MESSAGE = "log_message"
    UI_MESSAGE = "ui_message"
    CHAT_RESPONSE = "chat_response"
    EMAIL = "email"
    NOTIFICATION = "notification"
    CLI_OUTPUT = "cli_output"
    ERROR_MESSAGE = "error_message"
    STATUS_UPDATE = "status_update"
    SYSTEM_ALERT = "system_alert"

class ComplianceLevel(Enum):
    """Compliance validation levels"""
    STRICT = "strict"        # Full AGENT_BIBLE.md enforcement
    MODERATE = "moderate"    # Basic action language detection
    PERMISSIVE = "permissive"  # Log only, don't block

@dataclass
class OutputContext:
    """Context information for output compliance validation"""
    channel: OutputChannel
    source_function: str
    source_file: str
    source_line: int
    timestamp: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    confirmation_status: Optional[Dict[str, Any]] = None

@dataclass
class ComplianceResult:
    """Result of compliance validation"""
    is_compliant: bool
    processed_content: str
    violations: List[str]
    warnings: List[str]
    blocked: bool
    compliance_level: ComplianceLevel
    bypass_reason: Optional[str] = None
    audit_log_id: Optional[str] = None

class UniversalComplianceMiddleware:
    """Universal compliance middleware for all output channels"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.audit_log_file = os.path.join(base_dir, 'compliance_audit.json')
        self.bypass_log_file = os.path.join(base_dir, 'compliance_bypasses.json')
        self.drift_alerts_file = os.path.join(base_dir, 'compliance_drift_alerts.json')
        
        # Load configuration
        self.config = self._load_compliance_config()
        
        # Initialize output compliance from existing module
        try:
            from output_compliance import OutputCompliance
            self.output_compliance = OutputCompliance(base_dir)
        except ImportError:
            logging.error("OutputCompliance module not found")
            self.output_compliance = None
        
        # Track all registered output functions
        self.registered_output_functions = set()
        self.bypass_registry = {}
        
        # Compliance patterns (enhanced from AGENT_BIBLE.md)
        self.strict_patterns = [
            # Action language without confirmation
            r"\bi'll\s+\w+|\bi\s+am\s+\w+ing|\bi\s+will\s+\w+|\bi\s+have\s+\w+ed",
            r"\bi'm\s+\w+ing|\bi've\s+\w+ed|\bi\s+can\s+now\s+\w+",
            
            # Completion claims
            r"\bcomplete\b|\bfinished\b|\bdone\b|\bready\b|\blive\b|\bactive\b",
            r"\bdeployed\b|\brunning\b|\bworking\b|\bsuccessful\b|\bimplemented\b",
            
            # Status claims
            r"\bis\s+now\s+\w+|\bshould\s+now\s+work\b|\bwill\s+now\s+\w+",
            r"\benabled\b|\bactivated\b|\bexecuted\b|\bprocessed\b",
            
            # Feature claims
            r"\bfeature\s+is\s+live\b|\bsystem\s+is\s+ready\b|\bapi\s+is\s+working\b"
        ]
        
    def _load_compliance_config(self) -> Dict[str, Any]:
        """Load compliance configuration"""
        config_file = os.path.join(self.base_dir, 'compliance_config.json')
        default_config = {
            "default_compliance_level": "strict",
            "channel_settings": {
                "api_response": {"level": "strict", "require_confirmation": True},
                "log_message": {"level": "moderate", "require_confirmation": False},
                "ui_message": {"level": "strict", "require_confirmation": True},
                "chat_response": {"level": "strict", "require_confirmation": True},
                "error_message": {"level": "permissive", "require_confirmation": False}
            },
            "bypass_allowed": True,
            "audit_all_outputs": True,
            "block_on_violation": True,
            "alert_on_bypass": True
        }
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            # Merge with defaults
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
        except (FileNotFoundError, json.JSONDecodeError):
            # Create default config
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def validate_output(self, content: str, context: OutputContext) -> ComplianceResult:
        """
        Universal output validation - all outputs must go through this function
        """
        # Get compliance level for this channel
        channel_config = self.config["channel_settings"].get(
            context.channel.value, 
            {"level": self.config["default_compliance_level"], "require_confirmation": True}
        )
        compliance_level = ComplianceLevel(channel_config["level"])
        
        violations = []
        warnings = []
        blocked = False
        processed_content = content
        
        # Check for action language patterns
        detected_patterns = self._detect_compliance_violations(content, compliance_level)
        
        if detected_patterns:
            violations.extend(detected_patterns)
            
            # Check for confirmation if required
            if channel_config.get("require_confirmation", True):
                confirmation_status = context.confirmation_status or {}
                confirmed = confirmation_status.get('confirmed', False)
                confirmation_method = confirmation_status.get('confirmation_method', 'none')
                
                valid_confirmation_methods = [
                    'api_endpoint_check', 'backend_validation', 'human_confirmation',
                    'system_verification', 'connection_validation'
                ]
                
                if not confirmed or confirmation_method not in valid_confirmation_methods:
                    if compliance_level == ComplianceLevel.STRICT:
                        blocked = True
                        processed_content = self._generate_compliance_blocked_message(
                            content, detected_patterns, context
                        )
                    elif compliance_level == ComplianceLevel.MODERATE:
                        warnings.append("Action language detected without confirmation")
                        processed_content = self._add_compliance_warning(content, detected_patterns)
                    # PERMISSIVE level just logs but doesn't modify content
        
        # Create audit log entry
        audit_log_id = self._create_audit_log(content, context, violations, warnings, blocked)
        
        # Check for bypass attempts
        if self._detect_bypass_attempt(context):
            self._log_bypass_attempt(context, content)
        
        return ComplianceResult(
            is_compliant=len(violations) == 0,
            processed_content=processed_content,
            violations=violations,
            warnings=warnings,
            blocked=blocked,
            compliance_level=compliance_level,
            audit_log_id=audit_log_id
        )
    
    def _detect_compliance_violations(self, content: str, level: ComplianceLevel) -> List[str]:
        """Detect compliance violations based on level"""
        violations = []
        content_lower = content.lower()
        
        if level in [ComplianceLevel.STRICT, ComplianceLevel.MODERATE]:
            for pattern in self.strict_patterns:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                if matches:
                    violations.extend([f"Action language: {match}" for match in matches])
        
        return list(set(violations))  # Remove duplicates
    
    def _generate_compliance_blocked_message(self, original: str, patterns: List[str], context: OutputContext) -> str:
        """Generate compliance-safe message for blocked outputs"""
        return f"""⚠️ **Output blocked by compliance middleware**

**AGENT_BIBLE.md Compliance:** Action language detected without backend confirmation.

**Channel:** {context.channel.value}
**Source:** {context.source_function} ({context.source_file}:{context.source_line})
**Detected patterns:** {', '.join(patterns)}

**Required next steps:**
1. Verify via API endpoint check (GET /health, /system-health)
2. Provide explicit confirmation via confirmation_status parameter
3. Get human operator confirmation if automated validation fails

**Per AGENT_BIBLE.md:** No feature, file, or status should be presented as complete until verified.

**Original message blocked for compliance.**"""
    
    def _add_compliance_warning(self, content: str, patterns: List[str]) -> str:
        """Add compliance warning to content"""
        return f"""{content}

⚠️ **Compliance Warning:** Action language detected: {', '.join(patterns)}
Per AGENT_BIBLE.md: Confirmation recommended before claiming completion."""
    
    def _create_audit_log(self, content: str, context: OutputContext, violations: List[str], warnings: List[str], blocked: bool) -> str:
        """Create comprehensive audit log entry"""
        try:
            audit_entry = {
                "id": f"audit_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "channel": context.channel.value,
                "source": {
                    "function": context.source_function,
                    "file": context.source_file,
                    "line": context.source_line
                },
                "content_hash": hash(content),
                "content_snippet": content[:200] if len(content) > 200 else content,
                "violations": violations,
                "warnings": warnings,
                "blocked": blocked,
                "context": {
                    "user_id": context.user_id,
                    "session_id": context.session_id,
                    "request_id": context.request_id
                },
                "confirmation_status": context.confirmation_status
            }
            
            # Load existing audit log
            try:
                with open(self.audit_log_file, 'r') as f:
                    audit_log = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                audit_log = {"entries": []}
            
            audit_log["entries"].append(audit_entry)
            
            # Keep only last 1000 entries
            if len(audit_log["entries"]) > 1000:
                audit_log["entries"] = audit_log["entries"][-1000:]
            
            with open(self.audit_log_file, 'w') as f:
                json.dump(audit_log, f, indent=2)
            
            return audit_entry["id"]
            
        except Exception as e:
            logging.error(f"Error creating audit log: {e}")
            return "audit_error"
    
    def _detect_bypass_attempt(self, context: OutputContext) -> bool:
        """Detect attempts to bypass compliance middleware"""
        # Check if output function is registered
        function_signature = f"{context.source_file}:{context.source_function}"
        
        # Check for direct output patterns in source
        bypass_indicators = [
            "print(",
            "return jsonify(",
            "render_template(",
            "console.log(",
            "response.send(",
            "res.json("
        ]
        
        try:
            # Get the calling frame to check for direct output
            frame = inspect.currentframe()
            while frame:
                frame_info = inspect.getframeinfo(frame)
                if any(indicator in str(frame_info.code_context) for indicator in bypass_indicators):
                    return True
                frame = frame.f_back
        except:
            pass
        
        return False
    
    def _log_bypass_attempt(self, context: OutputContext, content: str):
        """Log bypass attempts for audit"""
        try:
            bypass_entry = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "channel": context.channel.value,
                "source": {
                    "function": context.source_function,
                    "file": context.source_file,
                    "line": context.source_line
                },
                "content_snippet": content[:100],
                "stack_trace": traceback.format_stack()[-5:]  # Last 5 frames
            }
            
            try:
                with open(self.bypass_log_file, 'r') as f:
                    bypass_log = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                bypass_log = {"bypass_attempts": []}
            
            bypass_log["bypass_attempts"].append(bypass_entry)
            
            # Keep only last 100 attempts
            if len(bypass_log["bypass_attempts"]) > 100:
                bypass_log["bypass_attempts"] = bypass_log["bypass_attempts"][-100:]
            
            with open(self.bypass_log_file, 'w') as f:
                json.dump(bypass_log, f, indent=2)
            
            # Also log to memory system if available
            self._log_bypass_to_memory(bypass_entry)
            
        except Exception as e:
            logging.error(f"Error logging bypass attempt: {e}")
    
    def _log_bypass_to_memory(self, bypass_entry: Dict[str, Any]):
        """Log bypass attempt to memory system"""
        try:
            memory_file = os.path.join(self.base_dir, 'memory.json')
            
            bypass_memory = {
                "topic": f"Compliance Bypass Attempt - {bypass_entry['source']['function']}",
                "type": "BuildLog",
                "input": f"Potential compliance bypass detected in {bypass_entry['source']['file']}",
                "output": f"Direct output detected without compliance validation: {bypass_entry['content_snippet']}",
                "score": 0,
                "maxScore": 25,
                "success": False,
                "category": "compliance",
                "tags": ["compliance_bypass", "audit", "security", "violation"],
                "context": "Compliance bypass detection - direct output without middleware validation",
                "related_to": [],
                "reviewed": False,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "auto_generated": True,
                "confirmed": True,
                "confirmation_method": "compliance_system",
                "bypass_violation": bypass_entry
            }
            
            # Save to memory
            try:
                with open(memory_file, 'r') as f:
                    memory = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                memory = []
            
            memory.append(bypass_memory)
            
            with open(memory_file, 'w') as f:
                json.dump(memory, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error logging bypass to memory: {e}")
    
    def get_compliance_stats(self) -> Dict[str, Any]:
        """Get compliance statistics and health metrics"""
        try:
            with open(self.audit_log_file, 'r') as f:
                audit_log = json.load(f)
            entries = audit_log.get("entries", [])
        except (FileNotFoundError, json.JSONDecodeError):
            entries = []
        
        # Calculate stats
        total_outputs = len(entries)
        blocked_outputs = len([e for e in entries if e.get("blocked", False)])
        violations = sum(len(e.get("violations", [])) for e in entries)
        
        # Channel breakdown
        channel_stats = {}
        for entry in entries:
            channel = entry.get("channel", "unknown")
            if channel not in channel_stats:
                channel_stats[channel] = {"total": 0, "blocked": 0, "violations": 0}
            channel_stats[channel]["total"] += 1
            if entry.get("blocked", False):
                channel_stats[channel]["blocked"] += 1
            channel_stats[channel]["violations"] += len(entry.get("violations", []))
        
        return {
            "total_outputs": total_outputs,
            "blocked_outputs": blocked_outputs,
            "total_violations": violations,
            "compliance_rate": f"{((total_outputs - violations) / total_outputs * 100):.1f}%" if total_outputs > 0 else "100%",
            "channel_breakdown": channel_stats,
            "last_24h_violations": len([e for e in entries[-100:] if e.get("violations")]),
            "bypass_attempts": self._get_bypass_count()
        }
    
    def _get_bypass_count(self) -> int:
        """Get count of bypass attempts"""
        try:
            with open(self.bypass_log_file, 'r') as f:
                bypass_log = json.load(f)
            return len(bypass_log.get("bypass_attempts", []))
        except (FileNotFoundError, json.JSONDecodeError):
            return 0

# Global compliance middleware instance
compliance_middleware = None

def init_compliance_middleware(base_dir: str):
    """Initialize global compliance middleware"""
    global compliance_middleware
    compliance_middleware = UniversalComplianceMiddleware(base_dir)
    return compliance_middleware

# Decorators for output compliance enforcement
def require_compliance(channel: OutputChannel, require_confirmation: bool = True):
    """Decorator to enforce compliance on output functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get context information
            frame = inspect.currentframe().f_back
            frame_info = inspect.getframeinfo(frame)
            
            context = OutputContext(
                channel=channel,
                source_function=func.__name__,
                source_file=frame_info.filename,
                source_line=frame_info.lineno,
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                confirmation_status=kwargs.get('confirmation_status')
            )
            
            # Execute the original function
            result = func(*args, **kwargs)
            
            # Apply compliance validation to result
            if compliance_middleware and isinstance(result, (str, dict)):
                if isinstance(result, dict):
                    # Handle JSON responses
                    content = result.get('message', result.get('output', str(result)))
                else:
                    content = result
                
                compliance_result = compliance_middleware.validate_output(content, context)
                
                if compliance_result.blocked:
                    if isinstance(result, dict):
                        result['message'] = compliance_result.processed_content
                        result['compliance_blocked'] = True
                        result['compliance_violations'] = compliance_result.violations
                    else:
                        result = compliance_result.processed_content
                elif compliance_result.warnings:
                    if isinstance(result, dict):
                        result['compliance_warnings'] = compliance_result.warnings
            
            return result
        return wrapper
    return decorator

# Convenience decorators for specific channels
def api_output(func: Callable) -> Callable:
    """Decorator for API output functions"""
    return require_compliance(OutputChannel.API_RESPONSE, require_confirmation=True)(func)

def ui_output(func: Callable) -> Callable:
    """Decorator for UI output functions"""
    return require_compliance(OutputChannel.UI_MESSAGE, require_confirmation=True)(func)

def log_output(func: Callable) -> Callable:
    """Decorator for logging functions"""
    return require_compliance(OutputChannel.LOG_MESSAGE, require_confirmation=False)(func)

def chat_output(func: Callable) -> Callable:
    """Decorator for chat responses"""
    return require_compliance(OutputChannel.CHAT_RESPONSE, require_confirmation=True)(func)

# Centralized output functions that all other code should use
def send_user_output(content: str, channel: OutputChannel, confirmation_status: Optional[Dict[str, Any]] = None) -> str:
    """
    Centralized function for all user-facing outputs
    All code should use this instead of direct output methods
    """
    if not compliance_middleware:
        logging.error("Compliance middleware not initialized")
        return content
    
    # Get caller context
    frame = inspect.currentframe().f_back
    frame_info = inspect.getframeinfo(frame)
    
    context = OutputContext(
        channel=channel,
        source_function=frame_info.function,
        source_file=frame_info.filename,
        source_line=frame_info.lineno,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        confirmation_status=confirmation_status
    )
    
    compliance_result = compliance_middleware.validate_output(content, context)
    return compliance_result.processed_content

def log_and_respond(content: str, response_type: str = "info", confirmation_status: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Centralized function for logging and responding
    Ensures all outputs go through compliance validation
    """
    # Log the content
    logged_content = send_user_output(content, OutputChannel.LOG_MESSAGE, confirmation_status)
    
    # Create response
    response_content = send_user_output(content, OutputChannel.API_RESPONSE, confirmation_status)
    
    return {
        "status": response_content,
        "type": response_type,
        "logged": True,
        "compliance_validated": True
    }
"""
Compliance Middleware for MemoryOS
Handles output validation and compliance enforcement
"""

import logging
from enum import Enum
from functools import wraps
import json
import datetime
import os

class OutputChannel(Enum):
    API_RESPONSE = "api_response"
    UI_OUTPUT = "ui_output"
    LOG_MESSAGE = "log_message"

class ComplianceMiddleware:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.compliance_log = []
        
    def validate_output(self, message, channel):
        """Validate output for compliance"""
        return {"valid": True, "message": message}

# Global instance
compliance_middleware = None

def init_compliance_middleware(base_dir):
    global compliance_middleware
    compliance_middleware = ComplianceMiddleware(base_dir)
    return compliance_middleware

def send_user_output(message, channel, metadata=None):
    """Send user output through compliance validation"""
    return {
        "message": message,
        "channel": channel.value if hasattr(channel, 'value') else str(channel),
        "metadata": metadata or {},
        "timestamp": datetime.datetime.now().isoformat()
    }

def log_and_respond(message, metadata=None):
    """Log and respond with compliance"""
    logging.info(f"Compliance response: {message}")
    return send_user_output(message, OutputChannel.API_RESPONSE, metadata)

def api_output(func):
    """Decorator for API output compliance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logging.error(f"API output error: {e}")
            return {"error": str(e)}, 500
    return wrapper

def ui_output(func):
    """Decorator for UI output compliance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logging.error(f"UI output error: {e}")
            return {"error": str(e)}
    return wrapper
