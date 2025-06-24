# MemoryOS Clean with Credit System

A bulletproof, minimal memory system built for production reliability with comprehensive credit management for AI productivity SaaS.

## Features

- ✅ Memory storage and retrieval with credit tracking
- ✅ User management with API key authentication
- ✅ Flexible credit plans (Free, Pro, Premium)
- ✅ Memory limits per plan with usage tracking
- ✅ Automatic monthly billing cycle resets
- ✅ Credit usage warnings and limits
- ✅ Memory limit enforcement and warnings
- ✅ Comprehensive logging and monitoring
- ✅ Health monitoring endpoints
- ✅ Statistics tracking
- ✅ GPT integration ready
- ✅ Production-grade error handling

## Credit System & Memory Limits

### Plans and Limits

| Plan | Monthly Credits | Memory Limit | Cost per API Call |
|------|----------------|--------------|-------------------|
| Free | 100 | 100 memories | 1-2 credits |
| Pro | 10,000 | 2,000 memories | 1-2 credits |
| Premium | 100,000 | Unlimited* | 1-2 credits |

*Premium plan has a practical limit of 1,000,000 memories

### Credit Costs by Endpoint

- `GET /memory` - 1 credit
- `POST /memory` - 2 credits + memory limit check
- `GET /stats` - 1 credit
- `GET /gpt-status` - 1 credit
- `GET /credits` - Free
- `POST /signup` - Free
- `POST /login` - Free
- `GET /health` - Free

### Memory Limit Features

- **Per-Plan Limits**: Each plan has specific memory storage limits
- **Usage Tracking**: Real-time tracking of memory count per user
- **Limit Enforcement**: 402 error when memory limit exceeded
- **Usage Warnings**: Warnings when approaching memory limits (90%+)
- **Plan Upgrades**: Instant memory limit increase on plan upgrade
- **Memory Tagging**: All memories tagged with owner's API key

### Credit Features

- **Automatic Reset**: Credits reset monthly on billing cycle
- **Low Credit Warnings**: Warnings when below 25% remaining
- **Credit Blocking**: 402 error when out of credits
- **Usage Tracking**: Track total and cycle usage
- **Plan Upgrades**: Instant credit refresh on plan upgrade

## Quick Start

```bash
python main.py
```

Server runs on port 5000 and is accessible at `https://your-repl-name.replit.app/`

## API Endpoints

### Authentication & Credits
- `POST /signup` - Create new user account
- `POST /login` - Login (placeholder)
- `GET /credits` - Check credit status and memory usage

### Core Endpoints (Require Credits)
- `GET /memory` - Get memories (1 credit, filtered by user)
- `POST /memory` - Add memory (2 credits + memory limit check)
- `GET /stats` - Statistics (1 credit, filtered by user)
- `GET /gpt-status` - GPT-friendly status (1 credit)

### System Endpoints (Free)
- `GET /` - Basic health check
- `GET /health` - Comprehensive health monitoring

### Admin Endpoints
- `GET /admin/users` - View all users (requires admin key)
- `PUT /admin/user/<api_key>/plan` - Update user plan (requires admin key)
- `POST /admin/sync-memory-counts` - Sync memory counts from file (requires admin key)

## Environment Variables

- `JAVLIN_API_KEY` - Default API key for backward compatibility
- `ADMIN_KEY` - Admin access key for user management

## User Management

### Creating a User

```bash
curl -X POST https://your-app.com/signup \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-unique-api-key",
    "plan": "Pro",
    "email": "user@example.com"
  }'
```

### Checking Credits and Memory Usage

```bash
curl -H "X-API-KEY: your-api-key" \
  https://your-app.com/credits
```

Response:
```json
{
  "api_key": "your-key...",
  "plan": "Pro",
  "credits_remaining": 8500,
  "credits_limit": 10000,
  "percent_remaining": 85.0,
  "days_until_reset": 15,
  "reset_date": "2025-02-01T00:00:00+00:00",
  "warnings": [],
  "credits_used_this_cycle": 1500,
  "last_activity": "2025-01-15T10:30:00+00:00",
  "memory_usage": {
    "current_count": 450,
    "limit": 2000,
    "percent_used": 22.5,
    "remaining": 1550
  }
}
```

### Using Protected Endpoints

All protected endpoints require the `X-API-KEY` header:

```bash
curl -H "X-API-KEY: your-api-key" \
  https://your-app.com/memory
```

## Memory Management

### Memory Limits by Plan

- **Free Plan**: 100 memories maximum
- **Pro Plan**: 2,000 memories maximum  
- **Premium Plan**: 1,000,000 memories (effectively unlimited)

### Memory Limit Enforcement

When attempting to create a memory:

1. **Credit Check**: Ensures user has sufficient credits (2 credits required)
2. **Memory Limit Check**: Verifies user hasn't exceeded their plan's memory limit
3. **Memory Creation**: If both checks pass, memory is created and tagged with user's API key
4. **Count Update**: User's memory count is automatically incremented

### Memory Limit Errors

When memory limit is exceeded:

```json
{
  "error": "Memory limit exceeded",
  "message": "Your Free plan allows 100 memories. You currently have 100. Please upgrade your plan to add more memories.",
  "current_count": 100,
  "limit": 100,
  "plan": "Free"
}
```

