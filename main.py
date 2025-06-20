import os
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import json
import datetime
import logging
from json.decoder import JSONDecodeError
import re
from collections import Counter

# Use absolute path for memory file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load configuration
def load_config():
    """Load system configuration"""
    config_file = os.path.join(BASE_DIR, 'config.json')
    default_config = {
        "agent_auto_log": True,
        "auto_log_threshold": 60,
        "trusted_agents": ["Javlin Builder Agent", "Assistant"],
        "audit_logging": True,
        "autolog_trace_file": "autolog_trace.json"
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
        # Create default config if not found
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config

SYSTEM_CONFIG = load_config()

app = Flask(__name__)
CORS(app)

# Register blueprints
from routes.task_output import task_output_bp
app.register_blueprint(task_output_bp)

logging.basicConfig(level=logging.DEBUG)

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

def detect_commit_type(commit_message):
    """Detect commit type from conventional commit message"""
    message_lower = commit_message.lower()
    
    if message_lower.startswith('feat'):
        return 'Feature'
    elif message_lower.startswith('fix'):
        return 'BugFix'
    elif message_lower.startswith('docs'):
        return 'Documentation'
    elif message_lower.startswith('refactor'):
        return 'Refactor'
    elif message_lower.startswith('test'):
        return 'SystemTest'
    elif message_lower.startswith('chore'):
        return 'Maintenance'
    elif any(word in message_lower for word in ['add', 'implement', 'create']):
        return 'Feature'
    elif any(word in message_lower for word in ['fix', 'resolve', 'correct']):
        return 'BugFix'
    elif any(word in message_lower for word in ['update', 'improve', 'enhance']):
        return 'Enhancement'
    else:
        return 'General'

def log_autolog_trace(data, user_agent, is_trusted_agent):
    """Log autolog request to audit trace"""
    try:
        trace_file = os.path.join(BASE_DIR, SYSTEM_CONFIG.get('autolog_trace_file', 'autolog_trace.json'))
        
        trace_entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "user_agent": user_agent,
            "is_trusted_agent": is_trusted_agent,
            "payload": data,
            "ip_address": request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        }
        
        try:
            with open(trace_file, 'r') as f:
                trace_log = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            trace_log = []
        
        trace_log.append(trace_entry)
        
        # Keep only last 1000 entries to prevent file bloat
        if len(trace_log) > 1000:
            trace_log = trace_log[-1000:]
        
        with open(trace_file, 'w') as f:
            json.dump(trace_log, f, indent=2)
            
    except Exception as e:
        logging.warning(f"Failed to log autolog trace: {e}")

def autolog_memory_trusted(input_text="", output_text="", topic="", type_="AutoLog", category="system"):
    """Trusted agent autolog with more permissive acceptance criteria"""
    
    # Try to get ML predictions first
    ml_predictions = get_ml_predictions(input_text, output_text, topic)
    
    # Use ML predictions if available, otherwise fall back to heuristics
    if ml_predictions and ml_predictions.get('confidence', {}).get('type', 0) > 0.5:  # Lower confidence threshold
        predicted_type = ml_predictions['type']
        predicted_category = ml_predictions['category']
        predicted_tags = ml_predictions['tags']
        predicted_score = ml_predictions['score']
        logging.info(f"Using ML predictions (trusted): type={predicted_type}, confidence={ml_predictions['confidence']['type']:.2f}")
    else:
        predicted_type = type_
        predicted_category = category
        predicted_tags = extract_keywords(f"{input_text} {output_text} {topic}")
        predicted_score = 20  # Higher base score for trusted agents
        logging.info("Using heuristic predictions for trusted agent")
    
    # Override with user-provided values if specified
    final_type = type_ if type_ != "AutoLog" else predicted_type
    final_category = category if category != "system" else predicted_category
    
    # Trusted agent types that are always accepted
    trusted_types = ['BuildLog', 'BugFix', 'Insight', 'Reflection', 'Decision', 'Feature', 'Enhancement', 'SystemTest']
    
    # Generate topic if not provided
    if not topic:
        if input_text:
            words = input_text.split()[:8]
            topic = " ".join(words) if len(" ".join(words)) < 50 else " ".join(words[:5]) + "..."
        else:
            topic = "Trusted Agent Auto-Log Entry"
    
    # Combine ML tags with heuristic tags
    all_text = f"{input_text} {output_text} {topic}"
    heuristic_tags = extract_keywords(all_text)
    combined_tags = list(set(predicted_tags + heuristic_tags))[:5]
    
    # Generate context summary
    context = generate_context_summary(input_text, output_text, topic)
    
    # Find related memories
    related_to = find_related_memories(topic, combined_tags, final_category)
    
    # Calculate importance score with trusted agent bonus
    heuristic_importance = calculate_importance_score(topic, input_text, output_text, final_category, final_type)
    ml_importance = predicted_score * 4
    
    # Weight the scores with trusted agent bonus (60% heuristic, 40% ML, +20 trusted bonus)
    importance = int(0.6 * heuristic_importance + 0.4 * ml_importance + 20)
    
    # More permissive threshold for trusted agents (40 instead of 60)
    threshold = SYSTEM_CONFIG.get('auto_log_threshold', 60) - 20
    should_log = importance >= threshold or final_type in trusted_types
    
    if not should_log:
        logging.info(f"Skipping trusted autolog: low importance score ({importance}, threshold: {threshold})")
        return None
    
    # Create memory entry with trusted agent marker
    memory_entry = {
        "topic": topic,
        "type": final_type,
        "input": input_text or "Trusted agent auto-generated entry",
        "output": output_text or "System logged automatically by trusted agent",
        "score": min(predicted_score, 25),
        "maxScore": 25,
        "success": True,
        "category": final_category,
        "tags": combined_tags,
        "context": context,
        "related_to": related_to,
        "reviewed": False,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "auto_generated": True,
        "trusted_agent": True,
        "importance_score": importance,
        "ml_predicted": ml_predictions is not None,
        "ml_confidence": ml_predictions.get('confidence', {}) if ml_predictions else {}
    }
    
    return memory_entry

