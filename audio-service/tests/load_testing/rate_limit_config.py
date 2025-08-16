"""
Rate Limiting Configuration for Tempo Processing API
Optimized rate limits based on processing complexity and resource usage
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import redis
import logging
from typing import Dict, Any, Optional
import time
from functools import wraps

logger = logging.getLogger(__name__)

# Redis connection for rate limiting
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=1,  # Use separate database for rate limiting
    decode_responses=True
)

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379/1",
    default_limits=["1000/hour", "100/minute"]  # Global fallback limits
)

# Rate limit configurations based on endpoint complexity and resource usage
RATE_LIMITS = {
    # Tempo processing endpoints (resource intensive)
    "tempo_processing": {
        "storage_process": "3/minute",      # Storage-based processing (recommended)
        "direct_process": "2/minute",       # Direct upload processing (more intensive)
        "sync_process": "1/minute",         # Synchronous processing (blocks worker)
    },
    
    # Information endpoints (lightweight)
    "tempo_info": {
        "presets": "60/minute",             # Get available presets
        "compatibility": "30/minute",       # System compatibility check
        "suggestions": "20/minute",         # Smart preset suggestions
    },
    
    # Performance and monitoring endpoints
    "tempo_performance": {
        "metrics": "10/minute",             # Performance metrics
        "cache_clear": "5/minute",          # Cache management (admin-like)
    },
    
    # User-specific limits (if authentication is available)
    "user_limits": {
        "free_tier": "5/hour",              # Free tier users
        "premium_tier": "50/hour",          # Premium users
        "enterprise_tier": "200/hour",      # Enterprise users
    }
}

# Enhanced rate limit decorator with dynamic limits
def dynamic_rate_limit(limit_key: str, user_tier: Optional[str] = None):
    """
    Dynamic rate limiting decorator that adjusts limits based on user tier and endpoint type
    
    Args:
        limit_key: Key to lookup rate limit (e.g., "tempo_processing.storage_process")
        user_tier: User tier for tier-based limiting (optional)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get rate limit for this endpoint
            category, endpoint = limit_key.split('.')
            base_limit = RATE_LIMITS.get(category, {}).get(endpoint, "10/minute")
            
            # Adjust limit based on user tier if available
            if user_tier and user_tier in RATE_LIMITS["user_limits"]:
                tier_limit = RATE_LIMITS["user_limits"][user_tier]
                # Use the more restrictive of the two limits
                limit = min_rate_limit(base_limit, tier_limit)
            else:
                limit = base_limit
            
            # Apply rate limiting
            try:
                await limiter.limit(limit)(request)
            except RateLimitExceeded as e:
                # Enhanced rate limit response with helpful information
                return create_rate_limit_response(e, limit_key, request)
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def min_rate_limit(limit1: str, limit2: str) -> str:
    """Compare two rate limit strings and return the more restrictive one"""
    def parse_limit(limit_str: str) -> tuple:
        count, period = limit_str.split('/')
        period_seconds = {
            'second': 1, 'minute': 60, 'hour': 3600, 'day': 86400
        }
        return int(count), period_seconds.get(period, 60)
    
    count1, period1 = parse_limit(limit1)
    count2, period2 = parse_limit(limit2)
    
    # Convert to requests per second for comparison
    rate1 = count1 / period1
    rate2 = count2 / period2
    
    return limit1 if rate1 <= rate2 else limit2


def create_rate_limit_response(
    exception: RateLimitExceeded, 
    limit_key: str, 
    request: Request
) -> JSONResponse:
    """Create enhanced rate limit response with helpful information"""
    
    # Extract useful information from the exception
    retry_after = getattr(exception, 'retry_after', 60)
    
    # Get current time and calculate reset time
    current_time = int(time.time())
    reset_time = current_time + retry_after
    
    # Create helpful error message based on endpoint type
    category = limit_key.split('.')[0] if '.' in limit_key else limit_key
    
    error_messages = {
        "tempo_processing": "You've reached the limit for tempo processing requests. This limit helps ensure optimal processing quality for all users.",
        "tempo_info": "You've made too many information requests. Please wait before requesting more data.",
        "tempo_performance": "Performance endpoint rate limit reached. These limits protect system monitoring capabilities."
    }
    
    message = error_messages.get(category, "Rate limit exceeded. Please wait before making more requests.")
    
    # Include upgrade suggestions for free tier users
    upgrade_message = ""
    if "free_tier" in str(request.url):
        upgrade_message = " Consider upgrading to Premium for higher rate limits."
    
    response_data = {
        "error": "Rate limit exceeded",
        "message": message + upgrade_message,
        "error_code": "RATE_LIMIT_EXCEEDED",
        "retry_after_seconds": retry_after,
        "reset_time": reset_time,
        "limit_type": category,
        "documentation": "https://docs.example.com/api/rate-limits",
        "current_time": current_time
    }
    
    headers = {
        "X-RateLimit-Limit": str(exception.detail.split()[0]),
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(reset_time),
        "Retry-After": str(retry_after)
    }
    
    logger.warning(f"Rate limit exceeded for {request.client.host} on {limit_key}")
    
    return JSONResponse(
        status_code=429,
        content=response_data,
        headers=headers
    )


