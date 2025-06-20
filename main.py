"""
MemoryOS - Clean Minimal Implementation
A bulletproof memory system with zero complexity cruft
"""

import os
import json
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS

# Setup
app = Flask(__name__)
CORS(app, origins="*")
logging.basicConfig(level=logging.INFO)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, 'memory.json')
API_KEY = os.getenv('JAVLIN_API_KEY', 'default-key-change-me')

def load_memory():
    """Load memory data safely"""
    try:
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_memory(data):
    """Save memory data safely"""
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving memory: {e}")
        return False

def validate_api_key():
    """Simple API key validation"""
    key = request.headers.get('X-API-KEY') or request.headers.get('x-api-key')
    return key == API_KEY

@app.route('/')
def health():
    """Root health check"""
    return jsonify({
        "status": "healthy",
        "service": "MemoryOS-Clean",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route('/health')
def health_check():
    """Detailed health check"""
    memory = load_memory()
    return jsonify({
        "status": "healthy",
        "memory_entries": len(memory),
        "memory_file_exists": os.path.exists(MEMORY_FILE),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route('/memory', methods=['GET'])
def get_memories():
    """Get memories with pagination"""
    try:
        memory = load_memory()

        # Pagination
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 200)
        offset = (page - 1) * limit

        # Filter if requested
        category = request.args.get('category')
        if category:
            memory = [m for m in memory if m.get('category', '').lower() == category.lower()]

        # Apply pagination
        total = len(memory)
        paginated = memory[offset:offset + limit]

        return jsonify({
            "memories": paginated,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "has_more": (offset + limit) < total
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/memory', methods=['POST'])
def add_memory():
    """Add new memory entry"""
    # Validate API key for POST requests
    if not validate_api_key():
        return jsonify({"error": "Invalid API key"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Ensure required fields
        required_fields = ["topic", "type", "input", "output", "success", "category"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Add metadata
        data.update({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "score": data.get("score", 15),
            "maxScore": data.get("maxScore", 25),
            "tags": data.get("tags", []),
            "reviewed": data.get("reviewed", False)
        })

        # Load, append, save
        memory = load_memory()
        memory.append(data)

        if save_memory(memory):
            return jsonify({
                "status": "success",
                "entry": data,
                "total_entries": len(memory)
            })
        else:
            return jsonify({"error": "Failed to save memory"}), 500

    except Exception as e:
        logging.error(f"Error adding memory: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/stats')
def get_stats():
    """Get memory statistics"""
    try:
        memory = load_memory()

        total = len(memory)
        successful = sum(1 for m in memory if m.get('success', False))

        # Category breakdown
        categories = {}
        types = {}
        for m in memory:
            cat = m.get('category', 'unknown')
            typ = m.get('type', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
            types[typ] = types.get(typ, 0) + 1

        return jsonify({
            "total_memories": total,
            "successful": successful,
            "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "0%",
            "categories": categories,
            "types": types
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/gpt-status')
def gpt_status():
    """GPT-friendly status endpoint"""
    try:
        memory = load_memory()
        return jsonify({
            "system_status": "online",
            "memory_entries": len(memory),
            "api_healthy": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"MemoryOS Clean is running with {len(memory)} memories"
        })
    except Exception as e:
        return jsonify({
            "system_status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

if __name__ == '__main__':
    # Ensure memory file exists
    if not os.path.exists(MEMORY_FILE):
        save_memory([])
        print(f"Created memory file: {MEMORY_FILE}")

    print("🚀 Starting MemoryOS Clean...")
    print(f"📁 Memory file: {MEMORY_FILE}")
    print(f"🔑 API Key required for POST /memory")

    app.run(host='0.0.0.0', port=5000, debug=False)