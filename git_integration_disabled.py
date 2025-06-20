
#!/usr/bin/env python3
"""
Git Integration Status - Manual Only Mode
This file indicates that automated Git integration is disabled per AGENT_BIBLE.md
"""

import datetime

GIT_INTEGRATION_STATUS = {
    "automated_git_enabled": False,
    "manual_git_only": True,
    "disabled_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "reason": "Compliance with AGENT_BIBLE.md - manual operator control required",
    "blocked_operations": [
        "git add",
        "git commit", 
        "git push",
        "git pull",
        "git merge",
        "git rebase"
    ],
    "manual_workflow_required": True,
    "operator_confirmation_needed": True
}

def is_git_automation_enabled():
    """Check if Git automation is enabled"""
    return GIT_INTEGRATION_STATUS["automated_git_enabled"]

def get_git_status():
    """Get current Git integration status"""
    return GIT_INTEGRATION_STATUS

def require_manual_git_message():
    """Get message for manual Git requirement"""
    return """
⚠️ **Manual Git Operation Required**

Per AGENT_BIBLE.md: All Git operations must be performed manually by the operator.

**To proceed:**
1. Open Replit Shell
2. Execute Git commands manually:
   ```
   git add .
   git commit -m "Your commit message"
   git push origin main
   ```
3. Confirm completion via system endpoint

**Automated Git integration is disabled for compliance.**
"""
