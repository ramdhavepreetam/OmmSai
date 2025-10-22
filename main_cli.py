"""
Main entry point for CLI application
Headless prescription extraction for automation
"""
import argparse
from getGoogleFiles.cli import main as cli_main
from getGoogleFiles.config.settings import Settings


def main():
    """Parse arguments and launch CLI processor"""
    parser = argparse.ArgumentParser(
        description='Prescription Extraction CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default folder ID
  python main_cli.py

  # Specify folder ID
  python main_cli.py --folder-id 15ZARfsIkva2O0ordMDZJJJZrj0WDLfLs

  # Custom output file
  python main_cli.py --output results.json

  # Both custom folder and output
  python main_cli.py --folder-id YOUR_FOLDER_ID --output my_data.json
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

    args = parser.parse_args()

    # Run CLI processor
    cli_main(folder_id=args.folder_id, output_file=args.output)


if __name__ == '__main__':
    main()
