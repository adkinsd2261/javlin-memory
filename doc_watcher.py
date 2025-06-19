
import hashlib
import json
import requests
import os
from datetime import datetime

class DocumentWatcher:
    def __init__(self, watchlist_file='watchlist.json', hashes_file='doc_hashes.json'):
        self.watchlist_file = watchlist_file
        self.hashes_file = hashes_file
        
    def load_watchlist(self):
        """Load the list of URLs to monitor"""
        try:
            with open(self.watchlist_file, 'r') as f:
                data = json.load(f)
                return data.get('urls', [])
        except FileNotFoundError:
            print(f"Watchlist file {self.watchlist_file} not found")
            return []
        except json.JSONDecodeError:
            print(f"Invalid JSON in {self.watchlist_file}")
            return []
    
    def load_previous_hashes(self):
        """Load previously stored hashes"""
        try:
            with open(self.hashes_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print(f"Invalid JSON in {self.hashes_file}")
            return {}
    
    def save_hashes(self, hashes):
        """Save current hashes to file"""
        with open(self.hashes_file, 'w') as f:
            json.dump(hashes, f, indent=2)
    
    def get_content_hash(self, url):
        """Fetch content from URL and return SHA256 hash"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text.encode('utf-8')
            return hashlib.sha256(content).hexdigest()
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def check_changes(self):
        """Check all URLs for changes"""
        urls = self.load_watchlist()
        previous_hashes = self.load_previous_hashes()
        current_hashes = {}
        changes_detected = []
        
        print(f"Checking {len(urls)} URLs for changes...")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("-" * 50)
        
        for url in urls:
            print(f"Checking: {url}")
            current_hash = self.get_content_hash(url)
            
            if current_hash is None:
                print(f"  ❌ Failed to fetch content")
                continue
                
            current_hashes[url] = {
                'hash': current_hash,
                'last_checked': datetime.now().isoformat()
            }
            
            if url in previous_hashes:
                if previous_hashes[url]['hash'] != current_hash:
                    print(f"  🔄 CHANGED - Content has been modified")
                    changes_detected.append({
                        'url': url,
                        'old_hash': previous_hashes[url]['hash'],
                        'new_hash': current_hash,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    print(f"  ✅ No changes detected")
            else:
                print(f"  📝 First time checking - baseline hash stored")
                changes_detected.append({
                    'url': url,
                    'old_hash': None,
                    'new_hash': current_hash,
                    'timestamp': datetime.now().isoformat(),
                    'note': 'Initial baseline'
                })
        
        # Save current hashes
        self.save_hashes(current_hashes)
        
        # Summary
        print("-" * 50)
        if changes_detected:
            print(f"📊 Summary: {len(changes_detected)} change(s) detected")
            for change in changes_detected:
                if change.get('note') == 'Initial baseline':
                    print(f"  • {change['url']} - Initial baseline set")
                else:
                    print(f"  • {change['url']} - Content changed")
        else:
            print("📊 Summary: No changes detected")
        
        return changes_detected

def main():
    watcher = DocumentWatcher()
    changes = watcher.check_changes()
    
    # Optionally save change log
    if changes:
        log_file = 'change_log.json'
        try:
            with open(log_file, 'r') as f:
                change_log = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            change_log = []
        
        change_log.extend(changes)
        
        with open(log_file, 'w') as f:
            json.dump(change_log, f, indent=2)
        
        print(f"📄 Changes logged to {log_file}")

if __name__ == "__main__":
    main()
