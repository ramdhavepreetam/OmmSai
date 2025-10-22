"""
GUI Application for Prescription Extraction
Modern Tkinter interface for downloading and processing prescription PDFs
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
from datetime import datetime

from ..core.google_drive import GoogleDriveService
from ..core.claude_processor import ClaudeProcessor
from ..config.settings import Settings
from ..utils.file_handler import FileHandler


class PrescriptionExtractorUI:
    """Main GUI application for prescription extraction"""

    def __init__(self, root):
        self.root = root
        self.root.title(Settings.WINDOW_TITLE)
        self.root.geometry(Settings.WINDOW_SIZE)
        self.root.configure(bg='#f0f0f0')

        # Services
        self.google_service = None
        self.claude_processor = None

        # Variables
        self.folder_id = tk.StringVar(value=Settings.DEFAULT_FOLDER_ID)
        self.output_file = tk.StringVar(value=Settings.OUTPUT_JSON_FILE)
        self.is_processing = False

        # Statistics
        self.total_files = 0
        self.processed_files = 0
        self.success_count = 0
        self.partial_count = 0
        self.failed_count = 0

        # Create UI
        self.create_widgets()

        # Ensure directories exist
        Settings.ensure_directories()

    def create_widgets(self):
        """Create and layout all UI components"""
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
        self._create_config_frame(main_container)

        # Progress Frame
        self._create_progress_frame(main_container)

        # Log Frame
        self._create_log_frame(main_container)

        # Control Frame
        self._create_control_frame(main_container)

    def _create_config_frame(self, parent):
        """Create configuration section"""
        config_frame = tk.LabelFrame(
            parent,
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
        tk.Entry(output_frame, textvariable=self.output_file, width=40).pack(side='left', fill='x', expand=True)
        tk.Button(output_frame, text="Browse", command=self.browse_output).pack(side='left', padx=(5, 0))

        config_frame.columnconfigure(1, weight=1)

    def _create_progress_frame(self, parent):
        """Create progress tracking section"""
        progress_frame = tk.LabelFrame(
            parent,
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
        self.total_label = self._create_stat_card(stats_frame, "Total Files", "0", "#3498db", 0)
        self.processed_label = self._create_stat_card(stats_frame, "Processed", "0", "#9b59b6", 1)
        self.success_label = self._create_stat_card(stats_frame, "Success", "0", "#27ae60", 2)
        self.partial_label = self._create_stat_card(stats_frame, "Partial", "0", "#f39c12", 3)
        self.failed_label = self._create_stat_card(stats_frame, "Failed", "0", "#e74c3c", 4)

    def _create_log_frame(self, parent):
        """Create logging section"""
        log_frame = tk.LabelFrame(
            parent,
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

        # Configure tags for colored output
        self.log_text.tag_config("info", foreground="#00ff00")
        self.log_text.tag_config("success", foreground="#00ff00", font=('Courier', 9, 'bold'))
        self.log_text.tag_config("warning", foreground="#f39c12")
        self.log_text.tag_config("error", foreground="#e74c3c")

    def _create_control_frame(self, parent):
        """Create control buttons section"""
        control_frame = tk.Frame(parent, bg='#f0f0f0')
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

    def _create_stat_card(self, parent, label, value, color, column):
        """Create a statistics display card"""
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
        """Open file browser for output file selection"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.output_file.set(filename)

    def log(self, message, level="INFO"):
        """Add a log message with timestamp and color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_tag = {
            "INFO": "info",
            "SUCCESS": "success",
            "WARNING": "warning",
            "ERROR": "error"
        }.get(level, "info")

        self.log_text.insert('end', f"[{timestamp}] {message}\n", color_tag)
        self.log_text.see('end')
        self.root.update_idletasks()

    def update_stats(self):
        """Update statistics display"""
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
        """Authenticate with Google Drive"""
        try:
            self.google_service = GoogleDriveService()
            self.google_service.authenticate()
            return True
        except FileNotFoundError as e:
            self.log(str(e), "ERROR")
            messagebox.showerror("Error", str(e))
            return False
        except Exception as e:
            self.log(f"Authentication error: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Authentication failed: {str(e)}")
            return False

    def process_files(self):
        """Main processing loop - runs in separate thread"""
        try:
            # Authenticate Google Drive
            self.log("Authenticating with Google Drive...")
            if not self.authenticate_google():
                return
            self.log("✓ Google Drive authentication successful", "SUCCESS")

            # Initialize Claude processor
            try:
                self.claude_processor = ClaudeProcessor()
                self.log("✓ Claude API initialized", "SUCCESS")
            except ValueError as e:
                self.log(str(e), "ERROR")
                messagebox.showerror("Error", str(e))
                return

            # List files
            self.log(f"Fetching files from folder: {self.folder_id.get()}")
            files = self.google_service.list_files(self.folder_id.get())

            if not files:
                self.log("No files found in the folder", "WARNING")
                return

            self.total_files = len(files)
            self.update_stats()
            self.log(f"Found {self.total_files} files", "SUCCESS")

            # Initialize output file
            output_path = self.output_file.get()
            FileHandler.write_json(output_path, [])
            self.log(f"✓ Output file initialized: {output_path}", "SUCCESS")

            # Process files sequentially
            for file in files:
                if not self.is_processing:
                    self.log("Processing stopped by user", "WARNING")
                    break

                try:
                    self.log(f"\nProcessing: {file['name']}")

                    # Download file
                    file_path = self.google_service.download_file(
                        file['id'],
                        file['name'],
                        file['mimeType']
                    )

                    if file_path:
                        self.log(f"  ✓ Downloaded: {file['name']}", "SUCCESS")
                        # Extract with Claude
                        extracted_data = self.claude_processor.extract_data(file_path, file['name'])
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

                    # Save to JSON
                    FileHandler.append_to_json_array(output_path, extracted_data)

                    self.processed_files += 1
                    self.update_stats()
                    self.log(f"  ✓ Status: {status}", "SUCCESS" if status == "success" else "WARNING")

                except Exception as e:
                    self.log(f"  ✗ Error: {str(e)}", "ERROR")
                    self.failed_count += 1
                    self.processed_files += 1
                    self.update_stats()

            # Final summary
            self.log(f"\n{'='*50}", "SUCCESS")
            self.log(f"EXTRACTION COMPLETE!", "SUCCESS")
            self.log(
                f"Total: {self.total_files} | Success: {self.success_count} | "
                f"Partial: {self.partial_count} | Failed: {self.failed_count}",
                "SUCCESS"
            )
            self.log(f"{'='*50}", "SUCCESS")

            if self.is_processing:
                messagebox.showinfo(
                    "Complete",
                    f"Processing complete!\n\n"
                    f"✓ Success: {self.success_count}\n"
                    f"⚠ Partial: {self.partial_count}\n"
                    f"✗ Failed: {self.failed_count}"
                )

        except Exception as e:
            self.log(f"ERROR: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

        finally:
            self.is_processing = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')

    def start_processing(self):
        """Start the processing workflow"""
        if not self.folder_id.get().strip():
            messagebox.showerror("Error", "Please enter a Google Drive Folder ID")
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

        # Start processing in background thread
        thread = threading.Thread(target=self.process_files, daemon=True)
        thread.start()

    def stop_processing(self):
        """Stop the processing workflow"""
        self.is_processing = False
        self.log("\nStopping process...", "WARNING")
        self.stop_button.config(state='disabled')

    def open_output_file(self):
        """Open the output JSON file in default application"""
        output_path = self.output_file.get()
        if os.path.exists(output_path):
            os.system(f'open "{output_path}"' if os.name == 'posix' else f'start "" "{output_path}"')
        else:
            messagebox.showwarning(
                "File Not Found",
                "Output file does not exist yet.\nPlease run the extraction first."
            )
