# Jav - Personal Dev Rules

## My Development Style
- **Practical, fast, proactive, clear** - No hand-holding
- **Show me the problem, give me the fix** - Don't explain why I should care
- **Preempt errors before they happen** - Audit before deploy
- **Keep me in flow** - Minimize context switching

## Common Patterns I Use
- Always run health checks before deploy
- Test endpoints manually with curl
- Check logs for errors after changes
- Git commit frequently with clear messages
- Use bulletproof error handling

## My Anti-Patterns (Flag These!)
- Skipping tests before deploy
- Leaving TODO comments in production code
- Not checking health endpoint after changes
- Silent failures or death loops
- Generic error messages without context

## Preferred Checks
- [ ] Health endpoint returns 200
- [ ] Memory file is valid JSON
- [ ] No syntax errors in Python files
- [ ] All TODOs are addressed or documented
- [ ] Error handling is comprehensive
- [ ] Logs are meaningful and searchable

## Debug Process
1. Check health endpoint first
2. Review recent logs for errors
3. Test the specific failing component
4. Fix root cause, not symptoms
5. Verify fix with health check
6. Document the fix in memory

## Deployment Rules
- Never deploy without running tests
- Always check health endpoint post-deploy
- Have rollback plan ready
- Monitor for 5 minutes after deploy
- Log deployment in memory system
