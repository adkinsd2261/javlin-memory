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

# Import bulletproof logging
try:
    from bulletproof_logger import bulletproof_logger
    BULLETPROOF_LOGGING = True
except ImportError:
    BULLETPROOF_LOGGING = False
    print("⚠️ Bulletproof logging not available, using standard logging")

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
    """Log and handle unexpected exceptions - BULLETPROOF VERSION"""
    try:
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        timestamp = datetime.now(timezone.utc).isoformat()

        # Log to multiple places for bulletproofing
        logger.error(f"CRITICAL EXCEPTION [{timestamp}]: {error_msg}")
        logger.error(f"FULL TRACEBACK: {error_traceback}")

        # Also log to console for immediate visibility in Replit
        print(f"🚨 CRITICAL ERROR [{timestamp}]: {error_msg}")
        print(f"📍 TRACEBACK: {error_traceback}")

        # Write to dedicated error log file
        try:
            with open('logs/errors.log', 'a') as f:
                f.write(f"[{timestamp}] CRITICAL ERROR: {error_msg}\n")
                f.write(f"TRACEBACK: {error_traceback}\n")
                f.write("-" * 80 + "\n")
        except Exception as log_error:
            print(f"⚠️ Could not write to error log: {log_error}")

        # Record error for alerting only for serious errors, not method errors
        if not isinstance(e, Exception.__class__.__bases__[0]):
            try:
                from alerts import alert_manager
                alert_manager.record_error(f"Unhandled exception: {error_msg}", "CRITICAL_ERROR")
            except ImportError:
                pass  # Alerting system not available

        return jsonify({
            "error": "Internal server error",
            "timestamp": timestamp,
            "status": "error",
            "error_id": str(hash(error_msg))[:8]  # Unique error ID for tracking
        }), 500

    except Exception as meta_error:
        # If error handling itself fails, fall back to basic response
        print(f"🔥 META ERROR: Error handler failed: {meta_error}")
        return jsonify({
            "error": "Critical system error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "critical_error"
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
    """BULLETPROOF health check - NEVER crashes, always returns status"""
    # Multiple fallback levels to ensure this endpoint NEVER fails
    try:
        start_time = time.time()

        # Initialize health status
        health_data = {
            "status": "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "MemoryOS-Clean",
            "version": "2.0.0",
            "bulletproof": True
        }

        # Level 1: Test memory file access
        try:
            memory = load_memory()
            memory_accessible = True
            memory_count = len(memory) if memory else 0
        except Exception as mem_error:
            memory_accessible = False
            memory_count = 0
            health_data["memory_error"] = str(mem_error)

        # Level 2: Test memory write capability
        try:
            test_write = os.access(MEMORY_FILE, os.W_OK) if os.path.exists(MEMORY_FILE) else False
        except Exception:
            test_write = False

        # Level 3: Calculate response time
        try:
            response_time_ms = round((time.time() - start_time) * 1000, 2)
        except Exception:
            response_time_ms = 999  # Fallback value

        # Level 4: Determine overall health with multiple checks
        healthy_checks = 0
        total_checks = 3

        if memory_accessible:
            healthy_checks += 1
        if test_write:
            healthy_checks += 1
        if response_time_ms < 1000:
            healthy_checks += 1

        # Calculate health status
        if healthy_checks == total_checks:
            status = "healthy"
        elif healthy_checks >= 1:
            status = "degraded"
        else:
            status = "unhealthy"

        # Build comprehensive health data
        health_data.update({
            "status": status,
            "response_time_ms": response_time_ms,
            "health_score": f"{healthy_checks}/{total_checks}",
            "checks": {
                "memory_file_accessible": memory_accessible,
                "memory_file_writable": test_write,
                "response_time_ok": response_time_ms < 1000
            },
            "metrics": {
                "memory_entries": memory_count,
                "memory_file_exists": os.path.exists(MEMORY_FILE) if MEMORY_FILE else False,
                "memory_file_size_bytes": os.path.getsize(MEMORY_FILE) if os.path.exists(MEMORY_FILE) else 0
            }
        })

        # Log health check (with fallback)
        try:
            logger.info(f"HEALTH CHECK: {status} - {response_time_ms}ms ({healthy_checks}/{total_checks})")
        except Exception:
            print(f"Health: {status} - {response_time_ms}ms")

        return jsonify(health_data), 200 if status == "healthy" else 503

    except Exception as critical_error:
        # ULTIMATE FALLBACK - If everything fails, still return something
        try:
            logger.error(f"CRITICAL HEALTH CHECK FAILURE: {str(critical_error)}")
        except Exception:
            print(f"🔥 CRITICAL HEALTH FAILURE: {str(critical_error)}")

        return jsonify({
            "status": "critical_failure",
            "error": str(critical_error),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "MemoryOS-Clean",
            "bulletproof": False,
            "message": "Health check failed but system is responding"
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

@app.route('/jav/chat', methods=['POST'])
def jav_chat():
    """Handle Jav chat messages with workspace integration and frustration detection"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context', {})

        if not message:
            return jsonify({"error": "No message provided"}), 400

        # Initialize Jav agent if not available
        try:
            from jav_agent import jav
        except:
            # Create minimal jav object for chat
            class MinimalJav:
                def __init__(self):
                    self.memory_api = "http://0.0.0.0:5000"
            jav = MinimalJav()

        # Process message through Jav chat interface
        from jav_chat import JavChat
        jav_chat_handler = JavChat(jav)

        result = jav_chat_handler.process_command(message, context)

        return jsonify({
            "status": "success",
            "message": result.get("message", "Message processed"),
            "type": result.get("type", "success"),
            "interventions": result.get("interventions", []),
            "suggestions": result.get("suggestions", []),
            "keyboard_hint": result.get("keyboard_hint"),
            "workspace_integration": result.get("workspace_integration", False),
            "response": result,  # For compatibility
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Jav chat error: {e}")

        # Track error for frustration detection
        try:
            from jav_chat import JavChat
            from jav_agent import jav
            jav_chat_handler = JavChat(jav)
            jav_chat_handler.frustration_detector.track_interaction(
                "message", 
                message, 
                False, 
                {"error": str(e), "context": "chat_endpoint_error"}
            )
        except:
            pass  # Don't let tracking errors break the response

        return jsonify({
            "status": "error", 
            "message": f"I encountered an issue, but I'm still here to help: {str(e)}",
            "error": str(e),
            "type": "error",
            "suggestions": ["Try rephrasing your request", "Ask for help with something specific"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/jav/status')
def jav_status():
    """Get Jav agent status"""
    try:
        from jav_agent import jav
        from persistent_memory_engine import persistent_memory

        # Get current state
        audit_result = jav.audit_current_state()

        # Get persistent memory insights
        persistent_insights = persistent_memory.get_cross_project_insights()

        return jsonify({
            "status": "active",
            "agent_version": "1.0.0",
            "current_state": audit_result,
            "config_loaded": bool(jav.me_config),
            "workflows_loaded": len(jav.workflows),
            "persistent_memory": {
                "total_projects": persistent_insights["total_projects"],
                "total_playbooks": persistent_insights["total_playbooks"],
                "global_memory_path": persistent_memory.global_memory_path
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Jav status error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/jav/suggestions')
def jav_suggestions():
    """Get memory-driven suggestions with user context"""
    try:
        from jav_agent import jav

        current_task = request.args.get('task', 'General development')
        context = request.get_json() if request.is_json else None

        suggestions = jav.get_memory_driven_suggestions(current_task, context)

        return jsonify({
            "suggestions": suggestions,
            "task": current_task,
            "user_preferences": {
                "automation_level": jav.user_preferences.get("automation_level", "suggest_only"),
                "show_reasoning": jav.user_preferences.get("suggestion_preferences", {}).get("show_reasoning", True)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/jav/suggestion-response', methods=['POST'])
def handle_suggestion_response():
    """Handle user response to suggestions with learning"""
    try:
        from jav_agent import jav

        data = request.get_json()
        if not data:
            return jsonify({"error": "Request data required"}), 400

        suggestion_id = data.get('suggestion_id')
        response = data.get('response')  # apply, ignore, never_again, etc.
        outcome = data.get('outcome')    # success, failure, partial (optional)

        if not suggestion_id or not response:
            return jsonify({"error": "suggestion_id and response required"}), 400

        result = jav.process_user_response(suggestion_id, response, outcome)

        return jsonify({
            "status": "success",
            "result": result,
            "message": f"Response '{response}' processed and learning updated",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Suggestion response error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/jav/suggestion-reasoning/<suggestion_id>')
def get_suggestion_reasoning(suggestion_id: str):
    """Get full transparency info for a suggestion"""
    try:
        from jav_chat import JavChat
        from jav_agent import jav

        chat = JavChat(jav)
        reasoning = chat.get_suggestion_reasoning(suggestion_id)

        return jsonify({
            "reasoning": reasoning,
            "editable": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Suggestion reasoning error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/jav/preferences', methods=['GET', 'POST'])
def jav_preferences():
    """Get or update user preferences"""
    try:
        from jav_agent import jav

        if request.method == 'GET':
            return jsonify({
                "preferences": jav.user_preferences,
                "learned_patterns_count": len(jav.learned_patterns.get("successful_automations", {})),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        elif request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({"error": "Preferences data required"}), 400

            # Update preferences
            jav.user_preferences.update(data)
            jav.save_user_preferences(jav.user_preferences)

            return jsonify({
                "status": "success",
                "message": "Preferences updated",
                "preferences": jav.user_preferences,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    except Exception as e:
        logger.error(f"Preferences error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/jav/apply-automation', methods=['POST'])
def apply_automation():
    """Apply an automation playbook"""
    try:
        from jav_agent import jav

        data = request.get_json()
        if not data or 'playbook_id' not in data:
            return jsonify({"error": "playbook_id required"}), 400

        playbook_id = data['playbook_id']
        context = data.get('context', {})

        result = jav.apply_automation(playbook_id, context)

        return jsonify({
            "status": "success",
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Apply automation error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/jav/create-playbook', methods=['POST'])
def create_playbook():
    """Create a new automation playbook"""
    try:
        from jav_agent import jav

        data = request.get_json()
        if not data:
            return jsonify({"error": "Request data required"}), 400

        problem_description = data.get('problem_description', '')
        solution_steps = data.get('solution_steps', [])
        success = data.get('success', True)

        if not problem_description or not solution_steps:
            return jsonify({"error": "problem_description and solution_steps required"}), 400

        playbook = jav.create_automation_from_solution(problem_description, solution_steps, success)

        return jsonify({
            "status": "success",
            "playbook": {
                "id": playbook.id,
                "name": playbook.name,
                "description": playbook.description,
                "auto_apply": playbook.auto_apply
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Create playbook error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/jav/playbooks')
def list_playbooks():
    """List all automation playbooks"""
    try:
        from persistent_memory_engine import persistent_memory

        playbooks = []
        for playbook in persistent_memory.playbooks:
            if not playbook.retired:
                playbooks.append({
                    "id": playbook.id,
                    "name": playbook.name,
                    "description": playbook.description,
                    "success_rate": playbook.success_rate,
                    "usage_count": playbook.usage_count,
                    "auto_apply": playbook.auto_apply,
                    "tags": playbook.tags,
                    "project_origin": playbook.project_origin,
                    "created_at": playbook.created_at,
                    "last_used": playbook.last_used
                })

        return jsonify({
            "playbooks": playbooks,
            "total": len(playbooks),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"List playbooks error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/jav/retire-playbook', methods=['POST'])
def retire_playbook():
    """Retire an outdated playbook"""
    try:
        from persistent_memory_engine import persistent_memory

        data = request.get_json()
        if not data or 'playbook_id' not in data:
            return jsonify({"error": "playbook_id required"}), 400

        playbook_id = data['playbook_id']
        reason = data.get('reason', 'User requested')

        persistent_memory.retire_playbook(playbook_id, reason)

        return jsonify({
            "status": "success",
            "message": f"Playbook {playbook_id} retired",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Retire playbook error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/jav/cross-project-insights')
def cross_project_insights():
    """Get cross-project insights and patterns"""
    try:
        from persistent_memory_engine import persistent_memory

        insights = persistent_memory.get_cross_project_insights()

        return jsonify({
            "insights": insights,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Cross-project insights error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/bible/deviations')
def get_bible_deviations():
    """Get tracked bible deviations"""
    try:
        from bible_evolution_engine import bible_evolution

        bible_file = request.args.get('bible_file')
        section = request.args.get('section')

        deviations = bible_evolution.deviations

        # Filter if requested
        if bible_file:
            deviations = [d for d in deviations if d.bible_file == bible_file]
        if section:
            deviations = [d for d in deviations if d.section == section]

        # Convert to dict for JSON serialization
        deviations_data = [
            {
                "id": d.id,
                "bible_file": d.bible_file,
                "section": d.section,
                "documented_process": d.documented_process,
                "actual_process": d.actual_process,
                "frequency": d.frequency,
                "first_seen": d.first_seen,
                "last_seen": d.last_seen,
                "success_rate": d.success_rate,
                "user_approved": d.user_approved,
                "override_reason": d.override_reason
            }
            for d in deviations
        ]

        return jsonify({
            "deviations": deviations_data,
            "total": len(deviations_data),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Bible deviations error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/bible/track-deviation', methods=['POST'])
def track_bible_deviation():
    """Track a new bible deviation"""
    try:
        from bible_evolution_engine import bible_evolution

        data = request.get_json()
        if not data:
            return jsonify({"error": "Request data required"}), 400

        required_fields = ["bible_file", "section", "documented_process", "actual_process", "context"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        deviation_id = bible_evolution.track_deviation(
            bible_file=data["bible_file"],
            section=data["section"],
            documented_process=data["documented_process"],
            actual_process=data["actual_process"],
            context=data["context"],
            override_reason=data.get("override_reason")
        )

        return jsonify({
            "status": "success",
            "deviation_id": deviation_id,
            "message": "Deviation tracked successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Track deviation error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/bible/analyze-patterns')
def analyze_bible_patterns():
    """Analyze deviation patterns for amendment suggestions"""
    try:
        from bible_evolution_engine import bible_evolution

        analysis = bible_evolution.analyze_deviation_patterns()

        return jsonify({
            "analysis": analysis,
            "summary": {
                "high_frequency_count": len(analysis["high_frequency_deviations"]),
                "successful_overrides_count": len(analysis["successful_overrides"]),
                "systematic_drift_count": len(analysis["systematic_drift"])
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Analyze patterns error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/bible/propose-amendment', methods=['POST'])
def propose_bible_amendment():
    """Propose an amendment to bible documentation"""
    try:
        from bible_evolution_engine import bible_evolution

        data = request.get_json()
        if not data:
            return jsonify({"error": "Request data required"}), 400

        required_fields = ["bible_file", "section", "current_text", "proposed_text", "reasoning"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        amendment_id = bible_evolution.propose_amendment(
            bible_file=data["bible_file"],
            section=data["section"],
            current_text=data["current_text"],
            proposed_text=data["proposed_text"],
            reasoning=data["reasoning"],
            supporting_deviations=data.get("supporting_deviations", [])
        )

        return jsonify({
            "status": "success",
            "amendment_id": amendment_id,
            "message": "Amendment proposed successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Propose amendment error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/bible/review-session')
def generate_bible_review_session():
    """Generate comprehensive bible review session"""
    try:
        from bible_integration import bible_integration

        review_session = bible_integration.generate_team_review_session()

        return jsonify({
            "review_session": review_session,
            "status": "generated",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Review session error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/bible/amendments')
def get_bible_amendments():
    """Get proposed bible amendments"""
    try:
        from bible_evolution_engine import bible_evolution

        status_filter = request.args.get('status')  # draft, reviewed, approved, etc.

        amendments = bible_evolution.amendments

        if status_filter:
            amendments = [a for a in amendments if a.status == status_filter]

        amendments_data = [
            {
                "id": a.id,
                "bible_file": a.bible_file,
                "section": a.section,
                "current_text": a.current_text[:200] + "..." if len(a.current_text) > 200 else a.current_text,
                "proposed_text": a.proposed_text[:200] + "..." if len(a.proposed_text) > 200 else a.proposed_text,
                "reasoning": a.reasoning,
                "confidence": a.confidence,
                "status": a.status,
                "created_at": a.created_at,
                "supporting_deviations_count": len(a.supporting_deviations)
            }
            for a in amendments
        ]

        return jsonify({
            "amendments": amendments_data,
            "total": len(amendments_data),
            "by_status": {
                "draft": len([a for a in amendments if a.status == "draft"]),
                "reviewed": len([a for a in amendments if a.status == "reviewed"]),
                "approved": len([a for a in amendments if a.status == "approved"]),
                "implemented": len([a for a in amendments if a.status == "implemented"])
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Get amendments error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/bible/onboarding-brief')
def get_onboarding_brief():
    """Get onboarding brief for new users"""
    try:
        from bible_evolution_engine import bible_evolution

        user_type = request.args.get('user_type', 'new_user')

        brief = bible_evolution.generate_onboarding_brief(user_type)

        return jsonify({
            "onboarding_brief": brief,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Onboarding brief error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/bible/compliance-report')
def get_compliance_report():
    """Get bible compliance report"""
    try:
        from bible_evolution_engine import bible_evolution

        bible_file = request.args.get('bible_file', 'AGENT_BIBLE.md')

        compliance_report = bible_evolution.monitor_compliance(bible_file)

        return jsonify({
            "compliance_report": compliance_report,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Compliance report error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/bible/versions')
def get_bible_versions():
    """Get bible version history"""
    try:
        from bible_evolution_engine import bible_evolution

        bible_file = request.args.get('bible_file')

        versions = bible_evolution.versions

        if bible_file:
            versions = [v for v in versions if v.bible_file == bible_file]

        versions_data = [
            {
                "version": v.version,
                "bible_file": v.bible_file,
                "changes": v.changes,
                "changelog": v.changelog,
                "created_at": v.created_at,
                "prompted_by": v.prompted_by,
                "context_sessions": v.context_sessions
            }
            for v in versions
        ]

        return jsonify({
            "versions": versions_data,
            "total": len(versions_data),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Get versions error: {e}")
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

def bulletproof_main():
    """Bulletproof main function with comprehensive error handling"""
    try:
        # Ensure logs directory exists
        try:
            os.makedirs('logs', exist_ok=True)
        except Exception as e:
            print(f"⚠️ Could not create logs directory: {e}")

        # Log startup with bulletproof logger
        if BULLETPROOF_LOGGING:
            bulletproof_logger.log_info("Starting MemoryOS with bulletproof safeguards")

        # Ensure memory file exists
        if not os.path.exists(MEMORY_FILE):
            try:
                save_memory([])
                print(f"✅ Created memory file: {MEMORY_FILE}")
                if BULLETPROOF_LOGGING:
                    bulletproof_logger.log_info(f"Created new memory file: {MEMORY_FILE}")
            except Exception as e:
                error_msg = f"CRITICAL: Could not create memory file: {e}"
                print(f"❌ {error_msg}")
                if BULLETPROOF_LOGGING:
                    bulletproof_logger.log_error("Failed to create memory file", e)
                raise

        # Initialize alerting with error handling
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

        except ImportError as e:
            print("⚠️  Alerting system not available")
            if BULLETPROOF_LOGGING:
                bulletproof_logger.log_warning(f"Alerting system not available: {e}")

        # Print startup information
        startup_info = [
            "🚀 Starting MemoryOS Clean with BULLETPROOF safeguards...",
            f"📁 Memory file: {MEMORY_FILE}",
            f"🔑 API Key required for POST /memory",
            f"📊 Logs: memoryos.log + logs/",
            f"🏥 Health check: /health (bulletproof)",
            f"🛡️  Error handling: Enhanced with bulletproof logging",
            f"🧪 Tests: Run 'python -m pytest test_memoryos.py' before deploy"
        ]

        for info in startup_info:
            print(info)
            if BULLETPROOF_LOGGING:
                bulletproof_logger.log_info(info.replace("🚀", "").replace("📁", "").replace("🔑", "").replace("📊", "").replace("🏥", "").replace("🛡️", "").replace("🧪", "").strip())

        # Start the Flask app with bulletproof error handling
        try:
            app.run(host='0.0.0.0', port=5000, debug=False)
        except Exception as e:
            error_msg = f"CRITICAL: Flask app failed to start: {e}"
            print(f"💥 {error_msg}")
            if BULLETPROOF_LOGGING:
                bulletproof_logger.log_error("Flask app startup failed", e, include_traceback=True)
            raise

    except KeyboardInterrupt:
        print("\n🛑 MemoryOS shutdown by user")
        if BULLETPROOF_LOGGING:
            bulletproof_logger.log_info("MemoryOS shutdown by user interrupt")

    except Exception as critical_error:
        error_msg = f"CRITICAL SYSTEM FAILURE: {critical_error}"
        print(f"💥 {error_msg}")
        print(f"📍 TRACEBACK: {traceback.format_exc()}")

        if BULLETPROOF_LOGGING:
            bulletproof_logger.log_error("Critical system failure during startup", critical_error, include_traceback=True)

        # Write emergency error log
        try:
            with open('emergency_startup_failure.log', 'a') as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] CRITICAL FAILURE\n")
                f.write(f"Error: {error_msg}\n")
                f.write(f"Traceback: {traceback.format_exc()}\n")
                f.write("-" * 80 + "\n")
        except Exception:
            pass  # Even emergency logging can fail

        # Exit with error code
        import sys
        sys.exit(1)

if __name__ == '__main__':
    bulletproof_main()