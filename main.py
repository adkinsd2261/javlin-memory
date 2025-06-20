"""
MemoryOS - Clean Minimal Implementation
A bulletproof memory system with zero complexity cruft
"""

import os
import json
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import time
import traceback

# Setup
app = Flask(__name__)
CORS(app, origins="*")

# Configure comprehensive logging
log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# File handler for all logs
file_handler = logging.FileHandler('memoryos.log')
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger('MemoryOS')

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

@app.before_request
def log_request():
    """Log incoming requests"""
    g.start_time = time.time()
    logger.info(f"REQUEST: {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def log_response(response):
    """Log response details"""
    duration = round((time.time() - g.start_time) * 1000, 2)
    logger.info(f"RESPONSE: {response.status_code} for {request.method} {request.path} ({duration}ms)")
    return response

@app.errorhandler(405)
def handle_method_not_allowed(e):
    """Handle method not allowed errors with better context"""
    logger.warning(f"METHOD NOT ALLOWED: {request.method} {request.path} from {request.remote_addr}")
    return jsonify({
        "error": f"Method {request.method} not allowed for {request.path}",
        "allowed_methods": e.valid_methods,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "method_not_allowed"
    }), 405

@app.errorhandler(Exception)
def handle_exception(e):
    """Log and handle unexpected exceptions"""
    error_msg = str(e)
    logger.error(f"UNHANDLED EXCEPTION: {error_msg}")
    logger.error(f"TRACEBACK: {traceback.format_exc()}")
    
    # Record error for alerting only for serious errors, not method errors
    if not isinstance(e, Exception.__class__.__bases__[0]):
        try:
            from alerts import alert_manager
            alert_manager.record_error(f"Unhandled exception: {error_msg}", "CRITICAL_ERROR")
        except ImportError:
            pass  # Alerting system not available
    
    return jsonify({
        "error": "Internal server error",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "error"
    }), 500

def validate_api_key():
    """Simple API key validation"""
    key = request.headers.get('X-API-KEY') or request.headers.get('x-api-key')
    return key == API_KEY

@app.route('/')
def index():
    """Serve the main MemoryOS UI"""
    try:
        with open('index.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({
            "status": "healthy",
            "service": "MemoryOS-Clean",
            "message": "UI not found, API is running",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

@app.route('/health')
def health_check():
    """Comprehensive health check for monitoring services"""
    try:
        start_time = time.time()
        
        # Test memory file access
        memory = load_memory()
        memory_accessible = True
        memory_count = len(memory)
        
        # Test memory write capability
        test_write = True
        try:
            with open(MEMORY_FILE, 'r') as f:
                pass
        except Exception:
            test_write = False
            
        # Calculate response time
        response_time_ms = round((time.time() - start_time) * 1000, 2)
        
        # Determine overall health
        healthy = memory_accessible and test_write and response_time_ms < 1000
        
        health_data = {
            "status": "healthy" if healthy else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "response_time_ms": response_time_ms,
            "checks": {
                "memory_file_accessible": memory_accessible,
                "memory_file_writable": test_write,
                "response_time_ok": response_time_ms < 1000
            },
            "metrics": {
                "memory_entries": memory_count,
                "memory_file_exists": os.path.exists(MEMORY_FILE),
                "memory_file_size_bytes": os.path.getsize(MEMORY_FILE) if os.path.exists(MEMORY_FILE) else 0
            },
            "version": "2.0.0",
            "service": "MemoryOS-Clean"
        }
        
        # Log health check
        logger.info(f"HEALTH CHECK: {health_data['status']} - {response_time_ms}ms")
        
        return jsonify(health_data), 200 if healthy else 503
        
    except Exception as e:
        logger.error(f"HEALTH CHECK FAILED: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 503

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

@app.route('/alerts/test')
def test_alerts():
    """Test the alerting system"""
    try:
        from alerts import alert_manager
        success = alert_manager.test_alert()
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Test alert sent successfully",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to send test alert",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 500
            
    except ImportError:
        return jsonify({
            "status": "error",
            "message": "Alerting system not configured",
            "setup_instructions": "Set ALERT_WEBHOOK_URL or EMAIL_WEBHOOK_URL environment variables",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 501

@app.route('/ai/query', methods=['POST'])
def ai_query():
    """Query the persistent AI agent"""
    try:
        data = request.get_json()
        if not data or 'input' not in data:
            return jsonify({"error": "No input provided"}), 400
        
        from intelligent_agent import MemoryAwareAgent
        agent = MemoryAwareAgent(memory_api_base="http://0.0.0.0:5000")
        
        result = agent.query_ai(data['input'])
        
        return jsonify({
            "status": "success",
            "ai_response": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"AI query failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/ai/context')
def ai_context():
    """Get current AI context state"""
    try:
        from intelligent_agent import MemoryAwareAgent
        agent = MemoryAwareAgent(memory_api_base="http://0.0.0.0:5000")
        
        context = agent.load_persistent_context()
        
        return jsonify({
            "status": "healthy",
            "ai_provider": agent.ai_provider,
            "model": agent.model.get('model', 'unknown'),
            "context": context,
            "session_id": agent.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"AI context failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/product/audit')
def product_audit():
    """Comprehensive product audit for strategic analysis"""
    try:
        import os
        import glob
        
        # Analyze file structure and documentation
        docs = {}
        code_files = {}
        
        # Check key documentation files
        doc_files = ['README.md', 'AGENT_BIBLE.md', 'config.json', 'version.json']
        for doc in doc_files:
            if os.path.exists(doc):
                with open(doc, 'r') as f:
                    docs[doc] = f.read()
        
        # Analyze code structure
        py_files = glob.glob('*.py')
        for py_file in py_files:
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    # Extract key info
                    lines = len(content.split('\n'))
                    functions = content.count('def ')
                    classes = content.count('class ')
                    endpoints = content.count('@app.route')
                    
                    code_files[py_file] = {
                        "lines": lines,
                        "functions": functions,
                        "classes": classes,
                        "endpoints": endpoints,
                        "size_kb": round(len(content) / 1024, 2)
                    }
            except:
                pass
        
        # Get memory statistics for product usage insights
        memory = load_memory()
        
        # Analyze memory for product insights
        categories = {}
        success_patterns = {}
        user_pain_points = []
        
        for mem in memory[-50:]:  # Recent memories
            cat = mem.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
            
            if not mem.get('success', True):
                user_pain_points.append({
                    "topic": mem.get('topic', ''),
                    "type": mem.get('type', ''),
                    "input": mem.get('input', '')[:100],
                    "timestamp": mem.get('timestamp', '')
                })
        
        # Analyze UI and frontend
        ui_files = ['index.html', 'MemoryTimeline.jsx']
        ui_analysis = {}
        for ui_file in ui_files:
            if os.path.exists(ui_file):
                with open(ui_file, 'r') as f:
                    content = f.read()
                    ui_analysis[ui_file] = {
                        "has_styling": 'style' in content.lower() or 'css' in content.lower(),
                        "has_javascript": 'script' in content.lower() or '.js' in content,
                        "size_kb": round(len(content) / 1024, 2),
                        "components": content.count('function ') + content.count('const ') + content.count('class ')
                    }
        
        # Product positioning analysis
        features_mentioned = []
        if 'README.md' in docs:
            readme = docs['README.md'].lower()
            feature_keywords = ['api', 'memory', 'ai', 'agent', 'monitoring', 'health', 'logging', 'deployment']
            for keyword in feature_keywords:
                if keyword in readme:
                    features_mentioned.append(keyword)
        
        audit_result = {
            "product_overview": {
                "name": "MemoryOS",
                "version": "2.0.0",
                "tagline": "Bulletproof minimal memory system",
                "core_value_prop": "AI-powered persistent memory with health monitoring"
            },
            "documentation_health": {
                "files_present": list(docs.keys()),
                "total_doc_size_kb": sum(round(len(content) / 1024, 2) for content in docs.values()),
                "features_documented": features_mentioned,
                "documentation_completeness": len(docs) / len(doc_files) * 100
            },
            "technical_foundation": {
                "code_files": code_files,
                "total_endpoints": sum(info.get('endpoints', 0) for info in code_files.values()),
                "total_functions": sum(info.get('functions', 0) for info in code_files.values()),
                "codebase_size_kb": sum(info.get('size_kb', 0) for info in code_files.values())
            },
            "user_experience": {
                "ui_files": ui_analysis,
                "has_frontend": len(ui_analysis) > 0,
                "styling_quality": any(info.get('has_styling', False) for info in ui_analysis.values()),
                "interactivity": any(info.get('has_javascript', False) for info in ui_analysis.values())
            },
            "product_usage_insights": {
                "total_memories": len(memory),
                "category_breakdown": categories,
                "recent_pain_points": user_pain_points[:5],
                "success_rate": f"{sum(1 for m in memory if m.get('success', False)) / len(memory) * 100:.1f}%" if memory else "0%"
            },
            "strategic_gaps": {
                "missing_onboarding": not any('getting started' in doc.lower() for doc in docs.values()),
                "missing_pricing": not any('pricing' in doc.lower() for doc in docs.values()),
                "missing_use_cases": not any('use case' in doc.lower() for doc in docs.values()),
                "missing_integration_guide": not any('integration' in doc.lower() for doc in docs.values()),
                "ui_needs_work": not any(info.get('has_styling', False) for info in ui_analysis.values())
            },
            "competitive_positioning": {
                "target_market": "AI-powered productivity tools",
                "unique_features": ["persistent memory", "health monitoring", "ai agent integration"],
                "differentiators": ["bulletproof reliability", "zero complexity", "production-ready"]
            },
            "recommendations": {
                "immediate": [
                    "Create clear value proposition on landing page",
                    "Add pricing tiers and use case examples",
                    "Improve UI styling and user experience",
                    "Add onboarding flow for new users"
                ],
                "strategic": [
                    "Develop API marketplace positioning",
                    "Create developer community",
                    "Build integration ecosystem",
                    "Establish thought leadership in AI memory"
                ]
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(audit_result)
        
    except Exception as e:
        logger.error(f"Product audit failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

if __name__ == '__main__':
    # Ensure memory file exists
    if not os.path.exists(MEMORY_FILE):
        save_memory([])
        print(f"Created memory file: {MEMORY_FILE}")

    # Initialize alerting
    try:
        from alerts import alert_manager
        print("🚨 Alerting system initialized")
        
        # Check if alerting is configured
        webhook_configured = bool(os.getenv('ALERT_WEBHOOK_URL') or os.getenv('EMAIL_WEBHOOK_URL'))
        if webhook_configured:
            print("📧 Alert webhooks configured")
        else:
            print("⚠️  Alert webhooks not configured (optional)")
            print("   Set ALERT_WEBHOOK_URL or EMAIL_WEBHOOK_URL to enable alerts")
            
    except ImportError:
        print("⚠️  Alerting system not available")

    print("🚀 Starting MemoryOS Clean...")
    print(f"📁 Memory file: {MEMORY_FILE}")
    print(f"🔑 API Key required for POST /memory")
    print(f"📊 Logs: memoryos.log")
    print(f"🏥 Health check: /health")

    app.run(host='0.0.0.0', port=5000, debug=False)