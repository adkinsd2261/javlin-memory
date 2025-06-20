
# 🔗 API_REFERENCE.md

> **Complete reference for all API endpoints and memory schemas in Javlin/MemoryOS.**

---

## 1. Base URL and Authentication

### Base URL
```
Production: https://your-repl-name.username.repl.co
Development: http://0.0.0.0:80
```

### Authentication
- **API Key Required**: POST operations to `/memory`
- **Header**: `X-API-KEY: your_api_key`
- **Location**: Set in Replit Secrets as `JAVLIN_API_KEY`

---

## 2. Memory Management Endpoints

### POST /memory
**Create new memory entry**

```http
POST /memory
Content-Type: application/json
X-API-KEY: your_api_key

{
  "topic": "API Documentation Complete",
  "type": "Feature",
  "input": "Created comprehensive API reference",
  "output": "Full API documentation with examples",
  "score": 25,
  "maxScore": 25,
  "success": true,
  "category": "development",
  "reviewed": false
}
```

**Response:**
```json
{
  "status": "✅ Memory saved",
  "entry": {
    "topic": "API Documentation Complete",
    "timestamp": "2025-06-20T13:37:00Z",
    "auto_generated": false
  }
}
```

### GET /memory
**Retrieve memory entries with optional filtering**

```http
GET /memory?category=development&success=true&limit=10
```

**Query Parameters:**
- `category` - Filter by memory category
- `topic` - Search within topics
- `success` - Filter by success status (true/false)
- `tag` - Filter by tag
- `related_to` - Filter by related memories
- `limit` - Limit number of results

**Response:**
```json
[
  {
    "topic": "API Documentation Complete",
    "type": "Feature",
    "input": "Created comprehensive API reference",
    "output": "Full API documentation with examples",
    "score": 25,
    "maxScore": 25,
    "success": true,
    "category": "development",
    "tags": ["api", "documentation", "feature"],
    "reviewed": false,
    "timestamp": "2025-06-20T13:37:00Z"
  }
]
```

### GET /stats
**Get memory analytics and statistics**

```http
GET /stats
```

**Response:**
```json
{
  "total_memories": 42,
  "successful": 38,
  "success_rate": "90.5%",
  "categories": {
    "development": 15,
    "system": 12,
    "testing": 8
  },
  "types": {
    "Feature": 10,
    "BugFix": 8,
    "SystemTest": 6
  },
  "tags": {
    "api": 5,
    "documentation": 3,
    "feature": 8
  }
}
```

### GET /digest
**Get weekly summary and insights**

```http
GET /digest
```

**Response:** Comprehensive weekly analysis including:
- Memory summary statistics
- Most common topics and tags
- Related memory groups
- Feedback prompts for unreviewed entries
- System insights and optimization suggestions

---

## 3. System Monitoring Endpoints

### GET /system-health
**Get comprehensive system health status**

```http
GET /system-health
```

**Response:**
```json
{
  "timestamp": "2025-06-20T13:37:00Z",
  "memory": {
    "total_entries": 42,
    "file_exists": true
  },
  "git": {
    "status": "clean",
    "has_changes": false,
    "last_sync": "2025-06-20T12:00:00Z"
  },
  "agent_bible_compliance": {
    "compliant": true,
    "last_updated": "2025-06-20T10:00:00Z",
    "warnings": []
  },
  "health_score": 95
}
```

### GET /last-commit
**Get last Git commit information**

```http
GET /last-commit
```

**Response:**
```json
{
  "hash": "abc12345",
  "full_hash": "abc1234567890abcdef",
  "author": "Developer Name",
  "timestamp": "1640995200",
  "message": "feat: Add comprehensive API documentation",
  "source": "git_command"
}
```

---

## 4. Context and State Endpoints

### GET /context
**Get complete context for AI agent decision making**

```http
GET /context
```

**Response:** Complete system context including:
- Current build state
- Daily focus/intent
- Recent memories (last 5)
- Version information
- Recent commits
- Feedback summary
- System status

### GET /build-state
**Get current build state**

```http
GET /build-state
```

### POST /build-state
**Update build state**

```http
POST /build-state
Content-Type: application/json

{
  "current_phase": "documentation",
  "completion_percentage": 75,
  "next_milestone": "API testing complete"
}
```

### GET /daily-focus
**Get daily focus/intent**

### POST /daily-focus
**Set daily focus**

```http
POST /daily-focus
Content-Type: application/json

{
  "date": "2025-06-20",
  "primary_goal": "Complete API documentation",
  "priorities": ["API reference", "Testing", "Examples"]
}
```

---

## 5. Automation and Integration Endpoints

