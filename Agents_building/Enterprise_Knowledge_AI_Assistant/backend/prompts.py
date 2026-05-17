def build_prompt(user_query, context):
    return f"""
You are an enterprise AI assistant.

User Request:
{user_query}

Relevant Company Documents:
{context}

Instructions:
1. Use the template structure from context.
2. Generate professional enterprise content.
3. Keep formatting clean.
4. Generate detailed output.
5. Tailor the response according to the request.

Generate the final document content.
"""