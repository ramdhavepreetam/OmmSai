"""
Google Drive API integration module
Handles authentication, file listing, and downloading
"""
import os
import pickle
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from ..config.settings import Settings


class GoogleDriveService:
    """Handles all Google Drive API operations"""

    def __init__(self):
        self.service = None
        self.authenticated = False

    def authenticate(self):
        """
        Authenticate with Google Drive using OAuth 2.0
        Returns True if successful, False otherwise
        """
        creds = None

        # Load existing credentials
        if os.path.exists(Settings.TOKEN_FILE):
            with open(Settings.TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)

        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(Settings.CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"{Settings.CREDENTIALS_FILE} not found! "
                        "Please download OAuth credentials from Google Cloud Console."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    Settings.CREDENTIALS_FILE, Settings.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for future use
            with open(Settings.TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)

        # Build service
        self.service = build('drive', 'v3', credentials=creds)
        self.authenticated = True
        return True

    def list_files(self, folder_id):
        """
        List all files in a specific Google Drive folder

        Args:
            folder_id (str): Google Drive folder ID

        Returns:
            list: List of file metadata dictionaries
        """
        if not self.authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        query = f"'{folder_id}' in parents and trashed=false"
        results = self.service.files().list(
            q=query,
            pageSize=1000,
            fields="nextPageToken, files(id, name, mimeType, size)"
        ).execute()

        return results.get('files', [])

    def download_file(self, file_id, file_name, mime_type, destination_folder=None):
        """
        Download a file from Google Drive

        Args:
            file_id (str): Google Drive file ID
            file_name (str): Name to save the file as
            mime_type (str): MIME type of the file
            destination_folder (str): Folder to save the file in

        Returns:
            str: Path to downloaded file, or None if failed
        """
        if not self.authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        # Use default download folder if not specified
        if destination_folder is None:
            destination_folder = Settings.DOWNLOAD_FOLDER

        # Create directory if it doesn't exist
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        try:
            # Handle Google Workspace files (export as PDF)
            if mime_type.startswith('application/vnd.google-apps'):
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='application/pdf'
                )
                # Ensure filename has .pdf extension
                if not file_name.endswith('.pdf'):
                    file_name = os.path.splitext(file_name)[0] + '.pdf'
            else:
                # Regular file download
                request = self.service.files().get_media(fileId=file_id)

            # Download file
            file_path = os.path.join(destination_folder, file_name)
            fh = io.FileIO(file_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            fh.close()
            return file_path

        except Exception as e:
            print(f"Error downloading {file_name}: {str(e)}")
            return None

    def get_file_metadata(self, file_id):
        """
        Get metadata for a specific file

        Args:
            file_id (str): Google Drive file ID

        Returns:
            dict: File metadata
        """
        if not self.authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.service.files().get(
            fileId=file_id,
            fields="id, name, mimeType, size, createdTime, modifiedTime"
        ).execute()
