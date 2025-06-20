
# Release Workflow

## Purpose
Step-by-step production release with custom checks

## Pre-Release Checks
1. **Code Quality**
   - [ ] All Python files have valid syntax
   - [ ] No TODO comments in production code
   - [ ] Error handling is comprehensive
   - [ ] Logging is meaningful and searchable

2. **Testing**
   - [ ] Health endpoint returns 200
   - [ ] All API endpoints respond correctly
   - [ ] Memory system functions properly
   - [ ] No recent errors in logs

3. **Git State**
   - [ ] All changes committed
   - [ ] Working directory clean
   - [ ] Commit messages are clear
   - [ ] No merge conflicts

## Release Steps
1. **Final Health Check**
   ```bash
   curl -s http://0.0.0.0:5000/health | python -m json.tool
   ```

2. **Run Tests**
   ```bash
   python -m pytest test_memoryos.py -v
   ```

3. **Create Release Tag**
   ```bash
   git tag -a v$(date +%Y%m%d-%H%M) -m "Release $(date)"
   ```

4. **Deploy**
   - Use Replit deployment
   - Monitor startup logs
   - Verify health endpoint

## Post-Release
1. **Monitor for 5 minutes**
   - Watch logs for errors
   - Test critical endpoints
   - Check system metrics

2. **Document Release**
   - Log to memory system
   - Update version info
   - Note any issues

## Rollback Plan
If issues detected:
1. Immediate rollback to previous version
2. Document what went wrong
3. Fix issues before retry
