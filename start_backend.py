"""
Simple Backend Starter
Starts the Flask backend with basic error handling
"""

import os
import sys

def start_backend():
    """Start the backend server"""
    print("🚀 Starting MemoryOS Backend...")
    
    # Check if main.py exists
    if not os.path.exists('main.py'):
        print("❌ main.py not found!")
        return False
    
    # Try to start the server
    try:
        os.system('python main.py')
        return True
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped by user")
        return True
    except Exception as e:
        print(f"❌ Backend failed to start: {e}")
        return False

if __name__ == "__main__":
    start_backend()