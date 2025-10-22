"""
Checkpoint manager for resumable processing
Saves progress periodically to allow resume from failures
"""
import json
import os
import threading
from datetime import datetime
from pathlib import Path


class CheckpointManager:
    """Manages processing checkpoints for crash recovery"""

    def __init__(self, checkpoint_file='processing_checkpoint.json', batch_size=100):
        """
        Initialize checkpoint manager

        Args:
            checkpoint_file (str): Path to checkpoint file
            batch_size (int): Save checkpoint every N files
        """
        self.checkpoint_file = checkpoint_file
        self.batch_size = batch_size
        self.lock = threading.Lock()

        # State
        self.processed_files = set()
        self.failed_files = {}  # file_id -> error_message
        self.stats = {
            'total': 0,
            'processed': 0,
            'success': 0,
            'partial': 0,
            'failed': 0,
            'started_at': None,
            'last_checkpoint': None
        }

        # Load existing checkpoint if available
        self._load_checkpoint()

    def _load_checkpoint(self):
        """Load checkpoint from file if it exists"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)

                self.processed_files = set(data.get('processed_files', []))
                self.failed_files = data.get('failed_files', {})
                self.stats = data.get('stats', self.stats)

                print(f"Loaded checkpoint: {len(self.processed_files)} files already processed")
            except Exception as e:
                print(f"Warning: Could not load checkpoint: {e}")

    def _save_checkpoint(self):
        """Save current state to checkpoint file"""
        try:
            data = {
                'processed_files': list(self.processed_files),
                'failed_files': self.failed_files,
                'stats': self.stats,
                'last_checkpoint': datetime.now().isoformat()
            }

            # Write to temporary file first, then rename (atomic operation)
            temp_file = f"{self.checkpoint_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)

            os.replace(temp_file, self.checkpoint_file)
            self.stats['last_checkpoint'] = data['last_checkpoint']

        except Exception as e:
            print(f"Warning: Could not save checkpoint: {e}")

    def should_process(self, file_id):
        """
        Check if file should be processed

        Args:
            file_id (str): File ID to check

        Returns:
            bool: True if file should be processed
        """
        with self.lock:
            return file_id not in self.processed_files

    def mark_processed(self, file_id, status='success'):
        """
        Mark a file as processed

        Args:
            file_id (str): File ID
            status (str): Processing status (success, partial_success, failed)
        """
        with self.lock:
            self.processed_files.add(file_id)
            self.stats['processed'] += 1

            if status == 'success':
                self.stats['success'] += 1
            elif status == 'partial_success':
                self.stats['partial'] += 1
            else:
                self.stats['failed'] += 1

            # Save checkpoint periodically
            if self.stats['processed'] % self.batch_size == 0:
                self._save_checkpoint()

    def mark_failed(self, file_id, error_message):
        """
        Mark a file as failed

        Args:
            file_id (str): File ID
            error_message (str): Error message
        """
        with self.lock:
            self.failed_files[file_id] = error_message
            self.mark_processed(file_id, status='failed')

    def get_remaining_count(self):
        """
        Get count of remaining files to process

        Returns:
            int: Number of files left
        """
        with self.lock:
            return self.stats['total'] - self.stats['processed']

    def set_total(self, total):
        """
        Set total number of files

        Args:
            total (int): Total file count
        """
        with self.lock:
            self.stats['total'] = total
            if not self.stats['started_at']:
                self.stats['started_at'] = datetime.now().isoformat()

    def get_stats(self):
        """
        Get current statistics

        Returns:
            dict: Stats dictionary (copy)
        """
        with self.lock:
            return self.stats.copy()

    def get_failed_files(self):
        """
        Get list of failed files for retry

        Returns:
            dict: Failed files and their errors
        """
        with self.lock:
            return self.failed_files.copy()

    def finalize(self):
        """Save final checkpoint and clean up"""
        with self.lock:
            self._save_checkpoint()

    def clear(self):
        """Clear checkpoint (start fresh)"""
        with self.lock:
            self.processed_files.clear()
            self.failed_files.clear()
            self.stats = {
                'total': 0,
                'processed': 0,
                'success': 0,
                'partial': 0,
                'failed': 0,
                'started_at': None,
                'last_checkpoint': None
            }

            # Remove checkpoint file
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)

    def export_failed_files(self, output_file='failed_files.json'):
        """
        Export failed files to a separate file for retry

        Args:
            output_file (str): Output file path
        """
        with self.lock:
            if not self.failed_files:
                print("No failed files to export")
                return

            with open(output_file, 'w') as f:
                json.dump(self.failed_files, f, indent=2)

            print(f"Exported {len(self.failed_files)} failed files to {output_file}")
