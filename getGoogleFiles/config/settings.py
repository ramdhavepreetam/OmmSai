"""
Application configuration and settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings and configuration"""

    # Google Drive Configuration
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    DEFAULT_FOLDER_ID = '15ZARfsIkva2O0ordMDZJJJZrj0WDLfLs'
    CREDENTIALS_FILE = 'credentials.json'
    TOKEN_FILE = 'token.pickle'

    # File Storage
    DOWNLOAD_FOLDER = 'downloads'
    OUTPUT_JSON_FILE = 'extracted_prescriptions.json'

    # API Configuration
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
    MAX_TOKENS = 8192

    # UI Configuration
    WINDOW_TITLE = "🏥 Prescription Extractor"
    WINDOW_SIZE = "900x700"

    @classmethod
    def validate(cls):
        """Validate required settings"""
        errors = []

        if not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY not found in environment variables")

        if not os.path.exists(cls.CREDENTIALS_FILE):
            errors.append(f"{cls.CREDENTIALS_FILE} not found")

        return errors

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        Path(cls.DOWNLOAD_FOLDER).mkdir(exist_ok=True)