### Memory Usage Warnings

Users receive warnings when:
- Memory usage exceeds 90% of their limit
- Memory limit is reached (cannot add more memories)

## Credit System Architecture

### Data Structure

Users are stored in `users.json`:

```json
{
  "api-key-123": {
    "api_key": "api-key-123",
    "plan": "Pro",
    "credits_remaining": 8500,
    "credits_used_this_cycle": 1500,
    "memory_count": 450,
    "memory_limit": 2000,
    "reset_date": "2025-02-01T00:00:00+00:00",
    "created_at": "2025-01-01T00:00:00+00:00",
    "email": "user@example.com",
    "last_activity": "2025-01-15T10:30:00+00:00",
    "total_credits_used": 15000
  }
}
```

### Memory Storage

Memories in `memory.json` are tagged with the owner's API key:

```json
{
  "topic": "User's memory entry",
  "type": "UserInteraction",
  "input": "User input",
  "output": "System response",
  "success": true,
  "category": "conversation",
  "api_key": "api-key-123",
  "timestamp": "2025-01-15T10:30:00+00:00"
}
```

### Credit & Memory Flow

1. **User makes API request** with `X-API-KEY` header
2. **System validates** API key and loads user
3. **Credit check** ensures sufficient credits available
4. **Memory limit check** (for POST /memory) ensures user can add more memories
5. **Credit deduction** happens before endpoint execution
6. **Memory count increment** (for successful memory creation)
7. **Response includes** credit info, memory usage, and warnings if needed

### Error Handling

- **401 Unauthorized**: Invalid or missing API key
- **402 Payment Required**: Out of credits OR memory limit exceeded
- **409 Conflict**: User already exists (signup)

## Testing

Run the credit system tests including memory limits:

```bash
python test_credit_system.py
```

Run the full test suite:

```bash
python -m pytest test_memoryos.py test_credit_system.py -v
```

## Monitoring & Logging

### Health Check Setup

The `/health` endpoint provides comprehensive system monitoring including credit system and memory usage status.

**Health Check URL:** `https://your-repl-name.replit.app/health`

### Credit & Memory System Monitoring

Monitor these metrics:
- Total users and their plans
- Credit usage patterns
- Memory usage patterns per plan
- Monthly reset cycles
- Low credit warnings
- Memory limit warnings
- Out of credit/memory blocks

### Logging

All credit and memory operations are logged:
- User creation
- Credit usage
- Memory limit checks
- Memory count updates
- Plan upgrades
- Monthly resets
- Credit and memory warnings

## Admin Operations

### View All Users with Memory Usage

```bash
curl -H "X-ADMIN-KEY: your-admin-key" \
  https://your-app.com/admin/users
```

Response includes memory usage:
```json
{
  "total_users": 150,
  "users": {
    "api-key...": {
      "plan": "Pro",
      "credits_remaining": 8500,
      "memory_count": 450,
      "memory_limit": 2000,
      "reset_date": "2025-02-01T00:00:00+00:00"
    }
  }
}
```

### Update User Plan

```bash
curl -X PUT \
  -H "X-ADMIN-KEY: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"plan": "Premium"}' \
  https://your-app.com/admin/user/api-key-123/plan
```

### Sync Memory Counts

Synchronize memory counts from the actual memory file:

```bash
curl -X POST \
  -H "X-ADMIN-KEY: your-admin-key" \
  https://your-app.com/admin/sync-memory-counts
```

## Production Deployment

### Security Considerations

1. **API Key Security**: Use strong, unique API keys
2. **Admin Key**: Set secure `ADMIN_KEY` environment variable
3. **HTTPS**: Always use HTTPS in production
4. **Rate Limiting**: Consider adding rate limiting for additional protection
5. **Memory Isolation**: Each user's memories are isolated by API key

### Scaling Considerations

1. **File Storage**: For high-volume usage, consider migrating to a database
2. **Memory Calculations**: Current system handles thousands of users efficiently
3. **Memory File Size**: Monitor memory.json size with high memory usage
4. **Backup Strategy**: Regularly backup `users.json` and `memory.json`

### Monitoring Setup

1. Monitor `/health` endpoint for system status
2. Set up alerts for credit system failures
3. Track user growth and credit usage patterns
4. Monitor memory usage patterns by plan
5. Alert on unusual API usage patterns
6. Monitor memory file size growth

## Migration from Previous Version

If upgrading from a version without credit system or memory limits:

1. **Backup** your existing `memory.json`
2. **Deploy** new version with credit and memory limit system
3. **Create users** for existing API keys:

```bash
curl -X POST https://your-app.com/signup \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "existing-api-key",
    "plan": "Pro"
  }'
```

4. **Sync memory counts** to update user memory usage:

```bash
curl -X POST \
  -H "X-ADMIN-KEY: your-admin-key" \
  https://your-app.com/admin/sync-memory-counts
```

## Support

For issues or questions:
1. Check the health endpoint for system status
2. Review logs for credit and memory system operations
3. Use admin endpoints to manage users and sync memory counts
4. Test credit and memory operations with the test suite

---

**Built for Production • Credit-Managed • Memory-Limited • Monitored • Scalable**