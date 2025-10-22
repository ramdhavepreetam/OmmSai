"""
DEPRECATED: This file is kept for backward compatibility only.
Please use: python test_api.py

This file now wraps the new modular implementation.
"""

from getGoogleFiles.core.claude_processor import ClaudeProcessor


def get_claude_response(prompt, model="claude-3-5-haiku-20241022", max_tokens=100):
    """
    Legacy function - use ClaudeProcessor class instead
    """
    processor = ClaudeProcessor()
    return processor.simple_query(prompt, model, max_tokens)


# Main execution
if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("⚠ DEPRECATION WARNING")
    print("=" * 60)
    print("This file (app.py) is deprecated.")
    print("Please use: python test_api.py")
    print("=" * 60 + "\n")

    try:
        result = get_claude_response("What is the capital of India?")
        if result["success"]:
            print("Response:", result["text"])
            print(f"\nTokens: {result['usage']['input_tokens']} input, "
                  f"{result['usage']['output_tokens']} output")
        else:
            print("Error:", result["error"])
    except Exception as e:
        print("Exception:", e)
