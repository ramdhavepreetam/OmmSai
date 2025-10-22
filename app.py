from dotenv import load_dotenv
import os
from anthropic import Anthropic

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=api_key)


def get_claude_response(prompt, model="claude-3-5-haiku-20241022", max_tokens=100):
    try:
        response = client.messages.create(
            model=model,
            max_tokens=100,
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


# Call AFTER function is defined
try:
    result = get_claude_response("What is the capital of India?")
    if result["success"]:
        print(result["text"])
    else:
        print("Error:", result["error"])
except Exception as e:
    print("Exception:", e)
