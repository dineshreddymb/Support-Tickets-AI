import os

from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    Groq = None

load_dotenv()

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def ask_llm(prompt):
    """Send a prompt to Groq and return the model response."""
    if Groq is None:
        raise RuntimeError(
            "The groq package is not installed. Run: python -m pip install -r requirements.txt"
        )

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", DEFAULT_MODEL),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()
