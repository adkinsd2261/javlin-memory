
#!/bin/bash

echo "🔧 Aggressive git lock clearing and sync..."

# Kill ALL git processes more thoroughly
pkill -9 -f git 2>/dev/null || true
pkill -9 git 2>/dev/null || true
killall -9 git 2>/dev/null || true

# Wait for processes to die
sleep 3

# Remove ALL possible git lock files recursively
find . -name "*.lock" -path "*/.git/*" -delete 2>/dev/null || true
find .git -name "*.lock" -type f -delete 2>/dev/null || true

# Specific lock files that commonly cause issues
rm -f .git/index.lock 2>/dev/null || true
rm -f .git/refs/heads/main.lock 2>/dev/null || true
rm -f .git/HEAD.lock 2>/dev/null || true
rm -f .git/config.lock 2>/dev/null || true
rm -f .git/COMMIT_EDITMSG.lock 2>/dev/null || true
rm -f .git/refs/remotes/origin/main.lock 2>/dev/null || true

# Reset git state if corrupted
git reset --hard HEAD 2>/dev/null || true

# Configure git identity
git config user.name "Darryl" 2>/dev/null || true
git config user.email "adkinsd226@gmail.com" 2>/dev/null || true

# Check if we're in a valid git repo
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "❌ Not in a valid git repository"
    exit 1
fi

# Fetch latest from remote to avoid conflicts
git fetch origin main 2>/dev/null || echo "⚠️ Fetch failed, continuing..."

# Check for changes
if git diff --quiet && git diff --cached --quiet; then
    echo "✅ No changes to commit"
    exit 0
fi

# Force add all changes
timeout 30 git add . 2>/dev/null || {
    echo "❌ Git add failed"
    exit 1
}

# Check if there are staged changes
if git diff --cached --quiet; then
    echo "✅ No staged changes after add"
    exit 0
fi

# Create commit with timestamp to avoid conflicts
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
COMMIT_MSG="🔧 Force sync ${TIMESTAMP}: Clear locks and push changes"

# Commit with timeout
timeout 30 git commit -m "$COMMIT_MSG" 2>/dev/null || {
    echo "❌ Commit failed"
    # Clear locks again if commit failed
    find .git -name "*.lock" -type f -delete 2>/dev/null || true
    exit 1
}

# Try regular push first
if timeout 60 git push origin main 2>/dev/null; then
    echo "✅ Git push completed successfully"
    exit 0
fi

echo "⚠️ Regular push failed, trying to sync with remote..."

# Pull with rebase to sync
git pull origin main --rebase 2>/dev/null || {
    echo "⚠️ Pull rebase failed, trying merge strategy..."
    git pull origin main --no-rebase 2>/dev/null || echo "⚠️ Pull also failed"
}

# Try push again after sync
if timeout 60 git push origin main 2>/dev/null; then
    echo "✅ Git push completed after sync"
    exit 0
fi

echo "❌ All push attempts failed, but changes are committed locally"
exit 1