def autolog_memory(input_text="", output_text="", topic="", type_="AutoLog", category="system"):
    """Intelligently generate memory log entry with ML predictions"""
    
    # Try to get ML predictions first
    ml_predictions = get_ml_predictions(input_text, output_text, topic)
    
    # Use ML predictions if available, otherwise fall back to heuristics
    if ml_predictions and ml_predictions.get('confidence', {}).get('type', 0) > 0.6:
        predicted_type = ml_predictions['type']
        predicted_category = ml_predictions['category']
        predicted_tags = ml_predictions['tags']
        predicted_score = ml_predictions['score']
        logging.info(f"Using ML predictions: type={predicted_type}, confidence={ml_predictions['confidence']['type']:.2f}")
    else:
        predicted_type = type_
        predicted_category = category
        predicted_tags = extract_keywords(f"{input_text} {output_text} {topic}")
        predicted_score = 15
        logging.info("Using heuristic predictions (ML confidence too low or unavailable)")
    
    # Override with user-provided values if specified
    final_type = type_ if type_ != "AutoLog" else predicted_type
    final_category = category if category != "system" else predicted_category
    
    # Generate topic if not provided
    if not topic:
        if input_text:
            # Extract first meaningful phrase as topic
            words = input_text.split()[:8]
            topic = " ".join(words) if len(" ".join(words)) < 50 else " ".join(words[:5]) + "..."
        else:
            topic = "System Auto-Log Entry"
    
    # Combine ML tags with heuristic tags
    all_text = f"{input_text} {output_text} {topic}"
    heuristic_tags = extract_keywords(all_text)
    combined_tags = list(set(predicted_tags + heuristic_tags))[:5]  # Max 5 unique tags
    
    # Generate context summary
    context = generate_context_summary(input_text, output_text, topic)
    
    # Find related memories
    related_to = find_related_memories(topic, combined_tags, final_category)
    
    # Calculate importance score (combine ML and heuristic)
    heuristic_importance = calculate_importance_score(topic, input_text, output_text, final_category, final_type)
    ml_importance = predicted_score * 4  # Convert 25-scale to 100-scale
    
    # Weight the importance scores (70% heuristic, 30% ML)
    importance = int(0.7 * heuristic_importance + 0.3 * ml_importance)
    
    # Determine if we should log this (threshold of 60)
    should_log = importance >= 60 or final_type in ['BugFix', 'Insight', 'BuildLog', 'Decision', 'Emotion']
    
    if not should_log:
        logging.info(f"Skipping auto-log: low importance score ({importance})")
        return None
    
    # Create memory entry
    memory_entry = {
        "topic": topic,
        "type": final_type,
        "input": input_text or "Auto-generated entry",
        "output": output_text or "System logged automatically",
        "score": min(predicted_score, 25),  # Use ML predicted score, cap at maxScore
        "maxScore": 25,
        "success": True,  # Assume success for auto-logs unless indicated otherwise
        "category": final_category,
        "tags": combined_tags,
        "context": context,
        "related_to": related_to,
        "reviewed": False,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "auto_generated": True,
        "importance_score": importance,
        "ml_predicted": ml_predictions is not None,
        "ml_confidence": ml_predictions.get('confidence', {}) if ml_predictions else {}
    }
    
    return memory_entry

def get_ml_predictions(input_text, output_text="", topic=""):
    """Get ML predictions for memory entry"""
    try:
        # Import here to avoid circular imports
        import sys
        sys.path.append(BASE_DIR)
        from tag_trainer import MemoryPredictor
        
        predictor = MemoryPredictor()
        if predictor.load_models():
            return predictor.predict(input_text, output_text, topic)
        else:
            # Try training if no models exist
            if predictor.train_models():
                return predictor.predict(input_text, output_text, topic)
    except Exception as e:
        logging.warning(f"ML prediction failed: {e}")
    
    return None

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

