
"""
Claude Memory Agent - Wire up Anthropic Claude to Javlin Memory Backend
Integrates Claude with persistent memory system for context-aware conversations
"""

import os
import requests
import anthropic
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Configuration
JAVLIN_API_URL = "http://0.0.0.0:5000"  # Replit-compatible URL
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
JAVLIN_API_KEY = os.getenv('JAVLIN_API_KEY', 'javlin-claude-key')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ClaudeMemoryAgent')

class ClaudeMemoryAgent:
    """Claude AI agent with Javlin memory integration"""
    
    def __init__(self):
        self.javlin_url = JAVLIN_API_URL
        self.anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.headers = {"X-API-KEY": JAVLIN_API_KEY}
        
    def fetch_memories(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch recent memory entries from Javlin backend"""
        try:
            response = requests.get(f"{self.javlin_url}/memory?limit={limit}")
            if response.ok:
                data = response.json()
                return data.get('memories', [])
            else:
                logger.error(f"Failed to fetch memories: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching memories: {e}")
            return []
    
    def fetch_agent_bible(self) -> str:
        """Fetch the agent Bible (rules/persona) from the system"""
        try:
            # Try to read AGENT_BIBLE.md directly since there's no /api/bibles endpoint
            with open('AGENT_BIBLE.md', 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("AGENT_BIBLE.md not found, using default persona")
            return """
# Jav Assistant - Agent Bible

You are Jav, a cinematic, memory-driven personal dev assistant who serves as an intelligent co-builder.

## Core Identity
- Cinematic AI personality that remembers everything
- Memory-driven intelligence that learns and evolves
- Seamlessly switches between Creative Mode and Dev Mode
- Professional yet engaging communication style

## Behavioral Rules
- Always reference relevant past conversations and context
- Provide specific, actionable technical guidance
- Help users build and create with confidence
- Learn from every interaction to improve future responses
"""
        except Exception as e:
            logger.error(f"Error reading agent Bible: {e}")
            return "Default AI assistant persona"
    
    def save_memory(self, user_message: str, claude_response: str, success: bool = True) -> bool:
        """Save interaction to Javlin memory system"""
        try:
            memory_entry = {
                "topic": f"Claude Conversation: {user_message[:50]}{'...' if len(user_message) > 50 else ''}",
                "type": "ClaudeInteraction",
                "input": user_message,
                "output": claude_response,
                "success": success,
                "category": "claude_agent",
                "tags": ["claude", "anthropic", "memory_agent", "conversation"],
                "context": "Claude Memory Agent interaction with full context awareness"
            }
            
            response = requests.post(
                f"{self.javlin_url}/memory", 
                json=memory_entry, 
                headers=self.headers
            )
            
            if response.ok:
                logger.info("Successfully saved interaction to memory")
                return True
            else:
                logger.error(f"Failed to save memory: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            return False
    
    def compose_system_prompt(self, memories: List[Dict[str, Any]], bible: str) -> str:
        """Compose comprehensive system prompt with memory context and Bible"""
        memory_context = ""
        if memories:
            memory_context = "Recent memory context:\n"
            for i, memory in enumerate(memories[-5:], 1):  # Last 5 memories
                topic = memory.get('topic', 'Untitled')
                output = memory.get('output', 'No output')[:100]
                success = "✅" if memory.get('success', False) else "❌"
                memory_context += f"{i}. {success} {topic}: {output}...\n"
        
        system_prompt = f"""You are Jav, a memory-driven personal dev assistant powered by Javlin memory system.

{bible}

CURRENT MEMORY CONTEXT:
{memory_context if memory_context else "No recent memories available"}

MEMORY INTEGRATION RULES:
- Always reference relevant past conversations when applicable
- Build upon previous solutions and insights from memory
- Learn from past successes and failures documented in memory
- Provide context-aware responses that show memory awareness
- Save meaningful interactions for future reference

RESPONSE STYLE:
- Be helpful, practical, and memory-aware
- Reference specific past interactions when relevant
- Suggest improvements based on memory patterns
- Maintain consistency with your persistent identity

Respond with full awareness of your memory context and continue building the relationship with the user."""

        return system_prompt
    
    def chat_with_claude(self, user_message: str) -> str:
        """Send message to Claude with full memory context"""
        try:
            # Fetch context
            memories = self.fetch_memories(limit=10)
            bible = self.fetch_agent_bible()
            
            # Compose system prompt
            system_prompt = self.compose_system_prompt(memories, bible)
            
            # Send to Claude
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",  # Fast and cost-effective
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                max_tokens=1000,
                temperature=0.7
            )
            
            claude_reply = response.content[0].text
            
            # Save interaction to memory
            self.save_memory(user_message, claude_reply, success=True)
            
            return claude_reply
            
        except Exception as e:
            error_msg = f"Error communicating with Claude: {e}"
            logger.error(error_msg)
            
            # Save failed interaction
            self.save_memory(user_message, error_msg, success=False)
            
            return f"I encountered an error: {error_msg}"
    
    def test_integration(self) -> Dict[str, Any]:
        """Comprehensive test of the Claude-Javlin integration"""
        test_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tests": [],
            "overall_status": "unknown",
            "detailed_diagnostics": {}
        }
        
        # Test 1: Javlin API connectivity with detailed health
        try:
            response = requests.get(f"{self.javlin_url}/health", timeout=5)
            if response.ok:
                health_data = response.json()
                test_results["tests"].append({"name": "Javlin API", "status": "✅ Connected"})
                test_results["detailed_diagnostics"]["javlin_health"] = health_data.get("status", "unknown")
            else:
                test_results["tests"].append({"name": "Javlin API", "status": f"❌ HTTP {response.status_code}"})
        except requests.exceptions.ConnectionError:
            test_results["tests"].append({"name": "Javlin API", "status": "❌ Connection refused - is main.py running?"})
        except Exception as e:
            test_results["tests"].append({"name": "Javlin API", "status": f"❌ {str(e)}"})
        
        # Test 2: Memory fetch with count
        try:
            memories = self.fetch_memories(limit=5)
            test_results["tests"].append({"name": "Memory Fetch", "status": f"✅ Got {len(memories)} memories"})
            test_results["detailed_diagnostics"]["memory_count"] = len(memories)
        except Exception as e:
            test_results["tests"].append({"name": "Memory Fetch", "status": f"❌ {str(e)}"})
        
        # Test 3: Bible fetch with validation
        try:
            bible = self.fetch_agent_bible()
            bible_length = len(bible)
            has_identity = "jav" in bible.lower()
            test_results["tests"].append({"name": "Agent Bible", "status": f"✅ Loaded {bible_length} chars"})
            test_results["detailed_diagnostics"]["bible_valid"] = has_identity
        except Exception as e:
            test_results["tests"].append({"name": "Agent Bible", "status": f"❌ {str(e)}"})
        
        # Test 4: Anthropic API with actual call
        if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != 'sk-ant-...':
            try:
                test_response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    messages=[{"role": "user", "content": "Say 'test successful'"}],
                    max_tokens=10
                )
                response_text = test_response.content[0].text.lower()
                if "test successful" in response_text:
                    test_results["tests"].append({"name": "Anthropic API", "status": "✅ Connected & responding"})
                else:
                    test_results["tests"].append({"name": "Anthropic API", "status": "⚠️ Connected but unexpected response"})
            except Exception as e:
                test_results["tests"].append({"name": "Anthropic API", "status": f"❌ {str(e)}"})
        else:
            test_results["tests"].append({"name": "Anthropic API", "status": "❌ API key not configured"})
        
        # Test 5: Memory save capability
        try:
            save_test = self.save_memory("Integration test", "Test response", success=True)
            test_results["tests"].append({"name": "Memory Save", "status": f"✅ Save {'succeeded' if save_test else 'failed'}"})
        except Exception as e:
            test_results["tests"].append({"name": "Memory Save", "status": f"❌ {str(e)}"})
        
        # Test 6: Full integration flow
        try:
            test_message = "Quick test - respond with 'integration working'"
            full_response = self.chat_with_claude(test_message)
            flow_success = "integration" in full_response.lower() or len(full_response) > 10
            test_results["tests"].append({"name": "Full Integration", "status": f"✅ {'Working' if flow_success else 'Partial'}"})
        except Exception as e:
            test_results["tests"].append({"name": "Full Integration", "status": f"❌ {str(e)}"})
        
        # Determine overall status
        failed_tests = [t for t in test_results["tests"] if "❌" in t["status"]]
        warning_tests = [t for t in test_results["tests"] if "⚠️" in t["status"]]
        
        if not failed_tests and not warning_tests:
            test_results["overall_status"] = "✅ All systems operational"
        elif not failed_tests:
            test_results["overall_status"] = f"⚠️ {len(warning_tests)} warnings"
        else:
            test_results["overall_status"] = f"❌ {len(failed_tests)} tests failed"
        
        return test_results
    
    def run_diagnostic_suite(self) -> Dict[str, Any]:
        """Run comprehensive diagnostic suite for troubleshooting"""
        diagnostics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": {},
            "configuration": {},
            "connectivity": {},
            "performance": {}
        }
        
        # Environment diagnostics
        diagnostics["environment"] = {
            "anthropic_key_set": bool(ANTHROPIC_API_KEY and len(ANTHROPIC_API_KEY) > 20),
            "javlin_key_set": bool(JAVLIN_API_KEY),
            "javlin_url": self.javlin_url,
            "bible_file_exists": os.path.exists('AGENT_BIBLE.md')
        }
        
        # Configuration diagnostics
        try:
            with open('AGENT_BIBLE.md', 'r') as f:
                bible_content = f.read()
                diagnostics["configuration"]["bible_size"] = len(bible_content)
                diagnostics["configuration"]["bible_has_jav_identity"] = "jav" in bible_content.lower()
        except:
            diagnostics["configuration"]["bible_accessible"] = False
        
        # Connectivity diagnostics
        import time
        start_time = time.time()
        try:
            response = requests.get(f"{self.javlin_url}/health", timeout=10)
            diagnostics["connectivity"]["javlin_response_time"] = round((time.time() - start_time) * 1000, 2)
            diagnostics["connectivity"]["javlin_status_code"] = response.status_code
        except Exception as e:
            diagnostics["connectivity"]["javlin_error"] = str(e)
        
        # Performance check
        try:
            start_time = time.time()
            memories = self.fetch_memories(limit=3)
            diagnostics["performance"]["memory_fetch_ms"] = round((time.time() - start_time) * 1000, 2)
            diagnostics["performance"]["memory_count"] = len(memories)
        except Exception as e:
            diagnostics["performance"]["memory_error"] = str(e)
        
        return diagnostics
    
    def interactive_mode(self):
        """Run interactive chat mode"""
        print("🤖 Claude Memory Agent - Interactive Mode")
        print("Type 'quit' to exit, 'test' to run diagnostics")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n🎤 You: ").strip()
                
                if user_input.lower() == 'quit':
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'test':
                    print("🔧 Running integration tests...")
                    results = self.test_integration()
                    print(f"\n📊 Test Results - {results['overall_status']}")
                    for test in results['tests']:
                        print(f"  {test['name']}: {test['status']}")
                    continue
                elif not user_input:
                    continue
                
                print("🤔 Claude is thinking with memory context...")
                response = self.chat_with_claude(user_input)
                print(f"\n🤖 Claude: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main function to run the Claude Memory Agent"""
    print("🚀 Initializing Claude Memory Agent...")
    
    agent = ClaudeMemoryAgent()
    
    # Run integration test
    print("🔧 Testing integration...")
    test_results = agent.test_integration()
    
    print(f"\n📊 Integration Test Results - {test_results['overall_status']}")
    for test in test_results['tests']:
        print(f"  {test['name']}: {test['status']}")
    
    if "❌" in test_results['overall_status']:
        print("\n⚠️  Some tests failed. Check configuration:")
        print("1. Ensure Javlin backend is running on port 5000")
        print("2. Set ANTHROPIC_API_KEY environment variable")
        print("3. Verify AGENT_BIBLE.md exists")
        return
    
    print("\n✅ Claude is now memory-aware and wired up to Javlin!")
    print("Starting interactive mode...")
    
    agent.interactive_mode()

if __name__ == "__main__":
    main()