### POST /autolog
**Passive auto-logging endpoint**

```http
POST /autolog
Content-Type: application/json

{
  "input": "Working on API documentation",
  "output": "Created comprehensive reference",
  "topic": "API Documentation",
  "type": "Feature",
  "category": "development"
}
```

**Response:**
- `✅ Auto-logged` - Entry created successfully
- `⏭️ Skipped` - Importance threshold not met
- `⚠️ Manual confirmation required` - AGENT_BIBLE compliance issue

### GET /task-output
**Get latest task runner output**

### POST /git-sync
**Manually trigger GitHub sync**

```http
POST /git-sync?force=false&dry_run=true
```

**Query Parameters:**
- `force` - Force sync even without significant changes
- `dry_run` - Preview what would be synced

---

## 6. Analysis and Insights

### GET /insights
**Get system insights and analysis**

```http
GET /insights?refresh=true
```

**Query Parameters:**
- `refresh` - Force regeneration of insights

### GET /audit
**Get infrastructure audit report**

```http
GET /audit?refresh=true&save=true&format=json
```

**Query Parameters:**
- `refresh` - Run fresh audit
- `save` - Save report to file
- `format` - Report format (json/markdown)

---

## 7. User Interaction Endpoints

### POST /feedback
**Add feedback for memory entries**

```http
POST /feedback
Content-Type: application/json

{
  "memory_id": "2025-06-20T13:37:00Z",
  "rating": 5,
  "comment": "Very helpful documentation"
}
```

**Ratings:** 1-5 scale
- 1: Not helpful
- 2: Somewhat helpful  
- 3: Moderately helpful
- 4: Very helpful
- 5: Extremely helpful

### GET /unreviewed
**Get unreviewed memories for feedback**

### GET /onboarding
**Get onboarding information and capabilities**

```http
GET /onboarding
```

**Response:** Complete onboarding guide including:
- What MemoryOS can and cannot do
- Required manual steps
- Getting started guide
- AGENT_BIBLE principles
- Success verification methods

---

## 8. Configuration and Management

### GET /config
**Get system configuration**

### POST /config
**Update system configuration**

```http
POST /config
Content-Type: application/json

{
  "agent_auto_log": true,
  "auto_log_threshold": 60,
  "trusted_agents": ["Javlin Builder Agent", "Assistant"]
}
```

### GET /version
**Get version information**

### POST /version
**Update version information**

---

## 9. Memory Schema Reference

### Core Memory Object
See [MEMORY_BIBLE.md](./MEMORY_BIBLE.md) for complete schema definition.

**Required Fields:**
- `topic` (string, max 200 chars)
- `type` (enum: BugFix|Feature|Decision|Insight|BuildLog|SystemTest|Enhancement|Reflection|Emotion)
- `input` (string)
- `output` (string)
- `score` (integer, 0-25)
- `maxScore` (integer, usually 25)
- `success` (boolean)
- `category` (enum: system|development|integration|monitoring|Infrastructure)
- `reviewed` (boolean)

**Optional Fields:**
- `tags` (array, max 5 strings)
- `context` (string, auto-generated if missing)
- `related_to` (array of strings)
- `auto_generated` (boolean)
- `importance_score` (integer, 0-100)

---

## 10. Error Response Format

All endpoints return consistent error formats:

```json
{
  "error": "Description of the error",
  "status": "❌ Failed",
  "missing": ["field1", "field2"],
  "hint": "Helpful suggestion for resolution"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid API key)
- `404` - Not Found
- `500` - Internal Server Error

---

## 11. Rate Limits and Quotas

### Current Limits
- **Memory creation**: 100 requests/hour per API key
- **Read operations**: 1000 requests/hour
- **System operations**: 10 requests/minute

### Best Practices
- Cache results when possible
- Use filtering to reduce response size
- Batch operations when available
- Monitor system health before heavy usage

---

## 12. Bible Compliance Reference

All endpoints and schemas must comply with:
- **[AGENT_BIBLE.md](./AGENT_BIBLE.md)** - Agent behavior boundaries
- **[MEMORY_BIBLE.md](./MEMORY_BIBLE.md)** - Memory schema standards
- **[SECURITY_BIBLE.md](./SECURITY_BIBLE.md)** - Security requirements
- **[PRIVACY_POLICY.md](./PRIVACY_POLICY.md)** - Data handling practices

Any endpoint handling personal/user data must reference privacy policy compliance.

---

## 13. Changelog

- **2025-06-20 — Initial comprehensive API reference**
- [add more as API evolves]

---

**This API reference is the definitive guide. All implementations must match this specification.**
