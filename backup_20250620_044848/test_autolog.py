
import requests
import json

# Test the intelligent auto-logging system
BASE_URL = "http://localhost"

def test_passive_logging():
    """Test passive auto-logging with various scenarios"""
    
    test_scenarios = [
        {
            "name": "Bug Fix Scenario",
            "data": {
                "input": "Debugging API endpoint returning 500 error",
                "output": "Fixed authentication header validation, endpoint now working",
                "topic": "API Bug Fix",
                "type": "BugFix",
                "category": "system"
            }
        },
        {
            "name": "Low Importance Test (should be skipped)",
            "data": {
                "input": "Simple test",
                "output": "Test passed",
                "topic": "Basic test",
                "category": "test"
            }
        },
        {
            "name": "Integration Milestone",
            "data": {
                "input": "Integrating GPT with Flask memory system",
                "output": "Successfully completed integration with auto-logging features",
                "topic": "GPT Integration Milestone",
                "type": "Milestone",
                "category": "integration"
            }
        },
        {
            "name": "Minimal Input (Auto-generate)",
            "data": {
                "input": "Testing intelligent passive logging system implementation"
            }
        }
    ]
    
    print("🧪 Testing Intelligent Auto-Logging System")
    print("=" * 50)
    
    for scenario in test_scenarios:
        print(f"\n📋 Test: {scenario['name']}")
        
        try:
            # Test via /autolog endpoint
            response = requests.post(f"{BASE_URL}/autolog", 
                                   json=scenario['data'],
                                   headers={'Content-Type': 'application/json'})
            result = response.json()
            
            if response.status_code == 200:
                if "Skipped" in result.get('status', ''):
                    print(f"   ⏭️  {result['reason']}")
                else:
                    print(f"   ✅ {result['status']}")
                    print(f"   📊 Importance Score: {result['entry'].get('importance_score', 'N/A')}")
                    print(f"   🏷️  Tags: {result['entry'].get('tags', [])}")
                    print(f"   📝 Context: {result['entry'].get('context', 'N/A')[:60]}...")
            else:
                print(f"   ❌ Error: {result}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n📊 Testing complete! Check /memory endpoint to see results.")

if __name__ == "__main__":
    test_passive_logging()
