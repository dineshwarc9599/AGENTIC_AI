"""
image_handler.py
────────────────
Handles image input → Qwen VL (via OpenRouter) → text description
"""

import os
import base64
import requests


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
QWEN_VL_MODEL  = "qwen/qwen-vl-plus"   


def analyze_image(image_file, prompt: str = "Describe this image in detail.") -> str:
    """
    Send an image to Qwen VL via OpenRouter and return the text description.

    Args:
        image_file: Streamlit UploadedFile object (jpg/png/webp)
        prompt: The question or instruction for the vision model

    Returns:
        Vision model's text response.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return "No image description available (OpenRouter API key not set)."

    try:
        # Encode image to base64
        image_bytes = image_file.read()
        image_file.seek(0)  # reset for potential re-use

        ext = image_file.name.split(".")[-1].lower()
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "png": "image/png", "webp": "image/webp"}
        media_type = mime_map.get(ext, "image/jpeg")

        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        data_url  = f"data:{media_type};base64,{b64_image}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
            "HTTP-Referer":  "https://multimodal-chatbot.streamlit.app",
            "X-Title":       "MultiModal AI Chatbot",
        }

        payload = {
            "model": QWEN_VL_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {"type": "text",      "text": prompt},
                    ],
                }
            ],
            "max_tokens": 1024,
        }

        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"[Qwen VL error] {e}")
        return f"Image analysis failed: {str(e)}"