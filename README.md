# MemoryOS Clean with Credit System and API Key Management

A bulletproof, minimal memory system built for production reliability with comprehensive credit management, memory limits, and secure API key generation for AI productivity SaaS.

## Features

- ✅ Memory storage and retrieval with credit tracking
- ✅ User management with API key authentication
- ✅ **Secure API key generation and management**
- ✅ **API key listing and revocation with security controls**
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

## API Key Management

### Security Features

- **Cryptographically Secure**: 32-character keys using `secrets` module
- **One-Time Display**: API keys shown only once during generation
- **Revocation Not Deletion**: Keys are marked inactive, preserving usage history
- **Permission Controls**: Users can only manage their own account's keys
- **Admin Override**: Admins can manage any user's keys
- **Active Key Protection**: Cannot revoke your only active API key

### API Key Endpoints

#### Generate New API Key
```bash
# Admin creating key for user
curl -X POST https://your-app.com/apikey/new \
  -H "X-ADMIN-KEY: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "plan": "Pro",
    "description": "Mobile app access key"
  }'

# User creating additional key for their account
curl -X POST https://your-app.com/apikey/new \
  -H "X-API-KEY: existing-user-key" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Desktop app key"
  }'
```

Response:
```json
{
  "message": "API key generated successfully",
  "api_key": "abcd1234efgh5678ijkl9012mnop3456",
  "plan": "Pro",
  "description": "Mobile app access key",
  "created_at": "2025-01-20T10:30:00+00:00",
  "warning": "Save this API key now. You will not be able to see it again.",
  "account_id": "user@example.com"
}
```

#### List API Keys
```bash
# User listing their account's keys
curl -H "X-API-KEY: your-api-key" \
  https://your-app.com/apikey/list

# Admin listing all keys
curl -H "X-ADMIN-KEY: your-admin-key" \
  https://your-app.com/apikey/list
```

Response (User):
```json
{
  "account_id": "user@example.com",
  "total_keys": 3,
  "api_keys": [
    {
      "api_key": "abcd1234...3456",
      "plan": "Pro",
      "description": "Main account key",
      "created_at": "2025-01-15T10:00:00+00:00",
      "last_activity": "2025-01-20T09:45:00+00:00",
      "status": "active",
      "is_current": true,
      "credits_remaining": 8500,
      "memory_count": 450
    },
    {
      "api_key": "efgh5678...7890",
      "plan": "Pro",
      "description": "Mobile app key",
      "created_at": "2025-01-18T14:30:00+00:00",
      "last_activity": "2025-01-19T16:20:00+00:00",
      "status": "active",
      "is_current": false,
      "credits_remaining": 9800,
      "memory_count": 25
    }
  ]
}
```

#### Revoke API Key
```bash
# User revoking their own key
curl -X DELETE https://your-app.com/apikey/efgh5678ijkl9012mnop3456qrst7890 \
  -H "X-API-KEY: your-main-key"

# Admin revoking any key
curl -X DELETE https://your-app.com/apikey/abcd1234efgh5678ijkl9012mnop3456 \
  -H "X-ADMIN-KEY: your-admin-key"
```

Response:
```json
{
  "message": "API key revoked successfully",
  "revoked_key": "abcd1234...3456",
  "revoked_at": "2025-01-20T10:45:00+00:00",
  "note": "Key is now inactive but usage history is preserved"
}
```

### API Key Security Model

#### Permission Matrix

| Action | User (Own Keys) | User (Other Keys) | Admin |
|--------|----------------|-------------------|-------|
| Generate Key | ✅ | ❌ | ✅ |
| List Keys | ✅ (Own Account) | ❌ | ✅ (All) |
| Revoke Key | ✅ (Own Account) | ❌ | ✅ (Any) |
| View Full Key | ❌ (Only at creation) | ❌ | ❌ (Only at creation) |

#### Security Protections

1. **Key Masking**: API keys are always displayed as `abcd1234...3456` except during generation
2. **One-Time Display**: Full API keys are shown only once when generated
3. **Account Isolation**: Users can only see and manage keys for their own account
4. **Revocation Safety**: Cannot revoke your only active API key (prevents lockout)
5. **History Preservation**: Revoked keys are marked inactive, not deleted
6. **Admin Oversight**: Admins can manage any user's keys for support purposes

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
- `POST /apikey/new` - Free
- `GET /apikey/list` - Free
- `DELETE /apikey/<key>` - Free
- `GET /health` - Free

## Quick Start

```bash
python main.py
```

Server runs on port 5000 and is accessible at `https://your-repl-name.replit.app/`

## API Endpoints

