# =========================
# backend/groq_client.py
# =========================

from groq import Groq

from config import (
    GROQ_API_KEY,
    MODEL_NAME
)

from prompts import (
    SYSTEM_PROMPT
)

client = Groq(
    api_key=GROQ_API_KEY
)

def generate_response(question, context):

    messages = [

        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },

        {
            "role": "user",
            "content": f"""
            Product Context:

            {context}

            User Question:

            {question}
            """
        }
    ]

    response = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=messages,

        temperature=0.3,

        max_tokens=1024,

        top_p=1
    )

    answer = (
        response
        .choices[0]
        .message
        .content
    )

    return answer