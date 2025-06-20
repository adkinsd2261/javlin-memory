
# MemoryOS Clean

A bulletproof, minimal memory system built for production reliability.

## Features

- ✅ Memory storage and retrieval
- ✅ Comprehensive logging and monitoring
- ✅ Health monitoring endpoints
- ✅ Statistics tracking
- ✅ API key authentication
- ✅ GPT integration ready
- ✅ Production-grade error handling

## Quick Start

```bash
python main.py
```

Server runs on port 5000 and is accessible at `https://your-repl-name.replit.app/`

## API Endpoints

### Core Endpoints
- `GET /` - Basic health check
- `GET /health` - Comprehensive health monitoring (for UptimeRobot/Cronitor)
- `GET /memory` - Get memories (paginated)
- `POST /memory` - Add memory (requires API key)
- `GET /stats` - Memory statistics
- `GET /gpt-status` - GPT-friendly status

### Monitoring Endpoints
- `GET /health` - **Primary monitoring endpoint** - Returns detailed system health

## Environment Variables

- `JAVLIN_API_KEY` - API key for memory creation (required for POST requests)

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

## 📊 Monitoring & Logging

### Health Check Setup

The `/health` endpoint provides comprehensive system monitoring and is designed for external monitoring services.

**Health Check URL:** `https://your-repl-name.replit.app/health`

**Response Format:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2025-06-20T16:01:15.025469+00:00",
  "response_time_ms": 45.2,
  "checks": {
    "memory_file_accessible": true,
    "memory_file_writable": true,
    "response_time_ok": true
  },
  "metrics": {
    "memory_entries": 150,
    "memory_file_exists": true,
    "memory_file_size_bytes": 45032
  },
  "version": "2.0.0",
  "service": "MemoryOS-Clean"
}
```

### Setting Up External Monitoring

#### UptimeRobot Setup
1. Sign up at [UptimeRobot](https://uptimerobot.com/)
2. Create new monitor:
   - **Monitor Type:** HTTP(s)
   - **URL:** `https://your-repl-name.replit.app/health`
   - **Monitoring Interval:** 5 minutes
   - **Monitor Timeout:** 30 seconds
3. Add keyword monitoring: Set keyword to `"healthy"` to ensure JSON response is correct
4. Configure alerts (email, SMS, webhook, etc.)

#### Cronitor Setup
1. Sign up at [Cronitor](https://cronitor.io/)
2. Create new monitor:
   - **Type:** HTTP Monitor
   - **URL:** `https://your-repl-name.replit.app/health`
   - **Frequency:** Every 5 minutes
3. Set up assertions:
   - Status code should be `200`
   - Response should contain `"healthy"`
   - Response time should be under `1000ms`
4. Configure notification channels

#### Other Monitoring Services
The `/health` endpoint works with any monitoring service that supports:
- HTTP GET requests
- JSON response parsing
- Status code monitoring (200 = healthy, 503 = unhealthy)

### Logging

All requests, responses, and errors are automatically logged to:

**Log File:** `memoryos.log` (in project root)

**Log Levels:**
- `INFO`: Normal operations, requests, responses
- `ERROR`: Exceptions, failures, critical issues

**Sample Log Entries:**
```
2025-06-20 16:01:15,025 - MemoryOS - INFO - REQUEST: GET /health from 172.31.128.17
2025-06-20 16:01:15,028 - MemoryOS - INFO - RESPONSE: 200 for GET /health (45.2ms)
2025-06-20 16:01:20,150 - MemoryOS - ERROR - UNHANDLED EXCEPTION: Memory file corrupted
```

### Checking Logs

**View recent logs:**
```bash
tail -f memoryos.log
```

**View last 50 log entries:**
```bash
tail -50 memoryos.log
```

**Search for errors:**
```bash
grep "ERROR" memoryos.log
```

**Search for specific timeframe:**
```bash
grep "2025-06-20 16:" memoryos.log
```

## 🚨 Troubleshooting

### Health Check Failures

#### Status: `degraded` or `unhealthy`

**Common Causes:**
1. **Memory file issues**
   - File corrupted or locked
   - Disk space full
   - Permission issues

2. **Performance issues**
   - High response times (>1000ms)
   - System resource constraints

3. **API connectivity issues**
   - Network problems
   - Port binding issues

#### Troubleshooting Steps

**Step 1: Check System Status**
```bash
# Check if process is running
ps aux | grep python

# Check memory usage
free -h

# Check disk space
df -h
```

**Step 2: Check Log Files**
```bash
# View recent errors
tail -20 memoryos.log | grep ERROR

# Check for specific issues
grep -i "exception\|error\|fail" memoryos.log | tail -10
```

**Step 3: Test Memory File**
```bash
# Verify memory file exists and is readable
ls -la memory.json

# Test JSON validity
python -m json.tool memory.json > /dev/null
```

**Step 4: Manual Health Check**
```bash
# Test health endpoint directly
curl -s https://your-repl-name.replit.app/health | python -m json.tool
```

**Step 5: Restart Service**
```bash
# Stop current process
pkill python

# Restart MemoryOS
python main.py
```

### Common Issues & Solutions

#### Issue: "Connection refused"
- **Cause:** Service not running or port issues
- **Solution:** Restart the service and verify it's listening on port 5000

#### Issue: "Memory file corrupted"
- **Cause:** Invalid JSON in memory.json
- **Solution:** Restore from backup or fix JSON syntax

#### Issue: High response times
- **Cause:** Resource constraints or large memory file
- **Solution:** Monitor system resources, consider memory file rotation

#### Issue: API key authentication failures
- **Cause:** Missing or incorrect `JAVLIN_API_KEY` environment variable
- **Solution:** Set the environment variable in Replit Secrets

### Emergency Recovery

**Backup Memory File:**
```bash
cp memory.json memory_backup_$(date +%Y%m%d_%H%M%S).json
```

**Reset Memory File (if corrupted):**
```bash
echo "[]" > memory.json
```

**View Process Information:**
```bash
ps aux | grep python
netstat -tlnp | grep :5000
```

## 🎨 Frontend Components

### Memory Timeline Component

A React component for displaying memory entries in a user-friendly timeline format.

**Features:**
- Loading states with spinner
- Empty state handling
- Error state with retry functionality
- Color-coded entry types
- Responsive design
- Real-time refresh capability

**Usage:**
```jsx
import MemoryTimeline from './MemoryTimeline';

function App() {
  return <MemoryTimeline apiUrl="https://your-repl-name.replit.app" />;
}
```

## 📈 Performance Monitoring

**Key Metrics to Monitor:**
- Response time (should be <1000ms)
- Memory file size growth
- Error rate from logs
- API endpoint availability

**Setting Up Alerts:**
- Monitor `/health` endpoint every 5 minutes
- Alert on status != "healthy"
- Alert on response time >1000ms
- Alert on HTTP status codes 5xx

## 🔧 Production Deployment

This system is designed to run reliably on Replit's production infrastructure:

1. **Autoscale Deployment** recommended for production traffic
2. **Always On** ensures 24/7 availability
3. **Custom Domain** for professional monitoring URLs
4. **Environment Variables** for secure API key management

## Support

For issues or questions:
1. Check the troubleshooting guide above
2. Review log files for specific errors
3. Test health endpoint manually
4. Restart service if needed

---

**Built for Production • Monitored • Reliable**