def get_top_unreviewed_for_feedback(memory, limit=10):
    """Get top unreviewed memories prioritized by importance and recency"""
    unreviewed = [m for m in memory if not m.get('reviewed', False)]
    
    # Sort by importance score (if available) and timestamp (recent first)
    def sort_key(m):
        importance = m.get('importance_score', m.get('score', 0))
        try:
            timestamp = datetime.fromisoformat(m.get('timestamp', '').replace('Z', '+00:00'))
            recency_bonus = (datetime.now(datetime.timezone.utc) - timestamp).days * -1  # Negative for recent first
        except:
            recency_bonus = -1000  # Very old or invalid timestamp
        
        return (importance, recency_bonus)
    
    sorted_unreviewed = sorted(unreviewed, key=sort_key, reverse=True)
    
    # Return limited list with feedback prompts
    feedback_candidates = []
    for m in sorted_unreviewed[:limit]:
        candidate = {
            'memory_id': m.get('timestamp', ''),  # Use timestamp as ID
            'topic': m.get('topic', ''),
            'type': m.get('type', ''),
            'category': m.get('category', ''),
            'importance_score': m.get('importance_score', m.get('score', 0)),
            'success': m.get('success', False),
            'timestamp': m.get('timestamp', ''),
            'feedback_prompt': generate_feedback_prompt(m)
        }
        feedback_candidates.append(candidate)
    
    return feedback_candidates

def generate_feedback_prompt(memory_entry):
    """Generate intelligent feedback prompt based on memory content"""
    topic = memory_entry.get('topic', '')
    memory_type = memory_entry.get('type', '')
    success = memory_entry.get('success', False)
    
    if memory_type in ['BugFix', 'SystemTest']:
        return f"How valuable was resolving '{topic}'? Did it prevent future issues?"
    elif memory_type in ['Decision', 'Insight']:
        return f"How impactful was this decision about '{topic}'? Would you make it again?"
    elif memory_type in ['BuildLog', 'Feature']:
        return f"How well did '{topic}' advance your goals? Any lessons learned?"
    elif not success:
        return f"What did you learn from this unsuccessful attempt at '{topic}'?"
    else:
        return f"How useful was logging '{topic}'? Should similar events be auto-logged?"

def get_feedback_trends():
    """Analyze feedback trends from feedback.json"""
    try:
        feedback_file = os.path.join(BASE_DIR, 'feedback.json')
        with open(feedback_file, 'r') as f:
            feedback_data = json.load(f)
        
        summary = feedback_data.get('ratings_summary', {})
        recent_feedback = feedback_data.get('feedback_entries', [])[-5:]  # Last 5 feedback entries
        
        trends = {
            'average_rating': summary.get('average_rating', 0),
            'total_ratings': summary.get('total_ratings', 0),
            'rating_distribution': summary.get('rating_distribution', {}),
            'recent_feedback': recent_feedback,
            'learning_insights': extract_learning_insights(recent_feedback)
        }
        
        return trends
        
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'average_rating': 0,
            'total_ratings': 0,
            'rating_distribution': {},
            'recent_feedback': [],
            'learning_insights': []
        }

def extract_learning_insights(feedback_entries):
    """Extract learning insights from feedback comments"""
    insights = []
    
    for feedback in feedback_entries:
        comment = feedback.get('comment', '').lower()
        rating = feedback.get('rating', 0)
        
        if rating >= 4 and any(word in comment for word in ['learn', 'insight', 'helpful', 'valuable']):
            insights.append(f"High-value learning: {feedback.get('comment', '')[:100]}")
        elif rating <= 2 and any(word in comment for word in ['noise', 'irrelevant', 'useless']):
            insights.append(f"Low-value pattern: {feedback.get('comment', '')[:100]}")
    
    return insights[:3]  # Return top 3 insights

def get_system_insights():
    """Load system insights from insight engine"""
    try:
        insights_file = os.path.join(BASE_DIR, 'insights.json')
        with open(insights_file, 'r') as f:
            insights = json.load(f)
        
        # Check if insights are recent (within last 7 days)
        analysis_time = insights.get('analysis_timestamp', '')
        try:
            analysis_dt = datetime.fromisoformat(analysis_time.replace('Z', '+00:00'))
            days_old = (datetime.now(datetime.timezone.utc) - analysis_dt).days
            
            if days_old > 7:
                # Run new analysis if insights are old
                logging.info("Insights are outdated, running new analysis")
                run_insight_analysis()
                with open(insights_file, 'r') as f:
                    insights = json.load(f)
        except:
            # Run analysis if timestamp is invalid
            run_insight_analysis()
            with open(insights_file, 'r') as f:
                insights = json.load(f)
        
        return insights
        
    except (FileNotFoundError, json.JSONDecodeError):
        # Generate insights if file doesn't exist
        logging.info("No insights file found, generating new analysis")
        run_insight_analysis()
        try:
            with open(insights_file, 'r') as f:
                return json.load(f)
        except:
            return {}

