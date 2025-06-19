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
        key = request.headers.get('X-API-KEY')
        if key != os.getenv('JAVLIN_API_KEY'):
            logging.warning(f"Unauthorized access attempt with key: {key}")
            abort(401, description="Unauthorized: Invalid or missing API key.")

@app.route('/memory', methods=['POST'])
def add_memory():
    try:
        # Debug logging for API key
        api_key = request.headers.get('X-API-KEY')
        logging.debug(f"Received API key: {api_key}")
        
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
        return jsonify(memory)
    except Exception as e:
        logging.error(f"Error loading memories: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return 'Javlin Memory API is live!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)







