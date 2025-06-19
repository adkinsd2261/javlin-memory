import os
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import json
import datetime
import logging
from json.decoder import JSONDecodeError
import re
from collections import Counter

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)

# Use absolute path for memory file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, 'memory.json')

@app.before_request
def require_api_key():
    # Require API key for POST /memory only
    if request.path == '/memory' and request.method == 'POST':
        # Try multiple header variations (case-insensitive)
        key = (request.headers.get('X-API-KEY') or 
               request.headers.get('x-api-key') or 
               request.headers.get('X-Api-Key'))
        
        # Debug: log all headers for troubleshooting
        logging.debug(f"All request headers: {dict(request.headers)}")
        
        if key != os.getenv('JAVLIN_API_KEY'):
            logging.warning(f"Unauthorized access attempt with key: {key}")
            abort(401, description="Unauthorized: Invalid or missing API key.")

@app.route('/memory', methods=['POST'])
def add_memory():
    try:
        # Debug logging for API key with multiple variations
        api_key = (request.headers.get('X-API-KEY') or 
                  request.headers.get('x-api-key') or 
                  request.headers.get('X-Api-Key'))
        logging.debug(f"Received API key: {api_key}")
        logging.debug(f"Request method: {request.method}")
        logging.debug(f"Request URL: {request.url}")
        
        # Check Content-Type
        if request.content_type != 'application/json':
            logging.warning(f"Invalid Content-Type: {request.content_type}")
            return jsonify({
                "error": "Content-Type must be application/json"
            }), 400

        data = request.get_json() or {}
        logging.info(f"Received memory entry: {data}")

        # Check if this should be auto-logged (minimal or no required fields)
        required_fields = ["topic", "type", "input", "output", "score", "maxScore", "success", "category", "reviewed"]
        missing = [field for field in required_fields if field not in data]
        
        # If most fields are missing, use auto-logging
        if len(missing) >= 7:  # If 7 or more fields missing, auto-generate
            logging.info("Using auto-logging due to minimal input")
            auto_entry = autolog_memory(
                input_text=data.get('input', ''),
                output_text=data.get('output', ''),
                topic=data.get('topic', ''),
                type_=data.get('type', 'AutoLog'),
                category=data.get('category', 'system')
            )
            
            if auto_entry is None:
                return jsonify({
                    "status": "⏭️ Skipped",
                    "reason": "Auto-log threshold not met"
                }), 200
            
            data = auto_entry
            logging.info(f"Auto-generated memory entry: {data}")
        
        # Validate required fields for manual entries
        elif missing:
            logging.warning(f"Missing fields: {missing}")
            return jsonify({
                "error": "Missing required fields for manual entry.",
                "missing": missing,
                "hint": "Provide minimal fields for auto-logging or all required fields for manual entry"
            }), 400

        # Validate data types for manual entries
        if "score" in data and "maxScore" in data:
            if not isinstance(data["score"], int) or not isinstance(data["maxScore"], int):
                logging.warning("Score or maxScore not integer")
                return jsonify({"error": "Score and maxScore must be integers."}), 400

        if "success" in data and "reviewed" in data:
            if not isinstance(data["success"], bool) or not isinstance(data["reviewed"], bool):
                logging.warning("Success or reviewed not boolean")
                return jsonify({"error": "Success and reviewed must be booleans."}), 400

        # Handle optional fields
        if "tags" in data:
            if not isinstance(data["tags"], list) or not all(isinstance(tag, str) for tag in data["tags"]):
                logging.warning("Tags must be a list of strings")
                return jsonify({"error": "Tags must be a list of strings."}), 400
        elif "tags" not in data:
            data["tags"] = []

        if "related_to" in data:
            if not isinstance(data["related_to"], list) or not all(isinstance(rel, str) for rel in data["related_to"]):
                logging.warning("Related_to must be a list of strings")
                return jsonify({"error": "Related_to must be a list of strings."}), 400
        elif "related_to" not in data:
            data["related_to"] = []

        if 'timestamp' not in data:
            data['timestamp'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            logging.info(f"Added timestamp: {data['timestamp']}")

        # Add context and auto-tagging for manual entries if not present
        if 'context' not in data and 'input' in data and 'output' in data:
            data['context'] = generate_context_summary(data['input'], data['output'], data.get('topic', ''))
        
        # Auto-enhance tags for manual entries
        if len(data.get('tags', [])) == 0 and 'input' in data and 'output' in data:
            all_text = f"{data['input']} {data['output']} {data.get('topic', '')}"
            data['tags'] = extract_keywords(all_text)

        logging.info(f"Writing to file: {MEMORY_FILE}")

        try:
            with open(MEMORY_FILE, 'r') as f:
                memory = json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            memory = []
            logging.info("Initialized empty memory list")

        memory.append(data)
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=2)

        status_msg = "✅ Auto-memory saved" if data.get('auto_generated') else "✅ Memory saved"
        logging.info(f"Memory entry saved. Total entries: {len(memory)}")
        return jsonify({"status": status_msg, "entry": data}), 200

    except Exception as e:
        logging.error(f"Exception in add_memory: {str(e)}", exc_info=True)
        return jsonify({"status": "❌ Failed", "error": str(e)}), 500

