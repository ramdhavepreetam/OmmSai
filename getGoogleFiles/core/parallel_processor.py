"""
Parallel processing engine for handling large batches of files
Uses ThreadPoolExecutor for concurrent downloads and AI processing
"""
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Callable, Optional

from .google_drive import GoogleDriveService
from .claude_processor import ClaudeProcessor
from ..utils.checkpoint_manager import CheckpointManager
from ..utils.progress_tracker import ProgressTracker
from ..utils.rate_limiter import ExponentialBackoff, google_drive_limiter, claude_limiter
from ..utils.file_handler import FileHandler
from ..config.settings import Settings


class ParallelProcessor:
    """Parallel processing engine for prescription extraction"""

    def __init__(
        self,
        google_service: GoogleDriveService,
        claude_processor: ClaudeProcessor,
        max_workers: int = None,
        checkpoint_file: str = 'processing_checkpoint.json',
        enable_checkpointing: bool = True,
        progress_callback: Optional[Callable] = None
    ):
        """
        Initialize parallel processor

        Args:
            google_service: GoogleDriveService instance
            claude_processor: ClaudeProcessor instance
            max_workers: Number of concurrent workers (default: from settings)
            checkpoint_file: Path to checkpoint file
            enable_checkpointing: Enable checkpoint/resume capability
            progress_callback: Optional callback function for progress updates
        """
        self.google_service = google_service
        self.claude_processor = claude_processor
        self.max_workers = max_workers or Settings.MAX_WORKERS
        self.progress_callback = progress_callback

        # Checkpoint manager
        self.checkpoint_manager = None
        if enable_checkpointing:
            self.checkpoint_manager = CheckpointManager(
                checkpoint_file=checkpoint_file,
                batch_size=Settings.CHECKPOINT_BATCH_SIZE
            )

        # Progress tracker
        self.progress_tracker = ProgressTracker()

        # Retry logic
        self.retry_backoff = ExponentialBackoff(
            base_delay=Settings.RETRY_BASE_DELAY,
            max_delay=Settings.RETRY_MAX_DELAY,
            max_attempts=Settings.RETRY_ATTEMPTS
        )

        # Control flags
        self.is_cancelled = False
        self.cancel_lock = threading.Lock()

    def cancel(self):
        """Cancel processing"""
        with self.cancel_lock:
            self.is_cancelled = True

    def is_processing_cancelled(self):
        """Check if processing was cancelled"""
        with self.cancel_lock:
            return self.is_cancelled

    def _process_single_file(self, file: Dict) -> Dict:
        """
        Process a single file with rate limiting and retry logic

        Args:
            file: File metadata dict from Google Drive

        Returns:
            dict: Extraction result
        """
        file_id = file['id']
        file_name = file['name']

        # Check if already processed (from checkpoint)
        if self.checkpoint_manager and not self.checkpoint_manager.should_process(file_id):
            return None  # Skip already processed files

        try:
            # Download file with rate limiting
            google_drive_limiter.acquire()

            def download_with_retry():
                return self.google_service.download_file(
                    file_id,
                    file_name,
                    file['mimeType']
                )

            file_path = self.retry_backoff.execute_with_retry(download_with_retry)

            if not file_path:
                raise Exception("Download failed")

            # Process with Claude AI with rate limiting
            claude_limiter.acquire()

            def extract_with_retry():
                return self.claude_processor.extract_data(file_path, file_name)

            extracted_data = self.retry_backoff.execute_with_retry(extract_with_retry)

            # Get token usage if available
            input_tokens = 0
            output_tokens = 0
            if hasattr(extracted_data, 'usage'):
                input_tokens = extracted_data.usage.get('input_tokens', 0)
                output_tokens = extracted_data.usage.get('output_tokens', 0)

            # Update progress
            status = extracted_data.get('read_status', 'failed')
            self.progress_tracker.update(status, input_tokens, output_tokens)

            # Update checkpoint
            if self.checkpoint_manager:
                self.checkpoint_manager.mark_processed(file_id, status)

            # Call progress callback if provided
            if self.progress_callback:
                self.progress_callback(self.progress_tracker.get_stats())

            return extracted_data

        except Exception as e:
            # Mark as failed
            error_msg = str(e)
            self.progress_tracker.update('failed')

            if self.checkpoint_manager:
                self.checkpoint_manager.mark_failed(file_id, error_msg)

            # Call progress callback
            if self.progress_callback:
                self.progress_callback(self.progress_tracker.get_stats())

            return {
                "document_id": file_name,
                "read_status": "failed",
                "comment": f"Error: {error_msg}",
                "fields": {}
            }

    def process_files(self, files: List[Dict], output_file: str) -> Dict:
        """
        Process files in parallel

        Args:
            files: List of file metadata dicts from Google Drive
            output_file: Path to output JSON file

        Returns:
            dict: Processing statistics
        """
        # Initialize trackers
        total_files = len(files)
        self.progress_tracker.set_total(total_files)

        if self.checkpoint_manager:
            self.checkpoint_manager.set_total(total_files)

        # Initialize output file
        FileHandler.write_json(output_file, [])

        # Thread-safe file writing
        write_lock = threading.Lock()

        def save_result(result):
            """Thread-safe result saving"""
            if result:  # Skip None results (already processed)
                with write_lock:
                    FileHandler.append_to_json_array(output_file, result)

        # Process files concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self._process_single_file, file): file
                for file in files
            }

            # Process completed tasks
            for future in as_completed(future_to_file):
                # Check for cancellation
                if self.is_processing_cancelled():
                    print("\nProcessing cancelled by user")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                file = future_to_file[future]

                try:
                    result = future.result()
                    save_result(result)

                except Exception as e:
                    print(f"Error processing {file['name']}: {str(e)}")
                    # Create error result
                    error_result = {
                        "document_id": file['name'],
                        "read_status": "failed",
                        "comment": f"Unexpected error: {str(e)}",
                        "fields": {}
                    }
                    save_result(error_result)

        # Finalize checkpoint
        if self.checkpoint_manager:
            self.checkpoint_manager.finalize()

        # Return final stats
        return self.progress_tracker.get_stats()

    def get_stats(self) -> Dict:
        """Get current processing statistics"""
        return self.progress_tracker.get_stats()

    def get_cost_estimate(self) -> Dict:
        """Get cost estimate"""
        return self.progress_tracker.get_cost_estimate()

    def print_summary(self):
        """Print processing summary"""
        print(self.progress_tracker.format_summary())


