from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.retriever import retrieve_documents
from backend.groq_client import generate_response
from backend.prompts import build_prompt
from backend.doc_generator import create_docx

app = FastAPI()


class UserRequest(BaseModel):
    query: str


@app.post("/generate")
def generate_document(request: UserRequest):

    context = retrieve_documents(request.query)

    final_prompt = build_prompt(
        request.query,
        context
    )

    ai_output = generate_response(final_prompt)

    filepath, filename = create_docx(ai_output)

    return {
        "message": "Document Generated Successfully",
        "download_url": f"/download/{filename}"
    }

@app.get("/download/{filename}")
def download_file(filename: str):
    filepath = f"output_docs/{filename}"

    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename
    )