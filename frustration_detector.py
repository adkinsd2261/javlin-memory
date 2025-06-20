
"""
Frustration Loop Detector - Gentle Creative Support
Watches for signs of user frustration without limiting creativity
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from collections import deque
import re

class FrustrationPattern:
    """Represents a detected frustration pattern"""
    
    def __init__(self, pattern_type: str, severity: float, evidence: List[str], 
                 suggested_interventions: List[str]):
        self.pattern_type = pattern_type
        self.severity = severity  # 0.0 to 1.0
        self.evidence = evidence
        self.suggested_interventions = suggested_interventions
        self.detected_at = datetime.now(timezone.utc)

class FrustrationDetector:
    """
    Detects frustration loops while preserving creative freedom
    """
    
    def __init__(self, jav_agent):
        self.jav = jav_agent
        self.logger = logging.getLogger('FrustrationDetector')
        
        # Track user interaction patterns
        self.interaction_history = deque(maxlen=50)  # Last 50 interactions
        self.error_history = deque(maxlen=20)  # Last 20 errors
        self.command_history = deque(maxlen=30)  # Last 30 commands
        
        # Pattern detection thresholds
        self.thresholds = {
            "repeated_command": 3,  # Same command 3+ times
            "repeated_error": 2,    # Same error 2+ times
            "no_progress_minutes": 15,  # 15 minutes without progress
            "error_spike": 5,       # 5+ errors in short time
            "session_length": 120   # 2+ hours continuous work
        }
        
        # Intervention levels
        self.intervention_levels = {
            "hint": 0.3,      # Light suggestion
            "help": 0.6,      # Active assistance offer
            "auto_debug": 0.8  # Automated debugging offer
        }
        
        self.last_intervention = None
        self.intervention_cooldown = timedelta(minutes=10)
        
    def track_interaction(self, interaction_type: str, content: str, 
                         success: bool, context: Dict[str, Any] = None):
        """Track user interactions for pattern analysis"""
        
        interaction = {
            "type": interaction_type,
            "content": content[:200],  # Truncate for storage
            "success": success,
            "timestamp": datetime.now(timezone.utc),
            "context": context or {}
        }
        
        self.interaction_history.append(interaction)
        
        # Track specific patterns
        if not success and interaction_type == "command":
            self.error_history.append({
                "command": content,
                "error": context.get("error", "Unknown error"),
                "timestamp": datetime.now(timezone.utc)
            })
        
        if interaction_type == "command":
            self.command_history.append({
                "command": content,
                "timestamp": datetime.now(timezone.utc),
                "success": success
            })
    
    def detect_frustration_patterns(self) -> List[FrustrationPattern]:
        """Analyze patterns and detect potential frustration"""
        
        patterns = []
        
        # Check for repeated commands
        repeated_cmd = self._detect_repeated_commands()
        if repeated_cmd:
            patterns.append(repeated_cmd)
        
        # Check for repeated errors
        repeated_err = self._detect_repeated_errors()
        if repeated_err:
            patterns.append(repeated_err)
        
        # Check for lack of progress
        no_progress = self._detect_no_progress()
        if no_progress:
            patterns.append(no_progress)
        
        # Check for error spikes
        error_spike = self._detect_error_spike()
        if error_spike:
            patterns.append(error_spike)
        
        # Check session fatigue
        session_fatigue = self._detect_session_fatigue()
        if session_fatigue:
            patterns.append(session_fatigue)
        
        return patterns
    
    def _detect_repeated_commands(self) -> Optional[FrustrationPattern]:
        """Detect when user repeats the same command multiple times"""
        
        if len(self.command_history) < self.thresholds["repeated_command"]:
            return None
        
        # Get last few commands
        recent_commands = list(self.command_history)[-self.thresholds["repeated_command"]:]
        
        # Check if they're all the same (or very similar)
        first_cmd = recent_commands[0]["command"]
        similar_count = 1
        
        for cmd in recent_commands[1:]:
            if self._commands_similar(first_cmd, cmd["command"]):
                similar_count += 1
        
        if similar_count >= self.thresholds["repeated_command"]:
            failed_attempts = sum(1 for cmd in recent_commands if not cmd["success"])
            
            severity = min(0.9, (similar_count * 0.2) + (failed_attempts * 0.2))
            
            evidence = [
                f"Repeated command '{first_cmd[:30]}...' {similar_count} times",
                f"{failed_attempts} failed attempts"
            ]
            
            interventions = self._suggest_command_interventions(first_cmd, failed_attempts)
            
            return FrustrationPattern(
                "repeated_command",
                severity,
                evidence,
                interventions
            )
        
        return None
    
    def _detect_repeated_errors(self) -> Optional[FrustrationPattern]:
        """Detect when user encounters the same error repeatedly"""
        
        if len(self.error_history) < self.thresholds["repeated_error"]:
            return None
        
        # Group errors by similarity
        error_groups = {}
        
        for error in self.error_history:
            error_key = self._normalize_error(error["error"])
            if error_key not in error_groups:
                error_groups[error_key] = []
            error_groups[error_key].append(error)
        
        # Find groups with repeated errors
        for error_key, errors in error_groups.items():
            if len(errors) >= self.thresholds["repeated_error"]:
                
                # Check if recent
                recent_errors = [e for e in errors 
                               if (datetime.now(timezone.utc) - e["timestamp"]).total_seconds() < 1800]  # 30 minutes
                
                if len(recent_errors) >= self.thresholds["repeated_error"]:
                    severity = min(0.9, len(recent_errors) * 0.3)
                    
                    evidence = [
                        f"Same error occurred {len(recent_errors)} times",
                        f"Error pattern: {error_key[:50]}..."
                    ]
                    
                    interventions = self._suggest_error_interventions(error_key, recent_errors)
                    
                    return FrustrationPattern(
                        "repeated_error",
                        severity,
                        evidence,
                        interventions
                    )
        
        return None
    
    def _detect_no_progress(self) -> Optional[FrustrationPattern]:
        """Detect when user hasn't made progress for a while"""
        
        if len(self.interaction_history) < 5:
            return None
        
        now = datetime.now(timezone.utc)
        
        # Look for last successful interaction
        last_success = None
        for interaction in reversed(self.interaction_history):
            if interaction["success"]:
                last_success = interaction["timestamp"]
                break
        
        if last_success:
            time_since_success = (now - last_success).total_seconds() / 60  # minutes
            
            if time_since_success >= self.thresholds["no_progress_minutes"]:
                severity = min(0.8, time_since_success / 30)  # Max at 30 minutes
                
                evidence = [
                    f"No successful actions for {int(time_since_success)} minutes",
                    f"Last success: {last_success.strftime('%H:%M')}"
                ]
                
                interventions = self._suggest_progress_interventions()
                
                return FrustrationPattern(
                    "no_progress",
                    severity,
                    evidence,
                    interventions
                )
        
        return None
    
    def _detect_error_spike(self) -> Optional[FrustrationPattern]:
        """Detect when errors spike in a short time"""
        
        if len(self.error_history) < self.thresholds["error_spike"]:
            return None
        
        now = datetime.now(timezone.utc)
        recent_errors = [e for e in self.error_history 
                        if (now - e["timestamp"]).total_seconds() < 600]  # 10 minutes
        
        if len(recent_errors) >= self.thresholds["error_spike"]:
            severity = min(0.9, len(recent_errors) * 0.15)
            
            evidence = [
                f"{len(recent_errors)} errors in the last 10 minutes",
                "Error spike detected"
            ]
            
            interventions = self._suggest_spike_interventions(recent_errors)
            
            return FrustrationPattern(
                "error_spike",
                severity,
                evidence,
                interventions
            )
        
        return None
    
    def _detect_session_fatigue(self) -> Optional[FrustrationPattern]:
        """Detect long coding sessions that might lead to fatigue"""
        
        if not self.interaction_history:
            return None
        
        session_start = self.interaction_history[0]["timestamp"]
        session_duration = (datetime.now(timezone.utc) - session_start).total_seconds() / 60  # minutes
        
        if session_duration >= self.thresholds["session_length"]:
            # Check error rate in recent interactions
            recent_interactions = [i for i in self.interaction_history if i["timestamp"] > datetime.now(timezone.utc) - timedelta(minutes=30)]
            
            if recent_interactions:
                error_rate = sum(1 for i in recent_interactions if not i["success"]) / len(recent_interactions)
                
                if error_rate > 0.4:  # 40% error rate
                    severity = min(0.7, (session_duration / 180) + error_rate)  # Factor in duration and errors
                    
                    evidence = [
                        f"Coding session: {int(session_duration)} minutes",
                        f"Recent error rate: {error_rate:.1%}"
                    ]
                    
                    interventions = self._suggest_fatigue_interventions()
                    
                    return FrustrationPattern(
                        "session_fatigue",
                        severity,
                        evidence,
                        interventions
                    )
        
        return None
    
    def should_intervene(self, patterns: List[FrustrationPattern]) -> Optional[Dict[str, Any]]:
        """Determine if and how to intervene based on detected patterns"""
        
        if not patterns:
            return None
        
        # Check intervention cooldown
        if (self.last_intervention and 
            datetime.now(timezone.utc) - self.last_intervention < self.intervention_cooldown):
            return None
        
        # Find highest severity pattern
        highest_pattern = max(patterns, key=lambda p: p.severity)
        
        # Determine intervention level
        intervention_level = None
        for level, threshold in self.intervention_levels.items():
            if highest_pattern.severity >= threshold:
                intervention_level = level
        
        if intervention_level:
            return {
                "level": intervention_level,
                "pattern": highest_pattern,
                "all_patterns": patterns,
                "suggested_actions": self._create_intervention_actions(highest_pattern, intervention_level)
            }
        
        return None
    
    def _commands_similar(self, cmd1: str, cmd2: str) -> bool:
        """Check if two commands are similar"""
        # Simple similarity check
        cmd1_norm = re.sub(r'\s+', ' ', cmd1.lower().strip())
        cmd2_norm = re.sub(r'\s+', ' ', cmd2.lower().strip())
        
        # Exact match
        if cmd1_norm == cmd2_norm:
            return True
        
        # Similar if they share most words
        words1 = set(cmd1_norm.split())
        words2 = set(cmd2_norm.split())
        
        if words1 and words2:
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            return intersection / union > 0.7
        
        return False
    
    def _normalize_error(self, error: str) -> str:
        """Normalize error message for grouping"""
        # Remove specific details but keep error type
        normalized = re.sub(r'\b\d+\b', 'NUM', error)  # Replace numbers
        normalized = re.sub(r'\'[^\']*\'', 'STR', normalized)  # Replace strings
        normalized = re.sub(r'/[^/\s]*', 'PATH', normalized)  # Replace paths
        return normalized[:100]  # Truncate
    
    def _suggest_command_interventions(self, command: str, failed_attempts: int) -> List[str]:
        """Suggest interventions for repeated commands"""
        interventions = []
        
        if failed_attempts > 0:
            interventions.extend([
                "Show similar command that worked before",
                "Debug the current command step-by-step",
                "Try alternative approach from memory"
            ])
        
        interventions.extend([
            "Explain what this command does",
            "Suggest similar commands",
            "Break down into smaller steps"
        ])
        
        return interventions
    
    def _suggest_error_interventions(self, error_pattern: str, errors: List[Dict]) -> List[str]:
        """Suggest interventions for repeated errors"""
        return [
            "Search memory for similar error solutions",
            "Explain the error in detail",
            "Suggest known fixes for this error type",
            "Auto-debug the issue",
            "Show step-by-step troubleshooting"
        ]
    
    def _suggest_progress_interventions(self) -> List[str]:
        """Suggest interventions when no progress is made"""
        return [
            "Review what we've tried so far",
            "Suggest a different approach",
            "Take a step back and reassess",
            "Show successful patterns from memory",
            "Break problem into smaller pieces"
        ]
    
    def _suggest_spike_interventions(self, errors: List[Dict]) -> List[str]:
        """Suggest interventions for error spikes"""
        return [
            "Pause and review the error patterns",
            "Suggest systematic debugging approach",
            "Show what's worked before in similar situations",
            "Auto-analyze the error cluster",
            "Reset to last known good state"
        ]
    
    def _suggest_fatigue_interventions(self) -> List[str]:
        """Suggest interventions for session fatigue"""
        return [
            "Celebrate progress made so far",
            "Suggest taking a short break",
            "Auto-save current work state",
            "Show session summary and achievements",
            "Offer to continue later with fresh perspective"
        ]
    
    def _create_intervention_actions(self, pattern: FrustrationPattern, level: str) -> List[Dict[str, Any]]:
        """Create actionable intervention suggestions"""
        actions = []
        
        for intervention in pattern.suggested_interventions[:3]:  # Top 3 suggestions
            actions.append({
                "title": intervention,
                "type": level,
                "pattern_type": pattern.pattern_type,
                "action_id": f"{pattern.pattern_type}_{level}_{len(actions)}"
            })
        
        return actions
    
    def mark_intervention_shown(self):
        """Mark that an intervention was shown to user"""
        self.last_intervention = datetime.now(timezone.utc)
    
    def get_encouragement_message(self, pattern: FrustrationPattern) -> str:
        """Generate encouraging message based on pattern"""
        
        encouragements = {
            "repeated_command": [
                "I notice you're working hard on this command - that persistence is great!",
                "You're really diving deep into this - let me help make it work!",
                "I see you're determined to get this right - that's the spirit!"
            ],
            "repeated_error": [
                "These kinds of errors can be tricky - you're not alone in this!",
                "I see you're tackling a challenging issue - let's solve it together!",
                "This error is giving you a workout - let's outsmart it!"
            ],
            "no_progress": [
                "Sometimes the best breakthroughs come after the toughest challenges!",
                "You're building valuable experience even when things feel stuck!",
                "Great minds work through complex problems - that's what you're doing!"
            ],
            "error_spike": [
                "Lots of trial and error means you're exploring thoroughly!",
                "You're learning fast - each error teaches us something new!",
                "This rapid iteration shows great problem-solving instincts!"
            ],
            "session_fatigue": [
                "Wow, you've been coding for a while - that dedication is impressive!",
                "Long sessions like this show real commitment to your project!",
                "You've accomplished a lot today - you should be proud!"
            ]
        }
        
        import random
        messages = encouragements.get(pattern.pattern_type, ["You're doing great - keep it up!"])
        return random.choice(messages)

# Global instance for the Jav agent
frustration_detector = None

def init_frustration_detector(jav_agent):
    """Initialize frustration detector with Jav agent"""
    global frustration_detector
    frustration_detector = FrustrationDetector(jav_agent)
    return frustration_detector
