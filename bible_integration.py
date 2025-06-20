
"""
Bible Integration - Connect Evolution Engine with Jav Agent
"""

from bible_evolution_engine import bible_evolution, BiblDeviation
from jav_agent import jav
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

class BibleIntegration:
    """
    Integrate bible evolution monitoring into Jav workflow
    """
    
    def __init__(self):
        self.bible_monitors = {
            "AGENT_BIBLE.md": self.monitor_agent_bible_compliance,
            "jav_config/Me.md": self.monitor_personal_workflow_compliance,
            "jav_config/*.workflow.md": self.monitor_workflow_compliance
        }
        
        self.compliance_patterns = self.load_compliance_patterns()
    
    def load_compliance_patterns(self) -> Dict[str, Any]:
        """Load patterns that indicate bible compliance or deviation"""
        return {
            "manual_confirmations": [
                r"manual\s+confirmation",
                r"human\s+verification",
                r"explicit\s+approval"
            ],
            "automated_claims": [
                r"automatically\s+deployed",
                r"feature\s+is\s+live",
                r"system\s+is\s+running"
            ],
            "workflow_overrides": [
                r"skipping\s+test",
                r"emergency\s+deploy",
                r"quick\s+fix"
            ],
            "documentation_updates": [
                r"updated\s+bible",
                r"amended\s+process",
                r"new\s+standard"
            ]
        }
    
    def monitor_agent_interaction(self, user_input: str, agent_response: str, 
                                 context: Dict[str, Any]) -> None:
        """Monitor agent interactions for bible compliance"""
        
        # Check for compliance violations
        violations = self.detect_compliance_violations(agent_response)
        
        for violation in violations:
            bible_evolution.track_deviation(
                bible_file="AGENT_BIBLE.md",
                section=violation["section"],
                documented_process=violation["expected"],
                actual_process=violation["actual"],
                context={
                    "user_input": user_input[:200],
                    "agent_response": agent_response[:200],
                    "violation_type": violation["type"],
                    "session_context": context
                },
                override_reason=violation.get("reason")
            )
        
        # Check for successful overrides
        overrides = self.detect_successful_overrides(user_input, agent_response)
        
        for override in overrides:
            bible_evolution.track_deviation(
                bible_file="AGENT_BIBLE.md",
                section=override["section"],
                documented_process=override["standard_process"],
                actual_process=override["override_process"],
                context={
                    "success_metrics": override["success_metrics"],
                    "context": context
                },
                override_reason=override["reason"]
            )
    
    def detect_compliance_violations(self, agent_response: str) -> List[Dict[str, Any]]:
        """Detect potential compliance violations in agent responses"""
        violations = []
        
        # Check for automated claims without confirmation
        if any(re.search(pattern, agent_response, re.IGNORECASE) 
               for pattern in self.compliance_patterns["automated_claims"]):
            
            if not any(re.search(pattern, agent_response, re.IGNORECASE) 
                      for pattern in self.compliance_patterns["manual_confirmations"]):
                
                violations.append({
                    "section": "Confirmation Requirements",
                    "type": "automated_claim_without_confirmation",
                    "expected": "Manual confirmation required for live status claims",
                    "actual": "Claimed live status without confirmation",
                    "severity": "high"
                })
        
        return violations
    
    def detect_successful_overrides(self, user_input: str, agent_response: str) -> List[Dict[str, Any]]:
        """Detect successful overrides that might warrant bible updates"""
        overrides = []
        
        # Look for workflow override patterns
        for pattern in self.compliance_patterns["workflow_overrides"]:
            if re.search(pattern, user_input, re.IGNORECASE):
                
                # Check if override was successful (look for success indicators)
                success_indicators = [
                    "worked", "successful", "fixed", "resolved", 
                    "deployed successfully", "test passed"
                ]
                
                if any(indicator in agent_response.lower() for indicator in success_indicators):
                    overrides.append({
                        "section": "Workflow Standards",
                        "standard_process": "Follow standard deployment process",
                        "override_process": f"Emergency override: {pattern}",
                        "reason": "Emergency situation required standard bypass",
                        "success_metrics": {
                            "outcome": "successful",
                            "time_saved": "estimated",
                            "risk_level": "managed"
                        }
                    })
        
        return overrides
    
    def monitor_personal_workflow_compliance(self, action: str, context: Dict[str, Any]) -> None:
        """Monitor compliance with personal workflow patterns"""
        
        # Load current Me.md preferences
        me_config = jav.load_me_config()
        
        # Check for anti-pattern violations
        for antipattern in me_config.get("anti_patterns", []):
            if self.action_matches_antipattern(action, antipattern):
                bible_evolution.track_deviation(
                    bible_file="jav_config/Me.md",
                    section="Anti-Patterns",
                    documented_process=f"Avoid: {antipattern}",
                    actual_process=f"Performed: {action}",
                    context=context,
                    override_reason=context.get("emergency_reason")
                )
        
        # Check for preferred pattern adherence
        for pattern in me_config.get("common_patterns", []):
            if self.action_should_follow_pattern(action, pattern):
                if not self.action_follows_pattern(action, pattern):
                    bible_evolution.track_deviation(
                        bible_file="jav_config/Me.md",
                        section="Common Patterns",
                        documented_process=pattern,
                        actual_process=action,
                        context=context
                    )
    
    def action_matches_antipattern(self, action: str, antipattern: str) -> bool:
        """Check if action matches an anti-pattern"""
        antipattern_keywords = antipattern.lower().split()
        action_lower = action.lower()
        
        return any(keyword in action_lower for keyword in antipattern_keywords[:2])
    
    def action_should_follow_pattern(self, action: str, pattern: str) -> bool:
        """Check if action should follow a specific pattern"""
        pattern_triggers = {
            "health check": ["deploy", "release", "push"],
            "test": ["commit", "merge", "deploy"],
            "error handling": ["exception", "error", "failure"]
        }
        
        action_lower = action.lower()
        for trigger_category, triggers in pattern_triggers.items():
            if trigger_category in pattern.lower():
                return any(trigger in action_lower for trigger in triggers)
        
        return False
    
    def action_follows_pattern(self, action: str, pattern: str) -> bool:
        """Check if action follows the expected pattern"""
        # Simple implementation - could be enhanced with AI analysis
        pattern_keywords = pattern.lower().split()
        action_lower = action.lower()
        
        return any(keyword in action_lower for keyword in pattern_keywords)
    
    def suggest_bible_amendments(self) -> List[Dict[str, Any]]:
        """Suggest bible amendments based on deviation patterns"""
        
        # Analyze patterns
        patterns = bible_evolution.analyze_deviation_patterns()
        
        amendments = []
        
        # High-frequency successful deviations suggest new standards
        for high_freq in patterns["high_frequency_deviations"]:
            deviation = high_freq["deviation"]
            
            if deviation.success_rate > 0.8:  # 80% success rate
                amendments.append({
                    "type": "process_update",
                    "bible_file": deviation.bible_file,
                    "section": deviation.section,
                    "current": deviation.documented_process,
                    "proposed": deviation.actual_process,
                    "reasoning": f"Pattern used successfully {deviation.frequency} times with {deviation.success_rate:.1%} success rate",
                    "confidence": min(0.9, deviation.frequency * 0.1),
                    "evidence": {
                        "frequency": deviation.frequency,
                        "success_rate": deviation.success_rate,
                        "contexts": deviation.context
                    }
                })
        
        # Systematic drift suggests section needs review
        for drift in patterns["systematic_drift"]:
            amendments.append({
                "type": "section_review",
                "bible_file": drift["bible_file"],
                "section": drift["section"],
                "reasoning": f"Multiple deviations ({drift['deviations']}) suggest systematic issues",
                "confidence": 0.7,
                "recommendation": "Comprehensive section review needed"
            })
        
        return amendments
    
    def generate_team_review_session(self) -> Dict[str, Any]:
        """Generate comprehensive team review session"""
        
        review_session = bible_evolution.generate_review_session()
        
        # Add team-specific context
        review_session["team_context"] = {
            "recent_projects": self.get_recent_project_context(),
            "workflow_changes": self.get_workflow_changes(),
            "success_patterns": self.get_success_patterns(),
            "pain_points": self.get_team_pain_points()
        }
        
        # Add discussion agenda
        review_session["discussion_agenda"] = [
            "Review high-frequency deviations",
            "Discuss successful override patterns",
            "Evaluate proposed amendments",
            "Identify missing documentation",
            "Plan implementation timeline",
            "Assign review responsibilities"
        ]
        
        # Add consensus tracking
        review_session["consensus_tracking"] = {
            "amendments_to_vote": len(review_session.get("proposed_amendments", [])),
            "voting_deadline": (datetime.now() + datetime.timedelta(days=7)).isoformat(),
            "required_approvals": 2,  # Configurable
            "voting_method": "async_comment_approval"
        }
        
        return review_session
    
    def get_recent_project_context(self) -> List[Dict[str, Any]]:
        """Get context from recent projects"""
        # This would integrate with project tracking
        return [
            {
                "project": "MemoryOS v2.0",
                "timeline": "Last 30 days",
                "workflow_changes": ["Emergency deploy process", "Health check automation"],
                "outcomes": "successful"
            }
        ]
    
    def get_workflow_changes(self) -> List[str]:
        """Get recent workflow changes"""
        return [
            "Added bulletproof error handling",
            "Implemented health check automation",
            "Enhanced logging and monitoring"
        ]
    
    def get_success_patterns(self) -> List[str]:
        """Get patterns that led to success"""
        return [
            "Pre-deploy health checks",
            "Gradual rollout process",
            "Comprehensive error logging"
        ]
    
    def get_team_pain_points(self) -> List[str]:
        """Get current team pain points"""
        return [
            "Manual confirmation overhead",
            "Inconsistent workflow documentation",
            "Emergency override tracking"
        ]
    
    def create_onboarding_materials(self, recent_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create onboarding materials for new team members"""
        
        materials = {
            "welcome_brief": bible_evolution.generate_onboarding_brief("new_team_member"),
            "workflow_summary": self.generate_workflow_summary(),
            "recent_changes_guide": self.generate_changes_guide(recent_changes),
            "practice_scenarios": self.generate_practice_scenarios(),
            "support_contacts": {
                "bible_questions": "@team-lead",
                "process_clarification": "@jav-agent",
                "technical_issues": "@technical-lead"
            }
        }
        
        return materials
    
    def generate_workflow_summary(self) -> Dict[str, Any]:
        """Generate current workflow summary"""
        return {
            "core_principles": [
                "Health checks before deploy",
                "Manual confirmation for critical changes",
                "Comprehensive error handling",
                "Document all deviations"
            ],
            "standard_processes": [
                "Development → Test → Health Check → Deploy",
                "Emergency Override → Document → Review → Update Bible",
                "Pattern Recognition → Propose Amendment → Team Review → Implement"
            ],
            "tools": [
                "Jav Agent for monitoring",
                "Bible Evolution Engine for tracking",
                "Memory system for logging"
            ]
        }
    
    def generate_changes_guide(self, recent_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate guide for recent changes"""
        return {
            "summary": f"{len(recent_changes)} recent changes to workflows",
            "impact_levels": {
                "high": [c for c in recent_changes if c.get("impact") == "high"],
                "medium": [c for c in recent_changes if c.get("impact") == "medium"],
                "low": [c for c in recent_changes if c.get("impact") == "low"]
            },
            "what_changed": [c["changes"] for c in recent_changes],
            "why_changed": [c["reasoning"] for c in recent_changes if "reasoning" in c],
            "action_required": "Review changes, ask questions, practice new workflows"
        }
    
    def generate_practice_scenarios(self) -> List[Dict[str, Any]]:
        """Generate practice scenarios for new team members"""
        return [
            {
                "scenario": "Emergency Deploy",
                "description": "Critical bug fix needs immediate deployment",
                "steps": [
                    "Identify override justification",
                    "Document emergency reason",
                    "Follow abbreviated health check",
                    "Deploy with monitoring",
                    "Create post-deploy review"
                ],
                "learning_goals": ["Emergency procedures", "Documentation requirements"]
            },
            {
                "scenario": "Process Deviation",
                "description": "Standard process doesn't fit current situation",
                "steps": [
                    "Identify why standard doesn't apply",
                    "Document alternative approach",
                    "Execute with extra monitoring",
                    "Track outcome for bible review"
                ],
                "learning_goals": ["Deviation tracking", "Pattern recognition"]
            }
        ]

# Global integration instance
bible_integration = BibleIntegration()
