"""
OmmSai - Prescription Extraction System
A modular system for downloading and processing prescription PDFs using Google Drive and Claude AI
"""

__version__ = "1.0.0"
__author__ = "OmmSai Team"

from .core.google_drive import GoogleDriveService
from .core.claude_processor import ClaudeProcessor
from .utils.logger import setup_logger

__all__ = [
    'GoogleDriveService',
    'ClaudeProcessor',
    'setup_logger'
]
