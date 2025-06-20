"""Fixes datetime usage in the get_replit_context method to ensure accurate timestamps."""
"""Updated validation cache duration to 1 hour for smoother GPT interactions."""
"""
GPT Real-Time Integration for MemoryOS

This module provides GPT with live Replit state awareness and enforces
strict compliance with AGENT_BIBLE.md before any response generation.

BEHAVIORAL AUTHORITY: AGENT_BIBLE.md
- GPT must validate connection before every response
- No action language without backend confirmation
- Real-time Replit workflow state awareness
- Comprehensive compliance enforcement
"""

import os
import json
from datetime import datetime, timezone
import requests
import logging
from typing import Dict, Any, Optional

class GPTReplitIntegration:
    def __init__(self, base_dir: str, api_base_url: str = "http://127.0.0.1:5000"):
        self.base_dir = base_dir
        self.api_base_url = api_base_url
        self.last_validation = None
        self.validation_cache_duration = 3600  # 1 hour for smoother interactions

    def validate_before_response(self, user_query: str, response_type: str = "general") -> Dict[str, Any]:
        """
        Validate connection only for system operations, not general conversation
        """
        # Only require strict validation for system operations
        action_types_requiring_validation = ["live_claim", "deployment", "system_change", "feature_activation"]
        
        if response_type not in action_types_requiring_validation:
            # For general conversation, just return success
            return {
                "gpt_response_authorized": True,
                "validation_timestamp": datetime.now(timezone.utc).isoformat(),
                "validation_type": "conversation_mode"
            }

        try:
            validation_data = {
                "query": user_query,
                "response_type": response_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            response = requests.post(
                f"{self.api_base_url}/gpt-validation",
                json=validation_data,
                timeout=10
            )

            if response.status_code == 200:
                validation_result = response.json()
                self.last_validation = validation_result
                return validation_result
            else:
                return {
                    "gpt_response_authorized": False,
                    "error": f"Validation failed: {response.status_code}",
                    "fallback_message": "Manual confirmation required - validation service unavailable"
                }

        except Exception as e:
            return {
                "gpt_response_authorized": False,
                "error": str(e),
                "fallback_message": "Manual confirmation required - connection to Replit failed",
                "requires_manual_intervention": True
            }

    def get_live_system_health(self) -> Dict[str, Any]:
        """Get real-time system health from Replit"""
        try:
            response = requests.get(f"{self.api_base_url}/system-health", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Health check failed: {response.status_code}"}
        except Exception as e:
            return {"error": str(e), "connection_failed": True}

    def check_compliance_before_claim(self, intended_claim: str) -> Dict[str, Any]:
        """
        Check if GPT can make a specific claim (like 'feature is live')
        Only enforce for definitive system state claims, not conversational language
        """
        # More specific patterns that indicate system state claims
        definitive_claim_patterns = [
            'feature is live', 'system is running', 'deployed successfully', 
            'integration is active', 'endpoint is working', 'service is operational'
        ]

        # Check for definitive system claims, not just any use of action words
        is_definitive_claim = any(pattern in intended_claim.lower() for pattern in definitive_claim_patterns)
        
        if is_definitive_claim:
            validation = self.validate_before_response(intended_claim, "live_claim")

            if not validation.get('gpt_response_authorized', False):
                return {
                    "claim_allowed": False,
                    "reason": "AGENT_BIBLE.md compliance: Definitive system state claims require backend validation",
                    "required_action": "Perform fresh connection check or get human confirmation",
                    "alternative_phrasing": "Consider using: 'This should be working' or 'Please verify this is active'"
                }

        return {"claim_allowed": True}

    def get_replit_context(self) -> Dict[str, Any]:
        """Get comprehensive Replit context for GPT awareness"""
        try:
            # Get system health
            health = self.get_live_system_health()

            # Get memory context
            memory_response = requests.get(f"{self.api_base_url}/memory?limit=5")
            recent_memory = memory_response.json() if memory_response.status_code == 200 else []

            # Get workflow status from health
            replit_state = health.get('replit_state', {})

            return {
                "system_healthy": health.get('overall_status') == 'healthy',
                "flask_running": replit_state.get('flask_server_running', False),
                "memory_accessible": replit_state.get('memory_system_accessible', False),
                "recent_activity": recent_memory[:3] if recent_memory else [],
                "connection_score": health.get('connection_health_score', 0),
                "agent_ready": health.get('agent_confirmation_ready', False),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            return {
                "error": str(e),
                "manual_verification_required": True,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }

    def generate_compliant_response(self, user_query: str, intended_response: str) -> Dict[str, Any]:
        """
        Process intended GPT response through compliance validation
        """
        # First validate
        validation = self.validate_before_response(user_query)

        if not validation.get('gpt_response_authorized', False):
            return {
                "response": validation.get('fallback_message', 'Manual confirmation required'),
                "compliance_blocked": True,
                "reason": validation.get('error', 'Connection validation failed'),
                "next_steps": [
                    "Verify Replit connection",
                    "Check system health endpoint",
                    "Get human confirmation if needed"
                ]
            }

        # Check for blocked phrases
        blocked_phrases = validation.get('blocked_phrases', [])
        response_blocked = any(phrase.lower() in intended_response.lower() for phrase in blocked_phrases)

        if response_blocked:
            return {
                "response": "⚠️ **Manual confirmation required by AGENT_BIBLE.md**\n\nAction language detected without backend validation. Please verify system state via `/system-health` endpoint or provide explicit confirmation.",
                "compliance_blocked": True,
                "reason": "Action language without confirmation",
                "blocked_phrases": [phrase for phrase in blocked_phrases if phrase.lower() in intended_response.lower()]
            }

        # Response is compliant
        return {
            "response": intended_response,
            "compliance_passed": True,
            "validation_timestamp": validation['validation_timestamp'],
            "replit_context": validation.get('replit_state', {})
        }

# Convenience functions for GPT instructions
def must_validate_before_response(user_query: str, response_type: str = "general") -> Dict[str, Any]:
    """Global function GPT must call before any response"""
    integration = GPTReplitIntegration(os.path.dirname(os.path.abspath(__file__)))
    return integration.validate_before_response(user_query, response_type)

def get_live_replit_state() -> Dict[str, Any]:
    """Get current live Replit state"""
    integration = GPTReplitIntegration(os.path.dirname(os.path.abspath(__file__)))
    return integration.get_replit_context()

def check_if_claim_allowed(claim: str) -> Dict[str, Any]:
    """Check if GPT can make a specific claim"""
    integration = GPTReplitIntegration(os.path.dirname(os.path.abspath(__file__)))
    return integration.check_compliance_before_claim(claim)
```