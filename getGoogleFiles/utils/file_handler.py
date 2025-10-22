"""
File handling utilities
"""
import json
import os
from pathlib import Path


class FileHandler:
    """Handles file operations for the application"""

    @staticmethod
    def write_json(file_path, data, indent=2):
        """
        Write data to JSON file

        Args:
            file_path (str): Path to output file
            data: Data to write (must be JSON serializable)
            indent (int): Indentation level
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    @staticmethod
    def read_json(file_path):
        """
        Read data from JSON file

        Args:
            file_path (str): Path to JSON file

        Returns:
            Data from JSON file
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def append_to_json_array(file_path, new_item):
        """
        Append an item to a JSON array file

        Args:
            file_path (str): Path to JSON file
            new_item: Item to append
        """
        # Read existing data
        if os.path.exists(file_path):
            data = FileHandler.read_json(file_path)
        else:
            data = []

        # Append new item
        data.append(new_item)

        # Write back
        FileHandler.write_json(file_path, data)

    @staticmethod
    def ensure_directory(directory):
        """
        Create directory if it doesn't exist

        Args:
            directory (str): Directory path
        """
        Path(directory).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_file_size(file_path):
        """
        Get file size in bytes

        Args:
            file_path (str): Path to file

        Returns:
            int: File size in bytes
        """
        return os.path.getsize(file_path)

    @staticmethod
    def format_size(bytes_size):
        """
        Format bytes to human-readable size

        Args:
            bytes_size (int): Size in bytes

        Returns:
            str: Formatted size (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"
