# OmmSai - Prescription Extraction System

A modular Python application for downloading prescription PDFs from Google Drive and extracting structured medical data using Claude AI.

## Features

- 🏥 **Medical Document Processing**: Extract structured data from handwritten prescriptions
- 🤖 **AI-Powered**: Uses Claude Sonnet 4.5 for intelligent document understanding
- 📁 **Google Drive Integration**: Automatic file discovery and download
- 🖥️ **Multiple Interfaces**: GUI and CLI modes
- ⚡ **Parallel Processing**: Process 15,000+ files efficiently with concurrent workers
- 💾 **Checkpoint/Resume**: Auto-save progress, resume from failures
- 📊 **Real-time Progress**: Throughput, ETA, and cost tracking
- 🔒 **Secure**: OAuth 2.0 authentication with credential management
- 🛡️ **Rate Limit Aware**: Automatic backoff and retry logic

## Project Structure

```
OmmSai/
├── getGoogleFiles/              # Main package (refactored modular code)
│   ├── __init__.py
│   ├── config/                  # Configuration and settings
│   │   ├── settings.py         # Application settings
│   │   └── prompts.py          # AI extraction prompts
│   ├── core/                    # Core business logic
│   │   ├── google_drive.py     # Google Drive API integration
│   │   └── claude_processor.py # Claude AI processing
│   ├── ui/                      # User interfaces
│   │   └── gui.py              # Tkinter GUI
│   ├── utils/                   # Utilities
│   │   ├── logger.py           # Logging utilities
│   │   └── file_handler.py     # File operations
│   └── cli.py                   # CLI interface
│
├── main_gui.py                  # GUI entry point (NEW - use this!)
├── main_cli.py                  # CLI entry point (NEW - use this!)
├── test_api.py                  # API connectivity tests (NEW - use this!)
│
├── GetGoogleFiles.py            # DEPRECATED (kept for compatibility)
├── CloudBackup.py               # DEPRECATED (kept for compatibility)
├── app.py                       # DEPRECATED (kept for compatibility)
├── CloudResponse.py             # DEPRECATED (old utility)
│
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .gitignore                   # Git exclusions
└── README.md                    # This file
```

## Prerequisites

- **Python**: 3.10 or higher
- **Google Cloud Project** with Drive API enabled
- **Anthropic API** key

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client anthropic python-dotenv
```

### 2. Configure Google Drive API

Follow the detailed setup guide in [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#google-drive-api-setup)

**Quick steps:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **Google Drive API**
4. Create **OAuth 2.0 credentials** (Desktop app type)
5. Download as `credentials.json` and place in project root

### 3. Configure Anthropic API

```bash
# Copy the template
cp .env.example .env

# Edit .env and add your API key
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