# Custom rate limit handler for the FastAPI app
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exception handler"""
    return create_rate_limit_response(exc, "unknown", request)


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts limits based on system load and performance
    """
    
    def __init__(self):
        self.base_limits = RATE_LIMITS.copy()
        self.current_multiplier = 1.0
        self.last_adjustment = time.time()
        
    def adjust_limits_based_on_load(self, system_metrics: Dict[str, Any]):
        """
        Adjust rate limits based on system performance metrics
        
        Args:
            system_metrics: Dictionary containing system performance data
        """
        current_time = time.time()
        
        # Only adjust every 5 minutes
        if current_time - self.last_adjustment < 300:
            return
        
        # Extract relevant metrics
        cpu_usage = system_metrics.get('cpu_usage_percent', 50)
        memory_usage = system_metrics.get('memory_usage_percent', 50)
        avg_response_time = system_metrics.get('avg_response_time', 10)
        error_rate = system_metrics.get('error_rate_percent', 0)
        queue_length = system_metrics.get('queue_length', 0)
        
        # Calculate load score (0-100, higher = more stressed)
        load_score = (
            cpu_usage * 0.3 +
            memory_usage * 0.2 +
            min(avg_response_time / 30 * 50, 50) * 0.3 +  # Cap response time impact at 30s
            error_rate * 0.1 +
            min(queue_length / 10 * 10, 10) * 0.1  # Cap queue impact at 10 jobs
        )
        
        # Determine new multiplier
        if load_score > 80:
            # High load - reduce limits
            new_multiplier = 0.5
            logger.warning(f"High system load ({load_score:.1f}), reducing rate limits by 50%")
        elif load_score > 60:
            # Medium load - slightly reduce limits
            new_multiplier = 0.75
            logger.info(f"Medium system load ({load_score:.1f}), reducing rate limits by 25%")
        elif load_score < 30:
            # Low load - can increase limits
            new_multiplier = 1.5
            logger.info(f"Low system load ({load_score:.1f}), increasing rate limits by 50%")
        else:
            # Normal load - keep current limits
            new_multiplier = 1.0
        
        # Apply gradual adjustment to avoid sudden changes
        if abs(new_multiplier - self.current_multiplier) > 0.1:
            self.current_multiplier = (
                self.current_multiplier * 0.7 + new_multiplier * 0.3
            )
            logger.info(f"Adjusted rate limit multiplier to {self.current_multiplier:.2f}")
            
            # Update Redis with new limits (would require custom limiter implementation)
            self._update_redis_limits()
        
        self.last_adjustment = current_time
    
    def _update_redis_limits(self):
        """Update Redis with adjusted rate limits"""
        # This would require a custom implementation to update the limiter's Redis storage
        # For now, just log the adjustment
        logger.info("Rate limits adjusted in Redis storage")
    
    def get_current_limit(self, limit_key: str) -> str:
        """Get current rate limit with multiplier applied"""
        category, endpoint = limit_key.split('.')
        base_limit = self.base_limits.get(category, {}).get(endpoint, "10/minute")
        
        # Parse and adjust the limit
        count, period = base_limit.split('/')
        adjusted_count = max(1, int(int(count) * self.current_multiplier))
        
        return f"{adjusted_count}/{period}"


# Global adaptive limiter instance
adaptive_limiter = AdaptiveRateLimiter()


