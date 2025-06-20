
"""
MemoryOS Test Suite - Bulletproof Testing
Tests all critical functions and endpoints to prevent regressions
"""

import pytest
import json
import os
import tempfile
import sys
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from main import app, load_memory, save_memory
from bulletproof_logger import BulletproofLogger

class TestMemoryOSCore:
    """Test core MemoryOS functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def temp_memory_file(self):
        """Create temporary memory file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump([], f)
            temp_file = f.name
        
        # Patch the MEMORY_FILE constant
        original_file = getattr(sys.modules['main'], 'MEMORY_FILE', None)
        sys.modules['main'].MEMORY_FILE = temp_file
        
        yield temp_file
        
        # Cleanup
        try:
            os.unlink(temp_file)
        except FileNotFoundError:
            pass
        
        if original_file:
            sys.modules['main'].MEMORY_FILE = original_file

class TestHealthEndpoint:
    """Test the bulletproof health endpoint"""
    
    def test_health_endpoint_always_responds(self, client):
        """Health endpoint must NEVER fail"""
        response = client.get('/health')
        
        # Must always return a response
        assert response.status_code in [200, 503]
        
        # Must always return JSON
        data = response.get_json()
        assert data is not None
        
        # Must always have these fields
        assert 'status' in data
        assert 'timestamp' in data
        assert 'service' in data
        assert data['service'] == 'MemoryOS-Clean'
    
    def test_health_endpoint_with_broken_memory(self, client):
        """Health endpoint works even when memory system fails"""
        # Simulate broken memory file
        with patch('main.load_memory', side_effect=Exception("Memory broken")):
            response = client.get('/health')
            
            # Should still respond
            assert response.status_code in [200, 503]
            data = response.get_json()
            
            # Should indicate degraded/unhealthy status
            assert data['status'] in ['degraded', 'unhealthy', 'critical_failure']

class TestMemoryOperations:
    """Test memory loading and saving"""
    
    def test_load_memory_with_valid_file(self, temp_memory_file):
        """Test loading valid memory file"""
        # Create test data
        test_data = [
            {
                "topic": "Test memory",
                "type": "SystemTest",
                "input": "test input",
                "output": "test output",
                "success": True,
                "category": "test"
            }
        ]
        
        # Write test data
        with open(temp_memory_file, 'w') as f:
            json.dump(test_data, f)
        
        # Test loading
        with patch('main.MEMORY_FILE', temp_memory_file):
            result = load_memory()
            assert result == test_data
    
    def test_load_memory_with_missing_file(self):
        """Test loading non-existent memory file"""
        with patch('main.MEMORY_FILE', '/nonexistent/file.json'):
            result = load_memory()
            assert result == []  # Should return empty list
    
    def test_load_memory_with_corrupted_file(self):
        """Test loading corrupted JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("invalid json {")
            corrupted_file = f.name
        
        try:
            with patch('main.MEMORY_FILE', corrupted_file):
                result = load_memory()
                assert result == []  # Should return empty list on error
        finally:
            os.unlink(corrupted_file)
    
    def test_save_memory(self, temp_memory_file):
        """Test saving memory data"""
        test_data = [{"test": "data"}]
        
        with patch('main.MEMORY_FILE', temp_memory_file):
            result = save_memory(test_data)
            assert result is True
            
            # Verify data was saved
            with open(temp_memory_file, 'r') as f:
                saved_data = json.load(f)
                assert saved_data == test_data

class TestAPIEndpoints:
    """Test API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns index.html or health info"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_gpt_status_endpoint(self, client):
        """Test GPT status endpoint"""
        response = client.get('/gpt-status')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'system_status' in data
        assert 'timestamp' in data
    
    def test_stats_endpoint(self, client):
        """Test stats endpoint"""
        response = client.get('/stats')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_memories' in data
        assert 'success_rate' in data
    
    def test_memory_get_endpoint(self, client):
        """Test GET /memory endpoint"""
        response = client.get('/memory')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'memories' in data
        assert 'pagination' in data

class TestBulletproofLogger:
    """Test the bulletproof logging system"""
    
    def test_logger_creation(self):
        """Test logger can be created"""
        logger = BulletproofLogger("TestLogger")
        assert logger.name == "TestLogger"
        assert logger.logger is not None
    
    def test_error_logging_never_fails(self):
        """Test error logging with various failure scenarios"""
        logger = BulletproofLogger("TestLogger")
        
        # Should not raise any exceptions
        try:
            logger.log_error("Test error message")
            logger.log_error("Test with exception", Exception("test exception"))
            logger.log_info("Test info message")
            logger.log_warning("Test warning message")
        except Exception as e:
            pytest.fail(f"Bulletproof logger failed: {e}")

# Performance and stress tests
class TestSystemResilience:
    """Test system resilience under stress"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_health_endpoint_performance(self, client):
        """Test health endpoint responds quickly"""
        import time
        
        start_time = time.time()
        response = client.get('/health')
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code in [200, 503]
        assert response_time_ms < 5000  # Should respond within 5 seconds even under stress
    
    def test_multiple_health_checks(self, client):
        """Test multiple concurrent health checks"""
        responses = []
        
        # Make multiple requests
        for _ in range(10):
            response = client.get('/health')
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code in [200, 503]
            data = response.get_json()
            assert data is not None

# Integration tests
class TestSystemIntegration:
    """Test full system integration"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_full_system_health_check(self, client):
        """Test that all critical endpoints are working"""
        critical_endpoints = [
            '/',
            '/health',
            '/memory',
            '/stats',
            '/gpt-status'
        ]
        
        for endpoint in critical_endpoints:
            response = client.get(endpoint)
            # All endpoints should at least respond (not crash)
            assert response.status_code < 500, f"Endpoint {endpoint} returned server error"

if __name__ == "__main__":
    # Run tests directly if script is executed
    pytest.main([__file__, "-v", "--tb=short"])
