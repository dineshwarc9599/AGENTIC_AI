"""
router.py
─────────
Central routing logic.
All input types (text, voice transcript, image description) are sent
to Groq LLaMA-3 for the final answer.
"""

import os
from groq import Groq

SYSTEM_PROMPTS = {
    "text": (
        "You are a helpful, concise AI assistant. "
        "Answer the user's question clearly and directly."
    ),
    "voice": (
        "You are a helpful AI assistant responding to a voice query "
        "that was transcribed from speech. "
        "Keep your answer conversational and clear."
    ),
    "image": (
        "You are a helpful AI assistant. The user has sent an image that has "
        "already been analyzed by a vision model. "
        "Use that analysis to answer any questions or provide insights. "
        "Be descriptive and helpful."
    ),
}


def route_input(text: str, input_type: str = "text") -> str:
    """
    Route the processed text input to Groq LLaMA-3 and return the response.

    Args:
        text: The processed text (transcription / image description / plain text)
        input_type: One of 'text', 'voice', 'image'

    Returns:
        The model's response as a string.
    """
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return "**Groq API key not set.** Please add it in the sidebar."

    system_prompt = SYSTEM_PROMPTS.get(input_type, SYSTEM_PROMPTS["text"])

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": text},
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        return completion.choices[0].message.content

    except Exception as e:
        return f"**Groq error:** {str(e)}"