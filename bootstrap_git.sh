
#!/bin/bash

echo "🔧 Setting Git identity..."
git config --global user.name "Addyn Adkins"
git config --global user.email "adkinsd2261@gmail.com"

echo "🧹 Removing stale lock files..."
rm -f .git/index.lock
rm -f .git/refs/heads/main.lock

echo "🔗 Adding remote if missing..."
git remote get-url origin &>/dev/null || git remote add origin https://github.com/adkinsd2261/memoryos.git

echo "📦 Staging all changes..."
git add .

echo "📝 Committing files..."
git commit -m "Initial sync with version automation"

echo "🚀 Pushing to GitHub..."
git push origin main

echo "📡 Triggering sync endpoint..."
curl -X POST "http://localhost/git-sync?force=true"

echo "✅ Git setup complete!"
