
"""
MemoryOS AI Provider Setup
Configure and test different AI providers for persistent memory awareness
"""

import os
import json
import requests
from typing import Dict, Any

def setup_anthropic():
    """Setup Anthropic Claude"""
    print("🤖 Setting up Anthropic Claude...")
    api_key = input("Enter your Anthropic API key: ").strip()
    
    if api_key:
        os.environ['AI_PROVIDER'] = 'anthropic'
        os.environ['AI_API_KEY'] = api_key
        print("✅ Anthropic configured")
        return True
    return False

def setup_groq():
    """Setup Groq (fast inference)"""
    print("⚡ Setting up Groq...")
    api_key = input("Enter your Groq API key: ").strip()
    
    if api_key:
        os.environ['AI_PROVIDER'] = 'groq'
        os.environ['AI_API_KEY'] = api_key
        print("✅ Groq configured")
        return True
    return False

def setup_together():
    """Setup Together AI"""
    print("🔗 Setting up Together AI...")
    api_key = input("Enter your Together AI API key: ").strip()
    
    if api_key:
        os.environ['AI_PROVIDER'] = 'together'
        os.environ['AI_API_KEY'] = api_key
        print("✅ Together AI configured")
        return True
    return False

def setup_local_ollama():
    """Setup local Ollama"""
    print("🏠 Setting up local Ollama...")
    print("Make sure Ollama is installed and running on port 11434")
    
    response = input("Do you have Ollama running? (y/n): ").strip().lower()
    if response == 'y':
        os.environ['AI_PROVIDER'] = 'local'
        print("✅ Local Ollama configured")
        return True
    else:
        print("Install Ollama first: https://ollama.ai")
        return False

def test_ai_setup():
    """Test the configured AI provider"""
    try:
        from intelligent_agent import MemoryAwareAgent
        
        print("\n🧪 Testing AI configuration...")
        agent = MemoryAwareAgent()
        
        test_result = agent.query_ai("Hello, can you see my memory context?")
        
        if test_result['status'] == 'success':
            print("✅ AI agent is working!")
            print(f"Provider: {agent.ai_provider}")
            print(f"Model: {agent.model.get('model', 'unknown')}")
            print(f"Context loaded: {test_result.get('context_loaded', 0)} memories")
            print(f"\nResponse: {test_result['response'][:200]}...")
            return True
        else:
            print(f"❌ Test failed: {test_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        return False

def save_config():
    """Save configuration to .env file"""
    config = {
        'AI_PROVIDER': os.getenv('AI_PROVIDER', ''),
        'AI_API_KEY': os.getenv('AI_API_KEY', ''),
        'JAVLIN_API_KEY': os.getenv('JAVLIN_API_KEY', 'default-key-change-me')
    }
    
    with open('.env', 'w') as f:
        for key, value in config.items():
            if value:
                f.write(f"{key}={value}\n")
    
    print("💾 Configuration saved to .env")

def main():
    """Main setup menu"""
    print("🧠 MemoryOS AI Provider Setup")
    print("=" * 40)
    
    providers = {
        '1': ('Anthropic Claude (Recommended)', setup_anthropic),
        '2': ('Groq (Fastest)', setup_groq),
        '3': ('Together AI (Open Source)', setup_together),
        '4': ('Local Ollama (Private)', setup_local_ollama)
    }
    
    print("\nSelect AI Provider:")
    for key, (name, _) in providers.items():
        print(f"{key}. {name}")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice in providers:
        name, setup_func = providers[choice]
        print(f"\n📋 Setting up {name}...")
        
        if setup_func():
            save_config()
            
            if test_ai_setup():
                print("\n🎉 Setup complete! Your AI agent is ready.")
                print("\nNext steps:")
                print("1. Run: python intelligent_agent.py")
                print("2. Or use the /ai/query API endpoint")
                print("3. Your AI maintains full memory awareness!")
            else:
                print("\n⚠️  Setup completed but test failed. Check your API key.")
        else:
            print("\n❌ Setup failed. Please try again.")
    else:
        print("Invalid choice. Please run again.")

if __name__ == "__main__":
    main()
