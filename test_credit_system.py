"""
Test Credit System
Comprehensive tests for the credit system functionality
"""

import pytest
import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from credit_system import CreditSystem, credit_system

class TestCreditSystem:
    
    @pytest.fixture
    def temp_credit_system(self):
        """Create a temporary credit system for testing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({}, f)
            temp_file = f.name
        
        cs = CreditSystem(temp_file)
        yield cs
        
        # Cleanup
        try:
            os.unlink(temp_file)
        except FileNotFoundError:
            pass
    
    def test_create_user(self, temp_credit_system):
        """Test user creation"""
        api_key = "test-api-key-123"
        user = temp_credit_system.create_user(api_key, "Pro", "test@example.com")
        
        assert user['api_key'] == api_key
        assert user['plan'] == "Pro"
        assert user['credits_remaining'] == 10000
        assert user['email'] == "test@example.com"
        assert 'reset_date' in user
        assert 'created_at' in user
    
    def test_invalid_plan(self, temp_credit_system):
        """Test creating user with invalid plan"""
        with pytest.raises(ValueError):
            temp_credit_system.create_user("test-key", "InvalidPlan")
    
    def test_use_credit(self, temp_credit_system):
        """Test using credits"""
        api_key = "test-api-key-123"
        temp_credit_system.create_user(api_key, "Free")
        
        # Use 1 credit
        success, user = temp_credit_system.use_credit(api_key, 1)
        
        assert success is True
        assert user['credits_remaining'] == 99
        assert user['credits_used_this_cycle'] == 1
        assert user['total_credits_used'] == 1
    
    def test_insufficient_credits(self, temp_credit_system):
        """Test using more credits than available"""
        api_key = "test-api-key-123"
        temp_credit_system.create_user(api_key, "Free")  # 100 credits
        
        # Try to use 101 credits
        success, result = temp_credit_system.use_credit(api_key, 101)
        
        assert success is False
        assert 'Out of credits' in result['error']
    
    def test_credit_status(self, temp_credit_system):
        """Test getting credit status"""
        api_key = "test-api-key-123"
        temp_credit_system.create_user(api_key, "Pro")
        temp_credit_system.use_credit(api_key, 1000)  # Use 1000 credits
        
        status = temp_credit_system.get_credit_status(api_key)
        
        assert status['plan'] == "Pro"
        assert status['credits_remaining'] == 9000
        assert status['credits_limit'] == 10000
        assert status['percent_remaining'] == 90.0
        assert status['credits_used_this_cycle'] == 1000
    
    def test_low_credit_warning(self, temp_credit_system):
        """Test low credit warning"""
        api_key = "test-api-key-123"
        temp_credit_system.create_user(api_key, "Free")  # 100 credits
        temp_credit_system.use_credit(api_key, 80)  # Use 80, leaving 20 (20%)
        
        status = temp_credit_system.get_credit_status(api_key)
        
        assert len(status['warnings']) > 0
        assert 'Low credits' in status['warnings'][0]
    
    def test_plan_upgrade(self, temp_credit_system):
        """Test upgrading user plan"""
        api_key = "test-api-key-123"
        temp_credit_system.create_user(api_key, "Free")
        temp_credit_system.use_credit(api_key, 50)  # Use some credits
        
        # Upgrade to Pro
        success = temp_credit_system.update_user_plan(api_key, "Pro")
        
        assert success is True
        
        user = temp_credit_system.get_user(api_key)
        assert user['plan'] == "Pro"
        assert user['credits_remaining'] == 10000  # Should get full Pro credits
    
    def test_credit_reset(self, temp_credit_system):
        """Test monthly credit reset"""
        api_key = "test-api-key-123"
        user = temp_credit_system.create_user(api_key, "Free")
        
        # Use some credits
        temp_credit_system.use_credit(api_key, 50)
        
        # Manually set reset date to past
        users = temp_credit_system.load_users()
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        users[api_key]['reset_date'] = past_date.isoformat()
        temp_credit_system.save_users(users)
        
        # Check status (should trigger reset)
        status = temp_credit_system.get_credit_status(api_key)
        
        assert status['credits_remaining'] == 100  # Should be reset to full
        assert status['credits_used_this_cycle'] == 0  # Should be reset

if __name__ == "__main__":
    pytest.main([__file__, "-v"])