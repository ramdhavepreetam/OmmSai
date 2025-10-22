"""
Command-line interface for prescription extraction
Headless version for automation and scripting
"""
import json
from .core.google_drive import GoogleDriveService
from .core.claude_processor import ClaudeProcessor
from .config.settings import Settings
from .utils.file_handler import FileHandler
from .utils.logger import setup_logger


class CLIProcessor:
    """Command-line processor for prescription extraction"""

    def __init__(self, folder_id=None, output_file=None):
        """
        Initialize CLI processor

        Args:
            folder_id (str): Google Drive folder ID
            output_file (str): Output JSON file path
        """
        self.folder_id = folder_id or Settings.DEFAULT_FOLDER_ID
        self.output_file = output_file or Settings.OUTPUT_JSON_FILE
        self.logger = setup_logger()

        # Services
        self.google_service = GoogleDriveService()
        self.claude_processor = ClaudeProcessor()

        # Statistics
        self.stats = {
            'total': 0,
            'success': 0,
            'partial': 0,
            'failed': 0
        }

    def run(self):
        """Execute the complete extraction pipeline"""
        try:
            self._print_header()

            # Step 1: Authenticate
            self.logger.info("Step 1: Authenticating with Google Drive...")
            self.google_service.authenticate()
            self.logger.info("✓ Authentication successful\n")

            # Step 2: List files
            self.logger.info(f"Step 2: Fetching files from folder: {self.folder_id}")
            files = self.google_service.list_files(self.folder_id)

            if not files:
                self.logger.warning("No files found in the folder!")
                return

            self.stats['total'] = len(files)
            self.logger.info(f"Found {self.stats['total']} files\n")

            # Step 3: Process files
            self.logger.info(f"Step 3: Processing {self.stats['total']} files...")
            self.logger.info("-" * 70 + "\n")

            # Initialize output file
            FileHandler.write_json(self.output_file, [])

            # Process each file
            for idx, file in enumerate(files, 1):
                self._process_single_file(file, idx, self.stats['total'])

            # Step 4: Display summary
            self._print_summary()

        except Exception as e:
            self.logger.error(f"Fatal error: {str(e)}")
            raise

    def _process_single_file(self, file, index, total):
        """Process a single file"""
        self.logger.info(f"[{index}/{total}] Processing: {file['name']}")
        print("-" * 70)

        try:
            # Download file
            file_path = self.google_service.download_file(
                file['id'],
                file['name'],
                file['mimeType']
            )

            if not file_path:
                self._record_failure(file['name'], "Download failed")
                return

            self.logger.info(f"  ✓ Downloaded: {file['name']}")

            # Extract with Claude
            self.logger.info("  → Sending to Claude AI...")
            extracted_data = self.claude_processor.extract_data(file_path, file['name'])

            # Record statistics
            status = extracted_data.get('read_status', 'failed')
            if status == 'success':
                self.stats['success'] += 1
            elif status == 'partial_success':
                self.stats['partial'] += 1
            else:
                self.stats['failed'] += 1

            # Save to output
            FileHandler.append_to_json_array(self.output_file, extracted_data)

            self.logger.info(f"  ✓ Extraction complete: {status}\n")

        except Exception as e:
            self.logger.error(f"  ✗ Error: {str(e)}\n")
            self._record_failure(file['name'], str(e))

    def _record_failure(self, filename, reason):
        """Record a failed extraction"""
        self.stats['failed'] += 1
        failure_data = {
            "document_id": filename,
            "read_status": "failed",
            "comment": reason,
            "fields": {}
        }
        FileHandler.append_to_json_array(self.output_file, failure_data)

    def _print_header(self):
        """Print application header"""
        print("\n" + "=" * 70)
        print("🏥 PRESCRIPTION EXTRACTION PIPELINE")
        print("=" * 70 + "\n")

    def _print_summary(self):
        """Print extraction summary"""
        print("\n" + "=" * 70)
        print("EXTRACTION SUMMARY")
        print("=" * 70)
        print(f"Total files processed: {self.stats['total']}")
        print(f"✓ Success: {self.stats['success']}")
        print(f"⚠ Partial success: {self.stats['partial']}")
        print(f"✗ Failed: {self.stats['failed']}")
        print(f"\nOutput saved to: {self.output_file}")
        print("=" * 70 + "\n")


def main(folder_id=None, output_file=None):
    """
    Main entry point for CLI

    Args:
        folder_id (str): Google Drive folder ID
        output_file (str): Output JSON file path
    """
    # Ensure directories exist
    Settings.ensure_directories()

    # Validate settings
    errors = Settings.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return

    # Run processor
    processor = CLIProcessor(folder_id, output_file)
    processor.run()


if __name__ == '__main__':
    main()
