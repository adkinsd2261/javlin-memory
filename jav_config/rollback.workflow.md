
# Rollback Workflow

## Purpose
Safe rollback to last known good state

## Pre-Rollback Checks
1. **Backup Current State**
   - Create emergency backup of current files
   - Log current commit hash
   - Save current memory state

2. **Identify Rollback Target**
   - Find last good commit
   - Verify target state integrity
   - Check for data loss risks

## Rollback Steps
1. **Git Rollback**
   ```bash
   git stash  # Save current changes
   git reset --hard <target-commit>
   ```

2. **Service Restart**
   ```bash
   pkill -f "python.*main.py"
   python main.py
   ```

3. **Verification**
   - Test health endpoint
   - Verify core functionality
   - Check logs for errors

## Post-Rollback
1. **Document Issue**
   - Log what went wrong
   - Record rollback reason
   - Note lessons learned

2. **Monitor System**
   - Watch for 5 minutes
   - Verify stability
   - Check all endpoints

## Recovery Options
- Forward rollback if issues persist
- Selective file restoration
- Manual state reconstruction
