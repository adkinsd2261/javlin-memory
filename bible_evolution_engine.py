
"""
Bible Evolution Engine - Living Documentation System
Monitors deviations, tracks patterns, and evolves product bibles with reality
"""

import os
import json
import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import re
import difflib

@dataclass
class BiblDeviation:
    """Track deviations from documented processes"""
    id: str
    bible_file: str
    section: str
    documented_process: str
    actual_process: str
    frequency: int
    first_seen: str
    last_seen: str
    context: Dict[str, Any]
    override_reason: Optional[str] = None
    success_rate: float = 0.0
    user_approved: bool = False

@dataclass
class BibleAmendment:
    """Proposed changes to bible documentation"""
    id: str
    bible_file: str
    section: str
    current_text: str
    proposed_text: str
    reasoning: str
    supporting_deviations: List[str]
    confidence: float
    created_at: str
    status: str = "draft"  # draft, reviewed, approved, rejected, implemented
    team_feedback: List[Dict[str, Any]] = None

@dataclass
class BibleVersion:
    """Track bible versions and changes"""
    version: str
    bible_file: str
    changes: List[str]
    changelog: str
    created_at: str
    prompted_by: str
    context_sessions: List[str]

class BibleEvolutionEngine:
    """
    Monitor and evolve product bibles based on real-world usage
    """
    
    def __init__(self, memory_api_base: str = "http://0.0.0.0:5000"):
        self.memory_api = memory_api_base
        self.evolution_dir = Path("bible_evolution")
        self.evolution_dir.mkdir(exist_ok=True)
        
        # Bible files to monitor
        self.bible_files = [
            "AGENT_BIBLE.md",
            "jav_config/Me.md",
            "jav_config/*.workflow.md"
        ]
        
        self.deviations = self.load_deviations()
        self.amendments = self.load_amendments()
        self.versions = self.load_versions()
        
        self.logger = logging.getLogger('BibleEvolution')
    
    def load_deviations(self) -> List[BiblDeviation]:
        """Load tracked deviations"""
        deviations_file = self.evolution_dir / "deviations.json"
        try:
            with open(deviations_file, 'r') as f:
                data = json.load(f)
                return [BiblDeviation(**item) for item in data]
        except FileNotFoundError:
            return []
    
    def save_deviations(self):
        """Save deviations to disk"""
        deviations_file = self.evolution_dir / "deviations.json"
        with open(deviations_file, 'w') as f:
            json.dump([asdict(dev) for dev in self.deviations], f, indent=2)
    
    def load_amendments(self) -> List[BibleAmendment]:
        """Load proposed amendments"""
        amendments_file = self.evolution_dir / "amendments.json"
        try:
            with open(amendments_file, 'r') as f:
                data = json.load(f)
                return [BibleAmendment(**item) for item in data]
        except FileNotFoundError:
            return []
    
    def save_amendments(self):
        """Save amendments to disk"""
        amendments_file = self.evolution_dir / "amendments.json"
        with open(amendments_file, 'w') as f:
            json.dump([asdict(amend) for amend in self.amendments], f, indent=2, default=str)
    
    def load_versions(self) -> List[BibleVersion]:
        """Load bible version history"""
        versions_file = self.evolution_dir / "versions.json"
        try:
            with open(versions_file, 'r') as f:
                data = json.load(f)
                return [BibleVersion(**item) for item in data]
        except FileNotFoundError:
            return []
    
    def save_versions(self):
        """Save version history to disk"""
        versions_file = self.evolution_dir / "versions.json"
        with open(versions_file, 'w') as f:
            json.dump([asdict(ver) for ver in self.versions], f, indent=2, default=str)
    
    def track_deviation(self, bible_file: str, section: str, 
                       documented_process: str, actual_process: str,
                       context: Dict[str, Any], override_reason: str = None) -> str:
        """Track a deviation from documented process"""
        
        # Create deviation signature for deduplication
        sig = hashlib.md5(f"{bible_file}:{section}:{actual_process}".encode()).hexdigest()[:8]
        
        # Check if deviation already exists
        existing = next((d for d in self.deviations if d.id == sig), None)
        
        if existing:
            existing.frequency += 1
            existing.last_seen = datetime.now(timezone.utc).isoformat()
            existing.context.update(context)
            if override_reason:
                existing.override_reason = override_reason
        else:
            deviation = BiblDeviation(
                id=sig,
                bible_file=bible_file,
                section=section,
                documented_process=documented_process,
                actual_process=actual_process,
                frequency=1,
                first_seen=datetime.now(timezone.utc).isoformat(),
                last_seen=datetime.now(timezone.utc).isoformat(),
                context=context,
                override_reason=override_reason
            )
            self.deviations.append(deviation)
        
        self.save_deviations()
        self.log_to_memory(
            topic=f"Bible Deviation Tracked: {section}",
            type_="BibleDeviation",
            input_=f"Documented: {documented_process[:100]}",
            output=f"Actual: {actual_process[:100]}",
            success=True,
            category="bible_evolution"
        )
        
        return sig
    
    def analyze_deviation_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in deviations to suggest amendments"""
        analysis = {
            "high_frequency_deviations": [],
            "successful_overrides": [],
            "systematic_drift": [],
            "amendment_candidates": []
        }
        
        for deviation in self.deviations:
            # High frequency deviations (5+ occurrences)
            if deviation.frequency >= 5:
                analysis["high_frequency_deviations"].append({
                    "deviation": deviation,
                    "recommendation": "Consider making this the new standard"
                })
            
            # Successful overrides (success rate > 80%)
            if deviation.success_rate > 0.8 and deviation.frequency >= 3:
                analysis["successful_overrides"].append({
                    "deviation": deviation,
                    "recommendation": "Update bible to reflect successful pattern"
                })
            
            # Look for systematic drift in specific sections
            section_deviations = [d for d in self.deviations if d.section == deviation.section]
            if len(section_deviations) >= 3:
                analysis["systematic_drift"].append({
                    "section": deviation.section,
                    "bible_file": deviation.bible_file,
                    "deviations": len(section_deviations),
                    "recommendation": "Section may need comprehensive review"
                })
        
        return analysis
    
    def propose_amendment(self, bible_file: str, section: str,
                         current_text: str, proposed_text: str,
                         reasoning: str, supporting_deviations: List[str]) -> str:
        """Propose an amendment to bible documentation"""
        
        amendment_id = hashlib.md5(f"{bible_file}:{section}:{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        
        # Calculate confidence based on supporting evidence
        confidence = min(0.9, len(supporting_deviations) * 0.2 + 0.3)
        
        amendment = BibleAmendment(
            id=amendment_id,
            bible_file=bible_file,
            section=section,
            current_text=current_text,
            proposed_text=proposed_text,
            reasoning=reasoning,
            supporting_deviations=supporting_deviations,
            confidence=confidence,
            created_at=datetime.now(timezone.utc).isoformat(),
            team_feedback=[]
        )
        
        self.amendments.append(amendment)
        self.save_amendments()
        
        self.log_to_memory(
            topic=f"Bible Amendment Proposed: {section}",
            type_="BibleAmendment",
            input_=f"Section: {section}, Confidence: {confidence:.1%}",
            output=f"Reasoning: {reasoning}",
            success=True,
            category="bible_evolution"
        )
        
        return amendment_id
    
    def generate_review_session(self) -> Dict[str, Any]:
        """Generate a comprehensive bible review session"""
        
        # Analyze all deviations since last review
        last_review = self.get_last_review_date()
        recent_deviations = [d for d in self.deviations 
                           if d.last_seen > last_review] if last_review else self.deviations
        
        # Get pattern analysis
        patterns = self.analyze_deviation_patterns()
        
        # Generate automatic amendment proposals
        auto_amendments = self.generate_automatic_amendments(patterns)
        
        review_session = {
            "session_id": f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_deviations": len(recent_deviations),
                "high_priority_issues": len(patterns["high_frequency_deviations"]),
                "proposed_amendments": len(auto_amendments),
                "files_affected": list(set(d.bible_file for d in recent_deviations))
            },
            "deviation_analysis": patterns,
            "proposed_amendments": auto_amendments,
            "recommendations": self.generate_review_recommendations(patterns),
            "next_steps": [
                "Review proposed amendments",
                "Gather team feedback",
                "Test proposed changes",
                "Update bible documentation",
                "Brief team on changes"
            ]
        }
        
        # Save review session
        review_file = self.evolution_dir / f"review_{review_session['session_id']}.json"
        with open(review_file, 'w') as f:
            json.dump(review_session, f, indent=2, default=str)
        
        return review_session
    
    def generate_automatic_amendments(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate automatic amendment proposals based on patterns"""
        amendments = []
        
        for high_freq in patterns["high_frequency_deviations"]:
            deviation = high_freq["deviation"]
            
            # Create amendment proposal
            proposed_text = self.generate_amendment_text(deviation)
            
            amendment_id = self.propose_amendment(
                bible_file=deviation.bible_file,
                section=deviation.section,
                current_text=deviation.documented_process,
                proposed_text=proposed_text,
                reasoning=f"High frequency deviation ({deviation.frequency} occurrences) suggests new standard practice",
                supporting_deviations=[deviation.id]
            )
            
            amendments.append({
                "amendment_id": amendment_id,
                "priority": "high",
                "type": "process_update",
                "evidence_strength": "strong" if deviation.frequency > 10 else "moderate"
            })
        
        return amendments
    
    def generate_amendment_text(self, deviation: BiblDeviation) -> str:
        """Generate proposed amendment text based on deviation"""
        # This is a simple implementation - could be enhanced with AI
        base_text = deviation.documented_process
        actual_process = deviation.actual_process
        
        # Create a hybrid approach
        proposed = f"""## {deviation.section} (Updated Process)

**Standard Approach:**
{base_text}

**Alternative Approach (when applicable):**
{actual_process}

**Guidelines:**
- Use standard approach for {self.infer_standard_conditions(deviation)}
- Use alternative approach when {self.infer_alternative_conditions(deviation)}
- Document reason for deviation in session notes

*Updated based on {deviation.frequency} successful applications*
"""
        return proposed
    
    def infer_standard_conditions(self, deviation: BiblDeviation) -> str:
        """Infer when standard approach should be used"""
        # Simple inference - could be enhanced
        if "deploy" in deviation.section.lower():
            return "deploying to production"
        elif "test" in deviation.section.lower():
            return "comprehensive testing"
        else:
            return "standard workflows"
    
    def infer_alternative_conditions(self, deviation: BiblDeviation) -> str:
        """Infer when alternative approach should be used"""
        if deviation.override_reason:
            return deviation.override_reason
        else:
            return "rapid prototyping or emergency situations"
    
    def get_last_review_date(self) -> Optional[str]:
        """Get the date of the last bible review"""
        review_files = list(self.evolution_dir.glob("review_*.json"))
        if not review_files:
            return None
        
        latest_review = max(review_files, key=lambda f: f.stat().st_mtime)
        try:
            with open(latest_review, 'r') as f:
                data = json.load(f)
                return data.get("created_at")
        except:
            return None
    
    def generate_review_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations for review"""
        recommendations = []
        
        if patterns["high_frequency_deviations"]:
            recommendations.append(
                f"Update {len(patterns['high_frequency_deviations'])} high-frequency deviation patterns to new standards"
            )
        
        if patterns["systematic_drift"]:
            recommendations.append(
                f"Comprehensive review needed for {len(patterns['systematic_drift'])} sections showing systematic drift"
            )
        
        if patterns["successful_overrides"]:
            recommendations.append(
                f"Incorporate {len(patterns['successful_overrides'])} successful override patterns into standard procedures"
            )
        
        recommendations.extend([
            "Schedule team discussion on workflow evolution",
            "Test proposed changes in non-critical context",
            "Create onboarding materials for new patterns",
            "Set up monitoring for new standard compliance"
        ])
        
        return recommendations
    
    def create_bible_version(self, bible_file: str, changes: List[str], 
                           changelog: str, prompted_by: str, 
                           context_sessions: List[str]) -> str:
        """Create new version of bible file"""
        
        # Generate version number
        existing_versions = [v for v in self.versions if v.bible_file == bible_file]
        version_num = len(existing_versions) + 1
        version = f"v{version_num}.0"
        
        bible_version = BibleVersion(
            version=version,
            bible_file=bible_file,
            changes=changes,
            changelog=changelog,
            created_at=datetime.now(timezone.utc).isoformat(),
            prompted_by=prompted_by,
            context_sessions=context_sessions
        )
        
        self.versions.append(bible_version)
        self.save_versions()
        
        # Create version backup
        self.backup_bible_version(bible_file, version)
        
        return version
    
    def backup_bible_version(self, bible_file: str, version: str):
        """Create backup of bible version"""
        backup_dir = self.evolution_dir / "versions"
        backup_dir.mkdir(exist_ok=True)
        
        if os.path.exists(bible_file):
            backup_file = backup_dir / f"{Path(bible_file).stem}_{version}.md"
            with open(bible_file, 'r') as src, open(backup_file, 'w') as dst:
                dst.write(src.read())
    
    def generate_onboarding_brief(self, user_type: str = "new_user") -> Dict[str, Any]:
        """Generate briefing for new users on recent bible changes"""
        
        # Get recent changes (last 30 days)
        cutoff_date = (datetime.now(timezone.utc) - 
                      datetime.timedelta(days=30)).isoformat()
        
        recent_versions = [v for v in self.versions 
                          if v.created_at > cutoff_date]
        
        brief = {
            "briefing_id": f"onboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_type": user_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "recent_changes": {
                "period": "Last 30 days",
                "total_updates": len(recent_versions),
                "files_updated": list(set(v.bible_file for v in recent_versions)),
                "major_changes": [v for v in recent_versions if "major" in v.changelog.lower()]
            },
            "key_updates": self.summarize_key_updates(recent_versions),
            "action_items": [
                "Review updated bible sections",
                "Ask questions about new processes",
                "Practice new workflows in safe environment",
                "Provide feedback on clarity"
            ],
            "contacts": {
                "bible_questions": "Ask in #engineering channel",
                "process_clarification": "Tag @jav-agent or team lead"
            }
        }
        
        return brief
    
    def summarize_key_updates(self, versions: List[BibleVersion]) -> List[Dict[str, Any]]:
        """Summarize key updates for briefing"""
        summaries = []
        
        for version in versions:
            summary = {
                "file": version.bible_file,
                "version": version.version,
                "date": version.created_at[:10],
                "changes": version.changes,
                "impact": self.assess_change_impact(version),
                "why_changed": version.changelog
            }
            summaries.append(summary)
        
        return summaries
    
    def assess_change_impact(self, version: BibleVersion) -> str:
        """Assess the impact level of changes"""
        change_text = " ".join(version.changes).lower()
        
        if any(word in change_text for word in ["critical", "major", "breaking"]):
            return "high"
        elif any(word in change_text for word in ["process", "workflow", "standard"]):
            return "medium"
        else:
            return "low"
    
    def monitor_compliance(self, bible_file: str) -> Dict[str, Any]:
        """Monitor compliance with current bible standards"""
        
        # Check recent activities against bible standards
        compliance_report = {
            "bible_file": bible_file,
            "check_date": datetime.now(timezone.utc).isoformat(),
            "compliance_score": 0.0,
            "violations": [],
            "deviations": [],
            "recommendations": []
        }
        
        # Get recent deviations for this bible
        recent_deviations = [d for d in self.deviations 
                           if d.bible_file == bible_file]
        
        if recent_deviations:
            # Calculate compliance score
            total_activities = sum(d.frequency for d in recent_deviations)
            compliant_activities = sum(d.frequency for d in recent_deviations 
                                     if d.user_approved)
            
            compliance_report["compliance_score"] = (
                compliant_activities / total_activities if total_activities > 0 else 1.0
            )
            
            compliance_report["deviations"] = [
                {
                    "section": d.section,
                    "frequency": d.frequency,
                    "approved": d.user_approved,
                    "last_seen": d.last_seen
                }
                for d in recent_deviations
            ]
        
        return compliance_report
    
    def log_to_memory(self, topic: str, type_: str, input_: str, output: str, 
                     success: bool = True, category: str = "bible_evolution") -> bool:
        """Log activities to memory system"""
        try:
            import requests
            
            data = {
                "topic": topic,
                "type": type_,
                "input": input_,
                "output": output,
                "success": success,
                "category": category,
                "tags": ["bible", "evolution", "documentation"],
                "context": "Bible Evolution Engine"
            }
            
            headers = {"X-API-KEY": os.getenv('JAVLIN_API_KEY', 'default-key-change-me')}
            response = requests.post(f"{self.memory_api}/memory", json=data, headers=headers)
            
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Failed to log to memory: {e}")
            return False

# Global instance
bible_evolution = BibleEvolutionEngine()
