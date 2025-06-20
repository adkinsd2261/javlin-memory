
"""
Intelligent Memory Agent - Persistent Context Awareness
Replaces ChatGPT with a memory-aware AI that never loses context
"""

import json
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import os

class MemoryAwareAgent:
    def __init__(self, memory_api_base: str = "http://0.0.0.0:5000"):
        self.memory_api_base = memory_api_base
        self.context_window = []
        self.persistent_memory = {}
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Configure AI provider (multiple options)
        self.ai_provider = os.getenv('AI_PROVIDER', 'anthropic')  # anthropic, groq, together, local
        self.api_key = os.getenv('AI_API_KEY')
        self.model = self._get_model_config()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('MemoryAgent')
        
    def _get_model_config(self) -> Dict[str, str]:
        """Get model configuration based on provider"""
        configs = {
            'anthropic': {
                'model': 'claude-3-haiku-20240307',
                'api_url': 'https://api.anthropic.com/v1/messages',
                'headers': {
                    'x-api-key': self.api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json'
                }
            },
            'groq': {
                'model': 'llama3-8b-8192',
                'api_url': 'https://api.groq.com/openai/v1/chat/completions',
                'headers': {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
            },
            'together': {
                'model': 'meta-llama/Llama-3-8b-chat-hf',
                'api_url': 'https://api.together.xyz/v1/chat/completions',
                'headers': {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
            },
            'local': {
                'model': 'llama3',
                'api_url': 'http://0.0.0.0:11434/api/generate',  # Ollama
                'headers': {'Content-Type': 'application/json'}
            }
        }
        return configs.get(self.ai_provider, configs['anthropic'])
    
    def load_persistent_context(self) -> Dict[str, Any]:
        """Load full memory context for awareness"""
        try:
            # Get recent memories
            response = requests.get(f"{self.memory_api_base}/memory?limit=50")
            memories = response.json().get('memories', [])
            
            # Get system stats
            stats_response = requests.get(f"{self.memory_api_base}/stats")
            stats = stats_response.json()
            
            # Build comprehensive context
            context = {
                "session_id": self.session_id,
                "total_memories": stats.get('total_memories', 0),
                "success_rate": stats.get('success_rate', '0%'),
                "recent_memories": memories[-10:],  # Last 10 for immediate context
                "categories": stats.get('categories', {}),
                "types": stats.get('types', {}),
                "system_health": self._get_health_status(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self.persistent_memory = context
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to load context: {e}")
            return {}
    
    def _get_health_status(self) -> Dict[str, Any]:
        """Get current system health"""
        try:
            response = requests.get(f"{self.memory_api_base}/health")
            return response.json()
        except:
            return {"status": "unknown"}
    
    def generate_context_prompt(self, user_input: str) -> str:
        """Generate full context-aware prompt"""
        context = self.load_persistent_context()
        
        # Build comprehensive system prompt
        system_prompt = f"""You are the MemoryOS AI Agent with full persistent awareness.

CURRENT SYSTEM STATE:
- Total memories: {context.get('total_memories', 0)}
- Success rate: {context.get('success_rate', '0%')}
- System health: {context.get('system_health', {}).get('status', 'unknown')}
- Session: {self.session_id}

RECENT MEMORY CONTEXT:
"""
        
        # Add recent memories for context
        recent_memories = context.get('recent_memories', [])
        for memory in recent_memories[-5:]:  # Last 5 memories
            system_prompt += f"- [{memory.get('type', 'Unknown')}] {memory.get('topic', 'No topic')}\n"
        
        system_prompt += f"""
CATEGORY BREAKDOWN:
{json.dumps(context.get('categories', {}), indent=2)}

USER INPUT: {user_input}

Respond with full awareness of the system state and memory context. You maintain persistent knowledge across all interactions."""

        return system_prompt
    
    def query_ai(self, user_input: str) -> Dict[str, Any]:
        """Query AI with full context awareness"""
        try:
            full_prompt = self.generate_context_prompt(user_input)
            
            if self.ai_provider == 'anthropic':
                payload = {
                    "model": self.model['model'],
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": full_prompt}]
                }
            elif self.ai_provider in ['groq', 'together']:
                payload = {
                    "model": self.model['model'],
                    "messages": [{"role": "user", "content": full_prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            elif self.ai_provider == 'local':
                payload = {
                    "model": self.model['model'],
                    "prompt": full_prompt,
                    "stream": False
                }
            
            response = requests.post(
                self.model['api_url'],
                headers=self.model['headers'],
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract response based on provider
                if self.ai_provider == 'anthropic':
                    ai_response = result['content'][0]['text']
                elif self.ai_provider in ['groq', 'together']:
                    ai_response = result['choices'][0]['message']['content']
                elif self.ai_provider == 'local':
                    ai_response = result['response']
                
                # Log this interaction
                self._log_interaction(user_input, ai_response)
                
                return {
                    "status": "success",
                    "response": ai_response,
                    "context_loaded": len(self.persistent_memory),
                    "session_id": self.session_id
                }
            else:
                return {
                    "status": "error",
                    "error": f"AI API error: {response.status_code}",
                    "fallback": "Using memory context without AI generation"
                }
                
        except Exception as e:
            self.logger.error(f"AI query failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "fallback": "AI temporarily unavailable"
            }
    
    def _log_interaction(self, user_input: str, ai_response: str):
        """Log AI interaction to memory system"""
        try:
            memory_entry = {
                "topic": f"AI Agent Interaction - {self.session_id}",
                "type": "Interaction",
                "input": user_input[:200] + "..." if len(user_input) > 200 else user_input,
                "output": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
                "success": True,
                "category": "ai_interaction",
                "tags": ["ai_agent", "conversation", self.ai_provider],
                "session_id": self.session_id,
                "ai_provider": self.ai_provider,
                "context_memories_loaded": len(self.persistent_memory.get('recent_memories', []))
            }
            
            # Post to memory system
            requests.post(
                f"{self.memory_api_base}/memory",
                json=memory_entry,
                headers={"X-API-KEY": os.getenv('JAVLIN_API_KEY', 'default-key-change-me')}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log interaction: {e}")
    
    def continuous_awareness_mode(self):
        """Run in continuous mode with persistent awareness"""
        print(f"🧠 MemoryOS AI Agent - {self.ai_provider.upper()} Model")
        print(f"📊 Loading persistent context...")
        
        context = self.load_persistent_context()
        print(f"✅ Loaded {context.get('total_memories', 0)} memories")
        print(f"🎯 System health: {context.get('system_health', {}).get('status', 'unknown')}")
        print(f"🔑 Session: {self.session_id}")
        print("\nType 'quit' to exit, 'reload' to refresh context")
        print("-" * 50)
        
        while True:
            user_input = input("\n🎤 You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'reload':
                context = self.load_persistent_context()
                print(f"🔄 Reloaded {context.get('total_memories', 0)} memories")
                continue
            elif not user_input:
                continue
            
            print("🤔 Thinking with full memory context...")
            result = self.query_ai(user_input)
            
            if result['status'] == 'success':
                print(f"\n🧠 AI Agent: {result['response']}")
                print(f"\n📊 Context: {result['context_loaded']} memories loaded")
            else:
                print(f"\n❌ Error: {result['error']}")
                if 'fallback' in result:
                    print(f"💡 {result['fallback']}")

# CLI interface
if __name__ == "__main__":
    agent = MemoryAwareAgent()
    agent.continuous_awareness_mode()
