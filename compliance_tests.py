
#!/usr/bin/env python3
"""
Comprehensive E2E Tests for Universal Compliance Enforcement

Tests all output channels and validates compliance middleware enforcement
across the entire MemoryOS system.

BEHAVIORAL AUTHORITY: AGENT_BIBLE.md, PRODUCT_BIBLE.md
"""

import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from compliance_middleware import (
    UniversalComplianceMiddleware, 
    OutputChannel, 
    ComplianceLevel,
    OutputContext,
    send_user_output,
    log_and_respond,
    api_output,
    ui_output
)

class TestUniversalCompliance(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.middleware = UniversalComplianceMiddleware(self.test_dir)
        
        # Create test context
        self.test_context = OutputContext(
            channel=OutputChannel.API_RESPONSE,
            source_function="test_function",
            source_file="test_file.py",
            source_line=42,
            timestamp="2025-01-20T12:00:00Z"
        )
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_action_language_detection(self):
        """Test detection of action language patterns"""
        # Test cases with action language
        action_phrases = [
            "I'll implement this feature",
            "I am running the system",
            "I will deploy the application", 
            "I have completed the task",
            "I'm processing the request",
            "I've finished the setup",
            "The feature is complete",
            "System is now ready",
            "API is working perfectly",
            "Task has been finished"
        ]
        
        for phrase in action_phrases:
            result = self.middleware.validate_output(phrase, self.test_context)
            self.assertTrue(len(result.violations) > 0, f"Should detect action language in: {phrase}")
            self.assertTrue(result.blocked, f"Should block output for: {phrase}")
    
    def test_safe_content_allowed(self):
        """Test that safe content passes through without blocking"""
        safe_phrases = [
            "Here is the information you requested",
            "The system requires configuration",
            "Please check the following steps",
            "Documentation shows the following",
            "Analysis indicates potential issues"
        ]
        
        for phrase in safe_phrases:
            result = self.middleware.validate_output(phrase, self.test_context)
            self.assertEqual(len(result.violations), 0, f"Should not detect violations in: {phrase}")
            self.assertFalse(result.blocked, f"Should not block: {phrase}")
    
    def test_confirmation_override(self):
        """Test that proper confirmation allows action language"""
        action_phrase = "The feature is now live and working"
        
        # Without confirmation - should be blocked
        result = self.middleware.validate_output(action_phrase, self.test_context)
        self.assertTrue(result.blocked)
        
        # With proper confirmation - should be allowed
        confirmed_context = OutputContext(
            channel=OutputChannel.API_RESPONSE,
            source_function="test_function",
            source_file="test_file.py", 
            source_line=42,
            timestamp="2025-01-20T12:00:00Z",
            confirmation_status={
                'confirmed': True,
                'confirmation_method': 'api_endpoint_check',
                'timestamp': '2025-01-20T12:00:00Z'
            }
        )
        
        result = self.middleware.validate_output(action_phrase, confirmed_context)
        self.assertFalse(result.blocked)
        self.assertIn("Backend Confirmed", result.processed_content)
    
    def test_compliance_levels(self):
        """Test different compliance levels"""
        action_phrase = "I have completed the deployment"
        
        # Test STRICT level (should block)
        strict_context = self.test_context
        strict_context.channel = OutputChannel.API_RESPONSE  # Configured as strict
        result = self.middleware.validate_output(action_phrase, strict_context)
        self.assertTrue(result.blocked)
        
        # Test MODERATE level (should warn but not block)
        moderate_context = self.test_context
        moderate_context.channel = OutputChannel.LOG_MESSAGE  # Configured as moderate
        result = self.middleware.validate_output(action_phrase, moderate_context)
        self.assertFalse(result.blocked)
        self.assertTrue(len(result.warnings) > 0)
        
        # Test PERMISSIVE level (should log but not modify)
        permissive_context = self.test_context
        permissive_context.channel = OutputChannel.ERROR_MESSAGE  # Configured as permissive
        result = self.middleware.validate_output(action_phrase, permissive_context)
        self.assertFalse(result.blocked)
        self.assertEqual(result.processed_content, action_phrase)
    
    def test_audit_logging(self):
        """Test that all outputs are properly audited"""
        test_phrase = "I will process this request"
        
        result = self.middleware.validate_output(test_phrase, self.test_context)
        
        # Check audit log was created
        audit_file = os.path.join(self.test_dir, 'compliance_audit.json')
        self.assertTrue(os.path.exists(audit_file))
        
        with open(audit_file, 'r') as f:
            audit_data = json.load(f)
        
        self.assertTrue(len(audit_data['entries']) > 0)
        entry = audit_data['entries'][-1]
        self.assertEqual(entry['channel'], 'api_response')
        self.assertTrue(len(entry['violations']) > 0)
        self.assertTrue(entry['blocked'])
    
    def test_decorator_enforcement(self):
        """Test compliance decorators work correctly"""
        
        @api_output
        def test_api_function():
            return "I have completed the API call"
        
        # Mock the global middleware
        with patch('compliance_middleware.compliance_middleware', self.middleware):
            result = test_api_function()
            
            # Should be blocked due to action language
            self.assertIn("Awaiting backend confirmation", result)
    
    def test_centralized_output_functions(self):
        """Test centralized output functions"""
        
        # Mock the global middleware
        with patch('compliance_middleware.compliance_middleware', self.middleware):
            # Test send_user_output
            result = send_user_output("I am processing the request", OutputChannel.API_RESPONSE)
            self.assertIn("Awaiting backend confirmation", result)
            
            # Test log_and_respond
            result = log_and_respond("The system is now active", "success")
            self.assertTrue(result['compliance_validated'])
            self.assertIn("Awaiting backend confirmation", result['status'])
    
    def test_bypass_detection(self):
        """Test bypass attempt detection"""
        # This is harder to test in unit tests since it requires call stack inspection
        # But we can test the logging mechanism
        bypass_log_file = os.path.join(self.test_dir, 'compliance_bypasses.json')
        
        # Simulate a bypass attempt
        self.middleware._log_bypass_attempt(self.test_context, "Direct output bypass")
        
        self.assertTrue(os.path.exists(bypass_log_file))
        
        with open(bypass_log_file, 'r') as f:
            bypass_data = json.load(f)
        
        self.assertTrue(len(bypass_data['bypass_attempts']) > 0)
    
    def test_compliance_stats(self):
        """Test compliance statistics generation"""
        # Generate some test data
        test_phrases = [
            "I will complete this task",  # Should be blocked
            "Here is the information",    # Should pass
            "The system is ready"         # Should be blocked
        ]
        
        for phrase in test_phrases:
            self.middleware.validate_output(phrase, self.test_context)
        
        stats = self.middleware.get_compliance_stats()
        
        self.assertEqual(stats['total_outputs'], 3)
        self.assertEqual(stats['blocked_outputs'], 2)
        self.assertEqual(stats['total_violations'], 2)
        self.assertIn('api_response', stats['channel_breakdown'])

class TestEndToEndCompliance(unittest.TestCase):
    """End-to-end tests for complete compliance enforcement"""
    
    def setUp(self):
        """Set up E2E test environment"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up E2E test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_flask_route_compliance(self):
        """Test Flask routes with compliance enforcement"""
        from flask import Flask, jsonify
        
        app = Flask(__name__)
        
        # Initialize compliance middleware
        middleware = UniversalComplianceMiddleware(self.test_dir)
        
        @app.route('/test-compliant')
        @api_output
        def compliant_route():
            return jsonify({"status": "Information provided as requested"})
        
        @app.route('/test-non-compliant')
        @api_output  
        def non_compliant_route():
            return jsonify({"status": "I have completed the operation successfully"})
        
        with app.test_client() as client:
            with patch('compliance_middleware.compliance_middleware', middleware):
                # Test compliant route
                response = client.get('/test-compliant')
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertNotIn("blocked", data.get('status', ''))
                
                # Test non-compliant route  
                response = client.get('/test-non-compliant')
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                # Should be modified by compliance middleware
                self.assertTrue(data.get('compliance_blocked', False))
    
    def test_memory_system_compliance(self):
        """Test memory system integration with compliance"""
        # This would test that memory entries are properly validated
        # and compliance violations are logged to the memory system
        pass
    
    def test_logging_compliance(self):
        """Test that logging systems are compliance-aware"""
        import logging
        
        # Test custom log handler that enforces compliance
        pass

if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
