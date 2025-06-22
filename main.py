"""
MemoryOS Clean - Bulletproof Memory System
A minimal, production-ready memory API with comprehensive error handling
"""

import os
import json
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import traceback

# Configuration
MEMORY_FILE = 'memory.json'
API_KEY = os.getenv('JAVLIN_API_KEY', 'default-key-change-me')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memoryos.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MemoryOS')

# Create Flask app
app = Flask(__name__)
CORS(app)

def load_memory():
    """Load memory entries from file with bulletproof error handling"""
    try:
        if not os.path.exists(MEMORY_FILE):
            logger.info(f"Memory file {MEMORY_FILE} not found, creating empty file")
            with open(MEMORY_FILE, 'w') as f:
                json.dump([], f)
            return []
        
        with open(MEMORY_FILE, 'r') as f:
            data = json.load(f)
            
        if not isinstance(data, list):
            logger.warning("Memory file contains non-list data, resetting to empty list")
            return []
            
        logger.info(f"Loaded {len(data)} memory entries")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"Memory file corrupted: {e}")
        # Create backup of corrupted file
        backup_name = f"memory_corrupted_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            os.rename(MEMORY_FILE, backup_name)
            logger.info(f"Corrupted file backed up as {backup_name}")
        except:
            pass
        
        # Create fresh memory file
        with open(MEMORY_FILE, 'w') as f:
            json.dump([], f)
        return []
        
    except Exception as e:
        logger.error(f"Unexpected error loading memory: {e}")
        return []

def save_memory(data):
    """Save memory entries to file with bulletproof error handling"""
    try:
        # Validate data
        if not isinstance(data, list):
            logger.error("Cannot save non-list data to memory file")
            return False
        
        # Create backup before saving
        if os.path.exists(MEMORY_FILE):
            backup_name = f"memory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            try:
                import shutil
                shutil.copy2(MEMORY_FILE, backup_name)
            except:
                pass  # Backup failed but continue with save
        
        # Save to temporary file first
        temp_file = f"{MEMORY_FILE}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        # Atomic move
        os.replace(temp_file, MEMORY_FILE)
        logger.info(f"Saved {len(data)} memory entries")
        return True
        
    except Exception as e:
        logger.error(f"Error saving memory: {e}")
        # Clean up temp file if it exists
        try:
            if os.path.exists(f"{MEMORY_FILE}.tmp"):
                os.remove(f"{MEMORY_FILE}.tmp")
        except:
            pass
        return False

def validate_memory_entry(data):
    """Validate memory entry data"""
    required_fields = ['topic', 'type', 'input', 'output', 'success', 'category']
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Type validation
    if not isinstance(data['success'], bool):
        return False, "Field 'success' must be boolean"
    
    if not isinstance(data['topic'], str) or len(data['topic'].strip()) == 0:
        return False, "Field 'topic' must be non-empty string"
    
    return True, "Valid"

