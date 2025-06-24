"""
Test Credit System
Comprehensive tests for the credit system functionality including memory limits
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
        assert user['memory_limit'] == 2000
        assert user['memory_count'] == 0
        assert user['email'] == "test@example.com"
        assert 'reset_date' in user
        assert 'created_at' in user
    
    def test_invalid_plan(self, temp_credit_system):
        """Test creating user with invalid plan"""
        with pytest.raises(ValueError):
            temp_credit_system.create_user("test-key", "InvalidPlan")
    
    def test_memory_limits(self, temp_credit_system):
        """Test memory limits for different plans"""
        # Test Free plan
        free_user = temp_credit_system.create_user("free-key", "Free")
        assert free_user['memory_limit'] == 100
        
        # Test Pro plan
        pro_user = temp_credit_system.create_user("pro-key", "Pro")
        assert pro_user['memory_limit'] == 2000
        
        # Test Premium plan
        premium_user = temp_credit_system.create_user("premium-key", "Premium")
        assert premium_user['memory_limit'] == 1000000
    
    def test_memory_limit_check(self, temp_credit_system):
        """Test memory limit checking"""
        api_key = "test-api-key-123"
        temp_credit_system.create_user(api_key, "Free")  # 100 memory limit
        
        # Should be able to add initially
        can_add, status = temp_credit_system.check_memory_limit(api_key)
        assert can_add is True
        assert status['current_count'] == 0
        assert status['limit'] == 100
        assert status['remaining'] == 100
        
        # Simulate reaching limit
        users = temp_credit_system.load_users()
        users[api_key]['memory_count'] = 100
        temp_credit_system.save_users(users)
        
        # Should not be able to add more
        can_add, status = temp_credit_system.check_memory_limit(api_key)
        assert can_add is False
        assert 'Memory limit exceeded' in status['error']
        assert status['current_count'] == 100
        assert status['limit'] == 100
    
    def test_increment_memory_count(self, temp_credit_system):
        """Test incrementing memory count"""
        api_key = "test-api-key-123"
        temp_credit_system.create_user(api_key, "Free")
        
        # Increment memory count
        success = temp_credit_system.increment_memory_count(api_key)
        assert success is True
        
        user = temp_credit_system.get_user(api_key)
        assert user['memory_count'] == 1
    
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
    
    def test_credit_status_with_memory(self, temp_credit_system):
        """Test getting credit status including memory usage"""
        api_key = "test-api-key-123"
        temp_credit_system.create_user(api_key, "Pro")
        temp_credit_system.use_credit(api_key, 1000)  # Use 1000 credits
        
        # Simulate some memory usage
        users = temp_credit_system.load_users()
        users[api_key]['memory_count'] = 500  # 500 out of 2000
        temp_credit_system.save_users(users)
        
        status = temp_credit_system.get_credit_status(api_key)
        
        assert status['plan'] == "Pro"
        assert status['credits_remaining'] == 9000
        assert status['credits_limit'] == 10000
        assert status['percent_remaining'] == 90.0
        assert status['credits_used_this_cycle'] == 1000
        
        # Check memory usage
        assert 'memory_usage' in status
        assert status['memory_usage']['current_count'] == 500
        assert status['memory_usage']['limit'] == 2000
        assert status['memory_usage']['percent_used'] == 25.0
        assert status['memory_usage']['remaining'] == 1500
    
    def test_memory_usage_warnings(self, temp_credit_system):
        """Test memory usage warnings"""
        api_key = "test-api-key-123"
        temp_credit_system.create_user(api_key, "Free")  # 100 memory limit
        
        # Simulate high memory usage (95%)
        users = temp_credit_system.load_users()
        users[api_key]['memory_count'] = 95
        temp_credit_system.save_users(users)
        
        status = temp_credit_system.get_credit_status(api_key)
        
        # Should have memory warning
        warnings = status['warnings']
        memory_warnings = [w for w in warnings if 'Memory usage' in w]
        assert len(memory_warnings) > 0
        
        # Simulate reaching limit
        users[api_key]['memory_count'] = 100
        temp_credit_system.save_users(users)
        
        status = temp_credit_system.get_credit_status(api_key)
        warnings = status['warnings']
        limit_warnings = [w for w in warnings if 'Memory limit reached' in w]
        assert len(limit_warnings) > 0
    
    def test_low_credit_warning(self, temp_credit_system):
        """Test low credit warning"""
        api_key = "test-api-key-123"
        temp_credit_system.create_user(api_key, "Free")  # 100 credits
        temp_credit_system.use_credit(api_key, 80)  # Use 80, leaving 20 (20%)
        
        status = temp_credit_system.get_credit_status(api_key)
        
        assert len(status['warnings']) > 0
        assert 'Low credits' in status['warnings'][0]
    
    def test_plan_upgrade_with_memory(self, temp_credit_system):
        """Test upgrading user plan with memory limits"""
        api_key = "test-api-key-123"
        temp_credit_system.create_user(api_key, "Free")
        temp_credit_system.use_credit(api_key, 50)  # Use some credits
        
        # Simulate some memory usage
        users = temp_credit_system.load_users()
        users[api_key]['memory_count'] = 80  # Near Free limit
        temp_credit_system.save_users(users)
        
        # Upgrade to Pro
        success = temp_credit_system.update_user_plan(api_key, "Pro")
        
        assert success is True
        
        user = temp_credit_system.get_user(api_key)
        assert user['plan'] == "Pro"
        assert user['credits_remaining'] == 10000  # Should get full Pro credits
        assert user['memory_limit'] == 2000  # Should get Pro memory limit
        assert user['memory_count'] == 80  # Memory count should remain
    
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
    
    def test_update_memory_count_from_file(self, temp_credit_system):
        """Test updating memory count from actual memory file"""
        api_key = "test-api-key-123"
        temp_credit_system.create_user(api_key, "Pro")
        
        # Create a temporary memory file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            memories = [
                {"topic": "Memory 1", "api_key": api_key},
                {"topic": "Memory 2", "api_key": api_key},
                {"topic": "Memory 3", "api_key": "other-key"},  # Different user
                {"topic": "Memory 4", "api_key": api_key}
            ]
            json.dump(memories, f)
            temp_memory_file = f.name
        
        try:
            # Update memory count from file
            success = temp_credit_system.update_memory_count_from_file(api_key, temp_memory_file)
            assert success is True
            
            user = temp_credit_system.get_user(api_key)
            assert user['memory_count'] == 3  # Should count only this user's memories
            
        finally:
            os.unlink(temp_memory_file)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])