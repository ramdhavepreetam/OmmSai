"""
Main entry point for GUI application
Launch the prescription extraction interface
"""
import tkinter as tk
from getGoogleFiles.ui.gui import PrescriptionExtractorUI


def main():
    """Launch the GUI application"""
    root = tk.Tk()
    app = PrescriptionExtractorUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
