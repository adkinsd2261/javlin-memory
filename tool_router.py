
#!/usr/bin/env python3
"""
Tool Router for Javlin Memory System
Intelligently routes commands to appropriate handlers based on command patterns
"""

import re
import requests
import json
from typing import Dict, Any, Optional
from urllib.parse import urljoin

class ToolRouter:
    def __init__(self, javlin_api_base: str = "https://javlin-core.replit.app"):
        self.javlin_api_base = javlin_api_base
        
        # Define command patterns for different routing destinations
        self.javlin_patterns = [
            r'^/memory\b',
            r'^/digest\b',
            r'^/autolog\b',
            r'^/feedback\b',
            r'^/context\b',
            r'^/stats\b',
            r'^/insights\b',
            r'^/unreviewed\b',
            r'^/build-state\b',
            r'^/daily-focus\b',
            r'^/version\b',
            r'^/commit-log\b',
            r'^/train-models\b',
            r'^/config\b',
            r'^/autolog-trace\b'
        ]
        
        self.web_search_patterns = [
            r'^search\s+',
            r'^docs\s+',
            r'^lookup\s+',
            r'^find\s+',
            r'^google\s+',
            r'^wiki\s+',
            r'^stackoverflow\s+',
            r'^github\s+search',
            r'^how\s+to\s+',
            r'^what\s+is\s+',
            r'^explain\s+'
        ]
    
    def route_command(self, command: str) -> str:
        """
        Route a command to the appropriate handler
        
        Args:
            command: The input command string
            
        Returns:
            String indicating the routing destination
        """
        command_clean = command.strip()
        
        # Check for Javlin API patterns
        for pattern in self.javlin_patterns:
            if re.match(pattern, command_clean, re.IGNORECASE):
                return "javlin_api"
        
        # Check for web search patterns
        for pattern in self.web_search_patterns:
            if re.match(pattern, command_clean, re.IGNORECASE):
                return "web_search_tool"
        
        # Default to internal handling
        return "default_internal"
    
    def execute_javlin_command(self, command: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Execute a command against the Javlin API
        
        Args:
            command: The command to execute (e.g., "/memory", "/digest")
            headers: Optional headers for authentication
            
        Returns:
            API response as dictionary
        """
        try:
            # Extract endpoint from command
            parts = command.strip().split()
            endpoint = parts[0].lstrip('/')
            
            # Handle query parameters if present
            query_params = {}
            if len(parts) > 1:
                # Simple query parameter parsing (extend as needed)
                for part in parts[1:]:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        query_params[key] = value
            
            url = urljoin(self.javlin_api_base, endpoint)
            
            response = requests.get(url, params=query_params, headers=headers or {})
            response.raise_for_status()
            
            return {
                "status": "success",
                "data": response.json(),
                "url": url
            }
            
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "url": url if 'url' in locals() else None
            }
    
    def execute_web_search(self, command: str) -> Dict[str, Any]:
        """
        Mock web search handler (would integrate with actual search API)
        
        Args:
            command: The search command
            
        Returns:
            Mock search results
        """
        # Extract search query
        search_query = re.sub(r'^(search|docs|lookup|find|google|wiki|stackoverflow|github\s+search|how\s+to|what\s+is|explain)\s+', 
                             '', command, flags=re.IGNORECASE).strip()
        
        # Mock search response (replace with actual search integration)
        return {
            "status": "success",
            "tool": "web_search",
            "query": search_query,
            "results": [
                {
                    "title": f"Search result for: {search_query}",
                    "url": f"https://example.com/search?q={search_query.replace(' ', '+')}",
                    "snippet": f"Mock search result snippet for '{search_query}'"
                }
            ],
            "note": "This is a mock response. Integrate with actual search API."
        }
    
    def execute_internal_command(self, command: str) -> Dict[str, Any]:
        """
        Handle internal/default commands
        
        Args:
            command: The command to handle internally
            
        Returns:
            Internal command response
        """
        return {
            "status": "handled_internally",
            "command": command,
            "handler": "default_internal",
            "message": f"Command '{command}' processed by internal handler"
        }
    
    def process_command(self, command: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Full command processing pipeline
        
        Args:
            command: The input command
            headers: Optional headers for API calls
            
        Returns:
            Complete response with routing and execution details
        """
        route_destination = self.route_command(command)
        
        result = {
            "original_command": command,
            "routed_to": route_destination,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
        
        if route_destination == "javlin_api":
            result.update(self.execute_javlin_command(command, headers))
        elif route_destination == "web_search_tool":
            result.update(self.execute_web_search(command))
        else:
            result.update(self.execute_internal_command(command))
        
        return result


def main():
    """Example usage and testing"""
    router = ToolRouter()
    
    # Test commands
    test_commands = [
        "/memory",
        "/digest",
        "/stats category=test",
        "search python flask tutorial",
        "docs flask authentication", 
        "lookup replit deployment",
        "how to configure flask app",
        "what is REST API",
        "help",
        "status",
        "/autolog",
        "github search flask examples",
        "/feedback",
        "explain dependency injection"
    ]
    
    print("🔀 Tool Router Testing")
    print("=" * 50)
    
    for command in test_commands:
        route = router.route_command(command)
        print(f"Command: '{command}'")
        print(f"  → Routed to: {route}")
        
        # Demonstrate full processing for a few examples
        if command in ["/memory", "search python flask tutorial", "help"]:
            print("  → Full processing:")
            result = router.process_command(command)
            print(f"     Status: {result.get('status', 'N/A')}")
            if 'data' in result:
                print(f"     Data keys: {list(result['data'].keys()) if isinstance(result['data'], dict) else 'N/A'}")
            elif 'query' in result:
                print(f"     Search query: {result['query']}")
            elif 'message' in result:
                print(f"     Message: {result['message']}")
        print()
    
    print("🧪 Unit Tests")
    print("=" * 50)
    
    # Basic unit tests
    def test_javlin_routing():
        assert router.route_command("/memory") == "javlin_api"
        assert router.route_command("/digest") == "javlin_api"
        assert router.route_command("/stats") == "javlin_api"
        print("✅ Javlin API routing tests passed")
    
    def test_web_search_routing():
        assert router.route_command("search something") == "web_search_tool"
        assert router.route_command("docs flask") == "web_search_tool"
        assert router.route_command("how to deploy") == "web_search_tool"
        print("✅ Web search routing tests passed")
    
    def test_default_routing():
        assert router.route_command("help") == "default_internal"
        assert router.route_command("status") == "default_internal"
        assert router.route_command("random command") == "default_internal"
        print("✅ Default routing tests passed")
    
    try:
        test_javlin_routing()
        test_web_search_routing()
        test_default_routing()
        print("\n🎉 All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    
    print("\n📋 Summary:")
    print("- Javlin API commands: /memory, /digest, /stats, etc.")
    print("- Web search commands: search, docs, lookup, how to, etc.")
    print("- Default internal: everything else")
    print("\nRouter is ready for integration!")


if __name__ == "__main__":
    main()
