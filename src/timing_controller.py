"""
Timing Controller for CinePi timelapse system.
Handles precise timing control and drift correction for accurate capture intervals.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class TimingStats:
    """Statistics for timing accuracy and drift correction."""
    expected_interval: float
    actual_interval: float
    drift_accumulated: float
    total_drift: float
    capture_count: int
    start_time: float
    last_capture_time: float
    next_capture_time: float
    system_clock_adjustments: int
    avg_interval: float
    min_interval: float
    max_interval: float
    interval_history: deque


class TimingController:
    """
    Precise timing controller with drift correction for timelapse photography.
    
    Features:
    - High-precision timing using time.perf_counter()
    - Drift correction to prevent cumulative timing errors
    - System clock adjustment detection
    - Comprehensive timing statistics
    - Adaptive sleep intervals for optimal performance
    - Configurable drift warning suppression
    """
    
    def __init__(self, interval_seconds: float, max_drift_threshold: float = 1.0, suppress_drift_warnings: bool = False):
        """
        Initialize the timing controller.
        
        Args:
            interval_seconds: Target interval between captures in seconds
            max_drift_threshold: Maximum allowed drift before correction (seconds)
        """
        if interval_seconds <= 0:
            raise ValueError("Interval must be greater than 0")
        
        self.interval_seconds = interval_seconds
        self.max_drift_threshold = max_drift_threshold
        
        # High-precision timing using perf_counter
        self.start_time = time.perf_counter()
        self.last_capture_time = self.start_time
        self.next_capture_time = self.start_time + interval_seconds
        
        # Drift tracking
        self.drift_accumulated = 0.0
        self.total_drift = 0.0
        self.capture_count = 0
        
        # System clock monitoring
        self.last_system_time = time.time()
        self.system_clock_adjustments = 0
        
        # Statistics tracking
        self.interval_history = deque(maxlen=100)  # Keep last 100 intervals
        self.min_interval = float('inf')
        self.max_interval = 0.0
        
        # Performance optimization
        self.sleep_interval = min(1.0, interval_seconds / 10)  # Adaptive sleep
        
        # Drift warning suppression
        self.suppress_drift_warnings = suppress_drift_warnings
        self.drift_warning_count = 0
        self.max_drift_warnings = 3  # Show first 3 warnings, then downgrade to INFO
        
        logger.info(f"Timing controller initialized: interval={interval_seconds}s, "
                   f"max_drift_threshold={max_drift_threshold}s, "
                   f"drift_warnings={'suppressed' if suppress_drift_warnings else 'enabled'}")
    
    def _detect_system_clock_adjustment(self) -> bool:
        """
        Detect if the system clock has been adjusted (e.g., NTP sync).
        
        Returns:
            True if system clock adjustment detected
        """
        current_system_time = time.time()
        time_diff = abs(current_system_time - self.last_system_time)
        
        # If system time jumped more than 1 second, likely a clock adjustment
        if time_diff > 1.0:
            self.drift_warning_count += 1
            
            # Determine log level based on suppression settings and warning count
            if self.suppress_drift_warnings:
                # Suppress all drift warnings
                log_level = logging.DEBUG
            elif self.drift_warning_count <= self.max_drift_warnings:
                # First N warnings at WARNING level
                log_level = logging.WARNING
            else:
                # Subsequent warnings at INFO level
                log_level = logging.INFO
            
            # Log the adjustment with appropriate level
            if log_level == logging.WARNING:
                logger.warning(f"System clock adjustment detected: {time_diff:.2f}s jump")
            elif log_level == logging.INFO:
                logger.info(f"System clock adjustment detected: {time_diff:.2f}s jump (warning #{self.drift_warning_count})")
            else:
                logger.debug(f"System clock adjustment detected: {time_diff:.2f}s jump (suppressed)")
            
            self.system_clock_adjustments += 1
            self.last_system_time = current_system_time
            return True
        
        self.last_system_time = current_system_time
        return False
    
    def _calculate_drift_correction(self, actual_interval: float) -> float:
        """
        Calculate drift correction to apply to next capture time.
        
        Args:
            actual_interval: Actual time since last capture
            
        Returns:
            Drift correction to apply (seconds)
        """
        drift = actual_interval - self.interval_seconds
        self.drift_accumulated += drift
        self.total_drift += abs(drift)
        
        # Apply correction to prevent cumulative drift
        correction = -self.drift_accumulated
        
        # Limit correction to prevent over-correction
        max_correction = self.interval_seconds * 0.5
        correction = max(-max_correction, min(max_correction, correction))
        
        logger.debug(f"Drift: {drift:.3f}s, Accumulated: {self.drift_accumulated:.3f}s, "
                    f"Correction: {correction:.3f}s")
        
        return correction
    
    def _update_statistics(self, actual_interval: float):
        """Update timing statistics."""
        self.interval_history.append(actual_interval)
        self.min_interval = min(self.min_interval, actual_interval)
        self.max_interval = max(self.max_interval, actual_interval)
    
    def wait_for_next_capture(self) -> Tuple[bool, float]:
        """
        Wait until the next scheduled capture time with drift correction.
        
        Returns:
            Tuple of (should_capture, time_until_next)
        """
        current_time = time.perf_counter()
        time_until_next = self.next_capture_time - current_time
        
        # Check for system clock adjustments
        self._detect_system_clock_adjustment()
        
        # If it's time to capture
        if time_until_next <= 0:
            return True, 0.0
        
        # Sleep in small intervals to maintain responsiveness
        while time_until_next > 0:
            sleep_time = min(self.sleep_interval, time_until_next)
            time.sleep(sleep_time)
            
            current_time = time.perf_counter()
            time_until_next = self.next_capture_time - current_time
            
            # Check for system clock adjustments during sleep
            self._detect_system_clock_adjustment()
        
        return True, 0.0
    
    def capture_completed(self) -> None:
        """
        Called after a capture is completed to update timing calculations.
        """
        current_time = time.perf_counter()
        actual_interval = current_time - self.last_capture_time
        
        # Update statistics
        self._update_statistics(actual_interval)
        
        # Calculate drift correction
        correction = self._calculate_drift_correction(actual_interval)
        
        # Update timing for next capture
        self.last_capture_time = current_time
        self.next_capture_time = current_time + self.interval_seconds + correction
        self.capture_count += 1
        
        # Log timing information
        logger.debug(f"Capture #{self.capture_count}: interval={actual_interval:.3f}s, "
                    f"drift={actual_interval - self.interval_seconds:.3f}s, "
                    f"next_capture={self.next_capture_time - current_time:.1f}s")
    
    def get_timing_stats(self) -> TimingStats:
        """
        Get comprehensive timing statistics.
        
        Returns:
            TimingStats object with current timing information
        """
        current_time = time.perf_counter()
        
        # Calculate average interval
        avg_interval = 0.0
        if self.interval_history:
            avg_interval = sum(self.interval_history) / len(self.interval_history)
        
        return TimingStats(
            expected_interval=self.interval_seconds,
            actual_interval=current_time - self.last_capture_time,
            drift_accumulated=self.drift_accumulated,
            total_drift=self.total_drift,
            capture_count=self.capture_count,
            start_time=self.start_time,
            last_capture_time=self.last_capture_time,
            next_capture_time=self.next_capture_time,
            system_clock_adjustments=self.system_clock_adjustments,
            avg_interval=avg_interval,
            min_interval=self.min_interval if self.min_interval != float('inf') else 0.0,
            max_interval=self.max_interval,
            interval_history=self.interval_history.copy()
        )
    
    def get_time_until_next(self) -> float:
        """
        Get time until next capture.
        
        Returns:
            Seconds until next capture
        """
        current_time = time.perf_counter()
        return max(0.0, self.next_capture_time - current_time)
    
    def get_elapsed_time(self) -> float:
        """
        Get total elapsed time since start.
        
        Returns:
            Elapsed time in seconds
        """
        current_time = time.perf_counter()
        return current_time - self.start_time
    
    def get_drift_info(self) -> Dict[str, float]:
        """
        Get drift correction information.
        
        Returns:
            Dictionary with drift statistics
        """
        stats = self.get_timing_stats()
        
        return {
            'current_drift': stats.drift_accumulated,
            'total_drift': stats.total_drift,
            'avg_drift_per_capture': stats.total_drift / max(1, stats.capture_count),
            'drift_percentage': (stats.drift_accumulated / self.interval_seconds) * 100,
            'system_clock_adjustments': stats.system_clock_adjustments,
            'drift_warnings_suppressed': self.suppress_drift_warnings,
            'drift_warning_count': self.drift_warning_count
        }
    
    def reset_drift(self) -> None:
        """Reset accumulated drift (useful after system clock adjustments)."""
        logger.info("Resetting accumulated drift")
        self.drift_accumulated = 0.0
        self.next_capture_time = time.perf_counter() + self.interval_seconds
    
    def reset_drift_warnings(self) -> None:
        """Reset drift warning counter (useful for new sessions)."""
        logger.debug("Resetting drift warning counter")
        self.drift_warning_count = 0
    
    def adjust_interval(self, new_interval: float) -> None:
        """
        Adjust the capture interval (useful for dynamic interval changes).
        
        Args:
            new_interval: New interval in seconds
        """
        logger.info(f"Adjusting interval from {self.interval_seconds}s to {new_interval}s")
        self.interval_seconds = new_interval
        self.sleep_interval = min(1.0, new_interval / 10)
        
        # Recalculate next capture time
        current_time = time.perf_counter()
        self.next_capture_time = current_time + new_interval
    
    def log_timing_report(self) -> None:
        """Log a comprehensive timing report."""
        stats = self.get_timing_stats()
        drift_info = self.get_drift_info()
        
        logger.info("=== Timing Accuracy Report ===")
        logger.info(f"Captures completed: {stats.capture_count}")
        logger.info(f"Expected interval: {stats.expected_interval:.3f}s")
        logger.info(f"Average interval: {stats.avg_interval:.3f}s")
        logger.info(f"Interval range: {stats.min_interval:.3f}s - {stats.max_interval:.3f}s")
        logger.info(f"Current drift: {stats.drift_accumulated:.3f}s ({drift_info['drift_percentage']:.2f}%)")
        logger.info(f"Total drift: {stats.total_drift:.3f}s")
        logger.info(f"System clock adjustments: {stats.system_clock_adjustments}")
        logger.info(f"Elapsed time: {self.get_elapsed_time():.1f}s")
        logger.info("=" * 30) 