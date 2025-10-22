def get_claude_response(prompt, model="claude-3.5-haiku-latest", max_tokens=100, client=None):
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return {
            "sucess": True,
            "text": response.content[0].text,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.total_tokens
            }

        }

    except Exception as e:
        return {
            "sucess": False,
            "error": str(e)
        }
