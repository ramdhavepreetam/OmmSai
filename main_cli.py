"""
Main entry point for CLI application
Headless prescription extraction for automation with parallel processing support
"""
import argparse
from getGoogleFiles.cli import CLIProcessor
from getGoogleFiles.config.settings import Settings


def main():
    """Parse arguments and launch CLI processor"""
    parser = argparse.ArgumentParser(
        description='Prescription Extraction CLI with Parallel Processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default folder ID with parallel processing (10 workers)
  python main_cli.py

  # Custom folder ID with 20 workers
  python main_cli.py --folder-id YOUR_ID --workers 20

  # Sequential mode (1 file at a time - old behavior)
  python main_cli.py --sequential

  # Resume from previous checkpoint
  python main_cli.py --resume

  # Custom output file
  python main_cli.py --output results.json

  # Process with 5 workers and custom output
  python main_cli.py --workers 5 --output my_data.json

Performance Tips:
  - 15,000 files: Use --workers 10-20 (~12-6 hours)
  - 1,000 files: Use --workers 5-10 (~1 hour)
  - Testing: Use --workers 2 for small batches
        """
    )

    parser.add_argument(
        '--folder-id',
        '-f',
        default=Settings.DEFAULT_FOLDER_ID,
        help=f'Google Drive folder ID (default: {Settings.DEFAULT_FOLDER_ID})'
    )

    parser.add_argument(
        '--output',
        '-o',
        default=Settings.OUTPUT_JSON_FILE,
        help=f'Output JSON file path (default: {Settings.OUTPUT_JSON_FILE})'
    )

    parser.add_argument(
        '--workers',
        '-w',
        type=int,
        default=Settings.MAX_WORKERS,
        help=f'Number of parallel workers (default: {Settings.MAX_WORKERS}, max: {Settings.MAX_WORKERS_LIMIT})'
    )

    parser.add_argument(
        '--sequential',
        '-s',
        action='store_true',
        help='Use sequential processing (old behavior, 1 file at a time)'
    )

    parser.add_argument(
        '--resume',
        '-r',
        action='store_true',
        help='Resume from previous checkpoint'
    )

    parser.add_argument(
        '--checkpoint',
        '-c',
        default=Settings.CHECKPOINT_FILE,
        help=f'Checkpoint file path (default: {Settings.CHECKPOINT_FILE})'
    )

    args = parser.parse_args()

    # Validate workers
    if args.workers < 1:
        print(f"Error: Workers must be >= 1")
        return

    if args.workers > Settings.MAX_WORKERS_LIMIT:
        print(f"Warning: Workers capped at {Settings.MAX_WORKERS_LIMIT}")
        args.workers = Settings.MAX_WORKERS_LIMIT

    # Create and run processor
    processor = CLIProcessor(
        folder_id=args.folder_id,
        output_file=args.output,
        parallel=not args.sequential,
        workers=args.workers,
        resume=args.resume,
        checkpoint_file=args.checkpoint
    )

    processor.run()


if __name__ == '__main__':
    main()
