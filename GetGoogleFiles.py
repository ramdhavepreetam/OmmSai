"""
DEPRECATED: This file is kept for backward compatibility only.
Please use the new modular structure:
  - GUI: python main_gui.py
  - CLI: python main_cli.py

This file now wraps the new modular implementation.
"""

import tkinter as tk
from getGoogleFiles.ui.gui import PrescriptionExtractorUI


def main():
    """
    Launch the GUI application
    NOTE: This is a compatibility wrapper. Use main_gui.py for new code.
    """
    root = tk.Tk()
    app = PrescriptionExtractorUI(root)
    root.mainloop()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("⚠ DEPRECATION WARNING")
    print("=" * 60)
    print("This file (GetGoogleFiles.py) is deprecated.")
    print("Please use the new entry points:")
    print("  - GUI: python main_gui.py")
    print("  - CLI: python main_cli.py")
    print("=" * 60 + "\n")
    main()
