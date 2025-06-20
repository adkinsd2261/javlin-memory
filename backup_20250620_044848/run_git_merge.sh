
#!/bin/bash

# Git Divergence Resolution Script
# This script safely merges MemoryOS and Javlin Memory Engine projects

echo "🔧 Git Divergence Resolution Tool"
echo "=================================="
echo ""
echo "This will:"
echo "1. Backup your current workspace"
echo "2. Merge MemoryOS into /MemoryOS/ subdirectory"
echo "3. Keep Javlin Memory Engine in root"
echo "4. Push everything to GitHub"
echo ""

# Make sure we have Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

# Run the merge script
python3 git_merge_divergent.py

# Check result
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Merge completed successfully!"
    echo "📁 Your projects are now merged in the repository"
    echo "🌐 Check your GitHub repository"
else
    echo ""
    echo "❌ Merge failed - check logs for details"
    echo "💾 Your files are backed up"
fi
