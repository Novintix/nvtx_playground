"""
Rate Limiting Guardrails
Prevents spam, abuse, and accidental overuse of tools
"""

import time
import hashlib
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, deque


class RateLimiter:
    """
    Simple in-memory rate limiter for agent actions.
    Tracks requests per tool and enforces limits.
    """
    
    def __init__(self):
        # Store timestamps of requests per tool
        # Format: {tool_name: deque([timestamp1, timestamp2, ...])}
        self.tool_requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Store recent request hashes for duplicate detection
        # Format: {request_hash: timestamp}
        self.recent_requests: Dict[str, float] = {}
        
        # Overall request tracking
        self.all_requests: deque = deque(maxlen=100)
    
    def _cleanup_old_entries(self, current_time: float, window_seconds: int):
        """Remove entries older than the time window"""
        cutoff = current_time - window_seconds
        
        # Clean tool requests
        for tool_name in list(self.tool_requests.keys()):
            timestamps = self.tool_requests[tool_name]
            # Remove old timestamps
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()
        
        # Clean recent requests (for duplicate detection)
        expired_keys = [
            key for key, ts in self.recent_requests.items()
            if ts < cutoff
        ]
        for key in expired_keys:
            del self.recent_requests[key]
        
        # Clean overall requests
        while self.all_requests and self.all_requests[0] < cutoff:
            self.all_requests.popleft()
    
    def _hash_request(self, user_request: str, tool: str) -> str:
        """Create a hash of the request for duplicate detection"""
        content = f"{user_request.lower().strip()}:{tool}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def check_rate_limit(
        self,
        tool_name: str,
        user_request: str = ""
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if the request exceeds rate limits.
        
        Args:
            tool_name: Name of the tool being called
            user_request: Original user request text (for duplicate detection)
            
        Returns:
            (is_allowed, error_message)
        """
        current_time = time.time()
        
        # Define rate limits (requests per time window)
        LIMITS = {
            "slack.post_message": (50, 3600),      # 50 per hour
            "calendar.create_event": (50, 3600),   # 50 per hour
            "overall": (100, 3600),                # 100 total per hour
        }
        
        # Duplicate detection window (30 seconds)
        DUPLICATE_WINDOW = 30
        
        # Cleanup old entries
        self._cleanup_old_entries(current_time, 3600)  # 1 hour window
        
        # 1. Check for duplicate request (same request within 30 seconds)
        if user_request:
            request_hash = self._hash_request(user_request, tool_name)
            if request_hash in self.recent_requests:
                time_since = current_time - self.recent_requests[request_hash]
                if time_since < DUPLICATE_WINDOW:
                    wait_time = int(DUPLICATE_WINDOW - time_since)
                    return False, f"Duplicate request detected. Please wait {wait_time} seconds before retrying."
            
            # Record this request
            self.recent_requests[request_hash] = current_time
        
        # 2. Check overall rate limit
        overall_limit, overall_window = LIMITS["overall"]
        if len(self.all_requests) >= overall_limit:
            oldest = self.all_requests[0]
            time_until_reset = int(overall_window - (current_time - oldest))
            return False, f"Too many requests. Global limit: {overall_limit} per hour. Try again in {time_until_reset // 60} minutes."
        
        # 3. Check tool-specific rate limit
        if tool_name in LIMITS:
            limit, window = LIMITS[tool_name]
            tool_timestamps = self.tool_requests[tool_name]
            
            if len(tool_timestamps) >= limit:
                oldest = tool_timestamps[0]
                time_until_reset = int(window - (current_time - oldest))
                minutes = time_until_reset // 60
                seconds = time_until_reset % 60
                
                time_str = f"{minutes} minutes" if minutes > 0 else f"{seconds} seconds"
                
                return False, f"Rate limit exceeded for {tool_name}. Limit: {limit} per hour. Try again in {time_str}."
        
        # All checks passed - record the request and allow it
        self.tool_requests[tool_name].append(current_time)
        self.all_requests.append(current_time)
        
        return True, None
    
    def get_stats(self) -> Dict[str, any]:
        """Get current rate limit statistics"""
        current_time = time.time()
        self._cleanup_old_entries(current_time, 3600)
        
        stats = {
            "overall_requests_last_hour": len(self.all_requests),
            "tool_usage": {}
        }
        
        for tool_name, timestamps in self.tool_requests.items():
            stats["tool_usage"][tool_name] = len(timestamps)
        
        return stats


# Global rate limiter instance (shared across requests)
_rate_limiter = RateLimiter()


def check_rate_limit(tool_name: str, user_request: str = "") -> Tuple[bool, Optional[str]]:
    """
    Check if a tool request is within rate limits.
    
    Args:
        tool_name: Name of the tool to check
        user_request: Original user request (for duplicate detection)
        
    Returns:
        (is_allowed, error_message)
    """
    return _rate_limiter.check_rate_limit(tool_name, user_request)


def get_rate_limit_stats() -> Dict[str, any]:
    """Get current rate limiting statistics"""
    return _rate_limiter.get_stats()
