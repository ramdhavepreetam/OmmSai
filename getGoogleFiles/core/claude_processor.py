"""
Claude AI integration module
Handles PDF processing and data extraction using Anthropic's Claude API
"""
import base64
import json
from anthropic import Anthropic

from ..config.settings import Settings
from ..config.prompts import EXTRACTION_PROMPT


class ClaudeProcessor:
    """Handles Claude AI operations for document processing"""

    def __init__(self, api_key=None):
        """
        Initialize Claude processor

        Args:
            api_key (str): Anthropic API key (uses Settings if not provided)
        """
        self.api_key = api_key or Settings.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=self.api_key)

    def encode_pdf_to_base64(self, file_path):
        """
        Encode PDF file to base64 string

        Args:
            file_path (str): Path to PDF file

        Returns:
            str: Base64 encoded PDF data
        """
        with open(file_path, 'rb') as f:
            return base64.standard_b64encode(f.read()).decode('utf-8')

    def extract_data(self, file_path, filename):
        """
        Extract structured data from prescription PDF using Claude AI

        Args:
            file_path (str): Path to PDF file
            filename (str): Name of the file (for document_id)

        Returns:
            dict: Extracted prescription data in JSON format
        """
        try:
            # Encode PDF to base64
            pdf_data = self.encode_pdf_to_base64(file_path)

            # Send to Claude API
            message = self.client.messages.create(
                model=Settings.CLAUDE_MODEL,
                max_tokens=Settings.MAX_TOKENS,
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

            # Extract response text
            response_text = message.content[0].text

            # Clean markdown code blocks if present
            response_text = self._clean_json_response(response_text)

            # Parse JSON
            extracted_data = json.loads(response_text)

            # Ensure document_id is set
            if not extracted_data.get('document_id'):
                extracted_data['document_id'] = filename

            return extracted_data

        except json.JSONDecodeError as e:
            return {
                "document_id": filename,
                "read_status": "failed",
                "comment": f"JSON parsing error: {str(e)}",
                "fields": {}
            }
        except Exception as e:
            return {
                "document_id": filename,
                "read_status": "failed",
                "comment": f"Error: {str(e)}",
                "fields": {}
            }

    def _clean_json_response(self, text):
        """
        Remove markdown code blocks from Claude response

        Args:
            text (str): Raw response text

        Returns:
            str: Cleaned JSON text
        """
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return text

    def simple_query(self, prompt, model=None, max_tokens=100):
        """
        Send a simple text query to Claude (for testing or general use)

        Args:
            prompt (str): Query text
            model (str): Model to use (default: haiku)
            max_tokens (int): Max response length

        Returns:
            dict: Response with success status, text, and usage stats
        """
        try:
            model = model or "claude-3-5-haiku-20241022"

            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            return {
                "success": True,
                "text": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
