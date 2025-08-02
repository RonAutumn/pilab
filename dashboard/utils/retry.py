#!/usr/bin/env python3
"""
Retry utilities for PiLab Dashboard

This module provides retry functionality for database operations.
"""

import time
import logging
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Exception raised when retry attempts are exhausted."""
    pass


def retry_on_error(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry a function on error.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay on each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed: {e}")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed")
                        raise RetryError(f"Function {func.__name__} failed after {max_attempts} attempts") from last_exception
            
            raise RetryError(f"Function {func.__name__} failed after {max_attempts} attempts") from last_exception
        
        return wrapper
    return decorator


# Alias for backward compatibility
retry_on_supabase_error = retry_on_error 