Get your API key from [Anthropic Console](https://console.anthropic.com/)

### 4. Test Setup

```bash
python test_api.py
```

This will verify:
- ✓ Claude API connection
- ✓ Google Drive authentication
- ✓ File listing capability

## Usage

### 🚀 Quick Start for Large Batches (15,000+ files)

#### 1. Test First

```bash
# Test with 5 files using 2 workers
python test_parallel.py --test-size 5 --workers 2
```

#### 2. Run Full Processing

```bash
# Recommended: 10 workers (~12 hours for 15,000 files)
python main_cli.py --workers 10

# Faster: 20 workers (~6 hours for 15,000 files)
python main_cli.py --workers 20

# Resume if interrupted
python main_cli.py --resume --workers 10
```

### GUI Mode (Interactive)

```bash
python main_gui.py
```

**Features:**
- Visual folder ID input
- Real-time progress tracking
- Statistics dashboard
- Colored logging
- Start/Stop controls

**Steps:**
1. Enter your Google Drive Folder ID
2. Click "Start Processing"
3. View progress in real-time
4. Results saved to `extracted_prescriptions.json`

### CLI Mode (Parallel Processing)

```bash
# Default: 10 parallel workers
python main_cli.py

# Custom workers (2-50)
python main_cli.py --workers 20

# Sequential mode (old behavior)
python main_cli.py --sequential

# Resume from checkpoint
python main_cli.py --resume

# Custom folder + workers
python main_cli.py --folder-id YOUR_ID --workers 15

# Custom output file
python main_cli.py --output results.json --workers 10
```

**CLI Options:**
- `--workers N` - Number of parallel workers (default: 10)
- `--sequential` - Use sequential mode (1 file at a time)
- `--resume` - Resume from checkpoint
- `--checkpoint FILE` - Custom checkpoint file
- `--folder-id ID` - Google Drive folder ID
- `--output FILE` - Output JSON file

**Performance:**
- **Sequential**: 1 file at a time (~125 hours for 15,000 files)
- **10 workers**: ~12.5 hours for 15,000 files (10x faster)
- **20 workers**: ~6.25 hours for 15,000 files (20x faster)

## Finding Your Google Drive Folder ID

1. Open Google Drive in browser
2. Navigate to your prescription folder
3. Look at the URL:
   ```
   https://drive.google.com/drive/folders/15ZARfsIkva2O0ordMDZJJJZrj0WDLfLs
                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                           This is your Folder ID
   ```
4. Copy the ID and paste it in the app

## Output Format

Extracted data is saved as JSON with confidence scores:

```json
{
  "document_id": "prescription_001.pdf",
  "read_status": "success",
  "document_quality": "good",
  "comment": "All major fields extracted successfully",
  "fields": {
    "patient_name": {
      "value": "John Doe",
      "confidence": "high"
    },
    "date": {
      "value": "2025-01-15",
      "confidence": "high"
    },
    "medications": {
      "value": "Amoxicillin 500mg tid x 7 days",
      "confidence": "high"
    }
  }
}
```

**Read Status Values:**
- `success`: ≥90% fields extracted
- `partial_success`: 50-89% fields extracted
- `failed`: <50% extractable

## Configuration

### Settings File

Edit `getGoogleFiles/config/settings.py` to customize:

```python
# Default folder ID
DEFAULT_FOLDER_ID = 'your-folder-id-here'

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"

# Output settings
OUTPUT_JSON_FILE = 'extracted_prescriptions.json'
DOWNLOAD_FOLDER = 'downloads'
```

### Extraction Prompt

Customize AI behavior in `getGoogleFiles/config/prompts.py`

## Migration Guide

### From Old Files to New Structure

**Old way (deprecated):**
```bash
python GetGoogleFiles.py  # GUI
python CloudBackup.py     # CLI
python app.py             # Test
```

**New way:**
```bash
python main_gui.py        # GUI
python main_cli.py        # CLI
python test_api.py        # Test
```

Old files still work (with warnings) but use the new modular implementation under the hood.

## Security Best Practices

### Never Commit These Files:
```
.env                           # Contains API keys
credentials.json              # OAuth credentials
token.pickle                  # OAuth tokens
downloads/                    # Patient data
extracted_prescriptions.json  # PHI data
```

All are already in `.gitignore`

### HIPAA Compliance
⚠️ **Important**: PDFs contain Protected Health Information (PHI)
- Ensure Claude API usage complies with data processing agreements
- Use encrypted storage for local files
- Implement access controls in production
- Consider on-premise AI for sensitive deployments
- Audit all API access

## Troubleshooting

### Common Issues

**"credentials.json not found"**
```bash
# Download from Google Cloud Console
# Place in project root directory
ls -la credentials.json  # Should exist
```

**"ANTHROPIC_API_KEY not found"**
```bash
# Check .env file
cat .env

# Should contain:
ANTHROPIC_API_KEY=sk-ant-...
```

**"Google hasn't verified this app"**
- Click "Advanced" → "Go to [App Name] (unsafe)"
- Safe for personal development apps
- Or publish app in Google Cloud Console (complex)

**Import errors**
```bash
# Ensure you're in project root
pwd  # Should show .../OmmSai

# Reinstall dependencies
pip install -r requirements.txt
```

### Getting Help

1. Check [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) for detailed docs
2. Run `python test_api.py` to diagnose connectivity issues
3. Review logs in the GUI for specific errors

## Development

### Adding New Features

1. **Core logic**: Add to `getGoogleFiles/core/`
2. **UI components**: Add to `getGoogleFiles/ui/`
3. **Utilities**: Add to `getGoogleFiles/utils/`
4. **Configuration**: Add to `getGoogleFiles/config/`

### Running Tests

```bash
# Test API connectivity
python test_api.py

# Test GUI (manual)
python main_gui.py

# Test CLI
python main_cli.py --folder-id YOUR_FOLDER_ID
```

## Performance

### Processing Times

| Mode | Workers | 15,000 Files | 1,000 Files |
|------|---------|--------------|-------------|
| Sequential (old) | 1 | ~125 hours | ~8 hours |
| Conservative | 5 | ~25 hours | ~1.6 hours |
| **Recommended** | **10** | **~12.5 hours** | **~50 min** |
| Aggressive | 20 | ~6.25 hours | ~25 min |

### Cost (Anthropic API)

- **Per file**: ~$0.02-0.05
- **1,000 files**: ~$20-50
- **15,000 files**: ~$300-750

**Test first to estimate costs:**
```bash
python test_parallel.py --test-size 10
# Check cost estimate, multiply by (total_files / 10)
```

See [PARALLEL_PROCESSING_GUIDE.md](PARALLEL_PROCESSING_GUIDE.md) for detailed guidance.

## Documentation

- **README.md** (this file): Quick start and usage
- **[PARALLEL_PROCESSING_GUIDE.md](PARALLEL_PROCESSING_GUIDE.md)**: Complete guide for large-scale processing
- **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)**: Architecture, API details, setup guides
- **[QUICK_START.md](QUICK_START.md)**: Get started in 5 minutes
- **Code comments**: Inline documentation in source files

## License

Private project - All rights reserved

## Changelog

### v2.0.0 (2025-01-22) - Parallel Processing
- ⚡ **MAJOR**: Added parallel processing with ThreadPoolExecutor
- 💾 Added checkpoint/resume capability for crash recovery
- 📊 Real-time progress tracking with throughput and ETA
- 🛡️ Rate limiting with exponential backoff
- 💰 Cost tracking and estimation
- 🧪 Added `test_parallel.py` for testing before full runs
- 📖 Created comprehensive [PARALLEL_PROCESSING_GUIDE.md](PARALLEL_PROCESSING_GUIDE.md)
- 🔧 CLI now supports `--workers`, `--resume`, `--sequential` options
- ⏱️ **Performance**: 10x faster (10 workers) - 15K files in ~12 hours vs ~125 hours

### v1.0.0 (2025-01-22) - Modular Refactor
- ✨ Refactored into modular package structure
- 📦 New `getGoogleFiles` package with organized modules
- 🎯 Separated GUI (`main_gui.py`) and CLI (`main_cli.py`) entry points
- 🧪 Added comprehensive API testing (`test_api.py`)
- 📝 Created detailed technical documentation
- ♻️ Deprecated old monolithic files (kept for compatibility)
- 🔧 Added `requirements.txt` for easy dependency management
- 📊 Improved logging and error handling
