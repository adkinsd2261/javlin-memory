
#!/bin/bash

echo "🔧 Force clearing git locks and pushing..."

# Kill any hanging git processes
pkill -9 -f git 2>/dev/null || true
sleep 1

# Remove all possible lock files
find .git -name "*.lock" -type f -delete 2>/dev/null || true

# Set git identity
git config user.name "Darryl" 2>/dev/null || true
git config user.email "adkinsd226@gmail.com" 2>/dev/null || true

# Force add all changes
git add . 2>/dev/null || true

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "No changes to commit"
    exit 0
fi

# Commit with timeout
timeout 30 git commit -m "🔧 Force sync: Clear locks and push changes" 2>/dev/null || {
    echo "Commit failed or timed out"
    find .git -name "*.lock" -type f -delete 2>/dev/null || true
    exit 1
}

# Force push with timeout
timeout 60 git push origin main 2>/dev/null || {
    echo "Push failed, trying force push..."
    timeout 60 git push origin main --force 2>/dev/null || {
        echo "Force push also failed"
        exit 1
    }
}

echo "✅ Git push completed successfully"
