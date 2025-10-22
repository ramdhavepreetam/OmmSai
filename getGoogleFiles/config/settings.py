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

    # Parallel Processing Configuration
    ENABLE_PARALLEL = True           # Enable parallel processing by default
    MAX_WORKERS = 10                 # Number of concurrent workers (threads)
    MIN_WORKERS = 1                  # Minimum workers (sequential mode)
    MAX_WORKERS_LIMIT = 50           # Maximum allowed workers

    # Checkpoint Configuration
    ENABLE_CHECKPOINTING = True      # Enable checkpoint/resume capability
    CHECKPOINT_FILE = 'processing_checkpoint.json'
    CHECKPOINT_BATCH_SIZE = 100      # Save checkpoint every N files

    # Retry Configuration
    RETRY_ATTEMPTS = 3               # Maximum retry attempts for failed operations
    RETRY_BASE_DELAY = 1             # Initial retry delay in seconds
    RETRY_MAX_DELAY = 60             # Maximum retry delay in seconds

    # Rate Limiting Configuration
    GOOGLE_DRIVE_RATE_LIMIT = 100    # Max requests per minute for Google Drive
    CLAUDE_RATE_LIMIT = 50           # Max requests per minute for Claude API

    @classmethod
    def validate(cls):
        """Validate required settings"""
        errors = []

        if not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY not found in environment variables")

        if not os.path.exists(cls.CREDENTIALS_FILE):
            errors.append(f"{cls.CREDENTIALS_FILE} not found")

        # Validate parallel processing settings
        if cls.MAX_WORKERS < cls.MIN_WORKERS:
            errors.append(f"MAX_WORKERS ({cls.MAX_WORKERS}) must be >= MIN_WORKERS ({cls.MIN_WORKERS})")

        if cls.MAX_WORKERS > cls.MAX_WORKERS_LIMIT:
            errors.append(f"MAX_WORKERS ({cls.MAX_WORKERS}) exceeds limit ({cls.MAX_WORKERS_LIMIT})")

        return errors

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        Path(cls.DOWNLOAD_FOLDER).mkdir(exist_ok=True)
