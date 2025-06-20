
"""
Session Context Manager for MemoryOS

This module implements session persistence, context rehydration, and state management
per AGENT_BIBLE.md requirements for context switches and user experience continuity.

BEHAVIORAL AUTHORITY: AGENT_BIBLE.md
- All context switches must be logged as BuildLogs with confirmation
- On new session, present summary of restored state and pending actions
- Manual confirmation required for session state changes
"""

import os
import json
import datetime
import logging
from typing import Dict, List, Optional, Any
from flask import request

class SessionManager:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.sessions_dir = os.path.join(base_dir, 'sessions')
        self.memory_file = os.path.join(base_dir, 'memory.json')
        
        # Ensure sessions directory exists
        os.makedirs(self.sessions_dir, exist_ok=True)
        
    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"session_{timestamp}"
    
    def save_session(self, session_id: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save current session context"""
        try:
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            
            # Capture current state
            session_context = {
                "session_id": session_id,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "context_data": context_data,
                "recent_memories": self._get_recent_memories(10),
                "build_state": self._get_build_state(),
                "daily_focus": self._get_daily_focus(),
                "agent_mode": context_data.get('agent_mode', 'user'),
                "open_threads": context_data.get('open_threads', []),
                "pending_actions": context_data.get('pending_actions', []),
                "confirmation_status": {
                    "confirmed": False,
                    "confirmation_method": "manual_save",
                    "confirmation_required": True
                }
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_context, f, indent=2)
            
            # Log session save as BuildLog
            self._log_session_event("Session Saved", session_id, "save", session_context)
            
            return {
                "status": "✅ Session saved",
                "session_id": session_id,
                "context_items": len(context_data),
                "confirmation_required": True
            }
            
        except Exception as e:
            logging.error(f"Error saving session: {e}")
            return {"status": "❌ Failed to save session", "error": str(e)}
    
    def load_session(self, session_id: str) -> Dict[str, Any]:
        """Load and restore session context"""
        try:
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            
            if not os.path.exists(session_file):
                return {"status": "❌ Session not found", "session_id": session_id}
            
            with open(session_file, 'r') as f:
                session_context = json.load(f)
            
            # Prepare restoration summary
            restoration_summary = {
                "session_id": session_id,
                "original_timestamp": session_context.get('timestamp'),
                "restored_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "context_items": len(session_context.get('context_data', {})),
                "recent_memories_count": len(session_context.get('recent_memories', [])),
                "agent_mode": session_context.get('agent_mode', 'user'),
                "open_threads": session_context.get('open_threads', []),
                "pending_actions": session_context.get('pending_actions', []),
                "restored_context": session_context,
                "confirmation_status": {
                    "confirmed": False,
                    "confirmation_method": "manual_load",
                    "confirmation_required": True
                }
            }
            
            # Log session load as BuildLog
            self._log_session_event("Session Restored", session_id, "load", restoration_summary)
            
            return {
                "status": "✅ Session restored",
                "restoration_summary": restoration_summary,
                "confirmation_required": True
            }
            
        except Exception as e:
            logging.error(f"Error loading session: {e}")
            return {"status": "❌ Failed to load session", "error": str(e)}
    
    def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of available sessions"""
        try:
            sessions = []
            session_files = [f for f in os.listdir(self.sessions_dir) if f.endswith('.json')]
            
            for session_file in sorted(session_files, reverse=True)[:limit]:
                session_path = os.path.join(self.sessions_dir, session_file)
                try:
                    with open(session_path, 'r') as f:
                        session_data = json.load(f)
                    
                    sessions.append({
                        "session_id": session_data.get('session_id'),
                        "timestamp": session_data.get('timestamp'),
                        "agent_mode": session_data.get('agent_mode', 'user'),
                        "context_items": len(session_data.get('context_data', {})),
                        "pending_actions": len(session_data.get('pending_actions', [])),
                        "file_name": session_file
                    })
                except Exception as e:
                    logging.warning(f"Error reading session file {session_file}: {e}")
            
            return sessions
            
        except Exception as e:
            logging.error(f"Error getting session history: {e}")
            return []
    
    def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear/delete specific session"""
        try:
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            
            if os.path.exists(session_file):
                os.remove(session_file)
                
                # Log session clear as BuildLog
                self._log_session_event("Session Cleared", session_id, "clear", {
                    "confirmation_status": {
                        "confirmed": False,
                        "confirmation_method": "manual_clear",
                        "confirmation_required": True
                    }
                })
                
                return {
                    "status": "✅ Session cleared",
                    "session_id": session_id,
                    "confirmation_required": True
                }
            else:
                return {"status": "❌ Session not found", "session_id": session_id}
                
        except Exception as e:
            logging.error(f"Error clearing session: {e}")
            return {"status": "❌ Failed to clear session", "error": str(e)}
    
    def _get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent memories for context"""
        try:
            with open(self.memory_file, 'r') as f:
                memories = json.load(f)
            return memories[-limit:] if memories else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _get_build_state(self) -> Optional[Dict[str, Any]]:
        """Get current build state"""
        try:
            build_state_file = os.path.join(self.base_dir, 'build_state.json')
            with open(build_state_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def _get_daily_focus(self) -> Optional[Dict[str, Any]]:
        """Get current daily focus"""
        try:
            daily_focus_file = os.path.join(self.base_dir, 'daily_focus.json')
            with open(daily_focus_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def _log_session_event(self, event_type: str, session_id: str, action: str, context: Dict[str, Any]):
        """Log session events as BuildLogs per AGENT_BIBLE.md requirements"""
        try:
            memory_entry = {
                "topic": f"{event_type}: {session_id}",
                "type": "BuildLog",
                "input": f"Session {action} operation for {session_id}",
                "output": f"Session context {action} completed. Context items: {len(context.get('context_data', {}))}",
                "score": 20,
                "maxScore": 25,
                "success": True,
                "category": "system",
                "tags": ["session", "context", action, "rehydration"],
                "context": f"Session management operation per AGENT_BIBLE.md context switch requirements",
                "related_to": [],
                "reviewed": False,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "auto_generated": True,
                "confirmed": context.get('confirmation_status', {}).get('confirmed', False),
                "confirmation_method": context.get('confirmation_status', {}).get('confirmation_method', 'manual'),
                "confirmation_required": context.get('confirmation_status', {}).get('confirmation_required', True),
                "replit_connection_confirmed": False,  # Will be updated by connection validator
                "session_data": {
                    "session_id": session_id,
                    "action": action,
                    "context_summary": {
                        "items_count": len(context.get('context_data', {})),
                        "agent_mode": context.get('agent_mode', 'unknown'),
                        "pending_actions": len(context.get('pending_actions', []))
                    }
                }
            }
            
            # Load existing memories
            try:
                with open(self.memory_file, 'r') as f:
                    memories = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                memories = []
            
            memories.append(memory_entry)
            
            with open(self.memory_file, 'w') as f:
                json.dump(memories, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error logging session event: {e}")

    def generate_session_summary(self, session_context: Dict[str, Any]) -> str:
        """Generate human-readable session summary per AGENT_BIBLE.md onboarding requirements"""
        try:
            summary_parts = []
            
            # Basic session info
            session_id = session_context.get('session_id', 'Unknown')
            timestamp = session_context.get('original_timestamp', 'Unknown')
            summary_parts.append(f"📋 **Session Restored**: {session_id}")
            summary_parts.append(f"🕒 **Original Session**: {timestamp}")
            
            # Agent mode and context
            agent_mode = session_context.get('agent_mode', 'user')
            summary_parts.append(f"🤖 **Agent Mode**: {agent_mode}")
            
            # Memory context
            memories_count = session_context.get('recent_memories_count', 0)
            summary_parts.append(f"📝 **Recent Memories**: {memories_count} entries")
            
            # Open threads and pending actions
            open_threads = session_context.get('open_threads', [])
            pending_actions = session_context.get('pending_actions', [])
            
            if open_threads:
                summary_parts.append(f"🧵 **Open Threads**: {len(open_threads)}")
                for i, thread in enumerate(open_threads[:3]):  # Show first 3
                    summary_parts.append(f"   • {thread}")
                if len(open_threads) > 3:
                    summary_parts.append(f"   • ... and {len(open_threads) - 3} more")
            
            if pending_actions:
                summary_parts.append(f"⏳ **Pending Actions**: {len(pending_actions)}")
                for i, action in enumerate(pending_actions[:3]):  # Show first 3
                    summary_parts.append(f"   • {action}")
                if len(pending_actions) > 3:
                    summary_parts.append(f"   • ... and {len(pending_actions) - 3} more")
            
            # Bible compliance notice
            summary_parts.append("\n🔒 **AGENT_BIBLE.md Compliance**:")
            summary_parts.append("• Manual confirmation required for context switches")
            summary_parts.append("• Session state restored with pending validation")
            summary_parts.append("• All actions logged per behavioral authority")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logging.error(f"Error generating session summary: {e}")
            return f"❌ Error generating session summary: {str(e)}"
"""
Session Manager for MemoryOS
Handles session state and persistence
"""

import json
import os
import datetime
import logging

class SessionManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.sessions_dir = os.path.join(base_dir, 'sessions')
        os.makedirs(self.sessions_dir, exist_ok=True)
        
    def save_session(self, session_id, data):
        """Save session data"""
        try:
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            with open(session_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error saving session: {e}")
            return False
            
    def load_session(self, session_id):
        """Load session data"""
        try:
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.error(f"Error loading session: {e}")
            return {}
