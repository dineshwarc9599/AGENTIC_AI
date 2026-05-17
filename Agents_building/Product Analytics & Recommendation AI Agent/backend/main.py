from fastapi import FastAPI
from pydantic import BaseModel

from fastapi.middleware.cors import (
    CORSMiddleware
)

from rag import product_qa_agent

from vectordb import ingest_data

from config import DATASET_PATH

app = FastAPI(
    title="Hybrid Product Intelligence Agent"
)

# Enable CORS
app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():

    ingest_data(DATASET_PATH)

class QueryRequest(BaseModel):

    question: str

@app.get("/")
def health_check():

    return {
        "status": "running"
    }

@app.post("/ask")
def ask_question(
    request: QueryRequest
):

    result = product_qa_agent(
        request.question
    )

    return result