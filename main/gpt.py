from openai import OpenAI

from config import OPENAI_API_KEY
from context import PROMPT_TEXT


def get_gpt_response(summary: str) -> str:
    """
    Sends a prompt and summary to OpenAI's GPT API and returns the response.

    Args:
        summary (str): The input text to use

    Returns:
        str: The response from GPT.
    """
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Make the API request to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": summary},
                {"role": "user", "content": PROMPT_TEXT}
            ]
        )

        # Extract the response content
        gpt_response = response.choices[0].message.content
        return gpt_response

    except Exception as e:
        print(f"Error communicating with GPT: {e}")
        return "Error: Unable to fetch GPT response."