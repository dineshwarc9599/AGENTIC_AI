"""
audio_handler.py
────────────────
Handles voice input → Groq Whisper transcription → text.

Compatible with:
  - st.audio_input()   → returns BytesIO-like with .name = "audio.wav"
  - st.file_uploader() → returns UploadedFile with real filename
"""

import os
import tempfile
from groq import Groq


def transcribe_audio(audio_file) -> str:
    """
    Transcribe an audio recording using Groq Whisper.

    Args:
        audio_file: BytesIO (from st.audio_input) or UploadedFile
                    (from st.file_uploader). Caller must seek(0) before passing.

    Returns:
        Stripped transcript string, or "" on failure.
    """
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return ""

    try:
        client = Groq(api_key=api_key)

        # Resolve filename / extension
        name   = getattr(audio_file, "name", None) or "audio.wav"
        suffix = "." + name.rsplit(".", 1)[-1]   # e.g. ".wav"

        audio_bytes = audio_file.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=f,
                response_format="text",
            )

        os.unlink(tmp_path)

        if isinstance(result, str):
            return result.strip()
        return str(result).strip()

    except Exception as e:
        print(f"[Groq Whisper error] {e}")
        return ""