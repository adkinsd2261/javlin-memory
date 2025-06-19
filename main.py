import os
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import json
import datetime
import logging
from json.decoder import JSONDecodeError

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

        data = request.get_json()
        logging.info(f"Received memory entry: {data}")

        required_fields = [
            "topic", "type", "input", "output",
            "score", "maxScore", "success", "category", "reviewed"
        ]
        missing = [field for field in required_fields if field not in data]
        if missing:
            logging.warning(f"Missing fields: {missing}")
            return jsonify({
                "error": "Missing required fields.",
                "missing": missing
            }), 400

        if not isinstance(data["score"], int) or not isinstance(data["maxScore"], int):
            logging.warning("Score or maxScore not integer")
            return jsonify({"error": "Score and maxScore must be integers."}), 400

        if not isinstance(data["success"], bool) or not isinstance(data["reviewed"], bool):
            logging.warning("Success or reviewed not boolean")
            return jsonify({"error": "Success and reviewed must be booleans."}), 400

        # Validate optional fields
        if "tags" in data:
            if not isinstance(data["tags"], list) or not all(isinstance(tag, str) for tag in data["tags"]):
                logging.warning("Tags must be a list of strings")
                return jsonify({"error": "Tags must be a list of strings."}), 400
        else:
            data["tags"] = []

        if "related_to" in data:
            if not isinstance(data["related_to"], list) or not all(isinstance(rel, str) for rel in data["related_to"]):
                logging.warning("Related_to must be a list of strings")
                return jsonify({"error": "Related_to must be a list of strings."}), 400
        else:
            data["related_to"] = []

        if 'timestamp' not in data:
            data['timestamp'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            logging.info(f"Added timestamp: {data['timestamp']}")

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

        logging.info(f"Memory entry saved. Total entries: {len(memory)}")
        return jsonify({"status": "✅ Memory saved", "entry": data}), 200

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
        
        for m in recent_memory:
            cat = m.get('category', 'unknown')
            typ = m.get('type', 'unknown')
            topic = m.get('topic', 'unknown')
            
            categories[cat] = categories.get(cat, 0) + 1
            types[typ] = types.get(typ, 0) + 1
            topics[topic] = topics.get(topic, 0) + 1
            
            for tag in m.get('tags', []):
                tags[tag] = tags.get(tag, 0) + 1
        
        # Find most common items
        most_common_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]
        most_common_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Group related logs
        related_groups, standalone = group_related_logs(recent_memory)
        
        # Unreviewed analysis
        unreviewed_data = find_unreviewed_logs()
        
        digest = {
            'period': 'Last 7 days',
            'summary': {
                'total_logs': total,
                'successful_logs': successful,
                'success_rate': f"{(successful/total*100):.1f}%" if total > 0 else "0%",
                'categories': categories,
                'types': types,
                'tags': tags
            },
            'insights': {
                'most_common_topics': most_common_topics,
                'most_common_tags': most_common_tags,
                'related_groups': related_groups,
                'standalone_logs': len(standalone)
            },
            'follow_up': unreviewed_data
        }
        
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

@app.route('/')
def home():
    return 'Javlin Memory API is live!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)







