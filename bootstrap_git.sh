
#!/bin/bash
echo "🔧 Setting Git identity..."
git config --global user.name "adkinsd2261"
git config --global user.email "adkinsd2261@gmail.com"

echo "🧹 Removing lock files..."
rm -f .git/index.lock .git/refs/heads/main.lock

echo "🔗 Checking or adding remote..."
git remote get-url origin &>/dev/null || git remote add origin https://github.com/adkinsd2261/memoryos.git

echo "📦 Staging changes..."
git add .

echo "📝 Committing if needed..."
git diff --cached --quiet || git commit -m '🔁 Bootstrap sync: Git identity and push configured'

echo "🚀 Pushing to GitHub..."
git push origin main

echo "📡 Triggering Git sync endpoint..."
curl -X POST "http://localhost/git-sync?force=true"