@app.route('/')
def index():
    """Serve the main page"""
    try:
        if os.path.exists('index.html'):
            return send_from_directory('.', 'index.html')
        else:
            return jsonify({
                "service": "MemoryOS-Clean",
                "status": "healthy",
                "version": "2.0.0",
                "endpoints": [
                    "GET / - This page",
                    "GET /health - Health check",
                    "GET /memory - Get memories",
                    "POST /memory - Add memory (requires API key)",
                    "GET /stats - Statistics",
                    "GET /gpt-status - GPT-friendly status"
                ]
            })
    except Exception as e:
        logger.error(f"Error serving index: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health')
def health():
    """Bulletproof health endpoint that NEVER fails"""
    try:
        start_time = datetime.now()
        
        # Basic health checks
        checks = {
            "memory_file_accessible": False,
            "memory_file_writable": False,
            "response_time_ok": True
        }
        
        metrics = {
            "memory_entries": 0,
            "memory_file_exists": False,
            "memory_file_size_bytes": 0
        }
        
        # Check memory file
        try:
            if os.path.exists(MEMORY_FILE):
                checks["memory_file_accessible"] = True
                metrics["memory_file_exists"] = True
                metrics["memory_file_size_bytes"] = os.path.getsize(MEMORY_FILE)
                
                # Try to load memory
                memory = load_memory()
                metrics["memory_entries"] = len(memory)
                
                # Test write access
                test_data = memory + [{"test": "write_test", "timestamp": datetime.now().isoformat()}]
                if save_memory(test_data[:-1]):  # Save without test entry
                    checks["memory_file_writable"] = True
            else:
                # Try to create memory file
                try:
                    with open(MEMORY_FILE, 'w') as f:
                        json.dump([], f)
                    checks["memory_file_accessible"] = True
                    checks["memory_file_writable"] = True
                    metrics["memory_file_exists"] = True
                except:
                    pass
        except Exception as e:
            logger.error(f"Health check memory error: {e}")
        
        # Calculate response time
        response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        checks["response_time_ok"] = response_time_ms < 1000
        
        # Determine overall status
        if all(checks.values()):
            status = "healthy"
            status_code = 200
        elif checks["memory_file_accessible"]:
            status = "degraded"
            status_code = 200
        else:
            status = "unhealthy"
            status_code = 503
        
        response = {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "response_time_ms": round(response_time_ms, 2),
            "checks": checks,
            "metrics": metrics,
            "version": "2.0.0",
            "service": "MemoryOS-Clean",
            "bulletproof": True
        }
        
        return jsonify(response), status_code
        
    except Exception as e:
        # Ultimate fallback - this should NEVER fail
        logger.error(f"Health endpoint critical error: {e}")
        return jsonify({
            "status": "critical_failure",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "service": "MemoryOS-Clean",
            "bulletproof": True
        }), 503

@app.route('/memory', methods=['GET'])
def get_memory():
    """Get memory entries with pagination"""
    try:
        memory = load_memory()
        
        # Pagination parameters
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 per page
        offset = (page - 1) * limit
        
        # Apply pagination
        paginated_memory = memory[offset:offset + limit]
        
        # Reverse for newest first
        paginated_memory.reverse()
        
        response = {
            "memories": paginated_memory,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(memory),
                "pages": (len(memory) + limit - 1) // limit
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        return jsonify({
            "error": "Failed to retrieve memories",
            "details": str(e),
            "memories": [],
            "pagination": {"page": 1, "limit": 50, "total": 0, "pages": 0}
        }), 500

@app.route('/memory', methods=['POST'])
def add_memory():
    """Add new memory entry (requires API key)"""
    try:
        # Check API key
        api_key = request.headers.get('X-API-KEY')
        if api_key != API_KEY:
            return jsonify({"error": "Invalid or missing API key"}), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate entry
        is_valid, message = validate_memory_entry(data)
        if not is_valid:
            return jsonify({"error": f"Invalid memory entry: {message}"}), 400
        
        # Add metadata
        data['timestamp'] = datetime.now(timezone.utc).isoformat()
        data['reviewed'] = data.get('reviewed', False)
        
        # Set defaults for optional fields
        data.setdefault('score', 15)
        data.setdefault('maxScore', 25)
        data.setdefault('tags', [])
        
        # Load current memory and add new entry
        memory = load_memory()
        memory.append(data)
        
        # Save updated memory
        if save_memory(memory):
            logger.info(f"Added memory entry: {data.get('topic', 'Unknown')}")
            return jsonify({
                "message": "Memory entry added successfully",
                "entry": data,
                "total_memories": len(memory)
            }), 201
        else:
            return jsonify({"error": "Failed to save memory entry"}), 500
            
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        return jsonify({
            "error": "Failed to add memory entry",
            "details": str(e)
        }), 500

@app.route('/stats')
def get_stats():
    """Get memory statistics"""
    try:
        memory = load_memory()
        
        if not memory:
            return jsonify({
                "total_memories": 0,
                "success_rate": "0%",
                "categories": {},
                "types": {},
                "recent_activity": "No activity"
            })
        
        # Calculate statistics
        total = len(memory)
        successful = sum(1 for entry in memory if entry.get('success', False))
        success_rate = f"{(successful/total*100):.1f}%" if total > 0 else "0%"
        
        # Count by category
        categories = {}
        for entry in memory:
            cat = entry.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        # Count by type
        types = {}
        for entry in memory:
            type_val = entry.get('type', 'unknown')
            types[type_val] = types.get(type_val, 0) + 1
        
        # Recent activity
        recent_activity = "No recent activity"
        if memory:
            latest = memory[-1]
            recent_activity = f"Latest: {latest.get('topic', 'Unknown')} ({latest.get('timestamp', 'Unknown time')})"
        
        return jsonify({
            "total_memories": total,
            "success_rate": success_rate,
            "successful_entries": successful,
            "failed_entries": total - successful,
            "categories": categories,
            "types": types,
            "recent_activity": recent_activity,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            "error": "Failed to get statistics",
            "details": str(e),
            "total_memories": 0,
            "success_rate": "0%"
        }), 500

@app.route('/gpt-status')
def gpt_status():
    """GPT-friendly status endpoint"""
    try:
        memory = load_memory()
        
        # Get health status
        health_response = health()
        health_data = health_response[0].get_json()
        
        return jsonify({
            "system_status": health_data.get('status', 'unknown'),
            "memory_count": len(memory),
            "last_activity": memory[-1].get('timestamp') if memory else None,
            "api_accessible": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "MemoryOS is operational and ready for GPT integration"
        })
        
    except Exception as e:
        logger.error(f"Error getting GPT status: {e}")
        return jsonify({
            "system_status": "error",
            "memory_count": 0,
            "api_accessible": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": ["/", "/health", "/memory", "/stats", "/gpt-status"]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

if __name__ == '__main__':
    # Startup checks
    logger.info("Starting MemoryOS Clean...")
    
    # Ensure memory file exists
    if not os.path.exists(MEMORY_FILE):
        logger.info("Creating initial memory file...")
        with open(MEMORY_FILE, 'w') as f:
            json.dump([], f)
    
    # Test memory operations
    try:
        test_memory = load_memory()
        logger.info(f"Memory system initialized with {len(test_memory)} entries")
    except Exception as e:
        logger.error(f"Memory system initialization failed: {e}")
    
    logger.info("MemoryOS Clean started successfully")
    app.run(host='0.0.0.0', port=5000, debug=False)