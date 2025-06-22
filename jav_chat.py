"""
Jav Chat Interface - Central Command Hub
Routes commands and integrates key features with frustration detection
"""

import logging
from typing import Dict, Any, List
from frustration_pattern import FrustrationPattern
from frustration_detector import init_frustration_detector
from datetime import datetime, timezone
import requests

class JavChat:
    """
    Jav Chat Interface - Living Voice of Project Memory
    Every interaction is memory-driven with full provenance tracking
    """

    def __init__(self, jav_agent):
        self.jav = jav_agent
        self.logger = logging.getLogger('JavChat')

        # Initialize frustration detection
        self.frustration_detector = init_frustration_detector(jav_agent)

        # Memory-driven conversation state
        self.conversation_memory = []
        self.active_memory_context = {}
        self.memory_provenance = {}  # Track where suggestions come from

        # Track intervention state
        self.pending_interventions = []
        self.user_intervention_preferences = {
            "auto_hints": True,
            "intervention_level": "help",  # hint, help, auto_debug
            "encouragement": True
        }

    def process_command(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user message/command and return response with workspace integration"""
        original_message = message
        message_lower = message.strip().lower()
        context = context or {}

        # Handle intervention responses first
        if message_lower.startswith("intervention:"):
            return self.handle_intervention_response(message_lower, context)

        result = None
        success = True

        try:
            # Enhanced command processing for workspace integration
            if any(word in message_lower for word in ["memory", "recall", "remember", "history"]):
                result = self.handle_memory_command(message)
            elif any(word in message_lower for word in ["timeline", "creative history", "past work"]):
                result = self.handle_timeline_command(message)
            elif any(word in message_lower for word in ["quick action", "debug", "improve", "feature"]):
                result = self.handle_quick_action_command(message)
            elif message_lower.startswith("audit"):
                result = self.handle_audit_command(message_lower)
            elif message_lower.startswith("health"):
                result = self.handle_health_command()
            elif message_lower.startswith("suggest"):
                result = self.handle_suggestions_command(message_lower)
            elif message_lower.startswith("fix"):
                result = self.handle_fix_command(message_lower)
            elif message_lower.startswith("deploy"):
                result = self.handle_deploy_command(message_lower)
            elif message_lower.startswith("test"):
                result = self.handle_test_command(message_lower)
            elif message_lower.startswith("bible"):
                result = self.handle_bible_command(message_lower)
            elif "help" in message_lower:
                result = self.get_help()
            else:
                result = self.handle_creative_conversation(message, context)

            # Check if command was successful
            success = result.get("type") != "error"

        except Exception as e:
            success = False
            result = {
                "type": "error",
                "message": f"Let's try a different approach together. {str(e)}",
                "suggestions": ["Try describing what you want to build", "Ask for help with a specific feature"]
            }
            context["error"] = str(e)

        # Track interaction for frustration detection
        self.frustration_detector.track_interaction(
            "message", 
            original_message, 
            success, 
            context
        )

        # Check for frustration patterns and gentle intervention
        intervention = self.check_for_gentle_intervention()
        if intervention:
            result = self.enhance_response_with_intervention(result, intervention)

        # STEP 3: Always enhance response with memory narrative (even for errors)
        result = self.enhance_response_with_memory_narrative(result)

        # STEP 4: Store this interaction as new memory
        self.store_interaction_as_memory(original_message, result, success)

        return result

    def store_interaction_as_memory(self, message: str, result: Dict[str, Any], success: bool):
        """Store this interaction as memory for future reference"""
        try:
            memory_entry = {
                "topic": f"Jav Interaction: {message[:50]}{'...' if len(message) > 50 else ''}",
                "type": "UserInteraction",
                "input": message,
                "output": str(result),
                "success": success,
                "category": "jav",
                "tags": ["jav", "agent", "audit"],
                "context": f"Jav Agent: {getattr(self.jav.state, 'context', 'Active')}"
            }

            # Use Jav's logging method to ensure consistency
            self.jav.log_to_memory(
                memory_entry["topic"],
                memory_entry["type"], 
                memory_entry["input"],
                memory_entry["output"],
                memory_entry["success"],
                memory_entry["category"]
            )

        except Exception as e:
            self.logger.error(f"Failed to store interaction as memory: {e}")
            # Don't fail the main response if memory storage fails

    def enhance_response_with_memory_narrative(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance the response with a narrative from memory"""
        try:
            recent_memories = self._get_recent_memories(limit=3)

            if recent_memories:
                memory_narrative = "🧠 **Recent Memory Context**:\n"
                for i, memory in enumerate(recent_memories):
                    memory_narrative += f"{i+1}. **{memory.get('topic', 'Untitled Memory')}**: {memory.get('output', 'No Output')[:80]}...\n"

                if "message" in result:
                    result["message"] = f"{memory_narrative}\n{result['message']}"
                else:
                    result["message"] = memory_narrative

            return result
        except Exception as e:
            self.logger.error(f"Failed to add memory narrative: {e}")
            return result  # Don't fail if memory narrative fails

    def _get_recent_memories(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch recent memories from memory system"""
        try:
            response = requests.get(f'http://0.0.0.0:5000/memory?limit={limit}')
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            return data.get('memories', [])
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch memories from API: {e}")
            return []

    def handle_audit_command(self, command: str) -> Dict[str, Any]:
        """Handle audit command"""
        # Placeholder for audit logic
        return {
            "type": "audit_result",
            "message": "Audit command executed"
        }

    def handle_health_command(self) -> Dict[str, Any]:
        """Handle health check command"""
        # Placeholder for health check logic
        return {
            "type": "health_status",
            "message": "Health command executed"
        }

    def handle_suggestions_command(self, command: str) -> Dict[str, Any]:
        """Handle suggestions command"""
        # Placeholder for suggestions logic
        return {
            "type": "suggestion",
            "message": "Suggestion command executed"
        }

    def handle_fix_command(self, command: str) -> Dict[str, Any]:
        """Handle fix command"""
        # Placeholder for fix logic
        return {
            "type": "fix_result",
            "message": "Fix command executed"
        }

    def handle_deploy_command(self, command: str) -> Dict[str, Any]:
        """Handle deploy command"""
        # Placeholder for deploy logic
        return {
            "type": "deploy_result",
            "message": "Deploy command executed"
        }

    def handle_test_command(self, command: str) -> Dict[str, Any]:
        """Handle test command"""
        # Placeholder for test logic
        return {
            "type": "test_result",
            "message": "Test command executed"
        }

    def handle_bible_command(self, command: str) -> Dict[str, Any]:
        """Handle bible-related commands"""
        try:
            from bible_evolution_engine import bible_evolution
            from bible_integration import bible_integration

            if "review" in command:
                return self.handle_bible_review()
            elif "deviations" in command:
                return self.handle_bible_deviations()
            elif "compliance" in command:
                return self.handle_bible_compliance()
            elif "amendments" in command:
                return self.handle_bible_amendments()
            elif "onboard" in command:
                return self.handle_bible_onboarding()
            else:
                return self.get_bible_help()

        except Exception as e:
            return {
                "type": "error",
                "message": f"Bible command error: {str(e)}",
                "suggestions": ["bible help", "bible review", "bible deviations"]
            }

    def handle_bible_review(self) -> Dict[str, Any]:
        """Handle bible review session generation"""
        try:
            from bible_integration import bible_integration

            review_session = bible_integration.generate_team_review_session()

            return {
                "type": "bible_review",
                "title": "📚 Bible Review Session Generated",
                "session_id": review_session["session_id"],
                "summary": review_session["summary"],
                "highlights": [
                    f"📊 {review_session['summary']['total_deviations']} deviations tracked",
                    f"🔧 {review_session['summary']['proposed_amendments']} amendments proposed",
                    f"📁 {len(review_session['summary']['files_affected'])} files affected"
                ],
                "next_steps": review_session["next_steps"],
                "discussion_agenda": review_session.get("discussion_agenda", []),
                "actions": [
                    {"text": "View Full Review", "action": "view_review_details"},
                    {"text": "Start Team Discussion", "action": "start_discussion"},
                    {"text": "Review Amendments", "action": "review_amendments"}
                ]
            }

        except Exception as e:
            return {
                "type": "error",
                "message": f"Failed to generate review session: {str(e)}"
            }

    def handle_bible_deviations(self) -> Dict[str, Any]:
        """Handle bible deviations query"""
        try:
            from bible_evolution_engine import bible_evolution

            # Get recent high-frequency deviations
            recent_deviations = [d for d in bible_evolution.deviations 
                               if d.frequency >= 3][-10:]  # Last 10 high-frequency

            if not recent_deviations:
                return {
                    "type": "bible_info",
                    "title": "✅ Bible Compliance Good",
                    "message": "No significant deviations detected",
                    "suggestions": ["Continue monitoring for patterns"]
                }

            deviation_summary = []
            for dev in recent_deviations:
                deviation_summary.append(
                    f"🔄 {dev.section}: {dev.frequency}x - {dev.actual_process[:50]}..."
                )

            return {
                "type": "bible_deviations",
                "title": f"📋 {len(recent_deviations)} Tracked Deviations",
                "deviations": deviation_summary,
                "patterns": {
                    "most_frequent": max(recent_deviations, key=lambda d: d.frequency),
                    "most_recent": max(recent_deviations, key=lambda d: d.last_seen)
                },
                "actions": [
                    {"text": "Analyze Patterns", "action": "analyze_patterns"},
                    {"text": "Propose Amendments", "action": "propose_amendments"},
                    {"text": "View Details", "action": "view_deviation_details"}
                ]
            }

        except Exception as e:
            return {
                "type": "error",
                "message": f"Failed to get deviations: {str(e)}"
            }

    def handle_bible_compliance(self) -> Dict[str, Any]:
        """Handle bible compliance check"""
        try:
            from bible_evolution_engine import bible_evolution

            compliance_report = bible_evolution.monitor_compliance("AGENT_BIBLE.md")

            score = compliance_report["compliance_score"]
            status = "🟢 Excellent" if score > 0.9 else "🟡 Good" if score > 0.7 else "🔴 Needs Attention"

            return {
                "type": "bible_compliance",
                "title": f"📊 Bible Compliance: {status}",
                "score": f"{score:.1%}",
                "details": {
                    "recent_deviations": len(compliance_report["deviations"]),
                    "violations": len(compliance_report["violations"]),
                    "last_check": compliance_report["check_date"][:10]
                },
                "recommendations": compliance_report["recommendations"],
                "actions": [
                    {"text": "View Full Report", "action": "view_compliance_report"},
                    {"text": "Address Issues", "action": "address_compliance"},
                    {"text": "Schedule Review", "action": "schedule_review"}
                ]
            }

        except Exception as e:
            return {
                "type": "error",
                "message": f"Failed to check compliance: {str(e)}"
            }

    def handle_bible_amendments(self) -> Dict[str, Any]:
        """Handle bible amendments query"""
        try:
            from bible_evolution_engine import bible_evolution

            pending_amendments = [a for a in bible_evolution.amendments 
                                if a.status in ["draft", "reviewed"]]

            if not pending_amendments:
                return {
                    "type": "bible_info",
                    "title": "📚 No Pending Amendments",
                    "message": "All amendments have been processed",
                    "suggestions": ["Check for new deviation patterns"]
                }

            amendment_summary = []
            for amend in pending_amendments[:5]:  # Top 5
                confidence_emoji = "🟢" if amend.confidence > 0.8 else "🟡" if amend.confidence > 0.6 else "🔴"
                amendment_summary.append(
                    f"{confidence_emoji} {amend.section}: {amend.reasoning[:60]}..."
                )

            return {
                "type": "bible_amendments",
                "title": f"📝 {len(pending_amendments)} Pending Amendments",
                "amendments": amendment_summary,
                "by_status": {
                    "draft": len([a for a in pending_amendments if a.status == "draft"]),
                    "reviewed": len([a for a in pending_amendments if a.status == "reviewed"])
                },
                "actions": [
                    {"text": "Review Amendments", "action": "review_amendments"},
                    {"text": "Approve High-Confidence", "action": "approve_high_confidence"},
                    {"text": "Schedule Team Review", "action": "schedule_team_review"}
                ]
            }

        except Exception as e:
            return {
                "type": "error",
                "message": f"Failed to get amendments: {str(e)}"
            }

    def handle_bible_onboarding(self) -> Dict[str, Any]:
        """Handle bible onboarding brief"""
        try:
            from bible_evolution_engine import bible_evolution

            brief = bible_evolution.generate_onboarding_brief("new_user")

            return {
                "type": "bible_onboarding",
                "title": "👋 Bible Onboarding Brief",
                "summary": brief["summary"],
                "recent_changes": {
                    "count": brief["recent_changes"]["total_updates"],
                    "files": brief["recent_changes"]["files_updated"],
                    "period": brief["recent_changes"]["period"]
                },
                "key_updates": brief["key_updates"][:3],  # Top 3
                "action_items": brief["action_items"],
                "support": brief["contacts"],
                "actions": [
                    {"text": "Start Onboarding", "action": "start_onboarding"},
                    {"text": "Review Changes", "action": "review_recent_changes"},
                    {"text": "Ask Questions", "action": "ask_questions"}
                ]
            }

        except Exception as e:
            return {
                "type": "error",
                "message": f"Failed to generate onboarding: {str(e)}"
            }

    def get_bible_help(self) -> Dict[str, Any]:
        """Get bible command help"""
        return {
            "type": "bible_help",
            "title": "📚 Bible Evolution Commands",
            "commands": {
                "bible review": "Generate comprehensive bible review session",
                "bible deviations": "Show tracked deviations from documented processes",
                "bible compliance": "Check current compliance with bible standards",
                "bible amendments": "View proposed amendments to documentation",
                "bible onboard": "Get onboarding brief for new team members"
            },
            "examples": [
                "bible review",
                "bible deviations",
                "bible compliance",
                "bible amendments"
            ],
            "features": [
                "📊 Track real-world vs documented processes",
                "🔄 Automatic amendment proposals",
                "👥 Team review and consensus flows",
                "📝 Version control for bible changes",
                "🎯 Onboarding for new users"
            ]
        }

    def check_for_gentle_intervention(self) -> Optional[Dict[str, Any]]:
        """Check if gentle intervention is needed"""

        patterns = self.frustration_detector.detect_frustration_patterns()

        if patterns:
            intervention = self.frustration_detector.should_intervene(patterns)

            if intervention and self.user_intervention_preferences.get("auto_hints", True):
                # Only intervene if user hasn't disabled it
                level_preference = self.user_intervention_preferences.get("intervention_level", "help")

                # Respect user's intervention level preference
                if self._intervention_level_ok(intervention["level"], level_preference):
                    self.frustration_detector.mark_intervention_shown()
                    return intervention

        return None

    def _intervention_level_ok(self, suggested_level: str, user_preference: str) -> bool:
        """Check if intervention level is within user's preference"""
        level_hierarchy = ["hint", "help", "auto_debug"]

        suggested_idx = level_hierarchy.index(suggested_level) if suggested_level in level_hierarchy else 0
        preference_idx = level_hierarchy.index(user_preference) if user_preference in level_hierarchy else 1

        return suggested_idx <= preference_idx

    def enhance_response_with_intervention(self, response: Dict[str, Any], 
                                         intervention: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance response with gentle intervention"""

        pattern = intervention["pattern"]
        level = intervention["level"]

        # Create encouraging message
        encouragement = ""
        if self.user_intervention_preferences.get("encouragement", True):
            encouragement = self.frustration_detector.get_encouragement_message(pattern)

        # Create intervention card
        intervention_card = {
            "type": "gentle_intervention",
            "level": level,
            "title": self._get_intervention_title(level, pattern.pattern_type),
            "encouragement": encouragement,
            "evidence": pattern.evidence,
            "suggested_actions": intervention["suggested_actions"],
            "pattern_summary": self._summarize_pattern(pattern),
            "dismissible": True,
            "escalation_options": self._get_escalation_options(level)
        }

        # Add intervention to response
        if "interventions" not in response:
            response["interventions"] = []
        response["interventions"].append(intervention_card)

        # Add gentle note to main message if it's an error
        if response.get("type") == "error" and encouragement:
            response["message"] = f"{encouragement}\n\n{response['message']}"

        return response

    def _get_intervention_title(self, level: str, pattern_type: str) -> str:
        """Get friendly intervention title"""

        titles = {
            "hint": {
                "repeated_command": "💡 I notice you're trying this command again",
                "repeated_error": "🤔 This error keeps coming up",
                "no_progress": "🎯 Let's try a fresh approach",
                "error_spike": "🔄 Lots of trial and error happening",
                "session_fatigue": "⭐ You've been coding hard!"
            },
            "help": {
                "repeated_command": "🚀 Let me help with that command",
                "repeated_error": "🛠️ I can help solve this error",
                "no_progress": "🎪 Ready to try something different?",
                "error_spike": "🔧 Let's debug this systematically",
                "session_fatigue": "🌟 Time to celebrate your progress!"
            },
            "auto_debug": {
                "repeated_command": "🤖 Auto-debug this command?",
                "repeated_error": "⚡ Auto-fix this error pattern?",
                "no_progress": "🎨 Let me suggest a breakthrough approach",
                "error_spike": "🔬 Run automated debugging?",
                "session_fatigue": "💫 Save state and refresh?"
            }
        }

        return titles.get(level, {}).get(pattern_type, f"✨ {level.title()} available")

    def _summarize_pattern(self, pattern: FrustrationPattern) -> str:
        """Create friendly pattern summary"""

        summaries = {
            "repeated_command": "You've tried this command a few times - let's make it work!",
            "repeated_error": "This error is being persistent - we can outsmart it!",
            "no_progress": "Sometimes stepping back reveals new paths forward.",
            "error_spike": "You're exploring lots of options - that's great problem solving!",
            "session_fatigue": "Long coding sessions show real dedication to your project!"
        }

        return summaries.get(pattern.pattern_type, "I notice a pattern we can address.")

    def _get_escalation_options(self, current_level: str) -> List[Dict[str, str]]:
        """Get options to escalate intervention level"""

        escalation_map = {
            "hint": [
                {"level": "help", "title": "Get more help", "description": "Show detailed assistance"},
                {"level": "auto_debug", "title": "Auto-debug", "description": "Let me fix this automatically"}
            ],
            "help": [
                {"level": "auto_debug", "title": "Auto-debug", "description": "Apply automated fix"}
            ],
            "auto_debug": []  # Already at highest level
        }

        return escalation_map.get(current_level, [])

    def handle_intervention_response(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user response to intervention"""

        # Parse intervention command: "intervention:action_id:response"
        parts = command.split(":", 2)
        if len(parts) < 3:
            return {"type": "error", "message": "Invalid intervention response format"}

        action_id = parts[1]
        response_type = parts[2]  # accept, dismiss, escalate, etc.

        if response_type == "dismiss":
            return {
                "type": "intervention_dismissed",
                "message": "Got it! I'll give you space to work. Type 'help' if you need me.",
                "action": "dismissed"
            }
        elif response_type == "accept":
            return self._execute_intervention_action(action_id, context)
        elif response_type.startswith("escalate:"):
            new_level = response_type.split(":", 1)[1]
            return self._escalate_intervention(action_id, new_level, context)
        elif response_type == "preferences":
            return self._show_intervention_preferences()

        return {"type": "error", "message": "Unknown intervention response"}

    def _execute_intervention_action(self, action_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the chosen intervention action"""

        # Parse action_id to understand what to do
        parts = action_id.split("_")
        if len(parts) < 2:
            return {"type": "error", "message": "Invalid action ID"}

        pattern_type = parts[0]
        level = parts[1]

        if pattern_type == "repeated_command":
            return self._help_with_repeated_command(level, context)
        elif pattern_type == "repeated_error":
            return self._help_with_repeated_error(level, context)
        elif pattern_type == "no_progress":
            return self._help_with_no_progress(level, context)
        elif pattern_type == "error_spike":
            return self._help_with_error_spike(level, context)
        elif pattern_type == "session_fatigue":
            return self._help_with_session_fatigue(level, context)

        return {"type": "error", "message": "Unknown intervention type"}

    def _help_with_repeated_command(self, level: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide help for repeated command issues"""

        if level == "hint":
            return {
                "type": "intervention_help",
                "title": "💡 Command Hint",
                "message": "Try checking if there are any typos, or if you need different arguments. You can also try 'help [command]' for syntax.",
                "suggestions": ["Check command syntax", "Verify arguments", "Try alternative command"]
            }
        elif level == "help":
            # Get memory of similar successful commands
            return {
                "type": "intervention_help",
                "title": "🚀 Command Help",
                "message": "Let me show you similar commands that worked before and suggest alternatives.",
                "memory_examples": self._get_memory_examples("command"),
                "alternatives": ["Use different approach", "Break into smaller steps", "Check documentation"]
            }
        elif level == "auto_debug":
            return {
                "type": "intervention_auto",
                "title": "🤖 Auto-Debug Command",
                "message": "I'll analyze this command and suggest or apply fixes automatically.",
                "action": "auto_debug_command",
                "status": "analyzing"
            }

        return {"type": "info", "message": "Help provided"}

    def _help_with_repeated_error(self, level: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide help for repeated errors"""

        if level == "auto_debug":
            return {
                "type": "intervention_auto",
                "title": "⚡ Auto-Fix Error",
                "message": "I'll search my memory for solutions to this error and apply the best fix.",
                "action": "auto_fix_error",
                "status": "searching_memory"
            }

        return {
            "type": "intervention_help",
            "title": "🛠️ Error Analysis",
            "message": "This error has appeared before. Let me show you what typically works.",
            "memory_solutions": self._get_memory_examples("error"),
            "systematic_approach": ["Identify root cause", "Apply known solution", "Verify fix"]
        }

    def _help_with_no_progress(self, level: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide help when no progress is made"""

        return {
            "type": "intervention_help",
            "title": "🎯 Fresh Perspective",
            "message": "Let's step back and look at this differently. Here's what we've tried and what might work:",
            "summary": self._summarize_recent_attempts(),
            "new_approaches": ["Try different strategy", "Use memory insights", "Break problem down"],
            "memory_patterns": self._get_memory_examples("progress")
        }

    def _get_memory_examples(self, example_type: str) -> List[Dict[str, Any]]:
        """Get relevant examples from memory"""
        # This would integrate with the memory system
        # For now, return placeholder structure

        return [
            {
                "description": f"Similar {example_type} that worked",
                "solution": "Example solution from memory",
                "context": "When this worked before",
                "success_rate": "85%"
            }
        ]

    def _summarize_recent_attempts(self) -> Dict[str, Any]:
        """Summarize what user has tried recently"""

        interactions = list(self.frustration_detector.interaction_history)[-10:]

        commands_tried = []
        errors_encountered = []

        for interaction in interactions:
            if interaction["type"] == "command":
                commands_tried.append(interaction["content"])
                if not interaction["success"]:
                    errors_encountered.append(interaction.get("context", {}).get("error", "Unknown error"))

        return {
            "commands_tried": len(set(commands_tried)),
            "unique_errors": len(set(errors_encountered)),
            "time_span": "last 30 minutes",
            "patterns": "Working on command execution and error handling"
        }

    def handle_memory_command(self, message: str) -> Dict[str, Any]:
        """Handle memory-related requests"""
        try:
            # Get recent memories for context
            import requests
            response = requests.get('http://0.0.0.0:5000/memory?limit=10')
            if response.status_code == 200:
                data = response.json()
                memories = data.get('memories', [])

                # Find relevant memories based on message content
                relevant_memories = []
                for memory in memories:
                    if any(word in memory.get('topic', '').lower() or 
                          word in memory.get('input', '').lower() or 
                          word in memory.get('output', '').lower() 
                          for word in message.lower().split()):
                        relevant_memories.append(memory)

                if relevant_memories:
                    memory_list = "\n".join([
                        f"• **{mem.get('topic', 'Untitled')}**: {mem.get('output', 'No details')[:100]}..."
                        for mem in relevant_memories[:3]
                    ])

                    return {
                        "type": "memory_recall",
                        "message": f"🧠 **Found {len(relevant_memories)} relevant memories:**\n\n{memory_list}\n\nWould you like me to elaborate on any of these or help you build on them?",
                        "memories": relevant_memories,
                        "suggestions": ["Build on this solution", "Find similar patterns", "Create new approach"]
                    }
                else:
                    return {
                        "type": "memory_info",
                        "message": f"🔍 I have {len(memories)} memories but none seem directly related to your query. Would you like me to:\n\n• Search more broadly\n• Help you create a new solution\n• Show you recent work patterns",
                        "suggestions": ["Search all memories", "Start fresh approach", "Show recent patterns"]
                    }
            else:
                return {
                    "type": "error",
                    "message": "I'm having trouble accessing my memory right now. Let's work through this step by step."
                }
        except Exception as e:
            return {
                "type": "error",
                "message": f"Memory recall error: {str(e)}. But I'm still here to help you build!"
            }

    def handle_timeline_command(self, message: str) -> Dict[str, Any]:
        """Handle timeline and creative history requests"""
        return {
            "type": "timeline_info",
            "message": "📊 **Creative Timeline Available**\n\nI can show you:\n• Recent project milestones\n• Creative breakthroughs\n• Solution patterns over time\n• Collaboration highlights\n\nUse ⌘M to open your timeline, or tell me what specific period you'd like to explore!",
            "suggestions": ["Open timeline view", "Show recent patterns", "Find breakthrough moments"],
            "keyboard_hint": "Press ⌘M to open timeline"
        }

    def handle_quick_action_command(self, message: str) -> Dict[str, Any]:
        """Handle quick action requests"""
        if "debug" in message.lower():
            return {
                "type": "debug_action",
                "message": "🔧 **Debug Mode Activated**\n\nI'm analyzing your current workspace for:\n• Potential errors or issues\n• Performance bottlenecks\n• Code quality improvements\n• Missing dependencies\n\nWhat specific area would you like me to focus on?",
                "suggestions": ["Analyze code quality", "Check for errors", "Review performance", "Validate dependencies"]
            }
        elif "improve" in message.lower():
            return {
                "type": "improvement_action",
                "message": "⚡ **Enhancement Mode Ready**\n\nI can help improve:\n• Code efficiency and structure\n• User experience and design\n• Feature completeness\n• Documentation and clarity\n\nWhat aspect would you like to enhance first?",
                "suggestions": ["Improve performance", "Enhance UX", "Add features", "Better documentation"]
            }
        elif "feature" in message.lower():
            return {
                "type": "feature_action",
                "message": "✨ **Feature Brainstorming**\n\nLet's explore new possibilities:\n• What would make this more powerful?\n• What would users love to have?\n• What would save time or effort?\n• What would make this unique?\n\nWhat type of feature are you envisioning?",
                "suggestions": ["User-focused features", "Developer tools", "Automation features", "Integration options"]
            }
        else:
            return {
                "type": "quick_actions_info",
                "message": "⚡ **Quick Actions Ready**\n\nI can help you:\n• 🔧 Debug current issues\n• ⚡ Improve existing code\n• ✨ Add new features\n• 🧠 Recall past solutions\n\nPress ⌘Q for quick actions panel, or tell me what you'd like to work on!",
                "suggestions": ["Debug this", "Improve this", "Add feature", "Recall solutions"],
                "keyboard_hint": "Press ⌘Q for quick actions"
            }

    def handle_creative_conversation(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general creative conversation with workspace awareness"""
        workspace_mode = context.get('workspace_mode', 'creative')

        if workspace_mode == 'creative':
            return {
                "type": "creative_response",
                "message": f"🎨 **Creative Mode Active**\n\nI love that you're thinking creatively! Let me help you explore this idea:\n\n\"{message}\"\n\nI can help you:\n• Brainstorm and expand on concepts\n• Find connections to past work\n• Prototype and test ideas\n• Build and iterate together\n\nWhat aspect excites you most? Let's dive deeper!",
                "suggestions": ["Expand this idea", "Find related patterns", "Start prototyping", "Explore alternatives"]
            }
        else:
            return {
                "type": "dev_response", 
                "message": f"⚙️ **Dev Mode Active**\n\nI'm ready to assist with your development needs. For your request:\n\n\"{message}\"\n\nI can help with:\n• Technical implementation\n• Code review and analysis\n• Problem-solving approach\n• Best practices guidance\n\nWhat specific technical aspect should we focus on?",
                "suggestions": ["Technical implementation", "Code review", "Problem analysis", "Best practices"]
            }

    def get_help(self) -> Dict[str, Any]:
        """Get help information with workspace features"""
        return {
            "type": "help",
            "title": "🚀 Jav Creative Workspace",
            "message": """**Your Memory-Driven Creative Partner**

**Core Features:**
• 💬 Natural conversation and collaboration
• 🧠 Memory-driven suggestions and recall
• 📊 Creative timeline and history
• ⚡ Quick actions for common tasks
• 🎯 Smart interventions when stuck

**Keyboard Shortcuts:**
• ⌘J - Open Jav Assistant
• ⌘K - Memory search & recall  
• ⌘M - Creative timeline
• ⌘Q - Quick actions panel
• ⌘⇧M - Switch workspace mode

**Workspace Modes:**
• 🎨 Creative Mode: Collaborative building
• ⚙️ Dev Mode: Technical assistance

**Commands:**
• "audit" - System health check
• "memory [topic]" - Recall past work
• "timeline" - Show creative history
• "debug this" - Analyze current code
• "improve this" - Enhancement suggestions
• "bible [action]" - Documentation management

Just talk to me naturally - I understand context and remember everything we build together!""",
            "suggestions": ["Try a quick action", "Search memories", "Open timeline", "Switch modes"],
            "workspace_integration": True
        }