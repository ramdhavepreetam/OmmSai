# Prescription Extractor

A Python GUI application for downloading prescription PDFs from Google Drive and extracting structured data using Claude AI.

## Prerequisites

- Python 3.10+
- Google Cloud Project with Drive API enabled
- Anthropic API key

## Setup Instructions

### 1. Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client anthropic python-dotenv
```

### 2. Configure Google Drive API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Drive API**
4. Create OAuth 2.0 credentials (Desktop application type)
5. Download the credentials file and save it as `credentials.json` in this directory

### 3. Configure Anthropic API

1. Get your API key from [Anthropic Console](https://console.anthropic.com/)
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_actual_api_key_here
   ```

### 4. Run the Application

```bash
python GetGoogleFiles.py
```

## Usage

1. Launch the application
2. Enter your Google Drive Folder ID (found in the folder URL)
3. Click "Start Processing"
4. The app will:
   - Authenticate with Google Drive (first time only)
   - Download all PDFs from the specified folder
   - Extract prescription data using Claude AI
   - Save results to `extracted_prescriptions.json`

## Security Notes

⚠️ **NEVER commit these files to git:**
- `.env` - Contains your API keys
- `credentials.json` - Contains Google OAuth credentials
- `token.pickle` - Contains Google OAuth tokens
- `extracted_prescriptions.json` - Contains sensitive patient data
- `downloads/` - Contains prescription PDFs

All sensitive files are already listed in `.gitignore`.

## Output Format

The application extracts structured data from prescriptions in JSON format:

```json
{
  "document_id": "prescription_001.pdf",
  "read_status": "success",
  "document_quality": "good",
  "comment": "All fields extracted successfully",
  "fields": {
    "patient_name": {
      "value": "John Doe",
      "confidence": "high"
    },
    "medications": {
      "value": "Amoxicillin 500mg tid x 7 days",
      "confidence": "high"
    }
  }
}
```

## Troubleshooting

### Authentication Issues
- Delete `token.pickle` and re-authenticate
- Verify `credentials.json` is correct

### API Errors
- Check your `.env` file has the correct API key
- Verify your Anthropic API key is active

### SSL Errors
- The app uses sequential processing to avoid SSL conflicts
- If issues persist, check your network connection

## License

Private project - All rights reserved
