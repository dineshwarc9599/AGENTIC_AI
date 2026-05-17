from groq_client import client
from config import MODEL_NAME

def generate_pandas_query(question):

    prompt = f"""
    You are a Pandas expert.

    Convert the user question into ONLY
    executable pandas code.

    The dataframe name is: df

    Dataset Columns:
    - Company
    - Product
    - TypeName
    - Inches
    - ScreenResolution
    - Cpu
    - Ram
    - Memory
    - Gpu
    - OpSys
    - Weight
    - Price_euros

    RULES:
    - Return ONLY pandas code
    - No explanations
    - No markdown
    - Code must return result

    User Question:
    {question}
    """

    response = client.chat.completions.create(

        model=MODEL_NAME,

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0
    )

    code = (
        response
        .choices[0]
        .message
        .content
        .strip()
    )

    return code