
from flask import Blueprint, jsonify
import json
import os

task_output_bp = Blueprint("task_output", __name__)

@task_output_bp.route("/task-output")
def task_output():
    try:
        # Use absolute path to ensure we find the file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        task_output_file = os.path.join(base_dir, "task_output.json")
        
        with open(task_output_file, 'r') as f:
            data = json.load(f)
        
        # Return the latest result if it's a list, otherwise return the data
        if isinstance(data, list) and data:
            return jsonify(data[-1])
        else:
            return jsonify(data)
            
    except FileNotFoundError:
        return jsonify({"error": "Task output file not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in task output file"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
