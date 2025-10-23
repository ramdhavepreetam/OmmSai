"""
Progress tracking and statistics for parallel processing
Provides real-time throughput, ETA, and cost estimation
"""
import threading
import time
from datetime import datetime, timedelta
from collections import deque


class ProgressTracker:
    """Thread-safe progress tracker with throughput and ETA calculation"""

    def __init__(self, total_files=0):
        """
        Initialize progress tracker

        Args:
            total_files (int): Total number of files to process
        """
        self.total_files = total_files
        self.processed = 0
        self.success = 0
        self.partial = 0
        self.failed = 0

        self.start_time = time.time()
        self.last_update = time.time()

        # Track recent completions for throughput calculation
        self.recent_completions = deque(maxlen=100)  # Last 100 completions

        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        # Thread safety (use RLock for reentrant locking to avoid deadlock)
        self.lock = threading.RLock()

    def update(self, status='success', input_tokens=0, output_tokens=0):
        """
        Update progress with a completed file

        Args:
            status (str): Processing status (success, partial_success, failed)
            input_tokens (int): Input tokens used
            output_tokens (int): Output tokens used
        """
        with self.lock:
            self.processed += 1
            current_time = time.time()

            # Record completion time
            self.recent_completions.append(current_time)

            # Update status counts
            if status == 'success':
                self.success += 1
            elif status == 'partial_success':
                self.partial += 1
            else:
                self.failed += 1

            # Update token usage
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens

            self.last_update = current_time

    def get_throughput(self):
        """
        Calculate current throughput (files per minute)

        Returns:
            float: Files per minute
        """
        with self.lock:
            if len(self.recent_completions) < 2:
                return 0.0

            # Calculate based on recent completions
            time_span = self.recent_completions[-1] - self.recent_completions[0]
            if time_span == 0:
                return 0.0

            files_per_second = (len(self.recent_completions) - 1) / time_span
            return files_per_second * 60  # Convert to per minute

    def get_average_throughput(self):
        """
        Calculate average throughput since start

        Returns:
            float: Average files per minute
        """
        with self.lock:
            elapsed = time.time() - self.start_time
            if elapsed == 0 or self.processed == 0:
                return 0.0

            files_per_second = self.processed / elapsed
            return files_per_second * 60

    def get_eta(self):
        """
        Calculate estimated time to completion

        Returns:
            timedelta: Estimated time remaining, or None if can't calculate
        """
        with self.lock:
            remaining = self.total_files - self.processed
            if remaining <= 0:
                return timedelta(0)

            throughput = self.get_throughput()
            if throughput == 0:
                # Fall back to average throughput
                throughput = self.get_average_throughput()

            if throughput == 0:
                return None

            minutes_remaining = remaining / throughput
            return timedelta(minutes=minutes_remaining)

    def get_elapsed_time(self):
        """
        Get elapsed time since start

        Returns:
            timedelta: Elapsed time
        """
        with self.lock:
            elapsed_seconds = time.time() - self.start_time
            return timedelta(seconds=elapsed_seconds)

    def get_completion_percentage(self):
        """
        Get completion percentage

        Returns:
            float: Percentage complete (0-100)
        """
        with self.lock:
            if self.total_files == 0:
                return 0.0
            return (self.processed / self.total_files) * 100

    def get_stats(self):
        """
        Get comprehensive statistics

        Returns:
            dict: Statistics dictionary
        """
        with self.lock:
            throughput = self.get_throughput()
            avg_throughput = self.get_average_throughput()
            eta = self.get_eta()
            elapsed = self.get_elapsed_time()
            completion_pct = self.get_completion_percentage()

            return {
                'total': self.total_files,
                'processed': self.processed,
                'remaining': self.total_files - self.processed,
                'success': self.success,
                'partial_success': self.partial,
                'failed': self.failed,
                'completion_percentage': completion_pct,
                'elapsed_time': str(elapsed).split('.')[0],  # Remove microseconds
                'eta': str(eta).split('.')[0] if eta else 'Calculating...',
                'throughput': f"{throughput:.2f}",
                'average_throughput': f"{avg_throughput:.2f}",
                'input_tokens': self.total_input_tokens,
                'output_tokens': self.total_output_tokens,
                'total_tokens': self.total_input_tokens + self.total_output_tokens
            }

    def get_cost_estimate(self, input_cost_per_million=3.0, output_cost_per_million=15.0):
        """
        Calculate estimated API costs

        Args:
            input_cost_per_million (float): Cost per million input tokens (USD)
            output_cost_per_million (float): Cost per million output tokens (USD)

        Returns:
            dict: Cost breakdown
        """
        with self.lock:
            input_cost = (self.total_input_tokens / 1_000_000) * input_cost_per_million
            output_cost = (self.total_output_tokens / 1_000_000) * output_cost_per_million
            total_cost = input_cost + output_cost

            # Estimate total cost based on completion percentage
            if self.processed > 0:
                estimated_total = total_cost * (self.total_files / self.processed)
            else:
                estimated_total = 0.0

            return {
                'current_cost': f"${total_cost:.2f}",
                'estimated_total_cost': f"${estimated_total:.2f}",
                'input_cost': f"${input_cost:.2f}",
                'output_cost': f"${output_cost:.2f}",
                'input_tokens': self.total_input_tokens,
                'output_tokens': self.total_output_tokens
            }

    def format_summary(self):
        """
        Format a human-readable summary

        Returns:
            str: Formatted summary
        """
        stats = self.get_stats()
        costs = self.get_cost_estimate()

        summary = f"""
Progress Summary:
================
Files: {stats['processed']}/{stats['total']} ({stats['completion_percentage']:.1f}%)
Success: {stats['success']} | Partial: {stats['partial_success']} | Failed: {stats['failed']}

Performance:
-----------
Elapsed: {stats['elapsed_time']}
ETA: {stats['eta']}
Throughput: {stats['throughput']} files/min (current)
Average: {stats['average_throughput']} files/min

API Usage:
----------
Tokens: {stats['total_tokens']:,} ({stats['input_tokens']:,} in, {stats['output_tokens']:,} out)
Cost: {costs['current_cost']} (estimated total: {costs['estimated_total_cost']})
        """.strip()

        return summary

    def set_total(self, total):
        """Update total file count"""
        with self.lock:
            self.total_files = total
