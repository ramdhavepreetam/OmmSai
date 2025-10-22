"""
Test script for parallel processing
Tests with a small batch before processing large dataset
"""
import sys
from getGoogleFiles.core.google_drive import GoogleDriveService
from getGoogleFiles.core.claude_processor import ClaudeProcessor
from getGoogleFiles.core.parallel_processor import ParallelProcessor
from getGoogleFiles.config.settings import Settings


def test_parallel_processing(folder_id=None, test_size=5, workers=2):
    """
    Test parallel processing with a small batch

    Args:
        folder_id (str): Google Drive folder ID (None = use default)
        test_size (int): Number of files to test with
        workers (int): Number of parallel workers
    """
    print("\n" + "=" * 70)
    print("PARALLEL PROCESSING TEST")
    print("=" * 70)
    print(f"Test size: {test_size} files")
    print(f"Workers: {workers}")
    print("=" * 70 + "\n")

    try:
        # Step 1: Authenticate
        print("Step 1: Authenticating with Google Drive...")
        google_service = GoogleDriveService()
        google_service.authenticate()
        print("✓ Authentication successful\n")

        # Step 2: Initialize Claude
        print("Step 2: Initializing Claude AI...")
        claude_processor = ClaudeProcessor()
        print("✓ Claude AI initialized\n")

        # Step 3: List files
        folder_id = folder_id or Settings.DEFAULT_FOLDER_ID
        print(f"Step 3: Fetching files from folder: {folder_id}")
        all_files = google_service.list_files(folder_id)

        if not all_files:
            print("✗ No files found in folder!")
            return

        print(f"✓ Found {len(all_files)} total files\n")

        # Limit to test size
        test_files = all_files[:test_size]
        print(f"Step 4: Testing with first {len(test_files)} files")
        print("-" * 70 + "\n")

        # Step 5: Process with parallel processor
        processor = ParallelProcessor(
            google_service=google_service,
            claude_processor=claude_processor,
            max_workers=workers,
            checkpoint_file='test_checkpoint.json',
            enable_checkpointing=True,
            progress_callback=lambda stats: print(
                f"Progress: {stats['processed']}/{stats['total']} | "
                f"Success: {stats['success']} | Failed: {stats['failed']}"
            )
        )

        print(f"Processing {len(test_files)} files with {workers} workers...")
        output_file = 'test_parallel_output.json'

        stats = processor.process_files(test_files, output_file)

        # Step 6: Print results
        print("\n" + "=" * 70)
        print("TEST RESULTS")
        print("=" * 70)
        print(f"Total files: {stats['total']}")
        print(f"Processed: {stats['processed']}")
        print(f"Success: {stats['success']}")
        print(f"Partial success: {stats.get('partial_success', 0)}")
        print(f"Failed: {stats['failed']}")
        print(f"Completion: {stats.get('completion_percentage', 0):.1f}%")
        print(f"Throughput: {stats.get('throughput', '0')} files/min")
        print(f"Elapsed: {stats.get('elapsed_time', 'N/A')}")
        print("=" * 70)

        # Cost estimate
        cost = processor.get_cost_estimate()
        print("\nCost Estimate:")
        print(f"Current cost: {cost['current_cost']}")
        print(f"Total tokens: {cost['input_tokens']:,} in + {cost['output_tokens']:,} out")

        # Estimate for full dataset
        if len(all_files) > test_size:
            estimated_total_cost = float(cost['estimated_total_cost'].replace('$', ''))
            actual_total = estimated_total_cost * (len(all_files) / test_size)
            print(f"\nEstimate for all {len(all_files)} files: ~${actual_total:.2f}")

            # Time estimate
            throughput = float(stats.get('throughput', '0'))
            if throughput > 0:
                minutes = len(all_files) / throughput
                hours = minutes / 60
                print(f"Estimated time for all files: ~{hours:.1f} hours ({minutes:.0f} minutes)")

        print("\n" + "=" * 70)
        print("✓ TEST COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"\nOutput saved to: {output_file}")
        print("Review the results before processing the full dataset.")
        print("\nTo process all files, run:")
        print(f"  python main_cli.py --folder-id {folder_id} --workers {workers * 2}")

    except KeyboardInterrupt:
        print("\n\n✗ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Test parallel processing with a small batch',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--folder-id',
        '-f',
        help='Google Drive folder ID (default: use from settings)'
    )

    parser.add_argument(
        '--test-size',
        '-n',
        type=int,
        default=5,
        help='Number of files to test with (default: 5)'
    )

    parser.add_argument(
        '--workers',
        '-w',
        type=int,
        default=2,
        help='Number of parallel workers (default: 2)'
    )

    args = parser.parse_args()

    test_parallel_processing(
        folder_id=args.folder_id,
        test_size=args.test_size,
        workers=args.workers
    )


if __name__ == '__main__':
    main()
