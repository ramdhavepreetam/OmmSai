"""
Prescription Extraction UI
A modern GUI for downloading and processing prescription PDFs with Claude AI

Prerequisites:
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client anthropic python-dotenv
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import pickle
import io
import json
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import time

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from anthropic import Anthropic

# Load environment variables from .env file
load_dotenv()

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
DEFAULT_FOLDER_ID = '15ZARfsIkva2O0ordMDZJJJZrj0WDLfLs'
DOWNLOAD_FOLDER = 'downloads'
OUTPUT_JSON_FILE = 'extracted_prescriptions.json'

EXTRACTION_PROMPT = """You are a specialized medical document understanding system tasked with extracting structured data from doctor's prescription PDFs. These documents contain printed field labels and handwritten entries by healthcare providers.

**Output Structure:**
{
  "document_id": "<filename or unique identifier>",
  "read_status": "<success|partial_success|failed>",
  "document_quality": "<excellent|good|fair|poor>",
  "comment": "<summary of extraction issues or quality notes>",
  "fields": {
    "<field_name>": {
      "value": "<extracted value or null if not readable>",
      "confidence": "<high|medium|low>",
      "note": "<optional: any clarification needed>"
    }
  }
}

**Common Prescription Fields to Extract:**
- Patient Name, Age, Gender, Contact Number
- Date (consultation/prescription date)
- Doctor Name, Registration Number, Specialty
- Diagnosis / Chief Complaint
- Medications (name, dosage, frequency, duration)
- Lab Tests / Investigations Ordered
- Follow-up Date / Next Visit
- Vital Signs (BP, Temperature, Pulse, Weight if present)
- Allergies / Medical History
- Special Instructions / Advice

**Extraction Guidelines:**

