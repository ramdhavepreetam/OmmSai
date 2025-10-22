# Quick Start Guide - OmmSai

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure APIs

#### Google Drive Setup (2 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable "Google Drive API"
3. Create OAuth credentials (Desktop app)
4. Download as `credentials.json` in project root

**Detailed guide**: See [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#google-drive-api-setup)

#### Anthropic API Setup (1 minute)

```bash
# Copy template
cp .env.example .env

# Edit and add your key
# ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

Get key from: [Anthropic Console](https://console.anthropic.com/)

### Step 3: Test Setup

```bash
python test_api.py
```

Expected output:
```
✓ Claude API is working!
✓ Google Drive authentication successful!
✓ Found X files
```

### Step 4: Run the Application

#### GUI Mode (Easiest)

```bash
python main_gui.py
```

1. Paste your Google Drive Folder ID
2. Click "Start Processing"
3. Done! Results in `extracted_prescriptions.json`

#### CLI Mode (For Automation)

```bash
python main_cli.py --folder-id YOUR_FOLDER_ID
```

---

## 📁 Find Your Folder ID

Open Google Drive folder → Look at URL:
```
https://drive.google.com/drive/folders/15ZARfsIkva2O0ordMDZJJJZrj0WDLfLs
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                         This is your Folder ID
```

---

## 🎯 What It Does

1. **Downloads** PDFs from your Google Drive folder
2. **Extracts** prescription data using AI (Claude)
3. **Outputs** structured JSON with confidence scores

Example output:
```json
{
  "document_id": "prescription_001.pdf",
  "read_status": "success",
  "fields": {
    "patient_name": { "value": "John Doe", "confidence": "high" },
    "medications": { "value": "Amoxicillin 500mg", "confidence": "high" }
  }
}
```

---

## 🛠️ Project Structure (New!)

```
OmmSai/
├── main_gui.py              ⭐ Run this for GUI
├── main_cli.py              ⭐ Run this for CLI
├── test_api.py              ⭐ Run this to test
├── getGoogleFiles/          📦 Modular package
│   ├── config/              ⚙️ Settings
│   ├── core/                💼 Business logic
│   ├── ui/                  🖥️ GUI
│   └── utils/               🔧 Utilities
└── README.md                📖 Full documentation
```

---

## ⚡ Quick Commands

```bash
# GUI (recommended for first time)
python main_gui.py

# CLI with default folder
python main_cli.py

# CLI with custom folder
python main_cli.py --folder-id YOUR_ID

# CLI with custom output
python main_cli.py --output results.json

# Test APIs
python test_api.py
```

---

## 🆘 Troubleshooting

### "credentials.json not found"
→ Download OAuth credentials from Google Cloud Console

### "ANTHROPIC_API_KEY not found"
→ Check `.env` file exists and contains your key

### Import errors
→ Run `pip install -r requirements.txt`

### Authentication popup
→ Click "Advanced" → "Go to app (unsafe)" (safe for your own app)

---

## 📚 Full Documentation

- **README.md** - Complete usage guide
- **TECHNICAL_DOCUMENTATION.md** - Architecture and setup
- **REFACTORING_SUMMARY.md** - Code structure changes

---

## 💡 Pro Tips

1. **First time?** Use GUI mode - easier to see what's happening
2. **Automation?** Use CLI mode with cron jobs
3. **Testing?** Always run `test_api.py` first
4. **Errors?** Check logs in GUI or terminal output

---

**Ready to go!** 🎉

Start with: `python test_api.py` → then `python main_gui.py`
