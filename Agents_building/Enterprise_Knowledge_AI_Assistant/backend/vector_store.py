from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
import os

from langchain_huggingface import HuggingFaceEmbeddings

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

DB_DIR = "chroma_db"

def load_documents(folder_path):
    docs = []

    for file in os.listdir(folder_path):
        if file.endswith(".txt"):
            loader = TextLoader(os.path.join(folder_path, file))
            docs.extend(loader.load())

    return docs

def create_vector_db():
    template_docs = load_documents("data/templates")
    deliverable_docs = load_documents("data/deliverables")

    all_docs = template_docs + deliverable_docs

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    split_docs = splitter.split_documents(all_docs)

    vectordb = Chroma.from_documents(
        split_docs,
        embedding_model,
        persist_directory=DB_DIR
    )

    vectordb.persist()

    print("Vector DB Created")


if __name__ == "__main__":
    create_vector_db()