class SequentialProcessor:
    """Sequential processor (original behavior) for backward compatibility"""

    def __init__(
        self,
        google_service: GoogleDriveService,
        claude_processor: ClaudeProcessor,
        progress_callback: Optional[Callable] = None
    ):
        """
        Initialize sequential processor

        Args:
            google_service: GoogleDriveService instance
            claude_processor: ClaudeProcessor instance
            progress_callback: Optional callback for progress updates
        """
        self.google_service = google_service
        self.claude_processor = claude_processor
        self.progress_callback = progress_callback
        self.progress_tracker = ProgressTracker()
        self.is_cancelled = False

    def cancel(self):
        """Cancel processing"""
        self.is_cancelled = True

    def process_files(self, files: List[Dict], output_file: str) -> Dict:
        """
        Process files sequentially (original implementation)

        Args:
            files: List of file metadata dicts
            output_file: Output JSON file path

        Returns:
            dict: Processing statistics
        """
        self.progress_tracker.set_total(len(files))
        FileHandler.write_json(output_file, [])

        for file in files:
            if self.is_cancelled:
                break

            try:
                # Download
                file_path = self.google_service.download_file(
                    file['id'],
                    file['name'],
                    file['mimeType']
                )

                if file_path:
                    # Extract
                    extracted_data = self.claude_processor.extract_data(file_path, file['name'])
                else:
                    extracted_data = {
                        "document_id": file['name'],
                        "read_status": "failed",
                        "comment": "Download failed",
                        "fields": {}
                    }

                # Update progress
                status = extracted_data.get('read_status', 'failed')
                self.progress_tracker.update(status)

                # Save result
                FileHandler.append_to_json_array(output_file, extracted_data)

                # Callback
                if self.progress_callback:
                    self.progress_callback(self.progress_tracker.get_stats())

            except Exception as e:
                print(f"Error processing {file['name']}: {str(e)}")
                self.progress_tracker.update('failed')

        return self.progress_tracker.get_stats()

    def get_stats(self) -> Dict:
        """Get current statistics"""
        return self.progress_tracker.get_stats()
