"""
Test API Key Management
Comprehensive tests for API key generation, listing, and revocation
"""

import pytest
import json
import os
import tempfile
from datetime import datetime, timezone
from main import app
from credit_system import CreditSystem

class TestAPIKeyManagement:
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def temp_credit_system(self):
        """Create a temporary credit system for testing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({}, f)
            temp_file = f.name
        
        # Patch the global credit system
        import credit_system
        original_file = credit_system.credit_system.users_file
        credit_system.credit_system.users_file = temp_file
        
        yield credit_system.credit_system
        
        # Restore and cleanup
        credit_system.credit_system.users_file = original_file
        try:
            os.unlink(temp_file)
        except FileNotFoundError:
            pass
    
    def test_generate_api_key_admin(self, client, temp_credit_system):
        """Test admin generating API key for user"""
        response = client.post('/apikey/new', 
            headers={'X-ADMIN-KEY': 'admin-secret-key'},
            json={
                'email': 'test@example.com',
                'plan': 'Pro',
                'description': 'Test API key'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert 'api_key' in data
        assert len(data['api_key']) == 32
        assert data['plan'] == 'Pro'
        assert data['account_id'] == 'test@example.com'
        assert 'warning' in data
        assert 'Save this API key now' in data['warning']
    
    def test_generate_api_key_user(self, client, temp_credit_system):
        """Test user generating additional API key"""
        # First create a user
        temp_credit_system.create_user('existing-key-123', 'Pro', 'user@example.com')
        
        response = client.post('/apikey/new',
            headers={'X-API-KEY': 'existing-key-123'},
            json={
                'description': 'Additional key for mobile app'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert 'api_key' in data
        assert len(data['api_key']) == 32
        assert data['plan'] == 'Pro'  # Should inherit from existing user
        assert data['account_id'] == 'user@example.com'
    
    def test_generate_api_key_no_auth(self, client, temp_credit_system):
        """Test generating API key without authentication"""
        response = client.post('/apikey/new',
            json={'email': 'test@example.com'}
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'Authentication required' in data['error']
    
    def test_list_api_keys_admin(self, client, temp_credit_system):
        """Test admin listing all API keys"""
        # Create some test users
        temp_credit_system.create_user('key1', 'Free', 'user1@example.com')
        temp_credit_system.create_user('key2', 'Pro', 'user2@example.com')
        
        response = client.get('/apikey/list',
            headers={'X-ADMIN-KEY': 'admin-secret-key'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'total_keys' in data
        assert data['total_keys'] == 2
        assert 'api_keys' in data
        
        # Check that keys are masked
        for key_info in data['api_keys']:
            assert '...' in key_info['api_key']
            assert len(key_info['api_key']) < 32  # Should be masked
    
    def test_list_api_keys_user(self, client, temp_credit_system):
        """Test user listing their own API keys"""
        # Create user with multiple keys
        temp_credit_system.create_user('main-key', 'Pro', 'user@example.com')
        
        # Create additional key for same account
        users = temp_credit_system.load_users()
        users['additional-key'] = {
            'api_key': 'additional-key',
            'plan': 'Pro',
            'email': 'user@example.com',
            'created_by': 'main-key',
            'status': 'active',
            'credits_remaining': 10000,
            'memory_count': 0,
            'memory_limit': 2000,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'last_activity': datetime.now(timezone.utc).isoformat()
        }
        temp_credit_system.save_users(users)
        
        response = client.get('/apikey/list',
            headers={'X-API-KEY': 'main-key'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['total_keys'] == 2
        assert data['account_id'] == 'user@example.com'
        
        # Check that one key is marked as current
        current_keys = [k for k in data['api_keys'] if k.get('is_current')]
        assert len(current_keys) == 1
    
    def test_revoke_api_key_admin(self, client, temp_credit_system):
        """Test admin revoking any API key"""
        # Create a user
        temp_credit_system.create_user('test-key-123', 'Free', 'user@example.com')
        
        response = client.delete('/apikey/test-key-123',
            headers={'X-ADMIN-KEY': 'admin-secret-key'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'revoked successfully' in data['message']
        assert 'revoked_at' in data
        
        # Verify key is marked as inactive
        user = temp_credit_system.get_user('test-key-123')
        assert user is None  # get_user returns None for inactive users
        
        # But the user data still exists in storage
        users = temp_credit_system.load_users()
        assert users['test-key-123']['status'] == 'inactive'
    
    def test_revoke_api_key_user_own_key(self, client, temp_credit_system):
        """Test user revoking their own API key"""
        # Create user with multiple keys
        temp_credit_system.create_user('main-key', 'Pro', 'user@example.com')
        
        users = temp_credit_system.load_users()
        users['secondary-key'] = {
            'api_key': 'secondary-key',
            'plan': 'Pro',
            'email': 'user@example.com',
            'created_by': 'main-key',
            'status': 'active',
            'credits_remaining': 10000,
            'memory_count': 0,
            'memory_limit': 2000,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'last_activity': datetime.now(timezone.utc).isoformat()
        }
        temp_credit_system.save_users(users)
        
        response = client.delete('/apikey/secondary-key',
            headers={'X-API-KEY': 'main-key'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'revoked successfully' in data['message']
    
    def test_revoke_api_key_unauthorized(self, client, temp_credit_system):
        """Test user trying to revoke someone else's API key"""
        # Create two different users
        temp_credit_system.create_user('user1-key', 'Free', 'user1@example.com')
        temp_credit_system.create_user('user2-key', 'Pro', 'user2@example.com')
        
        response = client.delete('/apikey/user2-key',
            headers={'X-API-KEY': 'user1-key'}
        )
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'Permission denied' in data['error']
    
    def test_revoke_last_active_key(self, client, temp_credit_system):
        """Test preventing user from revoking their only active key"""
        # Create user with only one key
        temp_credit_system.create_user('only-key', 'Free', 'user@example.com')
        
        response = client.delete('/apikey/only-key',
            headers={'X-API-KEY': 'only-key'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Cannot revoke your only active API key' in data['error']
    
    def test_revoked_key_cannot_access_endpoints(self, client, temp_credit_system):
        """Test that revoked API keys cannot access protected endpoints"""
        # Create and then revoke a key
        temp_credit_system.create_user('test-key', 'Free', 'user@example.com')
        
        # Revoke the key (admin action)
        client.delete('/apikey/test-key',
            headers={'X-ADMIN-KEY': 'admin-secret-key'}
        )
        
        # Try to use the revoked key
        response = client.get('/credits',
            headers={'X-API-KEY': 'test-key'}
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'Invalid API key' in data['error']
    
    def test_api_key_security_features(self, client, temp_credit_system):
        """Test security features of API key system"""
        # Generate a key
        response = client.post('/apikey/new',
            headers={'X-ADMIN-KEY': 'admin-secret-key'},
            json={'email': 'test@example.com', 'plan': 'Free'}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        api_key = data['api_key']
        
        # Verify key properties
        assert len(api_key) == 32
        assert api_key.isalnum()  # Only letters and numbers
        
        # Verify key is unique (generate another and compare)
        response2 = client.post('/apikey/new',
            headers={'X-ADMIN-KEY': 'admin-secret-key'},
            json={'email': 'test2@example.com', 'plan': 'Free'}
        )
        
        data2 = response2.get_json()
        assert data2['api_key'] != api_key  # Should be different
    
    def test_api_key_metadata(self, client, temp_credit_system):
        """Test API key metadata tracking"""
        # Generate key with description
        response = client.post('/apikey/new',
            headers={'X-ADMIN-KEY': 'admin-secret-key'},
            json={
                'email': 'test@example.com',
                'plan': 'Pro',
                'description': 'Mobile app key'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        api_key = data['api_key']
        
        # Check that metadata is stored
        users = temp_credit_system.load_users()
        user = users[api_key]
        
        assert user['description'] == 'Mobile app key'
        assert user['created_by'] == 'admin'
        assert user['status'] == 'active'
        assert 'created_at' in user

if __name__ == "__main__":
    pytest.main([__file__, "-v"])