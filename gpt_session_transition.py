
"""
GPT Session Transition Helper for MemoryOS

Helps transition GPT to new chat while maintaining Replit context awareness
"""

import requests
import json
import datetime
from typing import Dict, Any

class GPTSessionTransition:
    def __init__(self, api_base_url: str = "http://127.0.0.1:5000"):
        self.api_base_url = api_base_url
    
    def prepare_new_session_context(self) -> Dict[str, Any]:
        """Prepare context summary for new GPT session"""
        try:
            # Get current system health
            health_response = requests.get(f"{self.api_base_url}/system-health")
            health_data = health_response.json() if health_response.status_code == 200 else {}
            
            # Get recent memories for context
            memory_response = requests.get(f"{self.api_base_url}/memory?limit=10")
            recent_memories = memory_response.json() if memory_response.status_code == 200 else []
            
            # Get current build state
            build_response = requests.get(f"{self.api_base_url}/build-state")
            build_state = build_response.json() if build_response.status_code == 200 else {}
            
            # Get daily focus
            focus_response = requests.get(f"{self.api_base_url}/daily-focus")
            daily_focus = focus_response.json() if focus_response.status_code == 200 else {}
            
            # Prepare transition summary
            transition_context = {
                "session_transition_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "system_status": {
                    "healthy": health_data.get('overall_status') == 'healthy',
                    "connection_score": health_data.get('connection_health_score', 0),
                    "flask_running": health_data.get('replit_state', {}).get('flask_server_running', False),
                    "compliance_status": health_data.get('bible_compliance', {}).get('compliant', False)
                },
                "current_context": {
                    "total_memories": len(recent_memories),
                    "recent_activity": [m.get('topic', '') for m in recent_memories[-3:]],
                    "build_state": build_state,
                    "daily_focus": daily_focus
                },
                "pending_items": {
                    "unreviewed_memories": len([m for m in recent_memories if not m.get('reviewed', False)]),
                    "pending_actions": build_state.get('pending_actions', [])
                },
                "compliance_requirements": {
                    "agent_bible_compliance": True,
                    "connection_validation_required": True,
                    "manual_confirmation_for_live_claims": True
                }
            }
            
            return transition_context
            
        except Exception as e:
            return {
                "error": str(e),
                "manual_verification_required": True,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
    
    def generate_new_session_prompt(self) -> str:
        """Generate prompt for new GPT session with current context"""
        context = self.prepare_new_session_context()
        
        prompt_parts = [
            "🔄 **NEW SESSION - CONTEXT TRANSFER**",
            "",
            "I'm continuing our MemoryOS founder work in a new chat. Here's my current state:",
            "",
            "**System Status:**",
            f"• System Health: {'✅ Healthy' if context.get('system_status', {}).get('healthy') else '⚠️ Degraded'}",
            f"• Flask API: {'🟢 Running' if context.get('system_status', {}).get('flask_running') else '🔴 Stopped'}",
            f"• Connection Score: {context.get('system_status', {}).get('connection_score', 0)}/100",
            f"• Bible Compliance: {'✅ Compliant' if context.get('system_status', {}).get('compliance_status') else '⚠️ Issues'}",
            "",
            "**Current Context:**",
            f"• Total Memories: {context.get('current_context', {}).get('total_memories', 0)}",
            f"• Unreviewed Items: {context.get('pending_items', {}).get('unreviewed_memories', 0)}",
        ]
        
        # Add recent activity
        recent_activity = context.get('current_context', {}).get('recent_activity', [])
        if recent_activity:
            prompt_parts.append("• Recent Activity:")
            for activity in recent_activity:
                prompt_parts.append(f"  - {activity}")
        
        prompt_parts.extend([
            "",
            "**Critical Compliance Requirements:**",
            "• Must validate connection before any 'live' claims",
            "• All responses must follow AGENT_BIBLE.md",
            "• Cannot claim features are working without backend validation",
            "• Must use /gpt-validation endpoint before responses",
            "",
            "Please acknowledge you have this context and are ready to continue with strict compliance."
        ])
        
        return "\n".join(prompt_parts)
    
    def save_transition_log(self, transition_data: Dict[str, Any]):
        """Save transition to memory system"""
        try:
            memory_entry = {
                "topic": "GPT Session Transition",
                "type": "BuildLog", 
                "input": "Starting new GPT chat session with context transfer",
                "output": f"New session initialized with system health score {transition_data.get('system_status', {}).get('connection_score', 0)}/100",
                "score": 20,
                "maxScore": 25,
                "success": True,
                "category": "system",
                "tags": ["gpt_session", "context_transfer", "compliance"],
                "context": "GPT session transition with full context preservation per AGENT_BIBLE.md",
                "related_to": [],
                "reviewed": False,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "auto_generated": True,
                "confirmed": True,
                "confirmation_method": "system_generated",
                "session_transition_data": transition_data
            }
            
            response = requests.post(
                f"{self.api_base_url}/memory",
                json=memory_entry,
                headers={"X-API-KEY": "your_api_key"}  # Replace with actual key
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error logging transition: {e}")
            return False

def main():
    """Generate new session context for GPT"""
    transition = GPTSessionTransition()
    
    # Get context and generate prompt
    context = transition.prepare_new_session_context()
    prompt = transition.generate_new_session_prompt()
    
    # Save transition log
    transition.save_transition_log(context)
    
    print("=" * 60)
    print("GPT NEW SESSION CONTEXT")
    print("=" * 60)
    print(prompt)
    print("=" * 60)
    print("\nCopy the above context and paste it into your new GPT chat session.")
    print("This will give your GPT full awareness of your current MemoryOS state.")

if __name__ == "__main__":
    main()
