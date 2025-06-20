# MemoryOS Clean

A bulletproof, minimal memory system built for reliability.
```

```
## Features

- ✅ Memory storage and retrieval
- ✅ Health monitoring
- ✅ Statistics tracking
- ✅ API key authentication
- ✅ GPT integration ready

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `GET /memory` - Get memories (paginated)
- `POST /memory` - Add memory (requires API key)
- `GET /stats` - Memory statistics
- `GET /gpt-status` - GPT-friendly status

## Environment Variables

- `JAVLIN_API_KEY` - API key for memory creation

## Running

```bash
python main.py
```

Server runs on port 5000.

## Memory Structure

```json
{
  "topic": "Description of what happened",
  "type": "SystemUpdate|Feature|BugFix|etc",
  "input": "What was attempted",
  "output": "What was the result",
  "success": true|false,
  "category": "system|feature|bug|etc",
  "tags": ["optional", "tags"],
  "score": 15,
  "maxScore": 25,
  "reviewed": false
}