
#!/usr/bin/env python3
"""
Sync Upgrades from Memory
Automatically updates SYSTEM_UPGRADES.md with relevant memory entries
"""

import json
import argparse
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, 'memory.json')
UPGRADES_FILE = os.path.join(BASE_DIR, 'SYSTEM_UPGRADES.md')

def load_memory_entries() -> List[Dict[Any, Any]]:
    """Load memory entries from memory.json"""
    try:
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading memory file: {e}")
        return []

def filter_relevant_entries(memory: List[Dict[Any, Any]], limit: int = 20) -> List[Dict[Any, Any]]:
    """Filter for relevant system upgrade entries"""
    # Get last N entries
    recent_entries = memory[-limit:] if len(memory) > limit else memory
    
    # Filter criteria
    relevant_types = ["BuildLog", "SystemUpdate", "SystemTest", "VersionChange"]
    relevant_categories = ["system", "Infrastructure", "integration", "development"]
    
    filtered = []
    for entry in recent_entries:
        # Check if already synced
        if entry.get('synced', False):
            continue
            
        # Must be successful
        if not entry.get('success', False):
            continue
            
        # Check type and category
        entry_type = entry.get('type', '')
        entry_category = entry.get('category', '')
        
        if (entry_type in relevant_types or 
            entry_category in relevant_categories):
            filtered.append(entry)
    
    return filtered

def load_existing_upgrades() -> str:
    """Load existing SYSTEM_UPGRADES.md content"""
    try:
        with open(UPGRADES_FILE, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"⚠️  {UPGRADES_FILE} not found, will create new file")
        return ""

def entry_already_documented(entry: Dict[Any, Any], existing_content: str) -> bool:
    """Check if entry is already documented in upgrades file"""
    topic = entry.get('topic', '')
    timestamp = entry.get('timestamp', '')
    
    # Simple check for topic or timestamp in existing content
    if topic in existing_content:
        return True
    
    # Check for similar timestamp (same day)
    try:
        entry_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d')
        if entry_date in existing_content:
            # More thorough check needed - look for similar topics on same day
            lines = existing_content.split('\n')
            for line in lines:
                if entry_date in line and any(word in line.lower() for word in topic.lower().split()[:3]):
                    return True
    except:
        pass
    
    return False

def format_upgrade_entry(entry: Dict[Any, Any]) -> str:
    """Format a memory entry as an upgrade section"""
    timestamp = entry.get('timestamp', '')
    topic = entry.get('topic', 'Unknown')
    input_text = entry.get('input', '')
    output_text = entry.get('output', '')
    entry_type = entry.get('type', 'SystemUpdate')
    category = entry.get('category', 'system')
    tags = entry.get('tags', [])
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        formatted_time = dt.strftime('%Y-%m-%d %H:%M UTC')
    except:
        formatted_time = timestamp
    
    # Create section
    section = f"\n### [{formatted_time}] Auto-logged System Update\n\n"
    section += f"**Type**: {entry_type} | **Category**: {category}\n\n"
    section += f"- **Summary**: {topic}\n"
    
    if input_text:
        section += f"- **Context**: {input_text[:200]}{'...' if len(input_text) > 200 else ''}\n"
    
    if output_text:
        section += f"- **Result**: {output_text[:200]}{'...' if len(output_text) > 200 else ''}\n"
    
    if tags:
        section += f"- **Tags**: {', '.join(tags[:5])}\n"
    
    section += f"- **Auto-sync**: ✅ Synced from memory.json\n\n"
    
    return section

def update_upgrades_file(new_sections: List[str], dry_run: bool = False) -> bool:
    """Update SYSTEM_UPGRADES.md with new sections"""
    if not new_sections:
        print("ℹ️  No new sections to add")
        return False
    
    existing_content = load_existing_upgrades()
    
    # Find insertion point (before last section or at end)
    if existing_content:
        # Insert before the final closing or at end
        if "## 🎯 Usage Recommendations" in existing_content:
            parts = existing_content.split("## 🎯 Usage Recommendations")
            new_content = parts[0] + ''.join(new_sections) + "\n## 🎯 Usage Recommendations" + parts[1]
        else:
            new_content = existing_content + '\n'.join(new_sections)
    else:
        # Create new file
        header = """# MemoryOS System Upgrades Summary

## 🚀 Recent Enhancements

"""
        new_content = header + ''.join(new_sections)
    
    if dry_run:
        print(f"🔍 DRY RUN - Would add {len(new_sections)} new section(s):")
        for i, section in enumerate(new_sections, 1):
            print(f"\n--- Section {i} ---")
            print(section[:300] + "..." if len(section) > 300 else section)
        return True
    
    # Write updated content
    try:
        with open(UPGRADES_FILE, 'w') as f:
            f.write(new_content)
        print(f"✅ Updated {UPGRADES_FILE} with {len(new_sections)} new section(s)")
        return True
    except Exception as e:
        print(f"❌ Error writing upgrades file: {e}")
        return False

def mark_entries_synced(entries: List[Dict[Any, Any]], memory: List[Dict[Any, Any]]) -> bool:
    """Mark memory entries as synced"""
    try:
        # Find and update entries in memory
        synced_topics = {entry['topic'] for entry in entries}
        
        for entry in memory:
            if entry.get('topic') in synced_topics:
                entry['synced'] = True
        
        # Save updated memory
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=2)
        
        print(f"📝 Marked {len(entries)} entries as synced in memory.json")
        return True
        
    except Exception as e:
        print(f"❌ Error marking entries as synced: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Sync system upgrades from memory to documentation")
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    parser.add_argument('--auto', action='store_true', help='Automatically commit changes')
    parser.add_argument('--limit', type=int, default=20, help='Number of recent entries to check (default: 20)')
    
    args = parser.parse_args()
    
    print("🔍 Loading memory entries...")
    memory = load_memory_entries()
    
    if not memory:
        print("❌ No memory entries found")
        sys.exit(1)
    
    print(f"📊 Found {len(memory)} total memory entries")
    
    # Filter relevant entries
    relevant_entries = filter_relevant_entries(memory, args.limit)
    print(f"🎯 Found {len(relevant_entries)} relevant system update entries")
    
    if not relevant_entries:
        print("ℹ️  No new system updates to sync")
        sys.exit(0)
    
    # Load existing upgrades to check for duplicates
    existing_content = load_existing_upgrades()
    
    # Filter out already documented entries
    new_entries = []
    for entry in relevant_entries:
        if not entry_already_documented(entry, existing_content):
            new_entries.append(entry)
        else:
            print(f"⏭️  Skipping already documented: {entry.get('topic', '')[:50]}")
    
    if not new_entries:
        print("ℹ️  All relevant entries already documented")
        sys.exit(0)
    
    print(f"📝 Found {len(new_entries)} new entries to sync")
    
    # Format new sections
    new_sections = []
    for entry in new_entries:
        section = format_upgrade_entry(entry)
        new_sections.append(section)
        print(f"  ✨ {entry.get('topic', '')[:60]}")
    
    # Update upgrades file
    success = update_upgrades_file(new_sections, args.dry_run)
    
    if success and not args.dry_run:
        # Mark entries as synced
        mark_entries_synced(new_entries, memory)
        
        if args.auto:
            print("🚀 Auto-commit mode - changes saved automatically")
        else:
            print("✅ Sync complete! Review SYSTEM_UPGRADES.md for new sections")

if __name__ == "__main__":
    main()
