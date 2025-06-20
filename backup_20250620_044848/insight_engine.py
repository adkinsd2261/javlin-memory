
#!/usr/bin/env python3
"""
Insight Evolution Engine
Analyzes memory patterns and generates insights for system improvement
"""

import json
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import re
from typing import Dict, List, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, 'memory.json')
INSIGHTS_FILE = os.path.join(BASE_DIR, 'insights.json')

class InsightEngine:
    def __init__(self):
        self.memory_data = []
        self.insights = {
            "analysis_timestamp": "",
            "repeated_patterns": [],
            "missed_tags": [],
            "redundant_logs": [],
            "trend_analysis": {},
            "optimization_suggestions": [],
            "learning_insights": [],
            "schema_health": {},
            "summary": {}
        }
    
    def load_memory_data(self):
        """Load memory data for analysis"""
        try:
            with open(MEMORY_FILE, 'r') as f:
                self.memory_data = json.load(f)
            print(f"📊 Loaded {len(self.memory_data)} memory entries for analysis")
            return True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Error loading memory data: {e}")
            return False
    
    def analyze_repeated_patterns(self):
        """Detect repeated patterns in memory logs"""
        patterns = []
        
        # Analyze repeated topics/themes
        topic_counts = Counter()
        type_counts = Counter()
        category_counts = Counter()
        tag_combinations = Counter()
        
        for entry in self.memory_data:
            topic = entry.get('topic', '').lower()
            entry_type = entry.get('type', '')
            category = entry.get('category', '')
            tags = tuple(sorted(entry.get('tags', [])))
            
            # Count occurrences
            topic_words = re.findall(r'\b\w+\b', topic)
            for word in topic_words:
                if len(word) > 3:  # Ignore short words
                    topic_counts[word] += 1
            
            type_counts[entry_type] += 1
            category_counts[category] += 1
            
            if tags:
                tag_combinations[tags] += 1
        
        # Find significant patterns
        # Repeated topic themes
        frequent_topics = [(word, count) for word, count in topic_counts.most_common(10) if count >= 3]
        if frequent_topics:
            patterns.append({
                "type": "repeated_topics",
                "description": f"Frequent topic themes detected",
                "details": frequent_topics,
                "suggestion": "Consider creating templates or workflows for common themes"
            })
        
        # Type frequency analysis
        frequent_types = [(t, count) for t, count in type_counts.most_common(5) if count >= 4]
        if frequent_types:
            patterns.append({
                "type": "frequent_log_types",
                "description": f"Most common log types",
                "details": frequent_types,
                "suggestion": "Optimize auto-logging rules for frequent types"
            })
        
        # Category concentration
        top_category = category_counts.most_common(1)[0] if category_counts else ('', 0)
        if top_category[1] > len(self.memory_data) * 0.6:
            patterns.append({
                "type": "category_concentration",
                "description": f"Over 60% of logs in '{top_category[0]}' category",
                "details": dict(category_counts.most_common(5)),
                "suggestion": "Consider subcategories or more specific categorization"
            })
        
        self.insights["repeated_patterns"] = patterns
        return patterns
    
    def detect_missed_tags(self):
        """Identify potential tags that should have been applied"""
        missed_tags = []
        
        # Common keywords that appear in content but not in tags
        all_content = []
        existing_tags = set()
        
        for entry in self.memory_data:
            content = f"{entry.get('input', '')} {entry.get('output', '')} {entry.get('topic', '')}"
            all_content.append(content.lower())
            existing_tags.update(entry.get('tags', []))
        
        # Extract potential keywords
        potential_keywords = set()
        for content in all_content:
            words = re.findall(r'\b[a-z]{4,}\b', content)  # Words 4+ chars
            potential_keywords.update(words)
        
        # Common technical/domain terms
        domain_terms = {
            'api', 'endpoint', 'database', 'auth', 'authentication', 'authorization',
            'deploy', 'deployment', 'test', 'testing', 'debug', 'debugging',
            'fix', 'bug', 'error', 'issue', 'feature', 'enhancement',
            'integration', 'config', 'configuration', 'setup', 'install',
            'performance', 'optimization', 'security', 'validation'
        }
        
        # Find domain terms that appear frequently but aren't used as tags
        content_text = ' '.join(all_content)
        for term in domain_terms:
            if term in content_text and term not in existing_tags:
                count = content_text.count(term)
                if count >= 3:  # Appears at least 3 times
                    missed_tags.append({
                        "tag": term,
                        "frequency": count,
                        "suggestion": f"Consider adding '{term}' as a tag for relevant entries"
                    })
        
        self.insights["missed_tags"] = missed_tags[:10]  # Top 10
        return missed_tags
    
    def find_redundant_logs(self):
        """Identify potentially redundant or low-value logs"""
        redundant_logs = []
        
        # Group similar entries
        similarity_groups = defaultdict(list)
        
        for i, entry in enumerate(self.memory_data):
            # Create a signature based on topic words and type
            topic_words = set(re.findall(r'\b\w{4,}\b', entry.get('topic', '').lower()))
            signature = (entry.get('type', ''), frozenset(topic_words))
            similarity_groups[signature].append((i, entry))
        
        # Find groups with multiple similar entries
        for signature, entries in similarity_groups.items():
            if len(entries) >= 3:  # 3 or more similar entries
                entry_details = []
                total_rating = 0
                rated_count = 0
                
                for idx, entry in entries:
                    details = {
                        "index": idx,
                        "topic": entry.get('topic', ''),
                        "timestamp": entry.get('timestamp', ''),
                        "rating": entry.get('user_rating', 0)
                    }
                    entry_details.append(details)
                    
                    if entry.get('user_rating', 0) > 0:
                        total_rating += entry.get('user_rating', 0)
                        rated_count += 1
                
                avg_rating = total_rating / rated_count if rated_count > 0 else 0
                
                redundant_logs.append({
                    "pattern": f"Type: {signature[0]}, Similar topics",
                    "count": len(entries),
                    "entries": entry_details,
                    "average_rating": avg_rating,
                    "suggestion": "Consider consolidating similar entries or adjusting auto-log filters"
                })
        
        # Find low-rated entries (if ratings exist)
        low_rated = []
        for entry in self.memory_data:
            rating = entry.get('user_rating', 0)
            if rating > 0 and rating <= 2:
                low_rated.append({
                    "topic": entry.get('topic', ''),
                    "rating": rating,
                    "type": entry.get('type', ''),
                    "timestamp": entry.get('timestamp', '')
                })
        
        if low_rated:
            redundant_logs.append({
                "pattern": "Low-rated entries",
                "count": len(low_rated),
                "entries": low_rated[:5],  # Show first 5
                "suggestion": "Review auto-logging criteria for these types of entries"
            })
        
        self.insights["redundant_logs"] = redundant_logs
        return redundant_logs
    
    def analyze_trends(self):
        """Analyze trends over time"""
        trends = {}
        
        if not self.memory_data:
            return trends
        
        # Group entries by time periods
        daily_counts = defaultdict(int)
        weekly_types = defaultdict(lambda: defaultdict(int))
        monthly_categories = defaultdict(lambda: defaultdict(int))
        
        for entry in self.memory_data:
            try:
                timestamp = entry.get('timestamp', '')
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                date_key = dt.strftime('%Y-%m-%d')
                week_key = dt.strftime('%Y-W%U')
                month_key = dt.strftime('%Y-%m')
                
                daily_counts[date_key] += 1
                weekly_types[week_key][entry.get('type', 'Unknown')] += 1
                monthly_categories[month_key][entry.get('category', 'unknown')] += 1
                
            except:
                continue
        
        # Analyze daily activity
        if daily_counts:
            daily_values = list(daily_counts.values())
            trends["daily_activity"] = {
                "average_per_day": sum(daily_values) / len(daily_values),
                "max_day": max(daily_values),
                "min_day": min(daily_values),
                "total_days": len(daily_counts)
            }
        
        # Analyze type evolution
        if weekly_types:
            recent_week = max(weekly_types.keys())
            recent_types = weekly_types[recent_week]
            
            trends["recent_focus"] = {
                "week": recent_week,
                "top_types": dict(Counter(recent_types).most_common(3)),
                "total_entries": sum(recent_types.values())
            }
        
        # Analyze category trends
        if monthly_categories:
            trends["category_evolution"] = dict(monthly_categories)
        
        self.insights["trend_analysis"] = trends
        return trends
    
    def generate_optimization_suggestions(self):
        """Generate suggestions for system optimization"""
        suggestions = []
        
        # Based on repeated patterns
        patterns = self.insights.get("repeated_patterns", [])
        for pattern in patterns:
            if pattern["type"] == "frequent_log_types":
                frequent_type = pattern["details"][0][0] if pattern["details"] else None
                if frequent_type:
                    suggestions.append({
                        "area": "auto_logging",
                        "priority": "medium",
                        "suggestion": f"Create specialized auto-logging rules for '{frequent_type}' type",
                        "reasoning": f"This type appears {pattern['details'][0][1]} times"
                    })
        
        # Based on missed tags
        missed_tags = self.insights.get("missed_tags", [])
        if len(missed_tags) >= 5:
            suggestions.append({
                "area": "tagging",
                "priority": "high",
                "suggestion": "Improve auto-tagging algorithm to include domain-specific terms",
                "reasoning": f"Found {len(missed_tags)} frequently used terms not being tagged"
            })
        
        # Based on redundant logs
        redundant_logs = self.insights.get("redundant_logs", [])
        for redundant in redundant_logs:
            if redundant["count"] >= 5:
                suggestions.append({
                    "area": "filtering",
                    "priority": "medium",
                    "suggestion": f"Adjust filters to reduce redundant '{redundant['pattern']}' entries",
                    "reasoning": f"Found {redundant['count']} similar entries"
                })
        
        # Based on trends
        trends = self.insights.get("trend_analysis", {})
        daily_activity = trends.get("daily_activity", {})
        if daily_activity.get("average_per_day", 0) > 10:
            suggestions.append({
                "area": "workflow",
                "priority": "low",
                "suggestion": "Consider implementing daily/weekly digest summaries",
                "reasoning": f"High activity ({daily_activity['average_per_day']:.1f} entries/day)"
            })
        
        self.insights["optimization_suggestions"] = suggestions
        return suggestions
    
    def generate_learning_insights(self):
        """Generate insights about learning and improvement patterns"""
        learning_insights = []
        
        # Analyze success patterns
        successful_entries = [e for e in self.memory_data if e.get('success', False)]
        failed_entries = [e for e in self.memory_data if not e.get('success', False)]
        
        if successful_entries and failed_entries:
            success_rate = len(successful_entries) / len(self.memory_data) * 100
            learning_insights.append({
                "type": "success_pattern",
                "insight": f"Overall success rate: {success_rate:.1f}%",
                "successful_count": len(successful_entries),
                "failed_count": len(failed_entries)
            })
        
        # Analyze rating patterns (if available)
        rated_entries = [e for e in self.memory_data if e.get('user_rating', 0) > 0]
        if rated_entries:
            avg_rating = sum(e.get('user_rating', 0) for e in rated_entries) / len(rated_entries)
            high_rated = [e for e in rated_entries if e.get('user_rating', 0) >= 4]
            
            learning_insights.append({
                "type": "rating_pattern",
                "insight": f"Average user rating: {avg_rating:.1f}/5",
                "total_rated": len(rated_entries),
                "high_rated_count": len(high_rated),
                "high_rated_types": list(Counter(e.get('type', '') for e in high_rated).most_common(3))
            })
        
        # Analyze improvement over time
        if len(self.memory_data) >= 10:
            recent_entries = self.memory_data[-10:]  # Last 10 entries
            recent_success_rate = sum(1 for e in recent_entries if e.get('success', False)) / len(recent_entries) * 100
            
            learning_insights.append({
                "type": "recent_performance",
                "insight": f"Recent success rate (last 10 entries): {recent_success_rate:.1f}%",
                "trend": "improving" if recent_success_rate > 70 else "needs_attention"
            })
        
        self.insights["learning_insights"] = learning_insights
        return learning_insights
    
    def analyze_schema_health(self):
        """Analyze schema field usage and health"""
        schema_health = {
            "field_usage": {},
            "empty_fields": {},
            "field_quality": {},
            "recommendations": []
        }
        
        if not self.memory_data:
            return schema_health
        
        # Define expected schema fields
        expected_fields = [
            'topic', 'type', 'input', 'output', 'score', 'maxScore', 
            'success', 'category', 'tags', 'context', 'related_to', 
            'reviewed', 'timestamp', 'user_rating', 'importance_score'
        ]
        
        total_entries = len(self.memory_data)
        field_stats = {}
        
        for field in expected_fields:
            present_count = 0
            non_empty_count = 0
            avg_length = 0
            total_length = 0
            
            for entry in self.memory_data:
                if field in entry:
                    present_count += 1
                    value = entry[field]
                    
                    # Check if non-empty/meaningful
                    if value is not None:
                        if isinstance(value, str) and value.strip():
                            non_empty_count += 1
                            total_length += len(value)
                        elif isinstance(value, (list, dict)) and value:
                            non_empty_count += 1
                            total_length += len(str(value))
                        elif isinstance(value, (int, float, bool)):
                            non_empty_count += 1
            
            if non_empty_count > 0:
                avg_length = total_length / non_empty_count
            
            field_stats[field] = {
                "presence_rate": present_count / total_entries * 100,
                "non_empty_rate": non_empty_count / total_entries * 100,
                "avg_content_length": avg_length,
                "present_count": present_count,
                "non_empty_count": non_empty_count
            }
        
        schema_health["field_usage"] = field_stats
        
        # Identify problematic fields
        rarely_used_fields = []
        often_empty_fields = []
        quality_issues = []
        
        for field, stats in field_stats.items():
            # Rarely used fields (present in <50% of entries)
            if stats["presence_rate"] < 50:
                rarely_used_fields.append({
                    "field": field,
                    "presence_rate": stats["presence_rate"],
                    "reason": "Field present in less than 50% of entries"
                })
            
            # Often empty fields (non-empty in <30% of entries)
            if stats["non_empty_rate"] < 30:
                often_empty_fields.append({
                    "field": field,
                    "non_empty_rate": stats["non_empty_rate"],
                    "reason": "Field empty or null in most entries"
                })
            
            # Quality issues (very short content for text fields)
            if field in ['input', 'output', 'topic', 'context'] and stats["avg_content_length"] < 10:
                quality_issues.append({
                    "field": field,
                    "avg_length": stats["avg_content_length"],
                    "reason": "Text content appears to be very short on average"
                })
        
        schema_health["empty_fields"] = often_empty_fields
        schema_health["field_quality"] = quality_issues
        
        # Generate recommendations
        recommendations = []
        
        if rarely_used_fields:
            recommendations.append({
                "priority": "medium",
                "area": "schema_optimization",
                "suggestion": f"Consider removing or making optional: {', '.join([f['field'] for f in rarely_used_fields[:3]])}",
                "reasoning": "These fields are rarely populated"
            })
        
        if often_empty_fields:
            recommendations.append({
                "priority": "high",
                "area": "data_quality",
                "suggestion": f"Improve auto-population for: {', '.join([f['field'] for f in often_empty_fields[:3]])}",
                "reasoning": "These fields are often empty but could provide value"
            })
        
        if quality_issues:
            recommendations.append({
                "priority": "medium",
                "area": "content_quality",
                "suggestion": f"Enhance content generation for: {', '.join([f['field'] for f in quality_issues[:3]])}",
                "reasoning": "These fields have very short content"
            })
        
        # Field utilization analysis
        well_used_fields = [f for f, stats in field_stats.items() if stats["non_empty_rate"] > 80]
        underused_fields = [f for f, stats in field_stats.items() if stats["non_empty_rate"] < 50]
        
        if well_used_fields:
            recommendations.append({
                "priority": "low",
                "area": "schema_success",
                "suggestion": f"Well-utilized fields: {', '.join(well_used_fields[:5])}",
                "reasoning": "These fields are consistently populated and valuable"
            })
        
        schema_health["recommendations"] = recommendations
        
        # Overall schema health score
        avg_usage = sum(stats["non_empty_rate"] for stats in field_stats.values()) / len(field_stats)
        schema_health["overall_health_score"] = int(avg_usage)
        schema_health["well_used_fields"] = well_used_fields
        schema_health["underused_fields"] = underused_fields
        
        self.insights["schema_health"] = schema_health
        return schema_health
    
    def generate_summary(self):
        """Generate overall analysis summary"""
        summary = {
            "total_entries": len(self.memory_data),
            "analysis_date": datetime.now().isoformat(),
            "key_findings": [],
            "action_items": [],
            "health_score": 0
        }
        
        # Key findings
        patterns = self.insights.get("repeated_patterns", [])
        if patterns:
            summary["key_findings"].append(f"Found {len(patterns)} repeated patterns")
        
        missed_tags = self.insights.get("missed_tags", [])
        if missed_tags:
            summary["key_findings"].append(f"Identified {len(missed_tags)} missed tagging opportunities")
        
        redundant_logs = self.insights.get("redundant_logs", [])
        if redundant_logs:
            summary["key_findings"].append(f"Found {len(redundant_logs)} potential redundancy issues")
        
        # Action items from suggestions
        suggestions = self.insights.get("optimization_suggestions", [])
        high_priority = [s for s in suggestions if s.get("priority") == "high"]
        summary["action_items"] = [s["suggestion"] for s in high_priority[:3]]
        
        # Calculate health score (0-100)
        health_score = 70  # Base score
        
        # Adjust based on findings
        if len(missed_tags) > 5:
            health_score -= 10
        if len(redundant_logs) > 3:
            health_score -= 10
        if len(patterns) < 2:
            health_score += 10  # Good variety
        
        # Adjust based on ratings if available
        rated_entries = [e for e in self.memory_data if e.get('user_rating', 0) > 0]
        if rated_entries:
            avg_rating = sum(e.get('user_rating', 0) for e in rated_entries) / len(rated_entries)
            health_score += int((avg_rating - 3) * 10)  # Bonus/penalty based on ratings
        
        summary["health_score"] = max(0, min(100, health_score))
        
        self.insights["summary"] = summary
        return summary
    
    def run_full_analysis(self):
        """Run complete insight analysis"""
        print("🧠 Starting memory insight analysis...")
        
        if not self.load_memory_data():
            return False
        
        # Run all analysis components
        print("🔍 Analyzing repeated patterns...")
        self.analyze_repeated_patterns()
        
        print("🏷️  Detecting missed tags...")
        self.detect_missed_tags()
        
        print("🗑️  Finding redundant logs...")
        self.find_redundant_logs()
        
        print("📈 Analyzing trends...")
        self.analyze_trends()
        
        print("💡 Generating optimization suggestions...")
        self.generate_optimization_suggestions()
        
        print("🎓 Extracting learning insights...")
        self.generate_learning_insights()
        
        print("🧬 Analyzing schema health...")
        self.analyze_schema_health()
        
        print("📊 Creating summary...")
        self.generate_summary()
        
        # Add timestamp
        self.insights["analysis_timestamp"] = datetime.now().isoformat()
        
        # Save insights
        self.save_insights()
        
        print("✅ Insight analysis complete!")
        return True
    
    def save_insights(self):
        """Save insights to file"""
        try:
            with open(INSIGHTS_FILE, 'w') as f:
                json.dump(self.insights, f, indent=2)
            print(f"💾 Insights saved to {INSIGHTS_FILE}")
        except Exception as e:
            print(f"❌ Error saving insights: {e}")
    
    def load_insights(self):
        """Load existing insights"""
        try:
            with open(INSIGHTS_FILE, 'r') as f:
                self.insights = json.load(f)
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False

def main():
    """Run insight analysis"""
    engine = InsightEngine()
    success = engine.run_full_analysis()
    
    if success:
        summary = engine.insights["summary"]
        print(f"\n📊 Analysis Summary:")
        print(f"   Total entries: {summary['total_entries']}")
        print(f"   Health score: {summary['health_score']}/100")
        print(f"   Key findings: {len(summary['key_findings'])}")
        print(f"   Action items: {len(summary['action_items'])}")
    
    return success

if __name__ == "__main__":
    main()