### Authentication & API Key Management
- `POST /signup` - Create new user account (returns API key)
- `POST /login` - Login (placeholder)
- `GET /credits` - Check credit status and memory usage
- `POST /apikey/new` - Generate new API key (admin or user auth required)
- `GET /apikey/list` - List API keys for account (admin or user auth required)
- `DELETE /apikey/<key>` - Revoke API key (admin or user auth required)

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
- `ADMIN_KEY` - Admin access key for user management (default: `admin-secret-key`)

## User Management Workflows

### Creating Your First Account

```bash
curl -X POST https://your-app.com/signup \
  -H "Content-Type: application/json" \
  -d '{
    "plan": "Pro",
    "email": "user@example.com"
  }'
```

Response includes your API key - **save it immediately**:
```json
{
  "message": "Account created successfully",
  "api_key": "abcd1234efgh5678ijkl9012mnop3456",
  "user": {
    "plan": "Pro",
    "credits_remaining": 10000,
    "memory_limit": 2000
  },
  "warning": "Save your API key securely. You will not be able to see it again."
}
```

### Generating Additional API Keys

For different applications or team members:

```bash
curl -X POST https://your-app.com/apikey/new \
  -H "X-API-KEY: your-main-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Mobile app key"
  }'
```

### Managing Your API Keys

List all keys for your account:
```bash
curl -H "X-API-KEY: your-api-key" \
  https://your-app.com/apikey/list
```

Revoke a key you no longer need:
```bash
curl -X DELETE https://your-app.com/apikey/old-key-to-revoke \
  -H "X-API-KEY: your-main-key"
```

### Admin User Management

Admins can create keys for users:
```bash
curl -X POST https://your-app.com/apikey/new \
  -H "X-ADMIN-KEY: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "plan": "Free",
    "description": "Initial account setup"
  }'
```

View all users and their API keys:
```bash
curl -H "X-ADMIN-KEY: your-admin-key" \
  https://your-app.com/admin/users
```

## API Key Best Practices

### For Users
1. **Save Keys Immediately**: API keys are shown only once during generation
2. **Use Descriptive Names**: Add meaningful descriptions to identify key purposes
3. **Generate Separate Keys**: Use different keys for different applications/environments
4. **Revoke Unused Keys**: Regularly audit and revoke keys you no longer need
5. **Keep One Active**: Always maintain at least one active key for account access

### For Developers
1. **Environment Variables**: Store API keys in environment variables, never in code
2. **Key Rotation**: Regularly generate new keys and revoke old ones
3. **Least Privilege**: Use separate keys for different applications with appropriate plans
4. **Monitor Usage**: Check credit usage and memory consumption regularly
5. **Error Handling**: Handle 401 (invalid/revoked key) and 402 (out of credits) responses

### For Admins
1. **User Support**: Help users who lose access by generating new keys
2. **Security Incidents**: Quickly revoke compromised keys
3. **Account Management**: Create initial keys for new enterprise users
4. **Monitoring**: Track API key usage patterns and security events

## Testing

Run the API key management tests:

```bash
python test_api_key_management.py
```

Run the full test suite:

```bash
python -m pytest test_memoryos.py test_credit_system.py test_api_key_management.py -v
```

## Security Considerations

### API Key Security
1. **Cryptographic Generation**: Keys use `secrets.choice()` for cryptographic security
2. **Sufficient Length**: 32 characters provide adequate entropy
3. **Alphanumeric Only**: Keys use letters and numbers for better compatibility
4. **No Predictable Patterns**: Each key is completely random

### Access Control
1. **Account Isolation**: Users can only access their own account's keys
2. **Admin Oversight**: Admins can manage any user's keys for support
3. **Revocation Safety**: System prevents users from locking themselves out
4. **History Preservation**: Revoked keys maintain audit trail

### Data Protection
1. **Key Masking**: API keys are masked in all responses except generation
2. **Secure Storage**: Keys are stored securely in the user database
3. **No Key Recovery**: Lost keys cannot be recovered, only replaced
4. **Audit Logging**: All key operations are logged for security monitoring

## Migration from Previous Version

If upgrading from a version without API key management:

1. **Backup** your existing `users.json` and `memory.json`
2. **Deploy** new version with API key management
3. **Existing users** can continue using their current API keys
4. **Generate additional keys** as needed using the new endpoints

Existing API keys will automatically have:
- `status: "active"` added to their user record
- `description: "Legacy API key"` for identification
- Full access to the new API key management features

## Support

For issues or questions:
1. Check the health endpoint for system status
2. Review logs for API key and credit system operations
3. Use admin endpoints to manage users and API keys
4. Test API key operations with the test suite

---

**Built for Production • Credit-Managed • Memory-Limited • Secure API Keys • Monitored • Scalable**