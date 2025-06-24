"""
Credit System for AI Productivity SaaS
Handles user credits, billing cycles, memory limits, and API usage tracking
"""

import json
import os
import logging
from datetime import datetime, timezone, timedelta
from functools import wraps
from typing import Dict, Any, Optional, Tuple
from flask import request, jsonify

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CreditSystem')

class CreditSystem:
    def __init__(self, users_file: str = 'users.json'):
        self.users_file = users_file
        self.plan_limits = {
            'Free': 100,
            'Pro': 10000,
            'Premium': 100000
        }
        self.memory_limits = {
            'Free': 100,
            'Pro': 2000,
            'Premium': 1000000  # Unlimited (practical limit)
        }
        self.ensure_users_file()
    
    def ensure_users_file(self):
        """Ensure users.json exists"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f, indent=2)
            logger.info(f"Created {self.users_file}")
    
    def load_users(self) -> Dict[str, Any]:
        """Load users from file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading users: {e}")
            return {}
    
    def save_users(self, users: Dict[str, Any]) -> bool:
        """Save users to file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Error saving users: {e}")
            return False
    
    def get_user(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get user by API key"""
        users = self.load_users()
        user = users.get(api_key)
        
        # Check if user exists and is active
        if user and user.get('status') == 'inactive':
            return None  # Treat inactive users as non-existent for auth purposes
        
        return user
    
    def create_user(self, api_key: str, plan: str = 'Free', email: str = None) -> Dict[str, Any]:
        """Create a new user"""
        if plan not in self.plan_limits:
            raise ValueError(f"Invalid plan: {plan}")
        
        now = datetime.now(timezone.utc)
        next_reset = self.calculate_next_reset(now)
        
        user = {
            'api_key': api_key,
            'plan': plan,
            'credits_remaining': self.plan_limits[plan],
            'credits_used_this_cycle': 0,
            'reset_date': next_reset.isoformat(),
            'created_at': now.isoformat(),
            'email': email,
            'last_activity': now.isoformat(),
            'total_credits_used': 0,
            'memory_count': 0,  # Track memory usage
            'memory_limit': self.memory_limits[plan],
            'status': 'active'  # Track API key status
        }
        
        users = self.load_users()
        users[api_key] = user
        self.save_users(users)
        
        logger.info(f"Created user with API key {api_key[:8]}... on {plan} plan")
        return user
    
    def calculate_next_reset(self, current_date: datetime) -> datetime:
        """Calculate next monthly reset date"""
        # Reset on the same day of next month
        if current_date.month == 12:
            next_month = current_date.replace(year=current_date.year + 1, month=1)
        else:
            next_month = current_date.replace(month=current_date.month + 1)
        
        return next_month
    
    def check_and_reset_credits(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Check if credits need to be reset and reset if needed"""
        now = datetime.now(timezone.utc)
        reset_date = datetime.fromisoformat(user['reset_date'].replace('Z', '+00:00'))
        
        if now >= reset_date:
            # Reset credits
            old_credits = user['credits_remaining']
            user['credits_remaining'] = self.plan_limits[user['plan']]
            user['credits_used_this_cycle'] = 0
            user['reset_date'] = self.calculate_next_reset(now).isoformat()
            
            logger.info(f"Reset credits for user {user['api_key'][:8]}... from {old_credits} to {user['credits_remaining']}")
        
        return user
    
    def use_credit(self, api_key: str, cost: int = 1) -> Tuple[bool, Dict[str, Any]]:
        """
        Use credits for a user
        Returns (success, user_data)
        """
        users = self.load_users()
        user = users.get(api_key)
        
        if not user:
            return False, {'error': 'Invalid API key'}
        
        # Check if user is active
        if user.get('status') == 'inactive':
            return False, {'error': 'API key has been revoked'}
        
        # Check and reset credits if needed
        user = self.check_and_reset_credits(user)
        
        # Check if user has enough credits
        if user['credits_remaining'] < cost:
            logger.warning(f"User {api_key[:8]}... out of credits (has {user['credits_remaining']}, needs {cost})")
            return False, {'error': 'Out of credits', 'credits_remaining': user['credits_remaining']}
        
        # Deduct credits
        user['credits_remaining'] -= cost
        user['credits_used_this_cycle'] += cost
        user['total_credits_used'] += cost
        user['last_activity'] = datetime.now(timezone.utc).isoformat()
        
        # Update users file
        users[api_key] = user
        self.save_users(users)
        
        logger.info(f"User {api_key[:8]}... used {cost} credit(s), {user['credits_remaining']} remaining")
        
        return True, user
    
    def check_memory_limit(self, api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if user can add more memories
        Returns (can_add, status_info)
        """
        users = self.load_users()
        user = users.get(api_key)
        
        if not user:
            return False, {'error': 'Invalid API key'}
        
        # Check if user is active
        if user.get('status') == 'inactive':
            return False, {'error': 'API key has been revoked'}
        
        # Ensure user has memory tracking fields
        if 'memory_count' not in user:
            user['memory_count'] = 0
        if 'memory_limit' not in user:
            user['memory_limit'] = self.memory_limits[user['plan']]
        
        current_count = user['memory_count']
        limit = user['memory_limit']
        
        if current_count >= limit:
            return False, {
                'error': 'Memory limit exceeded',
                'current_count': current_count,
                'limit': limit,
                'plan': user['plan']
            }
        
        return True, {
            'current_count': current_count,
            'limit': limit,
            'remaining': limit - current_count
        }
    
    def increment_memory_count(self, api_key: str) -> bool:
        """Increment user's memory count"""
        users = self.load_users()
        user = users.get(api_key)
        
        if not user or user.get('status') == 'inactive':
            return False
        
        # Ensure user has memory tracking fields
        if 'memory_count' not in user:
            user['memory_count'] = 0
        
        user['memory_count'] += 1
        user['last_activity'] = datetime.now(timezone.utc).isoformat()
        
        users[api_key] = user
        self.save_users(users)
        
        logger.info(f"User {api_key[:8]}... memory count incremented to {user['memory_count']}")
        return True
    
    def update_memory_count_from_file(self, api_key: str, memory_file: str = 'memory.json') -> bool:
        """Update user's memory count based on actual memory file"""
        try:
            # Load memory file
            with open(memory_file, 'r') as f:
                memories = json.load(f)
            
            # Count memories for this user
            user_memories = [m for m in memories if m.get('api_key') == api_key]
            count = len(user_memories)
            
            # Update user
            users = self.load_users()
            user = users.get(api_key)
            
            if user:
                user['memory_count'] = count
                users[api_key] = user
                self.save_users(users)
                logger.info(f"Updated memory count for user {api_key[:8]}... to {count}")
                return True
            
        except Exception as e:
            logger.error(f"Error updating memory count: {e}")
        
        return False
    
    def get_credit_status(self, api_key: str) -> Dict[str, Any]:
        """Get credit status for a user"""
        users = self.load_users()
        user = users.get(api_key)
        
        if not user:
            return {'error': 'Invalid API key'}
        
        # Check if user is active
        if user.get('status') == 'inactive':
            return {'error': 'API key has been revoked'}
        
        # Check and reset credits if needed
        user = self.check_and_reset_credits(user)
        
        # Ensure memory tracking fields exist
        if 'memory_count' not in user:
            user['memory_count'] = 0
        if 'memory_limit' not in user:
            user['memory_limit'] = self.memory_limits[user['plan']]
        
        users[api_key] = user
        self.save_users(users)
        
        # Calculate status
        plan_limit = self.plan_limits[user['plan']]
        percent_remaining = (user['credits_remaining'] / plan_limit) * 100
        
        # Calculate memory usage
        memory_percent = (user['memory_count'] / user['memory_limit']) * 100
        
        # Calculate days until reset
        now = datetime.now(timezone.utc)
        reset_date = datetime.fromisoformat(user['reset_date'].replace('Z', '+00:00'))
        days_until_reset = (reset_date - now).days
        
        # Check for warnings
        warnings = []
        if percent_remaining < 25:
            warnings.append('Low credits - less than 25% remaining')
        if user['credits_remaining'] == 0:
            warnings.append('Out of credits')
        if memory_percent > 90:
            warnings.append('Memory usage over 90% - consider upgrading plan')
        if user['memory_count'] >= user['memory_limit']:
            warnings.append('Memory limit reached - cannot add more memories')
        
        return {
            'api_key': api_key[:8] + '...',  # Masked for security
            'plan': user['plan'],
            'credits_remaining': user['credits_remaining'],
            'credits_limit': plan_limit,
            'percent_remaining': round(percent_remaining, 1),
            'days_until_reset': max(0, days_until_reset),
            'reset_date': user['reset_date'],
            'warnings': warnings,
            'credits_used_this_cycle': user['credits_used_this_cycle'],
            'last_activity': user['last_activity'],
            'status': user.get('status', 'active'),
            'memory_usage': {
                'current_count': user['memory_count'],
                'limit': user['memory_limit'],
                'percent_used': round(memory_percent, 1),
                'remaining': user['memory_limit'] - user['memory_count']
            }
        }
    
    def update_user_plan(self, api_key: str, new_plan: str) -> bool:
        """Update user's plan"""
        if new_plan not in self.plan_limits:
            return False
        
        users = self.load_users()
        user = users.get(api_key)
        
        if not user:
            return False
        
        old_plan = user['plan']
        user['plan'] = new_plan
        
        # Update memory limit
        user['memory_limit'] = self.memory_limits[new_plan]
        
        # If upgrading, give them the new plan's credits immediately
        if self.plan_limits[new_plan] > self.plan_limits[old_plan]:
            user['credits_remaining'] = self.plan_limits[new_plan]
            logger.info(f"Upgraded user {api_key[:8]}... from {old_plan} to {new_plan}, credits reset to {user['credits_remaining']}")
        
        users[api_key] = user
        self.save_users(users)
        
        return True

# Global credit system instance
credit_system = CreditSystem()

def require_credits(cost: int = 1):
    """
    Decorator to require credits for an endpoint
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from header
            api_key = request.headers.get('X-API-KEY')
            
            if not api_key:
                return jsonify({'error': 'API key required'}), 401
            
            # Check if user exists and is active
            user = credit_system.get_user(api_key)
            if not user:
                return jsonify({'error': 'Invalid or inactive API key'}), 401
            
            # Try to use credits
            success, result = credit_system.use_credit(api_key, cost)
            
            if not success:
                if 'Out of credits' in result.get('error', ''):
                    return jsonify({
                        'error': 'Out of credits',
                        'message': 'Your account has run out of credits. Please upgrade your plan or wait for your monthly reset.',
                        'credits_remaining': result.get('credits_remaining', 0)
                    }), 402
                elif 'revoked' in result.get('error', ''):
                    return jsonify({
                        'error': 'API key revoked',
                        'message': 'This API key has been revoked and is no longer valid.'
                    }), 401
                else:
                    return jsonify(result), 400
            
            # Add credit info to response
            def add_credit_info(response):
                if hasattr(response, 'get_json') and response.get_json():
                    data = response.get_json()
                    
                    # Add credit warnings if needed
                    plan_limit = credit_system.plan_limits[result['plan']]
                    percent_remaining = (result['credits_remaining'] / plan_limit) * 100
                    
                    credit_info = {
                        'credits_remaining': result['credits_remaining'],
                        'credits_used': cost
                    }
                    
                    if percent_remaining < 25:
                        credit_info['warning'] = 'Low credits - less than 25% remaining'
                    
                    data['credit_info'] = credit_info
                    response.data = json.dumps(data)
                
                return response
            
            # Execute the original function
            response = f(*args, **kwargs)
            
            # Add credit info to successful responses
            if hasattr(response, 'status_code') and 200 <= response.status_code < 300:
                response = add_credit_info(response)
            
            return response
        
        return decorated_function
    return decorator

def require_memory_limit():
    """
    Decorator to check memory limits for memory creation endpoints
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from header
            api_key = request.headers.get('X-API-KEY')
            
            if not api_key:
                return jsonify({'error': 'API key required'}), 401
            
            # Check memory limit
            can_add, status = credit_system.check_memory_limit(api_key)
            
            if not can_add:
                if 'revoked' in status.get('error', ''):
                    return jsonify({
                        'error': 'API key revoked',
                        'message': 'This API key has been revoked and is no longer valid.'
                    }), 401
                else:
                    return jsonify({
                        'error': 'Memory limit exceeded',
                        'message': f'Your {status.get("plan", "current")} plan allows {status.get("limit", 0)} memories. You currently have {status.get("current_count", 0)}. Please upgrade your plan to add more memories.',
                        'current_count': status.get('current_count', 0),
                        'limit': status.get('limit', 0),
                        'plan': status.get('plan', 'Unknown')
                    }), 402
            
            # Execute the original function
            response = f(*args, **kwargs)
            
            # If successful, increment memory count
            if hasattr(response, 'status_code') and 200 <= response.status_code < 300:
                credit_system.increment_memory_count(api_key)
                
                # Add memory usage info to response
                if hasattr(response, 'get_json') and response.get_json():
                    data = response.get_json()
                    data['memory_usage'] = {
                        'current_count': status['current_count'] + 1,
                        'limit': status['limit'],
                        'remaining': status['remaining'] - 1
                    }
                    response.data = json.dumps(data)
            
            return response
        
        return decorated_function
    return decorator

def get_api_key_from_request() -> Optional[str]:
    """Helper to get API key from request"""
    return request.headers.get('X-API-KEY')