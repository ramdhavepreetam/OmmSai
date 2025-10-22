# OmmSai - Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Details](#component-details)
4. [Google Drive API Setup](#google-drive-api-setup)
5. [Environment Configuration](#environment-configuration)
6. [Data Flow](#data-flow)
7. [API Integration](#api-integration)
8. [Security Considerations](#security-considerations)
9. [Troubleshooting](#troubleshooting)

---

## Overview

**OmmSai** is a medical document processing system that automates the extraction of structured data from doctor's prescription PDFs. It integrates Google Drive API for document retrieval and Anthropic's Claude AI for intelligent document understanding and data extraction.

### Key Features
- Google Drive integration for automated document retrieval
- AI-powered handwriting recognition and data extraction
- Structured JSON output with confidence scoring
- GUI interface for easy operation
- Sequential processing to avoid SSL conflicts
- Real-time progress tracking and statistics

### Technology Stack
- **Language**: Python 3.10+
- **GUI Framework**: Tkinter
- **Cloud Storage**: Google Drive API v3
- **AI Model**: Claude Sonnet 4.5 (Anthropic)
- **Authentication**: OAuth 2.0
- **Data Format**: JSON

---

## System Architecture

### High-Level Architecture

```
┌─────────────────┐
│   User (GUI)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│      GetGoogleFiles.py (Main UI)        │
│  ┌─────────────────────────────────┐    │
│  │  PrescriptionExtractorUI Class  │    │
│  │  - Configuration Management     │    │
│  │  - Progress Tracking            │    │
│  │  - Statistics Display           │    │
│  │  - Log Management               │    │
│  └─────────────────────────────────┘    │
└──────┬───────────────────────┬──────────┘
       │                       │
       ▼                       ▼
┌──────────────┐      ┌────────────────────┐
│  Google      │      │  Anthropic Claude  │
│  Drive API   │      │      API           │
│              │      │                    │
│ - OAuth 2.0  │      │ - PDF Analysis     │
│ - File List  │      │ - Data Extraction  │
│ - Download   │      │ - JSON Output      │
└──────────────┘      └────────────────────┘
       │                       │
       ▼                       ▼
┌─────────────────────────────────────────┐
│           Local Storage                 │
│  - downloads/ (PDFs)                    │
│  - extracted_prescriptions.json         │
│  - token.pickle (OAuth tokens)          │
└─────────────────────────────────────────┘
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
├─────────────────────────────────────────────────────────┤
│  GetGoogleFiles.py │ CloudBackup.py │ CloudResponse.py  │
│       (GUI)        │   (Headless)   │   (Utilities)     │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼─────────┐              ┌────────────▼──────────┐
│ Authentication  │              │  Processing Engine    │
│   Module        │              │                       │
│ - OAuth Flow    │              │ - File Download       │
│ - Token Mgmt    │              │ - AI Processing       │
│ - Credentials   │              │ - Result Aggregation  │
└─────────────────┘              └───────────────────────┘
```

---

## Component Details

### 1. GetGoogleFiles.py (Main GUI Application)

**Location**: `GetGoogleFiles.py:1-697`

**Purpose**: Primary user interface with full-featured GUI for prescription extraction.

**Key Classes**:

#### PrescriptionExtractorUI (`GetGoogleFiles.py:138`)

**Responsibilities**:
- Manage GUI components and user interactions
- Handle Google Drive authentication
- Coordinate file download and processing
- Display real-time progress and statistics
- Write results to JSON incrementally

**Key Methods**:

| Method | Line | Description |
|--------|------|-------------|
| `__init__()` | 139 | Initialize UI components and variables |
| `create_widgets()` | 160 | Build GUI layout with frames and controls |
| `authenticate_google()` | 394 | Handle OAuth 2.0 authentication flow |
| `process_files()` | 421 | Main processing loop (sequential) |
| `list_files_in_folder()` | 550 | Retrieve file list from Google Drive |
| `download_file()` | 558 | Download individual file from Drive |
| `extract_with_claude()` | 592 | Send PDF to Claude for extraction |
| `write_to_json_file()` | 533 | Append results to output JSON |

**Configuration Variables**:
```python
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
DEFAULT_FOLDER_ID = '15ZARfsIkva2O0ordMDZJJJZrj0WDLfLs'
DOWNLOAD_FOLDER = 'downloads'
OUTPUT_JSON_FILE = 'extracted_prescriptions.json'
```

**Statistics Tracking**:
- Total files
- Processed files
- Success count (≥90% fields extracted)
- Partial success count (50-89% fields)
- Failed count (<50% fields)

---

### 2. CloudBackup.py (Headless Processor)

**Location**: `CloudBackup.py:1-369`

**Purpose**: Command-line version for automated/scheduled processing.

**Key Functions**:

| Function | Line | Description |
|----------|------|-------------|
| `authenticate_google()` | 131 | OAuth authentication for Drive API |
| `list_files_in_folder()` | 154 | Query files in specified folder |
| `download_file()` | 167 | Download file with error handling |
| `encode_pdf_to_base64()` | 198 | Convert PDF to base64 for Claude |
| `extract_data_with_claude()` | 204 | Process PDF with Claude AI |
| `process_all_files()` | 275 | Main orchestration function |

**Processing Flow** (`CloudBackup.py:275-351`):
1. Validate ANTHROPIC_API_KEY environment variable
2. Fetch file list from Google Drive
3. Download each file to local storage
4. Encode PDF to base64
5. Send to Claude API with extraction prompt
6. Parse JSON response
7. Aggregate all results
8. Write final JSON output
9. Display summary statistics

---

### 3. CloudResponse.py (Utility Module)

**Location**: `CloudResponse.py:1-24`

**Purpose**: Reusable utility for Claude API interactions.

**Function**: `get_claude_response()`

**Parameters**:
```python
prompt: str              # User query
model: str              # Claude model ID (default: haiku)
max_tokens: int         # Response length limit
client: Anthropic       # Pre-initialized client instance
```

**Returns**:
```python
{
    "success": bool,
    "text": str,           # AI response
    "usage": {
        "input_tokens": int,
        "output_tokens": int,
        "total_tokens": int
    },
    "error": str          # Only if success=False
}
```

**Note**: Contains typo in key name (`sucess` instead of `success`) at lines 9 and 21.

---

### 4. app.py (Standalone Test)

**Location**: `app.py:1-43`

**Purpose**: Simple test script for validating Anthropic API integration.

**Functionality**:
- Loads API key from `.env` file
- Creates Anthropic client
- Sends test query ("What is the capital of India?")
- Displays response or error

---

## Google Drive API Setup

### Step-by-Step Configuration Guide

#### Step 1: Create Google Cloud Project

1. Navigate to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Enter project name (e.g., "OmmSai Prescription Extractor")
4. Click **"Create"**
5. Wait for project creation notification

#### Step 2: Enable Google Drive API

1. In the Cloud Console, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Drive API"**
3. Click on the result
4. Click **"Enable"** button
5. Wait for API to be enabled

#### Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Select **"External"** (or "Internal" if using Google Workspace)
3. Click **"Create"**
4. Fill in required fields:
   - **App name**: "OmmSai Prescription Extractor"
   - **User support email**: Your email
   - **Developer contact**: Your email
5. Click **"Save and Continue"**
6. On **"Scopes"** page, click **"Add or Remove Scopes"**
7. Filter for `drive.readonly` and select:
   - `https://www.googleapis.com/auth/drive.readonly`
8. Click **"Update"** → **"Save and Continue"**
9. Add test users (your email addresses)
10. Click **"Save and Continue"** → **"Back to Dashboard"**

#### Step 4: Create OAuth 2.0 Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ Create Credentials"** → **"OAuth client ID"**
3. Select application type: **"Desktop app"**
4. Enter name: "OmmSai Desktop Client"
5. Click **"Create"**
6. In the popup, click **"Download JSON"**
7. Save the file as `credentials.json` in your project directory

**Important**: The `credentials.json` file should look like this:
```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```

#### Step 5: First-Time Authentication

When you run the application for the first time:

1. The app will open your default browser
2. You'll see a Google sign-in page
3. Select your Google account
4. You may see a warning: **"Google hasn't verified this app"**
   - Click **"Advanced"** → **"Go to [App Name] (unsafe)"**
   - This is safe for apps you develop yourself
5. Review permissions and click **"Allow"**
6. You'll see: **"The authentication flow has completed"**
7. Close the browser tab
8. The app will create `token.pickle` to store credentials

#### Step 6: Get Google Drive Folder ID

1. Open Google Drive in your browser
2. Navigate to the folder containing prescription PDFs
3. Look at the URL, which will be:
   ```
   https://drive.google.com/drive/folders/FOLDER_ID_HERE
   ```
4. Copy the `FOLDER_ID_HERE` part
5. Paste it into the application's **"Google Drive Folder ID"** field

**Example**:
- URL: `https://drive.google.com/drive/folders/15ZARfsIkva2O0ordMDZJJJZrj0WDLfLs`
- Folder ID: `15ZARfsIkva2O0ordMDZJJJZrj0WDLfLs`

---

## Environment Configuration

### Required Files

#### 1. `.env` file

Create from template:
```bash
cp .env.example .env
```

Contents:
```bash
# Anthropic API Key
# Get your API key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**How to get Anthropic API key**:
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign in or create an account
3. Navigate to **"API Keys"**
4. Click **"Create Key"**
5. Copy the key (starts with `sk-ant-`)
6. Paste into `.env` file

#### 2. `credentials.json` (Google OAuth)

Obtained from Google Cloud Console (see Step 4 above).

**Never commit this file to git!**

#### 3. `token.pickle` (Auto-generated)

Created automatically after first OAuth flow.

**Security**: Contains refresh tokens - never commit to git!

---

## Data Flow

### Complete Processing Pipeline

```
1. USER INPUT
   ├─ Google Drive Folder ID
   ├─ Output JSON filename
   └─ Click "Start Processing"
         │
         ▼
2. AUTHENTICATION
   ├─ Check for token.pickle
   ├─ If missing/invalid → OAuth flow
   ├─ Store credentials
   └─ Build Google Drive service
         │
         ▼
3. FILE DISCOVERY
   ├─ Query: "'{folder_id}' in parents and trashed=false"
   ├─ Retrieve file metadata (id, name, mimeType, size)
   ├─ Display count: "Found X files"
   └─ Initialize progress tracking
         │
         ▼
4. SEQUENTIAL PROCESSING (for each file)
   │
   ├─ DOWNLOAD
   │  ├─ Check mime type
   │  ├─ If Google Workspace → export as PDF
   │  ├─ Else → download directly
   │  └─ Save to downloads/
   │      │
   │      ▼
   ├─ ENCODE
   │  └─ Convert PDF to base64 string
   │      │
   │      ▼
   ├─ AI PROCESSING
   │  ├─ Create Claude message with:
   │  │  ├─ Document type: "document"
   │  │  ├─ Source: base64 PDF data
   │  │  └─ Prompt: EXTRACTION_PROMPT
   │  ├─ Model: claude-sonnet-4-5-20250929
   │  ├─ Max tokens: 8192
   │  └─ Parse JSON response
   │      │
   │      ▼
   ├─ VALIDATION
   │  ├─ Strip markdown code blocks
   │  ├─ Parse JSON
   │  ├─ Validate structure
   │  └─ Categorize: success/partial/failed
   │      │
   │      ▼
   └─ STORAGE
      ├─ Append to JSON array
      ├─ Update statistics
      └─ Log result
            │
            ▼
5. COMPLETION
   ├─ Display final summary
   ├─ Show success/partial/failed counts
   └─ Enable "Open Output File" button
```

### Data Transformation

**Input**: Scanned prescription PDF (handwritten + printed text)

**Intermediate**: Base64-encoded PDF string

**AI Prompt**: Structured extraction template (129 lines, `CloudBackup.py:31-128`)

**Output**: Structured JSON

Example output structure:
```json
{
  "document_id": "prescription_001.pdf",
  "read_status": "success | partial_success | failed",
  "document_quality": "excellent | good | fair | poor",
  "comment": "Summary of extraction quality or issues",
  "fields": {
    "patient_name": {
      "value": "John Doe",
      "confidence": "high | medium | low",
      "note": "Optional clarification"
    },
    "date": {
      "value": "2025-01-15",
      "confidence": "high"
    },
    "diagnosis": {
      "value": "Acute bronchitis",
      "confidence": "medium",
      "note": "Handwriting slightly unclear"
    },
    "medication_1": {
      "value": "Amoxicillin 500mg tid x 7 days",
      "confidence": "high"
    }
  }
}
```

---

## API Integration

### Google Drive API

**Version**: v3
**Documentation**: https://developers.google.com/drive/api/v3/reference

**Used Endpoints**:

1. **List Files**
   ```python
   service.files().list(
       q="'{folder_id}' in parents and trashed=false",
       pageSize=1000,
       fields="nextPageToken, files(id, name, mimeType, size)"
   ).execute()
   ```

2. **Download File**
   ```python
   # For regular files
   request = service.files().get_media(fileId=file_id)

   # For Google Workspace files (export as PDF)
   request = service.files().export_media(
       fileId=file_id,
       mimeType='application/pdf'
   )
   ```

**Authentication**: OAuth 2.0 with offline access
**Scope**: `https://www.googleapis.com/auth/drive.readonly`

---

### Anthropic Claude API

**SDK**: `anthropic` (Python)
**Documentation**: https://docs.anthropic.com/

**Model Used**: `claude-sonnet-4-5-20250929`

**Key Features**:
- Native PDF understanding
- Vision capabilities for handwritten text
- Structured JSON output
- Context window: 200K tokens

**API Call Structure** (`GetGoogleFiles.py:599-621`):
```python
client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=8192,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    }
                },
                {
                    "type": "text",
                    "text": EXTRACTION_PROMPT
                }
            ]
        }
    ]
)
```

**Rate Limits**: Check your API tier at https://console.anthropic.com/settings/limits

---

## Security Considerations

### Sensitive Files (Never Commit)

The `.gitignore` includes:
```
.env                           # API keys
credentials.json              # Google OAuth credentials
token.pickle                  # Google OAuth tokens
downloads/                    # Downloaded PDFs (patient data)
extracted_prescriptions.json  # Extracted patient data
```

### Authentication Security

1. **OAuth Tokens**:
   - Stored in `token.pickle` (binary format)
   - Contains refresh tokens with long expiration
   - Encrypted by pickle serialization
   - Automatically refreshed when expired

2. **API Keys**:
   - Stored in `.env` (never hardcoded)
   - Loaded via `python-dotenv`
   - Not logged or displayed in UI

3. **Credential Files**:
   - `credentials.json` contains client secrets
   - Required for OAuth flow
   - Should have restricted file permissions (chmod 600)

### Data Privacy

**HIPAA Compliance Considerations**:
- PDFs contain Protected Health Information (PHI)
- Ensure Claude API usage complies with your data processing agreements
- Consider on-premise AI solutions for sensitive deployments
- Implement audit logging for production use
- Encrypt local storage (`downloads/`, output JSON)

**Best Practices**:
1. Run on encrypted drives
2. Use secure network connections (VPN)
3. Implement user access controls
4. Regularly delete processed files
5. Audit API access logs

---

## Troubleshooting

### Common Issues

#### 1. "credentials.json not found"

**Cause**: OAuth credentials not downloaded from Google Cloud Console

**Solution**:
```bash
# Verify file exists
ls -la credentials.json

# Should be in project root alongside GetGoogleFiles.py
# If missing, re-download from Google Cloud Console
```

#### 2. "ANTHROPIC_API_KEY not found"

**Cause**: Environment variable not loaded

**Solution**:
```bash
# Check .env file exists
cat .env

# Should contain:
# ANTHROPIC_API_KEY=sk-ant-api03-...

# Verify it's loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY'))"
```

#### 3. "Google hasn't verified this app"

**Cause**: App not published (normal for personal projects)

**Solution**:
1. Click "Advanced"
2. Click "Go to [App Name] (unsafe)"
3. This is safe for your own development apps
4. Alternatively, publish app in Google Cloud Console (complex process)

#### 4. SSL Certificate Errors

**Cause**: Concurrent API requests causing SSL context issues

**Solution**: Already implemented in code
```python
# Code uses sequential processing (not parallel)
# See GetGoogleFiles.py:462-509
for file in files:  # Not using ThreadPoolExecutor
    process_file(file)
```

#### 5. "Failed to parse Claude response"

**Cause**: Claude returned text instead of JSON, or included markdown

**Solution**: Already handled in code
```python
# See CloudBackup.py:244-249
if "```json" in response_text:
    response_text = response_text.split("```json")[1].split("```")[0].strip()
```

#### 6. Empty or Incomplete Extractions

**Possible Causes**:
- Poor image quality (blurry, low resolution)
- Heavily handwritten prescriptions
- Non-standard document formats

**Debug Steps**:
1. Check `document_quality` field in output
2. Review `comment` field for specific issues
3. Check `confidence` scores for extracted fields
4. Manually review the source PDF in `downloads/`

**Improve Results**:
- Use higher resolution scans (300+ DPI)
- Ensure good lighting in scanned images
- Prefer typed prescriptions over handwritten
- Clean scans (remove noise, shadows)

#### 7. Rate Limit Errors (Anthropic API)

**Error**: `429 Too Many Requests`

**Solution**:
```python
# Add delay between requests (modify CloudBackup.py)
import time

for file in files:
    process_file(file)
    time.sleep(1)  # Wait 1 second between files
```

Check rate limits: https://console.anthropic.com/settings/limits

#### 8. Out of Memory Errors

**Cause**: Processing very large PDFs or too many files

**Solution**:
```python
# Process in smaller batches
# Modify folder to contain fewer files
# Increase system RAM
# Or implement pagination in file listing
```

---

## Performance Metrics

### Processing Times (Approximate)

| Component | Typical Duration |
|-----------|------------------|
| OAuth authentication | 0-5 seconds (cached: instant) |
| File listing (100 files) | 1-2 seconds |
| Download single PDF | 0.5-3 seconds |
| Claude API processing | 3-10 seconds per PDF |
| JSON write | <0.1 seconds |

**Total**: ~5-15 seconds per document (primarily Claude processing)

### Cost Estimation (Anthropic API)

**Model**: Claude Sonnet 4.5

**Pricing** (as of 2025):
- Input: $3.00 per million tokens
- Output: $15.00 per million tokens

**Typical Usage per Prescription**:
- Input tokens: ~5,000 (PDF + prompt)
- Output tokens: ~1,000 (JSON response)

**Cost per document**: ~$0.03
**Cost per 1000 documents**: ~$30

---

## Dependencies

### Python Packages

```
google-auth==2.27.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.116.0
anthropic==0.39.0
python-dotenv==1.0.0
```

Install all:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client anthropic python-dotenv
```

### System Requirements

- **Python**: 3.10 or higher
- **OS**: Windows, macOS, or Linux
- **RAM**: 2GB minimum (4GB recommended)
- **Disk Space**: 500MB + space for downloaded PDFs
- **Internet**: Required for API access

---

## File Structure

```
OmmSai/
├── .env                              # API keys (gitignored)
├── .env.example                      # Template for .env
├── .gitignore                        # Git exclusions
├── credentials.json                  # Google OAuth credentials (gitignored)
├── token.pickle                      # OAuth tokens (gitignored)
│
├── GetGoogleFiles.py                 # Main GUI application
├── CloudBackup.py                    # Headless CLI version
├── CloudResponse.py                  # Claude API utility
├── app.py                            # API test script
│
├── downloads/                        # Downloaded PDFs (gitignored)
│   └── prescription_001.pdf
│
├── extracted_prescriptions.json     # Output data (gitignored)
├── README.md                         # User documentation
└── TECHNICAL_DOCUMENTATION.md       # This file
```

---

## Maintenance and Updates

### Updating Google API Credentials

If credentials expire or are revoked:
```bash
rm token.pickle
# Re-run app to trigger OAuth flow
python GetGoogleFiles.py
```

### Updating Claude Model

Change model version in code:
```python
# GetGoogleFiles.py:600 or CloudBackup.py:215
model="claude-sonnet-4-5-20250929"  # Update to newer version
```

Check available models: https://docs.anthropic.com/en/docs/about-claude/models

### Modifying Extraction Prompt

Edit `EXTRACTION_PROMPT` constant:
- `GetGoogleFiles.py:38-135`
- `CloudBackup.py:31-128`

**Tips for prompt engineering**:
1. Provide clear examples
2. Specify exact JSON structure
3. Define confidence criteria
4. Include medical terminology guide
5. Test with sample prescriptions

---

## Support and Resources

### Official Documentation
- [Google Drive API](https://developers.google.com/drive/api/v3/reference)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Python Tkinter](https://docs.python.org/3/library/tkinter.html)

### Debugging Tools
```bash
# Enable verbose logging for Google API
export GOOGLE_API_PYTHON_CLIENT_LOG_LEVEL=DEBUG

# Test Anthropic API connection
python app.py

# Validate JSON output
cat extracted_prescriptions.json | python -m json.tool
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-22
**Author**: Technical Documentation (Auto-generated)
