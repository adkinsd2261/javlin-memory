
# Performance Configuration for MemoryOS
import os

PERFORMANCE_CONFIG = {
    "memory_cache_size": 1000,  # Cache last 1000 entries
    "pagination_default": 25,   # Default page size
    "pagination_max": 100,      # Max items per page
    "cache_timeout": 60,        # 1 minute cache
    "async_operations": True,   # Enable async where possible
    "compression": True,        # Compress large responses
    "lazy_loading": True        # Load data on demand
}

# Memory file optimization
def optimize_memory_file(memory_file_path):
    """Optimize memory file by archiving old entries"""
    try:
        import json
        import datetime
        
        with open(memory_file_path, 'r') as f:
            memory = json.load(f)
        
        # Keep only last 1000 entries for quick access
        if len(memory) > 1000:
            archive_file = memory_file_path.replace('.json', '_archive.json')
            archived_entries = memory[:-1000]
            active_entries = memory[-1000:]
            
            # Save archived entries
            with open(archive_file, 'w') as f:
                json.dump(archived_entries, f, indent=2)
            
            # Keep only active entries
            with open(memory_file_path, 'w') as f:
                json.dump(active_entries, f, indent=2)
            
            return len(archived_entries)
        
        return 0
    except Exception as e:
        print(f"Memory optimization failed: {e}")
        return 0