# Middleware for request tracking and adaptive limiting
class RateLimitMiddleware:
    """Custom middleware for enhanced rate limiting features"""
    
    def __init__(self, app):
        self.app = app
        self.request_counts = {}
        self.window_start = time.time()
        self.window_duration = 300  # 5 minute windows
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Track requests for adaptive limiting
        await self._track_request(request)
        
        # Continue with normal processing
        await self.app(scope, receive, send)
    
    async def _track_request(self, request: Request):
        """Track request patterns for adaptive rate limiting"""
        current_time = time.time()
        client_ip = request.client.host
        endpoint = request.url.path
        
        # Reset window if needed
        if current_time - self.window_start > self.window_duration:
            self.request_counts = {}
            self.window_start = current_time
        
        # Track request
        key = f"{client_ip}:{endpoint}"
        self.request_counts[key] = self.request_counts.get(key, 0) + 1
        
        # Check for suspicious patterns
        if self.request_counts[key] > 100:  # More than 100 requests in 5 minutes
            logger.warning(f"High request rate from {client_ip} to {endpoint}: {self.request_counts[key]} requests")


# Rate limiting utility functions
def get_user_tier(request: Request) -> str:
    """Determine user tier from request (mock implementation)"""
    # This would typically check authentication headers or user database
    auth_header = request.headers.get("Authorization", "")
    
    if "premium" in auth_header.lower():
        return "premium_tier"
    elif "enterprise" in auth_header.lower():
        return "enterprise_tier"
    else:
        return "free_tier"


def check_rate_limit_health() -> Dict[str, Any]:
    """Check rate limiting system health"""
    try:
        # Test Redis connection
        redis_client.ping()
        redis_healthy = True
        redis_info = redis_client.info('memory')
        memory_usage = redis_info.get('used_memory', 0)
    except Exception as e:
        redis_healthy = False
        memory_usage = 0
        logger.error(f"Redis health check failed: {e}")
    
    return {
        "redis_healthy": redis_healthy,
        "redis_memory_usage": memory_usage,
        "adaptive_limiter_multiplier": adaptive_limiter.current_multiplier,
        "rate_limits": RATE_LIMITS
    }


def get_rate_limit_stats() -> Dict[str, Any]:
    """Get rate limiting statistics"""
    try:
        # Get rate limit keys from Redis
        keys = redis_client.keys("slowapi:*")
        
        stats = {
            "total_rate_limit_keys": len(keys),
            "active_limits": {},
            "top_limited_ips": []
        }
        
        # Analyze rate limit usage (simplified)
        for key in keys[:100]:  # Limit to first 100 keys for performance
            value = redis_client.get(key)
            if value:
                # Extract IP and endpoint info from key
                parts = key.split(':')
                if len(parts) >= 3:
                    ip = parts[1]
                    stats["active_limits"][ip] = stats["active_limits"].get(ip, 0) + 1
        
        # Sort by most limited IPs
        stats["top_limited_ips"] = sorted(
            stats["active_limits"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get rate limit stats: {e}")
        return {"error": str(e)}


# Configuration for production deployment
PRODUCTION_RATE_LIMITS = {
    "tempo_processing": {
        "storage_process": "5/minute",      # Increased for production
        "direct_process": "3/minute",       
        "sync_process": "1/minute",         
    },
    "tempo_info": {
        "presets": "100/minute",            # Higher for production
        "compatibility": "50/minute",       
        "suggestions": "30/minute",         
    },
    "tempo_performance": {
        "metrics": "20/minute",             
        "cache_clear": "10/minute",         
    },
    "user_limits": {
        "free_tier": "10/hour",             # More generous for production
        "premium_tier": "100/hour",         
        "enterprise_tier": "500/hour",      
    }
}


def apply_production_limits():
    """Apply production rate limits"""
    global RATE_LIMITS
    RATE_LIMITS = PRODUCTION_RATE_LIMITS.copy()
    logger.info("Applied production rate limits")


if __name__ == "__main__":
    # Test rate limiting configuration
    print("Rate Limiting Configuration Test")
    print("================================")
    
    print("\nCurrent Rate Limits:")
    for category, endpoints in RATE_LIMITS.items():
        print(f"\n{category}:")
        for endpoint, limit in endpoints.items():
            print(f"  {endpoint}: {limit}")
    
    print(f"\nRedis Health: {check_rate_limit_health()}")
    print(f"Rate Limit Stats: {get_rate_limit_stats()}")