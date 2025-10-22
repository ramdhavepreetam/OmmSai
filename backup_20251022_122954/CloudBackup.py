"""
Google Drive to Claude AI Document Processor
Downloads prescription PDFs from Google Drive and extracts structured JSON using Claude AI

Prerequisites:
1. pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client anthropic
2. Set up Google Drive API credentials (credentials.json)
3. Set ANTHROPIC_API_KEY environment variable
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import os
import pickle
import io
import json
from anthropic import Anthropic
import base64
from pathlib import Path

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = '15ZARfsIkva2O0ordMDZJJJZrj0WDLfLs'
DOWNLOAD_FOLDER = 'downloads'
OUTPUT_JSON_FILE = 'extracted_prescriptions.json'

# Extraction prompt
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


def authenticate_google():
    """Authenticate and return the Google Drive service"""
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)
    return service


def list_files_in_folder(service, folder_id):
    """List all files in a specific folder"""
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        pageSize=1000,
        fields="nextPageToken, files(id, name, mimeType, size)").execute()
    items = results.get('files', [])

    print(f'Found {len(items)} files in the folder')
    return items


def download_file(service, file_id, file_name, mime_type, destination_folder):
    """Download a file from Google Drive"""
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    try:
        if mime_type.startswith('application/vnd.google-apps'):
            # Export Google Workspace files as PDF
            request = service.files().export_media(
                fileId=file_id, mimeType='application/pdf')
            if not file_name.endswith('.pdf'):
                file_name = os.path.splitext(file_name)[0] + '.pdf'
        else:
            request = service.files().get_media(fileId=file_id)

        file_path = os.path.join(destination_folder, file_name)
        fh = io.FileIO(file_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while done is False:
            status, done = downloader.next_chunk()

        print(f"  ✓ Downloaded: {file_name}")
        return file_path

    except Exception as e:
        print(f"  ✗ Error downloading {file_name}: {str(e)}")
        return None


def encode_pdf_to_base64(file_path):
    """Encode PDF file to base64"""
    with open(file_path, 'rb') as f:
        return base64.standard_b64encode(f.read()).decode('utf-8')


def extract_data_with_claude(file_path, api_key):
    """Send PDF to Claude AI and extract structured JSON"""
    try:
        client = Anthropic(api_key=api_key)

        # Encode the PDF
        pdf_data = encode_pdf_to_base64(file_path)

        # Send to Claude
        print(f"  → Sending to Claude AI for processing...")
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

        # Extract JSON from response
        response_text = message.content[0].text

        # Try to parse the JSON
        try:
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split(
                    "```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split(
                    "```")[1].split("```")[0].strip()

            extracted_data = json.loads(response_text)
            print(f"  ✓ Successfully extracted data")
            return extracted_data

        except json.JSONDecodeError as e:
            print(f"  ✗ JSON parsing error: {str(e)}")
            return {
                "document_id": os.path.basename(file_path),
                "read_status": "failed",
                "comment": f"Failed to parse Claude response: {str(e)}",
                "fields": {},
                "raw_response": response_text
            }

    except Exception as e:
        print(f"  ✗ Error processing with Claude: {str(e)}")
        return {
            "document_id": os.path.basename(file_path),
            "read_status": "failed",
            "comment": f"Error: {str(e)}",
            "fields": {}
        }


def process_all_files(service, folder_id, download_folder, output_json):
    """Download and process all files"""
    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set!")
        print("Please set it using: export ANTHROPIC_API_KEY='your-api-key'")
        return

    print(f"\n{'='*70}")
    print(f"PRESCRIPTION EXTRACTION PIPELINE")
    print(f"{'='*70}\n")

    # List files
    print("Step 1: Fetching file list from Google Drive...")
    files = list_files_in_folder(service, folder_id)

    if not files:
        print("No files found in the folder!")
        return

    print(f"\nStep 2: Downloading and processing {len(files)} files...\n")

    all_extracted_data = []

    for idx, file in enumerate(files, 1):
        print(f"\n[{idx}/{len(files)}] Processing: {file['name']}")
        print("-" * 70)

        # Download file
        file_path = download_file(service, file['id'], file['name'],
                                  file['mimeType'], download_folder)

        if file_path:
            # Process with Claude
            extracted_data = extract_data_with_claude(file_path, api_key)

            # Ensure document_id is set
            if not extracted_data.get('document_id'):
                extracted_data['document_id'] = file['name']

            all_extracted_data.append(extracted_data)
        else:
            # If download failed, add error entry
            all_extracted_data.append({
                "document_id": file['name'],
                "read_status": "failed",
                "comment": "Failed to download file",
                "fields": {}
            })

    # Save all extracted data to JSON
    print(f"\n{'='*70}")
    print(f"Step 3: Saving extracted data...")
    print(f"{'='*70}\n")

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(all_extracted_data, f, indent=2, ensure_ascii=False)

    print(f"✓ All data saved to: {os.path.abspath(output_json)}")

    # Summary
    success_count = sum(
        1 for d in all_extracted_data if d['read_status'] == 'success')
    partial_count = sum(
        1 for d in all_extracted_data if d['read_status'] == 'partial_success')
    failed_count = sum(
        1 for d in all_extracted_data if d['read_status'] == 'failed')

    print(f"\n{'='*70}")
    print(f"EXTRACTION SUMMARY")
    print(f"{'='*70}")
    print(f"Total files processed: {len(files)}")
    print(f"✓ Success: {success_count}")
    print(f"⚠ Partial success: {partial_count}")
    print(f"✗ Failed: {failed_count}")
    print(f"{'='*70}\n")


def main():
    """Main function"""
    print("\n🏥 Doctor's Prescription Extraction System\n")

    # Authenticate with Google Drive
    print("Authenticating with Google Drive...")
    service = authenticate_google()
    print("✓ Google Drive authentication successful!\n")

    # Process all files
    process_all_files(service, FOLDER_ID, DOWNLOAD_FOLDER, OUTPUT_JSON_FILE)


if __name__ == '__main__':
    main()