1. **Field Identification:** Match printed labels with handwritten values. If a standard field is missing from the document, omit it from the output (don't include empty fields).

2. **Handwriting Recognition:**
   - HIGH confidence: Clear, legible text
   - MEDIUM confidence: Mostly readable with minor ambiguity
   - LOW confidence: Partially legible, best-effort interpretation
   - NULL value: Completely illegible, heavily smudged, or ambiguous

3. **Medical Terminology:**
   - Recognize common abbreviations: bid (twice daily), tid (three times daily), qd (once daily), prn (as needed), po (by mouth), IM (intramuscular)
   - Parse dosage formats: "500mg", "5ml", "2 tablets"
   - Identify duration: "5 days", "2 weeks", "1 month"

4. **Data Validation:**
   - Dates: Format as YYYY-MM-DD or DD/MM/YYYY (preserve original format)
   - Phone numbers: Extract as-is, include country code if visible
   - Dosages: Keep units attached to numbers (e.g., "500mg" not "500 mg")

5. **Document Quality Assessment:**
   - EXCELLENT: High-resolution, clear scan, minimal handwriting issues
   - GOOD: Readable with minor imperfections
   - FAIR: Some blur/distortion but most content extractable
   - POOR: Significant quality issues affecting readability

6. **Read Status Criteria:**
   - SUCCESS: ≥90% of fields extracted with high/medium confidence
   - PARTIAL_SUCCESS: 50-89% of fields extracted, or multiple low-confidence reads
   - FAILED: <50% extractable, severe quality issues, or wrong document type

7. **Comments Field:** Provide actionable notes:
   - "Prescription date unclear due to smudging"
   - "Medication #3 dosage illegible - requires verification"
   - "Excellent scan quality, all fields clearly visible"

**Output Format:**
- Return ONLY valid JSON
- No markdown code blocks, no explanatory text
- Use null for unreadable values, not empty strings
- Include confidence scores for all extracted fields
- Keep medical terminology as written (don't translate abbreviations unless clarification is needed in the note)

**Example Output:**
{
  "document_id": "prescription_001.pdf",
  "read_status": "success",
  "document_quality": "good",
  "comment": "All major fields extracted. Minor blur on medication #2 duration.",
  "fields": {
    "patient_name": {
      "value": "John Doe",
      "confidence": "high"
    },
    "date": {
      "value": "2025-01-15",
      "confidence": "high"
    },
    "diagnosis": {
      "value": "Acute bronchitis",
      "confidence": "medium",
      "note": "Handwriting slightly unclear but context suggests bronchitis"
    },
    "medication_1": {
      "value": "Amoxicillin 500mg tid x 7 days",
      "confidence": "high"
    }
  }
}"""


class PrescriptionExtractorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🏥 Prescription Extractor")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')

        # Variables
        self.folder_id = tk.StringVar(value=DEFAULT_FOLDER_ID)
        self.output_file = tk.StringVar(value=OUTPUT_JSON_FILE)
        self.is_processing = False
        self.google_service = None

        # Stats
        self.total_files = 0
        self.processed_files = 0
        self.success_count = 0
        self.partial_count = 0
        self.failed_count = 0

        self.create_widgets()

    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        header_frame.pack(fill='x', pady=(0, 10))
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="🏥 Doctor's Prescription Extractor",
            font=('Helvetica', 18, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=15)

        # Main container
        main_container = tk.Frame(self.root, bg='#f0f0f0')
        main_container.pack(fill='both', expand=True, padx=20, pady=10)

        # Configuration Frame
        config_frame = tk.LabelFrame(
            main_container,
            text="Configuration",
            font=('Helvetica', 12, 'bold'),
            bg='white',
            padx=15,
            pady=15
        )
        config_frame.pack(fill='x', pady=(0, 10))

        # Google Drive Folder ID
        tk.Label(config_frame, text="Google Drive Folder ID:", bg='white', font=('Helvetica', 10)).grid(
            row=0, column=0, sticky='w', pady=5
        )
        tk.Entry(config_frame, textvariable=self.folder_id, width=50).grid(
            row=0, column=1, pady=5, padx=10, sticky='ew'
        )

        # Output File
        tk.Label(config_frame, text="Output JSON File:", bg='white', font=('Helvetica', 10)).grid(
            row=1, column=0, sticky='w', pady=5
        )
        output_frame = tk.Frame(config_frame, bg='white')
        output_frame.grid(row=1, column=1, pady=5, padx=10, sticky='ew')
        tk.Entry(output_frame, textvariable=self.output_file,
                 width=40).pack(side='left', fill='x', expand=True)
        tk.Button(output_frame, text="Browse", command=self.browse_output).pack(
            side='left', padx=(5, 0))

        config_frame.columnconfigure(1, weight=1)

        # Progress Frame
        progress_frame = tk.LabelFrame(
            main_container,
            text="Progress",
            font=('Helvetica', 12, 'bold'),
            bg='white',
            padx=15,
            pady=15
        )
        progress_frame.pack(fill='x', pady=(0, 10))

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill='x', pady=(0, 10))

        # Progress label
        self.progress_label = tk.Label(
            progress_frame,
            text="Ready to start",
            font=('Helvetica', 10),
            bg='white'
        )
        self.progress_label.pack()

        # Stats Frame
        stats_frame = tk.Frame(progress_frame, bg='white')
        stats_frame.pack(fill='x', pady=(10, 0))

        # Create stat cards
        self.total_label = self.create_stat_card(
            stats_frame, "Total Files", "0", "#3498db", 0)
        self.processed_label = self.create_stat_card(
            stats_frame, "Processed", "0", "#9b59b6", 1)
        self.success_label = self.create_stat_card(
            stats_frame, "Success", "0", "#27ae60", 2)
        self.partial_label = self.create_stat_card(
            stats_frame, "Partial", "0", "#f39c12", 3)
        self.failed_label = self.create_stat_card(
            stats_frame, "Failed", "0", "#e74c3c", 4)

        # Log Frame
        log_frame = tk.LabelFrame(
            main_container,
            text="Processing Log",
            font=('Helvetica', 12, 'bold'),
            bg='white',
            padx=15,
            pady=15
        )
        log_frame.pack(fill='both', expand=True, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            font=('Courier', 9),
            bg='#1e1e1e',
            fg='#00ff00',
            insertbackground='white'
        )
        self.log_text.pack(fill='both', expand=True)

        # Control Frame
        control_frame = tk.Frame(main_container, bg='#f0f0f0')
        control_frame.pack(fill='x')

        self.start_button = tk.Button(
            control_frame,
            text="Start Processing",
            command=self.start_processing,
            bg='#27ae60',
            fg='white',
            font=('Helvetica', 12, 'bold'),
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        self.start_button.pack(side='left', padx=5)

        self.stop_button = tk.Button(
            control_frame,
            text="Stop",
            command=self.stop_processing,
            bg='#e74c3c',
            fg='white',
            font=('Helvetica', 12, 'bold'),
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2',
            state='disabled'
        )
        self.stop_button.pack(side='left', padx=5)

        self.open_output_button = tk.Button(
            control_frame,
            text="Open Output File",
            command=self.open_output_file,
            bg='#3498db',
            fg='white',
            font=('Helvetica', 12, 'bold'),
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        self.open_output_button.pack(side='right', padx=5)

    def create_stat_card(self, parent, label, value, color, column):
        frame = tk.Frame(parent, bg=color, relief='raised', borderwidth=2)
        frame.grid(row=0, column=column, padx=5, pady=5, sticky='ew')

        tk.Label(
            frame,
            text=label,
            font=('Helvetica', 9),
            bg=color,
            fg='white'
        ).pack(pady=(5, 0))

        value_label = tk.Label(
            frame,
            text=value,
            font=('Helvetica', 16, 'bold'),
            bg=color,
            fg='white'
        )
        value_label.pack(pady=(0, 5))

        parent.columnconfigure(column, weight=1)

        return value_label

    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.output_file.set(filename)

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_tag = {
            "INFO": "info",
            "SUCCESS": "success",
            "WARNING": "warning",
            "ERROR": "error"
        }.get(level, "info")

        self.log_text.insert('end', f"[{timestamp}] {message}\n", color_tag)
        self.log_text.see('end')

        # Configure tags
        self.log_text.tag_config("info", foreground="#00ff00")
        self.log_text.tag_config(
            "success", foreground="#00ff00", font=('Courier', 9, 'bold'))
        self.log_text.tag_config("warning", foreground="#f39c12")
        self.log_text.tag_config("error", foreground="#e74c3c")

        self.root.update_idletasks()

    def update_stats(self):
        self.total_label.config(text=str(self.total_files))
        self.processed_label.config(text=str(self.processed_files))
        self.success_label.config(text=str(self.success_count))
        self.partial_label.config(text=str(self.partial_count))
        self.failed_label.config(text=str(self.failed_count))

        if self.total_files > 0:
            progress = (self.processed_files / self.total_files) * 100
            self.progress_var.set(progress)
            self.progress_label.config(
                text=f"Processing: {self.processed_files}/{self.total_files} files ({progress:.1f}%)"
            )

    def authenticate_google(self):
        creds = None

        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    self.log("ERROR: credentials.json not found!", "ERROR")
                    messagebox.showerror(
                        "Error", "credentials.json not found!\n\nPlease download OAuth credentials from Google Cloud Console.")
                    return None

                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('drive', 'v3', credentials=creds)
        return service

    def process_files(self):
        try:
            # Authenticate Google Drive
            self.log("Authenticating with Google Drive...")
            self.google_service = self.authenticate_google()
            if not self.google_service:
                return
            self.log("✓ Google Drive authentication successful", "SUCCESS")

            # Get API key from environment
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                self.log("ERROR: ANTHROPIC_API_KEY not found in .env file!", "ERROR")
                messagebox.showerror(
                    "Error", "ANTHROPIC_API_KEY not found in .env file!\n\nPlease add it to your .env file.")
                return

            self.log("✓ Claude API key loaded from .env", "SUCCESS")

            # List files
            self.log(f"Fetching files from folder: {self.folder_id.get()}")
            files = self.list_files_in_folder(self.folder_id.get())

            if not files:
                self.log("No files found in the folder", "WARNING")
                return

            self.total_files = len(files)
            self.update_stats()
            self.log(f"Found {self.total_files} files", "SUCCESS")
            self.log(f"Starting sequential processing...", "INFO")

            # Initialize output file with empty array
            output_path = self.output_file.get()
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
            self.log(f"✓ Output file initialized: {output_path}", "SUCCESS")

            # Create single Claude client
            client = Anthropic(api_key=api_key)

            # Process files one by one (sequential)
            all_results = []

            for file in files:
                if not self.is_processing:
                    self.log("Processing stopped by user", "WARNING")
                    break

                try:
                    self.log(f"\nProcessing: {file['name']}")

                    # Download file
                    file_path = self.download_file(file)

                    if file_path:
                        # Extract with Claude
                        extracted_data = self.extract_with_claude(
                            client, file_path, file['name'])
                    else:
                        extracted_data = {
                            "document_id": file['name'],
                            "read_status": "failed",
                            "comment": "Failed to download file",
                            "fields": {}
                        }

                    # Update stats
                    status = extracted_data.get('read_status', 'failed')
                    if status == 'success':
                        self.success_count += 1
                    elif status == 'partial_success':
                        self.partial_count += 1
                    else:
                        self.failed_count += 1

                    # Save immediately to output file
                    all_results.append(extracted_data)
                    self.write_to_json_file(output_path, extracted_data)

                    self.processed_files += 1
                    self.update_stats()
                    self.log(f"Progress: {self.processed_files}/{self.total_files} ({status})")

                except Exception as e:
                    self.log(f"  ✗ Error processing {file['name']}: {str(e)}", "ERROR")
                    self.failed_count += 1
                    self.processed_files += 1
                    self.update_stats()

            # Final stats update
            self.update_stats()

            self.log(f"\n{'='*50}", "SUCCESS")
            self.log(f"EXTRACTION COMPLETE!", "SUCCESS")
            self.log(
                f"Total: {self.total_files} | Success: {self.success_count} | Partial: {self.partial_count} | Failed: {self.failed_count}", "SUCCESS")
            self.log(f"{'='*50}", "SUCCESS")

            if self.is_processing:
                messagebox.showinfo(
                    "Complete", f"Processing complete!\n\n✓ Success: {self.success_count}\n⚠ Partial: {self.partial_count}\n✗ Failed: {self.failed_count}")

        except Exception as e:
            self.log(f"ERROR: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

        finally:
            self.is_processing = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')

    def write_to_json_file(self, file_path, new_data):
        """Append data to JSON file immediately"""
        try:
            # Read existing data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Append new data
            data.append(new_data)

            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.log(f"  ✗ Error writing to file: {str(e)}", "ERROR")

    def list_files_in_folder(self, folder_id):
        query = f"'{folder_id}' in parents and trashed=false"
        results = self.google_service.files().list(
            q=query,
            pageSize=1000,
            fields="nextPageToken, files(id, name, mimeType, size)").execute()
        return results.get('files', [])

    def download_file(self, file):
        try:
            if not os.path.exists(DOWNLOAD_FOLDER):
                os.makedirs(DOWNLOAD_FOLDER)

            file_name = file['name']
            mime_type = file['mimeType']

            if mime_type.startswith('application/vnd.google-apps'):
                request = self.google_service.files().export_media(
                    fileId=file['id'],
                    mimeType='application/pdf'
                )
                if not file_name.endswith('.pdf'):
                    file_name = os.path.splitext(file_name)[0] + '.pdf'
            else:
                request = self.google_service.files().get_media(fileId=file['id'])

            file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
            fh = io.FileIO(file_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while done is False:
                status, done = downloader.next_chunk()

            fh.close()
            self.log(f"  ✓ Downloaded: {file_name}", "SUCCESS")
            return file_path

        except Exception as e:
            self.log(f"  ✗ Download error: {str(e)}", "ERROR")
            return None

    def extract_with_claude(self, client, file_path, filename):
        try:
            self.log(f"  → Sending to Claude AI...")

            with open(file_path, 'rb') as f:
                pdf_data = base64.standard_b64encode(f.read()).decode('utf-8')

            message = client.messages.create(
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

            response_text = message.content[0].text

            if "```json" in response_text:
                response_text = response_text.split(
                    "```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split(
                    "```")[1].split("```")[0].strip()

            extracted_data = json.loads(response_text)

            if not extracted_data.get('document_id'):
                extracted_data['document_id'] = filename

            status = extracted_data.get('read_status', 'unknown')
            self.log(f"  ✓ Extraction complete: {status}", "SUCCESS")

            return extracted_data

        except Exception as e:
            self.log(f"  ✗ Claude error: {str(e)}", "ERROR")
            return {
                "document_id": filename,
                "read_status": "failed",
                "comment": f"Error: {str(e)}",
                "fields": {}
            }

    def start_processing(self):
        if not self.folder_id.get().strip():
            messagebox.showerror(
                "Error", "Please enter a Google Drive Folder ID")
            return

        # Reset stats
        self.processed_files = 0
        self.success_count = 0
        self.partial_count = 0
        self.failed_count = 0
        self.total_files = 0
        self.update_stats()

        self.is_processing = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.log_text.delete(1.0, 'end')

        # Start processing in thread
        thread = threading.Thread(target=self.process_files, daemon=True)
        thread.start()

    def stop_processing(self):
        self.is_processing = False
        self.log("\nStopping process...", "WARNING")
        self.stop_button.config(state='disabled')

    def open_output_file(self):
        output_path = self.output_file.get()
        if os.path.exists(output_path):
            os.system(f'open "{output_path}"' if os.name ==
                      'posix' else f'start "" "{output_path}"')
        else:
            messagebox.showwarning(
                "File Not Found", "Output file does not exist yet.\nPlease run the extraction first.")


def main():
    root = tk.Tk()
    app = PrescriptionExtractorUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
