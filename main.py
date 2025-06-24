"""
MemoryOS Clean - Bulletproof Memory System with Credit System
A minimal, production-ready memory API with comprehensive error handling and credit management
"""

import os
import json
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import traceback

# Import credit system
from credit_system import credit_system, require_credits, require_memory_limit, get_api_key_from_request

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
                    "GET /memory - Get memories (requires credits)",
                    "POST /memory - Add memory (requires credits)",
                    "GET /stats - Statistics (requires credits)",
                    "GET /gpt-status - GPT-friendly status (requires credits)",
                    "GET /credits - Check credit status",
                    "POST /signup - Create account",
                    "POST /login - Login (placeholder)"
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
            "response_time_ok": True,
            "credit_system_accessible": False
        }
        
        metrics = {
            "memory_entries": 0,
            "memory_file_exists": False,
            "memory_file_size_bytes": 0,
            "total_users": 0
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
        
        # Check credit system
        try:
            users = credit_system.load_users()
            metrics["total_users"] = len(users)
            checks["credit_system_accessible"] = True
        except Exception as e:
            logger.error(f"Health check credit system error: {e}")
        
        # Calculate response time
        response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        checks["response_time_ok"] = response_time_ms < 1000
        
        # Determine overall status
        if all(checks.values()):
            status = "healthy"
            status_code = 200
        elif checks["memory_file_accessible"] and checks["credit_system_accessible"]:
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

@app.route('/credits')
def get_credits():
    """Get credit status for the API key"""
    try:
        api_key = get_api_key_from_request()
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        status = credit_system.get_credit_status(api_key)
        
        if 'error' in status:
            return jsonify(status), 401
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting credits: {e}")
        return jsonify({
            "error": "Failed to retrieve credit status",
            "details": str(e)
        }), 500

@app.route('/signup', methods=['POST'])
def signup():
    """Create a new user account"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        api_key = data.get('api_key')
        plan = data.get('plan', 'Free')
        email = data.get('email')
        
        if not api_key:
            return jsonify({"error": "API key required"}), 400
        
        # Check if user already exists
        existing_user = credit_system.get_user(api_key)
        if existing_user:
            return jsonify({"error": "User already exists"}), 409
        
        # Create user
        user = credit_system.create_user(api_key, plan, email)
        
        # Return user info (without sensitive data)
        return jsonify({
            "message": "Account created successfully",
            "user": {
                "plan": user['plan'],
                "credits_remaining": user['credits_remaining'],
                "memory_limit": user['memory_limit'],
                "reset_date": user['reset_date'],
                "created_at": user['created_at']
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({
            "error": "Failed to create account",
            "details": str(e)
        }), 500

@app.route('/login', methods=['POST'])
def login():
    """Login endpoint (placeholder for future authentication)"""
    return jsonify({
        "message": "Login endpoint placeholder",
        "note": "Currently using API key authentication. Future versions will support email/password login."
    })

@app.route('/memory', methods=['GET'])
@require_credits(cost=1)
def get_memory():
    """Get memory entries with pagination (requires 1 credit)"""
    try:
        # Get API key to filter memories
        api_key = get_api_key_from_request()
        
        memory = load_memory()
        
        # Filter memories for this user (if api_key field exists)
        user_memories = []
        for entry in memory:
            # Include memories that belong to this user or have no api_key (legacy)
            if entry.get('api_key') == api_key or 'api_key' not in entry:
                user_memories.append(entry)
        
        # Pagination parameters
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 per page
        offset = (page - 1) * limit
        
        # Apply pagination
        paginated_memory = user_memories[offset:offset + limit]
        
        # Reverse for newest first
        paginated_memory.reverse()
        
        response = {
            "memories": paginated_memory,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(user_memories),
                "pages": (len(user_memories) + limit - 1) // limit
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
@require_credits(cost=2)
@require_memory_limit()
def add_memory():
    """Add new memory entry (requires 2 credits and memory limit check)"""
    try:
        # Get API key
        api_key = get_api_key_from_request()
        
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
        data['api_key'] = api_key  # Tag with owner
        
        # Set defaults for optional fields
        data.setdefault('score', 15)
        data.setdefault('maxScore', 25)
        data.setdefault('tags', [])
        
        # Load current memory and add new entry
        memory = load_memory()
        memory.append(data)
        
        # Save updated memory
        if save_memory(memory):
            logger.info(f"Added memory entry: {data.get('topic', 'Unknown')} for user {api_key[:8]}...")
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
@require_credits(cost=1)
def get_stats():
    """Get memory statistics (requires 1 credit)"""
    try:
        # Get API key to filter stats
        api_key = get_api_key_from_request()
        
        memory = load_memory()
        
        # Filter memories for this user
        user_memories = [entry for entry in memory if entry.get('api_key') == api_key or 'api_key' not in entry]
        
        if not user_memories:
            return jsonify({
                "total_memories": 0,
                "success_rate": "0%",
                "categories": {},
                "types": {},
                "recent_activity": "No activity"
            })
        
        # Calculate statistics
        total = len(user_memories)
        successful = sum(1 for entry in user_memories if entry.get('success', False))
        success_rate = f"{(successful/total*100):.1f}%" if total > 0 else "0%"
        
        # Count by category
        categories = {}
        for entry in user_memories:
            cat = entry.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        # Count by type
        types = {}
        for entry in user_memories:
            type_val = entry.get('type', 'unknown')
            types[type_val] = types.get(type_val, 0) + 1
        
        # Recent activity
        recent_activity = "No recent activity"
        if user_memories:
            latest = user_memories[-1]
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
@require_credits(cost=1)
def gpt_status():
    """GPT-friendly status endpoint (requires 1 credit)"""
    try:
        # Get API key to filter data
        api_key = get_api_key_from_request()
        
        memory = load_memory()
        user_memories = [entry for entry in memory if entry.get('api_key') == api_key or 'api_key' not in entry]
        
        # Get health status
        health_response = health()
        health_data = health_response[0].get_json()
        
        return jsonify({
            "system_status": health_data.get('status', 'unknown'),
            "memory_count": len(user_memories),
            "last_activity": user_memories[-1].get('timestamp') if user_memories else None,
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

# Admin endpoints (no credit cost)
@app.route('/admin/users', methods=['GET'])
def admin_get_users():
    """Admin endpoint to view all users (no credit cost)"""
    admin_key = request.headers.get('X-ADMIN-KEY')
    if admin_key != os.getenv('ADMIN_KEY', 'admin-secret-key'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        users = credit_system.load_users()
        
        # Remove sensitive data
        safe_users = {}
        for api_key, user in users.items():
            safe_users[api_key[:8] + '...'] = {
                'plan': user['plan'],
                'credits_remaining': user['credits_remaining'],
                'credits_used_this_cycle': user['credits_used_this_cycle'],
                'total_credits_used': user['total_credits_used'],
                'memory_count': user.get('memory_count', 0),
                'memory_limit': user.get('memory_limit', 0),
                'reset_date': user['reset_date'],
                'created_at': user['created_at'],
                'last_activity': user['last_activity']
            }
        
        return jsonify({
            'total_users': len(users),
            'users': safe_users
        })
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'error': 'Failed to retrieve users'}), 500

@app.route('/admin/user/<api_key>/plan', methods=['PUT'])
def admin_update_plan(api_key):
    """Admin endpoint to update user plan (no credit cost)"""
    admin_key = request.headers.get('X-ADMIN-KEY')
    if admin_key != os.getenv('ADMIN_KEY', 'admin-secret-key'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        data = request.get_json()
        new_plan = data.get('plan')
        
        if not new_plan:
            return jsonify({'error': 'Plan required'}), 400
        
        success = credit_system.update_user_plan(api_key, new_plan)
        
        if success:
            return jsonify({'message': f'Plan updated to {new_plan}'})
        else:
            return jsonify({'error': 'Failed to update plan'}), 400
            
    except Exception as e:
        logger.error(f"Error updating plan: {e}")
        return jsonify({'error': 'Failed to update plan'}), 500

@app.route('/admin/sync-memory-counts', methods=['POST'])
def admin_sync_memory_counts():
    """Admin endpoint to sync memory counts from actual memory file"""
    admin_key = request.headers.get('X-ADMIN-KEY')
    if admin_key != os.getenv('ADMIN_KEY', 'admin-secret-key'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        users = credit_system.load_users()
        updated_count = 0
        
        for api_key in users.keys():
            if credit_system.update_memory_count_from_file(api_key):
                updated_count += 1
        
        return jsonify({
            'message': f'Synced memory counts for {updated_count} users',
            'total_users': len(users)
        })
        
    except Exception as e:
        logger.error(f"Error syncing memory counts: {e}")
        return jsonify({'error': 'Failed to sync memory counts'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": ["/", "/health", "/memory", "/stats", "/gpt-status", "/credits", "/signup", "/login"]
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
    logger.info("Starting MemoryOS Clean with Credit System...")
    
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
    
    # Test credit system
    try:
        users = credit_system.load_users()
        logger.info(f"Credit system initialized with {len(users)} users")
    except Exception as e:
        logger.error(f"Credit system initialization failed: {e}")
    
    logger.info("MemoryOS Clean with Credit System started successfully")
    app.run(host='0.0.0.0', port=5000, debug=False)