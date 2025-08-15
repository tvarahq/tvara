import json
import os
import time
from typing import Dict, Optional
from datetime import datetime, timedelta

class AuthCache:
    def __init__(self, cache_dir: str = "./cache", cache_validity_minutes: int = 10):
        """
        Initialize authentication cache manager.
        
        Args:
            cache_dir (str): Directory to store cache files
            cache_validity_minutes (int): Cache validity in minutes
        """
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "composio_auth_cache.json")
        self.validity_duration = timedelta(minutes=cache_validity_minutes)
        
        os.makedirs(cache_dir, exist_ok=True)
    
    def _load_cache(self) -> Dict:
        """Load cache from JSON file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_cache(self, cache_data: Dict):
        """Save cache to JSON file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save auth cache: {e}")
    
    def is_toolkit_cached(self, toolkit: str, user_id: str = "default") -> bool:
        """
        Check if toolkit authentication is cached and valid.
        
        Args:
            toolkit (str): Toolkit name
            user_id (str): User identifier
            
        Returns:
            bool: True if cached and valid
        """
        cache_data = self._load_cache()
        key = f"{user_id}_{toolkit.lower()}"
        
        if key not in cache_data:
            return False
        
        cached_time = datetime.fromisoformat(cache_data[key]["timestamp"])
        return datetime.now() - cached_time < self.validity_duration
    
    def cache_toolkit_auth(self, toolkit: str, user_id: str = "default"):
        """
        Cache successful toolkit authentication.
        
        Args:
            toolkit (str): Toolkit name
            user_id (str): User identifier
        """
        cache_data = self._load_cache()
        key = f"{user_id}_{toolkit.lower()}"
        
        cache_data[key] = {
            "toolkit": toolkit,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "status": "authorized"
        }
        
        self._save_cache(cache_data)
    
    def clear_cache(self):
        """Clear all cached authentication data."""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
        except Exception as e:
            print(f"Failed to clear auth cache: {e}")
    
    def get_cache_status(self) -> Dict:
        """Get current cache status for debugging."""
        cache_data = self._load_cache()
        status = {}
        
        for key, data in cache_data.items():
            cached_time = datetime.fromisoformat(data["timestamp"])
            is_valid = datetime.now() - cached_time < self.validity_duration
            
            status[key] = {
                "toolkit": data["toolkit"],
                "cached_at": data["timestamp"],
                "valid": is_valid,
                "expires_in": str(self.validity_duration - (datetime.now() - cached_time)) if is_valid else "expired"
            }
        
        return status
