from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


DB_DIR = "chroma_db"

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectordb = Chroma(
    persist_directory=DB_DIR,
    embedding_function=embedding_model
)

def retrieve_documents(query):
    
    results = vectordb.similarity_search(query, k=3)
    
    context = "\n\n".join([
        doc.page_content for doc in results
    ])
    return context