@app.route('/memory', methods=['GET'])
def get_memories():
    try:
        with open(MEMORY_FILE, 'r') as f:
            memory = json.load(f)
        
        # Optional filtering by query parameters
        category = request.args.get('category')
        topic = request.args.get('topic')
        success = request.args.get('success')
        tag = request.args.get('tag')
        related_to = request.args.get('related_to')
        
        if category:
            memory = [m for m in memory if m.get('category', '').lower() == category.lower()]
        if topic:
            memory = [m for m in memory if topic.lower() in m.get('topic', '').lower()]
        if success is not None:
            success_bool = success.lower() == 'true'
            memory = [m for m in memory if m.get('success') == success_bool]
        if tag:
            memory = [m for m in memory if tag.lower() in [t.lower() for t in m.get('tags', [])]]
        if related_to:
            memory = [m for m in memory if related_to in m.get('related_to', [])]
            
        return jsonify(memory)
    except Exception as e:
        logging.error(f"Error loading memories: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/stats')
def get_stats():
    try:
        with open(MEMORY_FILE, 'r') as f:
            memory = json.load(f)
        
        total = len(memory)
        successful = len([m for m in memory if m.get('success', False)])
        categories = {}
        types = {}
        tags = {}
        
        for m in memory:
            cat = m.get('category', 'unknown')
            typ = m.get('type', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
            types[typ] = types.get(typ, 0) + 1
            
            # Count tags
            for tag in m.get('tags', []):
                tags[tag] = tags.get(tag, 0) + 1
        
        return jsonify({
            'total_memories': total,
            'successful': successful,
            'success_rate': f"{(successful/total*100):.1f}%" if total > 0 else "0%",
            'categories': categories,
            'types': types,
            'tags': tags
        })
    except Exception as e:
        logging.error(f"Error generating stats: {e}")
        return jsonify({"error": str(e)}), 500

def extract_keywords(text):
    """Extract meaningful keywords from text for auto-tagging"""
    if not text:
        return []
    
    # Common meaningful keywords in development context
    keywords = {
        'bug', 'fix', 'error', 'issue', 'problem', 'resolved', 'solution',
        'milestone', 'feature', 'enhancement', 'improvement', 'optimization',
        'decision', 'choice', 'approach', 'strategy', 'refactor',
        'test', 'testing', 'debug', 'deployment', 'integration',
        'api', 'endpoint', 'database', 'auth', 'security',
        'performance', 'scale', 'config', 'setup', 'install'
    }
    
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    # Also extract technical terms (words with capitals, underscores, etc.)
    tech_terms = re.findall(r'\b[A-Z][a-zA-Z]*(?:[_][a-zA-Z]+)*\b', text)
    found_keywords.extend([term.lower() for term in tech_terms[:3]])  # Limit to 3
    
    return list(set(found_keywords))[:5]  # Return max 5 unique keywords

def calculate_importance_score(topic, input_text, output_text, category, type_):
    """Calculate importance score (0-100) for memory significance"""
    score = 0
    
    # Impact scoring (0-30)
    impact_keywords = ['fix', 'resolved', 'completed', 'deployed', 'milestone', 'breakthrough']
    if any(keyword in (input_text + output_text).lower() for keyword in impact_keywords):
        score += 25
    elif 'success' in (input_text + output_text).lower():
        score += 15
    elif 'test' in (input_text + output_text).lower():
        score += 10
    
    # Resolution scoring (0-20)
    resolution_keywords = ['solution', 'answer', 'resolved', 'fixed', 'working']
    if any(keyword in output_text.lower() for keyword in resolution_keywords):
        score += 20
    elif 'completed' in output_text.lower():
        score += 15
    
    # Novelty scoring (0-20)
    novelty_keywords = ['new', 'first', 'initial', 'created', 'implemented', 'added']
    if any(keyword in (input_text + output_text).lower() for keyword in novelty_keywords):
        score += 15
    
    # Emotion/significance indicators (0-20)
    emotion_keywords = ['important', 'critical', 'urgent', 'major', 'significant', 'breakthrough']
    if any(keyword in (input_text + output_text).lower() for keyword in emotion_keywords):
        score += 20
    elif any(keyword in topic.lower() for keyword in emotion_keywords):
        score += 15
    
    # Reflection/learning (0-10)
    reflection_keywords = ['learned', 'insight', 'understand', 'realize', 'discovered']
    if any(keyword in (input_text + output_text).lower() for keyword in reflection_keywords):
        score += 10
    
    # Always prioritize certain types
    priority_types = ['BugFix', 'Insight', 'BuildLog', 'Decision', 'Emotion']
    if type_ in priority_types:
        score += 20
    
    # Category bonuses
    if category in ['system', 'integration', 'Infrastructure']:
        score += 10
    
    return min(score, 100)

def generate_context_summary(input_text, output_text, topic):
    """Generate contextual summary of what happened"""
    context_parts = []
    
    # What was the user trying to do?
    if 'test' in input_text.lower():
        context_parts.append("Testing system functionality")
    elif 'fix' in input_text.lower() or 'error' in input_text.lower():
        context_parts.append("Debugging and resolving issues")
    elif 'deploy' in input_text.lower():
        context_parts.append("Deploying application changes")
    elif 'integrate' in input_text.lower():
        context_parts.append("Integrating system components")
    else:
        context_parts.append(f"Working on: {topic}")
    
    # What was the outcome?
    if 'success' in output_text.lower() or 'completed' in output_text.lower():
        context_parts.append("Successfully completed task")
    elif 'failed' in output_text.lower() or 'error' in output_text.lower():
        context_parts.append("Encountered issues requiring resolution")
    elif 'progress' in output_text.lower():
        context_parts.append("Made progress toward goal")
    
    return ". ".join(context_parts) + "."

def find_related_memories(topic, tags, category):
    """Find related memories based on topic, tags, and category"""
    try:
        with open(MEMORY_FILE, 'r') as f:
            memory = json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        return []
    
    related = []
    topic_lower = topic.lower()
    
    for m in memory[-10:]:  # Check last 10 entries for efficiency
        # Topic similarity
        if any(word in m.get('topic', '').lower() for word in topic_lower.split()):
            related.append(m.get('topic', ''))
        
        # Tag overlap
        m_tags = m.get('tags', [])
        if any(tag in m_tags for tag in tags):
            related.append(m.get('topic', ''))
        
        # Category match
        if m.get('category') == category:
            related.append(m.get('topic', ''))
    
    return list(set(related))[:3]  # Return max 3 unique related topics

def autolog_memory(input_text="", output_text="", topic="", type_="AutoLog", category="system"):
    """Intelligently generate memory log entry"""
    
    # Generate topic if not provided
    if not topic:
        if input_text:
            # Extract first meaningful phrase as topic
            words = input_text.split()[:8]
            topic = " ".join(words) if len(" ".join(words)) < 50 else " ".join(words[:5]) + "..."
        else:
            topic = "System Auto-Log Entry"
    
    # Auto-generate tags
    all_text = f"{input_text} {output_text} {topic}"
    tags = extract_keywords(all_text)
    
    # Generate context summary
    context = generate_context_summary(input_text, output_text, topic)
    
    # Find related memories
    related_to = find_related_memories(topic, tags, category)
    
    # Calculate importance score
    importance = calculate_importance_score(topic, input_text, output_text, category, type_)
    
    # Determine if we should log this (threshold of 60)
    should_log = importance >= 60 or type_ in ['BugFix', 'Insight', 'BuildLog', 'Decision', 'Emotion']
    
    if not should_log:
        logging.info(f"Skipping auto-log: low importance score ({importance})")
        return None
    
    # Create memory entry
    memory_entry = {
        "topic": topic,
        "type": type_,
        "input": input_text or "Auto-generated entry",
        "output": output_text or "System logged automatically",
        "score": min(importance, 25),  # Cap at maxScore
        "maxScore": 25,
        "success": True,  # Assume success for auto-logs unless indicated otherwise
        "category": category,
        "tags": tags,
        "context": context,
        "related_to": related_to,
        "reviewed": False,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "auto_generated": True,
        "importance_score": importance
    }
    
    return memory_entry

def find_unreviewed_logs():
    """Helper function to find unreviewed or unresolved logs"""
    try:
        with open(MEMORY_FILE, 'r') as f:
            memory = json.load(f)
        
        unreviewed = [m for m in memory if not m.get('reviewed', True)]
        unsuccessful = [m for m in memory if not m.get('success', False)]
        
        return {
            'unreviewed': unreviewed,
            'unsuccessful': unsuccessful,
            'total_unreviewed': len(unreviewed),
            'total_unsuccessful': len(unsuccessful)
        }
    except Exception as e:
        logging.error(f"Error finding unreviewed logs: {e}")
        return None

def group_related_logs(memory):
    """Group logs that reference each other via related_to"""
    groups = {}
    standalone = []
    
    for m in memory:
        related = m.get('related_to', [])
        topic = m.get('topic', '')
        
        if related:
            # Find or create group
            group_key = None
            for key in groups:
                if any(rel in groups[key]['topics'] for rel in related) or topic in groups[key]['topics']:
                    group_key = key
                    break
            
            if not group_key:
                group_key = f"group_{len(groups) + 1}"
                groups[group_key] = {'logs': [], 'topics': set()}
            
            groups[group_key]['logs'].append(m)
            groups[group_key]['topics'].add(topic)
            groups[group_key]['topics'].update(related)
        else:
            standalone.append(m)
    
    # Convert sets to lists for JSON serialization
    for group in groups.values():
        group['topics'] = list(group['topics'])
    
    return groups, standalone

@app.route('/digest')
def get_digest():
    try:
        with open(MEMORY_FILE, 'r') as f:
            memory = json.load(f)
        
        # Filter for last 7 days
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)
        
        recent_memory = []
        for m in memory:
            try:
                log_time = datetime.fromisoformat(m.get('timestamp', '').replace('Z', '+00:00'))
                if log_time.replace(tzinfo=None) >= week_ago:
                    recent_memory.append(m)
            except:
                # Include logs without valid timestamps
                recent_memory.append(m)
        
        # Analyze weekly data
        total = len(recent_memory)
        successful = len([m for m in recent_memory if m.get('success', False)])
        
        # Category analysis
        categories = {}
        types = {}
        tags = {}
        topics = {}
        auto_generated_count = 0
        importance_scores = []
        
        for m in recent_memory:
            cat = m.get('category', 'unknown')
            typ = m.get('type', 'unknown')
            topic = m.get('topic', 'unknown')
            
            categories[cat] = categories.get(cat, 0) + 1
            types[typ] = types.get(typ, 0) + 1
            topics[topic] = topics.get(topic, 0) + 1
            
            # Track auto-generated logs
            if m.get('auto_generated'):
                auto_generated_count += 1
            
            # Track importance scores
            if 'importance_score' in m:
                importance_scores.append(m['importance_score'])
            
            for tag in m.get('tags', []):
                tags[tag] = tags.get(tag, 0) + 1
        
        # Find most common items
        most_common_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]
        most_common_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Group related logs
        related_groups, standalone = group_related_logs(recent_memory)
        
        # Unreviewed analysis
        unreviewed_data = find_unreviewed_logs()
        
        # Calculate auto-log analytics
        avg_importance = sum(importance_scores) / len(importance_scores) if importance_scores else 0
        
        digest = {
            'period': 'Last 7 days',
            'summary': {
                'total_logs': total,
                'successful_logs': successful,
                'success_rate': f"{(successful/total*100):.1f}%" if total > 0 else "0%",
                'categories': categories,
                'types': types,
                'tags': tags,
                'auto_generated_logs': auto_generated_count,
                'manual_logs': total - auto_generated_count
            },
            'insights': {
                'most_common_topics': most_common_topics,
                'most_common_tags': most_common_tags,
                'related_groups': related_groups,
                'standalone_logs': len(standalone),
                'auto_logging_stats': {
                    'percentage_auto': f"{(auto_generated_count/total*100):.1f}%" if total > 0 else "0%",
                    'avg_importance_score': f"{avg_importance:.1f}",
                    'high_importance_logs': len([s for s in importance_scores if s >= 80])
                }
            },
            'follow_up': unreviewed_data
        }
        
        # Debug output - print to console
        print("Digest data:", digest)
        
        # Debug output - write to file for easy access
        output_file = os.path.join(BASE_DIR, "digest_output.json")
        with open(output_file, "w") as f:
            json.dump(digest, f, indent=2)
        print(f"Digest saved to: {output_file}")
        
        return jsonify(digest)
        
    except Exception as e:
        logging.error(f"Error generating digest: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/unreviewed')
def get_unreviewed():
    """Endpoint to get unreviewed or unresolved logs for follow-up"""
    unreviewed_data = find_unreviewed_logs()
    if unreviewed_data:
        return jsonify(unreviewed_data)
    else:
        return jsonify({"error": "Could not retrieve unreviewed logs"}), 500

@app.route('/autolog', methods=['POST'])
def passive_autolog():
    """Endpoint for passive auto-logging - no authentication required for system use"""
    try:
        data = request.get_json() or {}
        
        # Extract context from request
        input_text = data.get('input', data.get('context', ''))
        output_text = data.get('output', data.get('result', ''))
        topic = data.get('topic', '')
        type_ = data.get('type', 'PassiveLog')
        category = data.get('category', 'system')
        
        # Generate auto-log entry
        auto_entry = autolog_memory(input_text, output_text, topic, type_, category)
        
        if auto_entry is None:
            return jsonify({
                "status": "⏭️ Skipped",
                "reason": "Auto-log threshold not met",
                "threshold": 60
            }), 200
        
        # Save to memory
        try:
            with open(MEMORY_FILE, 'r') as f:
                memory = json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            memory = []
        
        memory.append(auto_entry)
        
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=2)
        
        logging.info(f"Passive auto-log saved: {auto_entry['topic']}")
        return jsonify({
            "status": "🤖 Auto-logged",
            "entry": auto_entry,
            "importance_score": auto_entry['importance_score']
        }), 200
        
    except Exception as e:
        logging.error(f"Error in passive autolog: {e}")
        return jsonify({"status": "❌ Failed", "error": str(e)}), 500

@app.route('/')
def home():
    return 'Javlin Memory API is live!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)







