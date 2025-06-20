
# Health Check Workflow

## Purpose
Comprehensive health audit before any major operation

## Steps
1. **Health Endpoint Test**
   - Check `/health` endpoint returns 200
   - Verify status is "healthy"
   - Check response time < 1000ms

2. **Memory System Test**
   - Validate memory.json is valid JSON
   - Check file is writable
   - Verify recent entries are well-formed

3. **Code Quality Check**
   - Scan Python files for syntax errors
   - Check for bare except clauses
   - Flag TODO comments

4. **Process Health**
   - Check for stuck processes
   - Verify port availability
   - Monitor resource usage

5. **Recent Activity Review**
   - Check git status for uncommitted changes
   - Review recent log entries for errors
   - Verify last deployment was successful

## Success Criteria
- All health checks pass
- No critical warnings
- System responsive and stable

## Failure Actions
- Log specific failures
- Provide fix recommendations
- Offer recovery options
