# MemoryOS Clean with Credit System

A bulletproof, minimal memory system built for production reliability with comprehensive credit management for AI productivity SaaS.

## Features

- ✅ Memory storage and retrieval with credit tracking
- ✅ User management with API key authentication
- ✅ Flexible credit plans (Free, Pro, Premium)
- ✅ Automatic monthly billing cycle resets
- ✅ Credit usage warnings and limits
- ✅ Comprehensive logging and monitoring
- ✅ Health monitoring endpoints
- ✅ Statistics tracking
- ✅ GPT integration ready
- ✅ Production-grade error handling

## Credit System

### Plans and Limits

| Plan | Monthly Credits | Cost per API Call |
|------|----------------|-------------------|
| Free | 100 | 1-2 credits |
| Pro | 10,000 | 1-2 credits |
| Premium | 100,000 | 1-2 credits |

### Credit Costs by Endpoint

- `GET /memory` - 1 credit
- `POST /memory` - 2 credits
- `GET /stats` - 1 credit
- `GET /gpt-status` - 1 credit
- `GET /credits` - Free
- `POST /signup` - Free
- `POST /login` - Free
- `GET /health` - Free

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
- `GET /credits` - Check credit status

### Core Endpoints (Require Credits)
- `GET /memory` - Get memories (1 credit)
- `POST /memory` - Add memory (2 credits)
- `GET /stats` - Statistics (1 credit)
- `GET /gpt-status` - GPT-friendly status (1 credit)

### System Endpoints (Free)
- `GET /` - Basic health check
- `GET /health` - Comprehensive health monitoring

### Admin Endpoints
- `GET /admin/users` - View all users (requires admin key)
- `PUT /admin/user/<api_key>/plan` - Update user plan (requires admin key)

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

### Checking Credits

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
  "last_activity": "2025-01-15T10:30:00+00:00"
}
```

### Using Protected Endpoints

All protected endpoints require the `X-API-KEY` header:

```bash
curl -H "X-API-KEY: your-api-key" \
  https://your-app.com/memory
```

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
    "reset_date": "2025-02-01T00:00:00+00:00",
    "created_at": "2025-01-01T00:00:00+00:00",
    "email": "user@example.com",
    "last_activity": "2025-01-15T10:30:00+00:00",
    "total_credits_used": 15000
  }
}
```

### Credit Flow

1. **User makes API request** with `X-API-KEY` header
2. **System validates** API key and loads user
3. **Credit check** ensures sufficient credits available
4. **Credit deduction** happens before endpoint execution
5. **Response includes** credit info and warnings if needed
6. **Monthly reset** automatically restores credits

### Error Handling

- **401 Unauthorized**: Invalid or missing API key
- **402 Payment Required**: Out of credits
- **409 Conflict**: User already exists (signup)

## Memory Structure

```json
{
  "topic": "Description of what happened",
  "type": "SystemUpdate|Feature|BugFix|UserInteraction|API|Database|Security|Performance|Documentation|Testing|Deployment|Monitoring",
  "input": "What was attempted",
  "output": "What was the result",
  "success": true|false,
  "category": "system|feature|bug|etc",
  "tags": ["optional", "tags"],
  "score": 15,
  "maxScore": 25,
  "reviewed": false
}
```

## Testing

Run the credit system tests:

```bash
python test_credit_system.py
```

Run the full test suite:

```bash
python -m pytest test_memoryos.py test_credit_system.py -v
```

## Monitoring & Logging

### Health Check Setup

The `/health` endpoint provides comprehensive system monitoring including credit system status.

**Health Check URL:** `https://your-repl-name.replit.app/health`

### Credit System Monitoring

Monitor these metrics:
- Total users and their plans
- Credit usage patterns
- Monthly reset cycles
- Low credit warnings
- Out of credit blocks

### Logging

All credit operations are logged:
- User creation
- Credit usage
- Plan upgrades
- Monthly resets
- Credit warnings and blocks

## Admin Operations

### View All Users

```bash
curl -H "X-ADMIN-KEY: your-admin-key" \
  https://your-app.com/admin/users
```

### Update User Plan

```bash
curl -X PUT \
  -H "X-ADMIN-KEY: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"plan": "Premium"}' \
  https://your-app.com/admin/user/api-key-123/plan
```

## Production Deployment

### Security Considerations

1. **API Key Security**: Use strong, unique API keys
2. **Admin Key**: Set secure `ADMIN_KEY` environment variable
3. **HTTPS**: Always use HTTPS in production
4. **Rate Limiting**: Consider adding rate limiting for additional protection

### Scaling Considerations

1. **File Storage**: For high-volume usage, consider migrating to a database
2. **Credit Calculations**: Current system handles thousands of users efficiently
3. **Backup Strategy**: Regularly backup `users.json` and `memory.json`

### Monitoring Setup

1. Monitor `/health` endpoint for system status
2. Set up alerts for credit system failures
3. Track user growth and credit usage patterns
4. Monitor for unusual API usage patterns

## Migration from Previous Version

If upgrading from a version without credit system:

1. **Backup** your existing `memory.json`
2. **Deploy** new version with credit system
3. **Create users** for existing API keys:

```bash
curl -X POST https://your-app.com/signup \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "existing-api-key",
    "plan": "Pro"
  }'
```

## Support

For issues or questions:
1. Check the health endpoint for system status
2. Review logs for credit system operations
3. Use admin endpoints to manage users
4. Test credit operations with the test suite

---

**Built for Production • Credit-Managed • Monitored • Scalable**