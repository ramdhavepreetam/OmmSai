"""
Simple test script for API connectivity
Tests both Google Drive and Claude API connections
"""
from getGoogleFiles.core.google_drive import GoogleDriveService
from getGoogleFiles.core.claude_processor import ClaudeProcessor
from getGoogleFiles.config.settings import Settings


def test_claude_api():
    """Test Claude API connection"""
    print("\n" + "=" * 50)
    print("Testing Claude API Connection")
    print("=" * 50)

    try:
        processor = ClaudeProcessor()
        result = processor.simple_query("What is the capital of India?")

        if result["success"]:
            print("✓ Claude API is working!")
            print(f"\nResponse: {result['text']}")
            print(f"\nTokens used: {result['usage']['input_tokens']} input, "
                  f"{result['usage']['output_tokens']} output")
        else:
            print(f"✗ Claude API error: {result['error']}")

    except Exception as e:
        print(f"✗ Error: {str(e)}")


def test_google_drive():
    """Test Google Drive API connection"""
    print("\n" + "=" * 50)
    print("Testing Google Drive API Connection")
    print("=" * 50)

    try:
        service = GoogleDriveService()
        print("Authenticating...")
        service.authenticate()
        print("✓ Google Drive authentication successful!")

        print(f"\nListing files in default folder: {Settings.DEFAULT_FOLDER_ID}")
        files = service.list_files(Settings.DEFAULT_FOLDER_ID)
        print(f"✓ Found {len(files)} files")

        if files:
            print("\nFirst 5 files:")
            for file in files[:5]:
                print(f"  - {file['name']} ({file['mimeType']})")

    except Exception as e:
        print(f"✗ Error: {str(e)}")


def main():
    """Run all tests"""
    print("\n🔧 API Connectivity Tests\n")

    # Validate configuration
    errors = Settings.validate()
    if errors:
        print("⚠ Configuration issues detected:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease fix these issues before proceeding.\n")
        return

    # Run tests
    test_claude_api()
    test_google_drive()

    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50 + "\n")


if __name__ == '__main__':
    main()