def run_insight_analysis():
    """Run insight analysis in background"""
    try:
        import sys
        sys.path.append(BASE_DIR)
        from insight_engine import InsightEngine
        
        engine = InsightEngine()
        engine.run_full_analysis()
        logging.info("Insight analysis completed")
        
    except Exception as e:
        logging.error(f"Error running insight analysis: {e}")

def get_infrastructure_health():
    """Get infrastructure health summary"""
    try:
        # Look for recent audit reports
        audit_files = [f for f in os.listdir(BASE_DIR) if f.startswith('infrastructure_audit_') and f.endswith('.json')]
        
        if not audit_files:
            return {
                'health_score': 100,
                'unregistered_components': 0,
                'architecture_mismatches': 0,
                'priority_improvements': [],
                'last_audit': 'Never'
            }
        
        # Load most recent audit
        latest_audit = sorted(audit_files)[-1]
        with open(os.path.join(BASE_DIR, latest_audit), 'r') as f:
            audit_data = json.load(f)
        
        summary = audit_data.get('summary', {})
        findings = audit_data.get('findings', {})
        
        # Extract high-priority improvements
        improvements = findings.get('structural_improvements', [])
        priority_improvements = [imp.get('description', '') for imp in improvements 
                               if imp.get('priority') == 'high'][:3]
        
        return {
            'health_score': summary.get('health_score', 100),
            'unregistered_components': summary.get('unregistered_components', 0),
            'architecture_mismatches': summary.get('architecture_mismatches', 0),
            'priority_improvements': priority_improvements,
            'last_audit': audit_data.get('audit_timestamp', 'Unknown')
        }
        
    except Exception as e:
        logging.warning(f"Error getting infrastructure health: {e}")
        return {
            'health_score': 100,
            'unregistered_components': 0,
            'architecture_mismatches': 0,
            'priority_improvements': [],
            'last_audit': 'Error'
        }

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
        
        # Get top 10 unreviewed memories for feedback
        unreviewed_for_feedback = get_top_unreviewed_for_feedback(memory, 10)
        
        # Load feedback ratings for trend analysis
        feedback_trends = get_feedback_trends()
        
        # Load system insights if available
        system_insights = get_system_insights()
        
        # Load infrastructure audit findings if available
        infrastructure_health = get_infrastructure_health()
        
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
            'feedback_prompts': {
                'unreviewed_for_feedback': unreviewed_for_feedback,
                'feedback_trends': feedback_trends,
                'pending_reviews': len(unreviewed_for_feedback)
            },
            'system_insights': system_insights,
            'learning_evolution': {
                'optimization_suggestions': system_insights.get('optimization_suggestions', [])[:3],
                'schema_health_score': system_insights.get('schema_health', {}).get('overall_health_score', 0),
                'key_patterns': len(system_insights.get('repeated_patterns', [])),
                'improvement_areas': len(system_insights.get('missed_tags', []))
            },
            'infrastructure_health': {
                'overall_health_score': infrastructure_health.get('health_score', 100),
                'unregistered_components': infrastructure_health.get('unregistered_components', 0),
                'architecture_mismatches': infrastructure_health.get('architecture_mismatches', 0),
                'priority_improvements': infrastructure_health.get('priority_improvements', []),
                'last_audit': infrastructure_health.get('last_audit', 'Never')
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
    """Endpoint for passive auto-logging with trusted agent support"""
    try:
        data = request.get_json() or {}
        
        # Check if this is from a trusted agent
        user_agent = request.headers.get('User-Agent', '')
        is_trusted_agent = any(agent in user_agent for agent in SYSTEM_CONFIG['trusted_agents'])
        agent_auto_log = SYSTEM_CONFIG.get('agent_auto_log', True)
        
        # Extract context from request
        input_text = data.get('input', data.get('context', ''))
        output_text = data.get('output', data.get('result', ''))
        topic = data.get('topic', '')
        type_ = data.get('type', 'PassiveLog')
        category = data.get('category', 'system')
        
        # Log to audit trace if enabled
        if SYSTEM_CONFIG.get('audit_logging', True):
            log_autolog_trace(data, user_agent, is_trusted_agent)
        
        # For trusted agents with agent_auto_log enabled, use more permissive logic
        if is_trusted_agent and agent_auto_log:
            # Trusted agent path - lower threshold and accept more types
            auto_entry = autolog_memory_trusted(input_text, output_text, topic, type_, category)
            
            if auto_entry is None:
                return jsonify({
                    "status": "⏭️ Skipped",
                    "reason": "Auto-log threshold not met (trusted agent)",
                    "threshold": SYSTEM_CONFIG.get('auto_log_threshold', 60)
                }), 200
        else:
            # Standard autolog path
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
        
        status_msg = "🤖 Auto-logged (trusted)" if is_trusted_agent else "🤖 Auto-logged"
        logging.info(f"Autolog saved: {auto_entry['topic']} (trusted: {is_trusted_agent})")
        
        return jsonify({
            "status": status_msg,
            "entry": auto_entry,
            "importance_score": auto_entry['importance_score'],
            "trusted_agent": is_trusted_agent
        }), 200
        
    except Exception as e:
        logging.error(f"Error in passive autolog: {e}")
        return jsonify({"status": "❌ Failed", "error": str(e)}), 500

@app.route('/build-state', methods=['GET', 'POST'])
def build_state():
    """Get or update build state for AI context awareness"""
    build_state_file = os.path.join(BASE_DIR, 'build_state.json')
    
    if request.method == 'GET':
        try:
            with open(build_state_file, 'r') as f:
                state = json.load(f)
            return jsonify(state)
        except (FileNotFoundError, JSONDecodeError):
            return jsonify({"error": "Build state not found"}), 404
    
    elif request.method == 'POST':
        try:
            data = request.get_json() or {}
            
            # Load current state
            try:
                with open(build_state_file, 'r') as f:
                    current_state = json.load(f)
            except (FileNotFoundError, JSONDecodeError):
                current_state = {}
            
            # Update with new data
            current_state.update(data)
            current_state['last_updated'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            # Save updated state
            with open(build_state_file, 'w') as f:
                json.dump(current_state, f, indent=2)
            
            return jsonify({"status": "✅ Build state updated", "state": current_state})
            
        except Exception as e:
            logging.error(f"Error updating build state: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/daily-focus', methods=['GET', 'POST'])
def daily_focus():
    """Get or update daily focus/intent for AI guidance"""
    daily_focus_file = os.path.join(BASE_DIR, 'daily_focus.json')
    
    if request.method == 'GET':
        try:
            with open(daily_focus_file, 'r') as f:
                focus = json.load(f)
            return jsonify(focus)
        except (FileNotFoundError, JSONDecodeError):
            return jsonify({"error": "Daily focus not found"}), 404
    
    elif request.method == 'POST':
        try:
            data = request.get_json() or {}
            
            # Auto-set today's date if not provided
            if 'date' not in data:
                data['date'] = datetime.datetime.now().strftime('%Y-%m-%d')
            
            with open(daily_focus_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return jsonify({"status": "✅ Daily focus updated", "focus": data})
            
        except Exception as e:
            logging.error(f"Error updating daily focus: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/feedback', methods=['POST'])
def add_feedback():
    """Add feedback for memory entries and mark as reviewed"""
    try:
        data = request.get_json() or {}
        required_fields = ['memory_id', 'rating']
        
        missing = [field for field in required_fields if field not in data]
        if missing:
            return jsonify({"error": f"Missing required fields: {missing}"}), 400
        
        if not isinstance(data['rating'], int) or data['rating'] < 1 or data['rating'] > 5:
            return jsonify({"error": "Rating must be integer between 1-5"}), 400
        
        feedback_file = os.path.join(BASE_DIR, 'feedback.json')
        
        # Load existing feedback
        try:
            with open(feedback_file, 'r') as f:
                feedback_data = json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            feedback_data = {
                "feedback_entries": [],
                "ratings_summary": {
                    "total_ratings": 0,
                    "average_rating": 0,
                    "rating_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
                },
                "common_feedback_themes": [],
                "last_updated": ""
            }
        
        # Add new feedback
        feedback_entry = {
            "memory_id": data['memory_id'],
            "rating": data['rating'],
            "comment": data.get('comment', ''),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        feedback_data['feedback_entries'].append(feedback_entry)
        
        # Update summary
        ratings = [f['rating'] for f in feedback_data['feedback_entries']]
        feedback_data['ratings_summary']['total_ratings'] = len(ratings)
        feedback_data['ratings_summary']['average_rating'] = sum(ratings) / len(ratings)
        
        # Reset distribution count
        feedback_data['ratings_summary']['rating_distribution'] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        
        # Update distribution
        for entry in feedback_data['feedback_entries']:
            rating_str = str(entry['rating'])
            feedback_data['ratings_summary']['rating_distribution'][rating_str] += 1
        
        feedback_data['last_updated'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # Save feedback
        with open(feedback_file, 'w') as f:
            json.dump(feedback_data, f, indent=2)
        
        # Mark corresponding memory as reviewed
        mark_memory_as_reviewed(data['memory_id'], data['rating'])
        
        return jsonify({
            "status": "✅ Feedback saved and memory marked as reviewed", 
            "feedback": feedback_entry
        })
        
    except Exception as e:
        logging.error(f"Error saving feedback: {e}")
        return jsonify({"error": str(e)}), 500

def mark_memory_as_reviewed(memory_id, rating):
    """Mark a memory entry as reviewed and store the rating"""
    try:
        with open(MEMORY_FILE, 'r') as f:
            memory = json.load(f)
        
        # Find and update the memory entry
        for entry in memory:
            if entry.get('timestamp') == memory_id:
                entry['reviewed'] = True
                entry['user_rating'] = rating
                entry['reviewed_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                break
        
        # Save updated memory
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=2)
            
        logging.info(f"Marked memory {memory_id} as reviewed with rating {rating}")
        
    except Exception as e:
        logging.error(f"Error marking memory as reviewed: {e}")

@app.route('/version', methods=['GET', 'POST'])
def version_control():
    """Get or update version information"""
    version_file = os.path.join(BASE_DIR, 'version.json')
    
    if request.method == 'GET':
        try:
            with open(version_file, 'r') as f:
                version_data = json.load(f)
            return jsonify(version_data)
        except (FileNotFoundError, JSONDecodeError):
            return jsonify({"error": "Version data not found"}), 404
    
    elif request.method == 'POST':
        try:
            data = request.get_json() or {}
            
            # Load current version data
            try:
                with open(version_file, 'r') as f:
                    version_data = json.load(f)
            except (FileNotFoundError, JSONDecodeError):
                return jsonify({"error": "Version file not found"}), 404
            
            # If this is a version bump, archive current version
            if 'version' in data and data['version'] != version_data.get('version'):
                # Archive current version
                current_version = {
                    "version": version_data.get('version'),
                    "date": version_data.get('date'),
                    "description": version_data.get('description')
                }
                version_data.setdefault('previous_versions', []).insert(0, current_version)
                
                # Auto-log version change
                version_memory = {
                    "topic": f"Version Update: {data['version']}",
                    "type": "VersionChange",
                    "input": f"Updating from {version_data.get('version', 'unknown')} to {data['version']}",
                    "output": f"Version {data['version']}: {data.get('description', 'Version updated')}",
                    "score": 20,
                    "maxScore": 25,
                    "success": True,
                    "category": "system",
                    "tags": ["version", "update", "milestone"],
                    "context": f"System version upgraded with new features and improvements",
                    "related_to": [],
                    "reviewed": False,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "auto_generated": True
                }
                
                # Save version change to memory
                try:
                    with open(MEMORY_FILE, 'r') as f:
                        memory = json.load(f)
                except (FileNotFoundError, JSONDecodeError):
                    memory = []
                
                memory.append(version_memory)
                with open(MEMORY_FILE, 'w') as f:
                    json.dump(memory, f, indent=2)
            
            # Update version data
            version_data.update(data)
            version_data['date'] = datetime.datetime.now().strftime('%Y-%m-%d')
            
            with open(version_file, 'w') as f:
                json.dump(version_data, f, indent=2)
            
            return jsonify({"status": "✅ Version updated", "version": version_data})
            
        except Exception as e:
            logging.error(f"Error updating version: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/commit-log', methods=['GET', 'POST'])
def commit_log():
    """Get or add git commit information"""
    commit_file = os.path.join(BASE_DIR, 'commit_log.json')
    
    if request.method == 'GET':
        try:
            with open(commit_file, 'r') as f:
                commits = json.load(f)
            return jsonify(commits)
        except (FileNotFoundError, JSONDecodeError):
            return jsonify({"error": "Commit log not found"}), 404
    
    elif request.method == 'POST':
        try:
            data = request.get_json() or {}
            required_fields = ['hash', 'message']
            
            missing = [field for field in required_fields if field not in data]
            if missing:
                return jsonify({"error": f"Missing required fields: {missing}"}), 400
            
            # Load existing commits
            try:
                with open(commit_file, 'r') as f:
                    commit_data = json.load(f)
            except (FileNotFoundError, JSONDecodeError):
                commit_data = {"commits": [], "auto_log_commits": True, "commit_types": {}}
            
            # Add new commit
            commit_entry = {
                "hash": data['hash'],
                "message": data['message'],
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "files_changed": data.get('files_changed', []),
                "logged_to_memory": False
            }
            
            commit_data['commits'].append(commit_entry)
            
            # Auto-log commit if enabled
            if commit_data.get('auto_log_commits', True):
                commit_type = detect_commit_type(data['message'])
                
                commit_memory = {
                    "topic": f"Git Commit: {data['message'][:50]}...",
                    "type": commit_type,
                    "input": f"Git commit: {data['message']}",
                    "output": f"Committed changes with hash {data['hash'][:8]}",
                    "score": 15,
                    "maxScore": 25,
                    "success": True,
                    "category": "development",
                    "tags": ["git", "commit", commit_type.lower()],
                    "context": f"Code changes committed to repository",
                    "related_to": [],
                    "reviewed": False,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "auto_generated": True
                }
                
                # Save commit to memory
                try:
                    with open(MEMORY_FILE, 'r') as f:
                        memory = json.load(f)
                except (FileNotFoundError, JSONDecodeError):
                    memory = []
                
                memory.append(commit_memory)
                with open(MEMORY_FILE, 'w') as f:
                    json.dump(memory, f, indent=2)
                
                commit_entry['logged_to_memory'] = True
            
            # Save commit log
            with open(commit_file, 'w') as f:
                json.dump(commit_data, f, indent=2)
            
            return jsonify({"status": "✅ Commit logged", "commit": commit_entry})
            
        except Exception as e:
            logging.error(f"Error logging commit: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/context', methods=['GET'])
def get_full_context():
    """Get complete context for AI agent decision making"""
    try:
        context = {}
        
        # Build state
        try:
            with open(os.path.join(BASE_DIR, 'build_state.json'), 'r') as f:
                context['build_state'] = json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            context['build_state'] = None
        
        # Daily focus
        try:
            with open(os.path.join(BASE_DIR, 'daily_focus.json'), 'r') as f:
                context['daily_focus'] = json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            context['daily_focus'] = None
        
        # Recent memory (last 5)
        try:
            with open(MEMORY_FILE, 'r') as f:
                memory = json.load(f)
                context['recent_memories'] = memory[-5:] if memory else []
                context['total_memories'] = len(memory)
        except (FileNotFoundError, JSONDecodeError):
            context['recent_memories'] = []
            context['total_memories'] = 0
        
        # Version info
        try:
            with open(os.path.join(BASE_DIR, 'version.json'), 'r') as f:
                context['version'] = json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            context['version'] = None
        
        # Recent commits (last 3)
        try:
            with open(os.path.join(BASE_DIR, 'commit_log.json'), 'r') as f:
                commit_data = json.load(f)
                context['recent_commits'] = commit_data.get('commits', [])[-3:]
        except (FileNotFoundError, JSONDecodeError):
            context['recent_commits'] = []
        
        # Feedback summary
        try:
            with open(os.path.join(BASE_DIR, 'feedback.json'), 'r') as f:
                feedback_data = json.load(f)
                context['feedback_summary'] = feedback_data.get('ratings_summary', {})
        except (FileNotFoundError, JSONDecodeError):
            context['feedback_summary'] = {}
        
        # System health
        context['system_status'] = {
            'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'files_exist': {
                'memory': os.path.exists(MEMORY_FILE),
                'build_state': os.path.exists(os.path.join(BASE_DIR, 'build_state.json')),
                'daily_focus': os.path.exists(os.path.join(BASE_DIR, 'daily_focus.json')),
                'version': os.path.exists(os.path.join(BASE_DIR, 'version.json'))
            }
        }
        
        return jsonify(context)
        
    except Exception as e:
        logging.error(f"Error getting context: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/insights', methods=['GET'])
def get_insights():
    """Get system insights and analysis"""
    try:
        insights = get_system_insights()
        
        # Add refresh option
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        if refresh:
            run_insight_analysis()
            insights = get_system_insights()
        
        return jsonify(insights)
        
    except Exception as e:
        logging.error(f"Error getting insights: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/train-models', methods=['POST'])
def train_prediction_models():
    """Train or retrain ML prediction models"""
    try:
        force_retrain = request.args.get('force', 'false').lower() == 'true'
        
        import sys
        sys.path.append(BASE_DIR)
        from tag_trainer import MemoryPredictor
        
        predictor = MemoryPredictor()
        
        if force_retrain:
            success = predictor.train_models()
        else:
            success = predictor.retrain_if_needed()
        
        if success:
            return jsonify({
                "status": "✅ Model training completed",
                "models_ready": predictor.is_trained
            })
        else:
            return jsonify({
                "status": "❌ Model training failed",
                "error": "Insufficient data or training error"
            }), 400
            
    except Exception as e:
        logging.error(f"Error training models: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/config', methods=['GET', 'POST'])
def manage_config():
    """Get or update system configuration"""
    global SYSTEM_CONFIG
    
    if request.method == 'GET':
        return jsonify(SYSTEM_CONFIG)
    
    elif request.method == 'POST':
        try:
            data = request.get_json() or {}
            
            # Update configuration
            SYSTEM_CONFIG.update(data)
            
            # Save to file
            config_file = os.path.join(BASE_DIR, 'config.json')
            with open(config_file, 'w') as f:
                json.dump(SYSTEM_CONFIG, f, indent=2)
            
            return jsonify({
                "status": "✅ Configuration updated",
                "config": SYSTEM_CONFIG
            })
            
        except Exception as e:
            logging.error(f"Error updating config: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/autolog-trace', methods=['GET'])
def get_autolog_trace():
    """Get autolog audit trace"""
    try:
        trace_file = os.path.join(BASE_DIR, SYSTEM_CONFIG.get('autolog_trace_file', 'autolog_trace.json'))
        
        try:
            with open(trace_file, 'r') as f:
                trace_log = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            trace_log = []
        
        # Optional filtering
        limit = int(request.args.get('limit', 50))
        trusted_only = request.args.get('trusted_only', 'false').lower() == 'true'
        
        if trusted_only:
            trace_log = [entry for entry in trace_log if entry.get('is_trusted_agent', False)]
        
        # Return most recent entries
        return jsonify({
            "total_entries": len(trace_log),
            "entries": trace_log[-limit:] if trace_log else [],
            "config": {
                "audit_logging": SYSTEM_CONFIG.get('audit_logging', True),
                "agent_auto_log": SYSTEM_CONFIG.get('agent_auto_log', True)
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting autolog trace: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/audit', methods=['GET'])
def get_infrastructure_audit():
    """Get infrastructure audit report"""
    try:
        import sys
        sys.path.append(BASE_DIR)
        from infra_audit import InfrastructureAuditor
        
        # Check if we should run a fresh audit or return cached results
        run_fresh = request.args.get('refresh', 'false').lower() == 'true'
        save_report = request.args.get('save', 'false').lower() == 'true'
        format_type = request.args.get('format', 'json')
        
        auditor = InfrastructureAuditor(BASE_DIR)
        
        if run_fresh:
            logging.info("Running fresh infrastructure audit")
            audit_report = auditor.run_full_audit()
        else:
            # Try to load recent audit report
            try:
                audit_files = [f for f in os.listdir(BASE_DIR) if f.startswith('infrastructure_audit_') and f.endswith('.json')]
                if audit_files:
                    latest_audit = sorted(audit_files)[-1]
                    with open(os.path.join(BASE_DIR, latest_audit), 'r') as f:
                        audit_report = json.load(f)
                    logging.info(f"Loaded cached audit report: {latest_audit}")
                else:
                    # No cached report, run fresh audit
                    audit_report = auditor.run_full_audit()
            except Exception as e:
                logging.warning(f"Error loading cached audit: {e}, running fresh audit")
                audit_report = auditor.run_full_audit()
        
        # Save report if requested
        if save_report:
            auditor.audit_results = audit_report
            saved_file = auditor.save_audit_report(format_type)
            audit_report['saved_to'] = saved_file
        
        # Log audit execution
        audit_memory = {
            "topic": "Infrastructure Audit Executed",
            "type": "SystemTest",
            "input": f"Infrastructure audit requested via /audit endpoint (refresh={run_fresh})",
            "output": f"Health score: {audit_report.get('summary', {}).get('health_score', 0)}/100. Found {audit_report.get('summary', {}).get('unregistered_components', 0)} unregistered components and {audit_report.get('summary', {}).get('architecture_mismatches', 0)} mismatches.",
            "score": 20,
            "maxScore": 25,
            "success": True,
            "category": "system",
            "tags": ["audit", "infrastructure", "health", "monitoring"],
            "context": "Running system health check and architecture audit",
            "related_to": [],
            "reviewed": False,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "auto_generated": True
        }
        
        # Save audit execution to memory
        try:
            with open(MEMORY_FILE, 'r') as f:
                memory = json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            memory = []
        
        memory.append(audit_memory)
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=2)
        
        return jsonify(audit_report)
        
    except Exception as e:
        logging.error(f"Error running infrastructure audit: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/git-sync', methods=['POST'])
def trigger_git_sync():
    """Manually trigger GitHub sync"""
    try:
        import sys
        sys.path.append(BASE_DIR)
        from git_sync import GitHubSyncer
        
        # Get parameters
        force = request.args.get('force', 'false').lower() == 'true'
        dry_run = request.args.get('dry_run', 'false').lower() == 'true'
        
        syncer = GitHubSyncer(BASE_DIR)
        
        if dry_run:
            # Dry run analysis
            recent_logs = syncer.load_memory_logs()
            bump_type, description = syncer.determine_version_bump(recent_logs)
            
            result = {
                "status": "dry_run",
                "analysis": {
                    "recent_logs_count": len(recent_logs),
                    "suggested_bump": bump_type,
                    "bump_description": description,
                    "would_auto_sync": syncer.should_auto_sync(recent_logs),
                    "has_changes": syncer.check_git_status()
                },
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        else:
            # Run actual sync
            result = syncer.run_auto_sync(force=force)
            
            # Log sync execution to memory
            sync_memory = {
                "topic": "GitHub Sync Executed",
                "type": "SystemUpdate",
                "input": f"Manual GitHub sync triggered via /git-sync endpoint (force={force})",
                "output": f"Sync result: {result['status']}. {result.get('version', 'No version change')}",
                "score": 20,
                "maxScore": 25,
                "success": result['status'] == 'success',
                "category": "development",
                "tags": ["git", "sync", "automation", "github"],
                "context": "Manual code synchronization with GitHub repository",
                "related_to": [],
                "reviewed": False,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "auto_generated": True
            }
            
            # Save sync execution to memory
            try:
                with open(MEMORY_FILE, 'r') as f:
                    memory = json.load(f)
            except (FileNotFoundError, JSONDecodeError):
                memory = []
            
            memory.append(sync_memory)
            with open(MEMORY_FILE, 'w') as f:
                json.dump(memory, f, indent=2)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error in git sync: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return {'status': 'healthy', 'service': 'Javlin Memory API'}, 200

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=80, debug=False)
    except Exception as e:
        logging.error(f'Application failed to start: {e}')
        import sys
        sys.exit(1)







