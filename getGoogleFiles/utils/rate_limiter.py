"""
Rate limiting utilities with exponential backoff
Handles API rate limits for Google Drive and Anthropic APIs
"""
import time
import threading
from datetime import datetime, timedelta


class RateLimiter:
    """Thread-safe rate limiter with exponential backoff"""

    def __init__(self, max_requests_per_minute=60):
        """
        Initialize rate limiter

        Args:
            max_requests_per_minute (int): Maximum requests per minute
        """
        self.max_requests = max_requests_per_minute
        self.window = 60  # seconds
        self.requests = []
        self.lock = threading.Lock()
        self.backoff_until = None
        self.backoff_lock = threading.Lock()

    def acquire(self):
        """
        Wait if necessary to respect rate limits
        Returns when it's safe to make a request
        """
        with self.lock:
            now = datetime.now()

            # Check if we're in backoff period
            with self.backoff_lock:
                if self.backoff_until and now < self.backoff_until:
                    wait_time = (self.backoff_until - now).total_seconds()
                    time.sleep(wait_time)
                    now = datetime.now()

            # Remove old requests outside the window
            cutoff = now - timedelta(seconds=self.window)
            self.requests = [req_time for req_time in self.requests if req_time > cutoff]

            # Wait if we've hit the limit
            if len(self.requests) >= self.max_requests:
                oldest = min(self.requests)
                wait_time = (oldest + timedelta(seconds=self.window) - now).total_seconds()
                if wait_time > 0:
                    time.sleep(wait_time)
                    now = datetime.now()
                    # Clean up again after waiting
                    cutoff = now - timedelta(seconds=self.window)
                    self.requests = [req_time for req_time in self.requests if req_time > cutoff]

            # Record this request
            self.requests.append(now)

    def set_backoff(self, seconds):
        """
        Set a backoff period (e.g., when rate limited)

        Args:
            seconds (float): Seconds to wait before allowing more requests
        """
        with self.backoff_lock:
            self.backoff_until = datetime.now() + timedelta(seconds=seconds)

    def clear_backoff(self):
        """Clear any active backoff"""
        with self.backoff_lock:
            self.backoff_until = None


class ExponentialBackoff:
    """Exponential backoff for retries"""

    def __init__(self, base_delay=1, max_delay=60, max_attempts=5):
        """
        Initialize backoff strategy

        Args:
            base_delay (float): Initial delay in seconds
            max_delay (float): Maximum delay in seconds
            max_attempts (int): Maximum retry attempts
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_attempts = max_attempts

    def get_delay(self, attempt):
        """
        Calculate delay for given attempt number

        Args:
            attempt (int): Current attempt number (0-indexed)

        Returns:
            float: Delay in seconds
        """
        if attempt >= self.max_attempts:
            return None  # No more retries

        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        return delay

    def execute_with_retry(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Result of function call

        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                delay = self.get_delay(attempt)

                if delay is None:
                    # Max attempts reached
                    break

                # Check if it's a rate limit error
                error_str = str(e).lower()
                if 'rate limit' in error_str or '429' in error_str or 'too many requests' in error_str:
                    # Use longer delay for rate limit errors
                    delay = min(delay * 2, self.max_delay)

                time.sleep(delay)

        # All retries exhausted
        raise last_exception


# Global rate limiters for shared use
google_drive_limiter = RateLimiter(max_requests_per_minute=100)  # Conservative limit
claude_limiter = RateLimiter(max_requests_per_minute=50)  # Claude API limit
