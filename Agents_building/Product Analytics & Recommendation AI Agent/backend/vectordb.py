import pandas as pd
import chromadb

from embeddings import (
    embedding_model
)

from config import (
    CHROMA_DB_PATH,
    COLLECTION_NAME
)

from dataframe_agent import (
    set_dataframe
)

# Global dataframe
df = None

# Chroma Client
client = chromadb.PersistentClient(
    path=str(CHROMA_DB_PATH)
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)

def create_product_document(row):

    return f"""
    
    Laptop Brand: {row['Company']}

    Product Name: {row['Product']}

    Product Type: {row['TypeName']}

    Screen Size: {row['Inches']} inch

    Processor: {row['Cpu']}

    RAM: {row['Ram']}

    Storage: {row['Memory']}

    Graphics: {row['Gpu']}

    Operating System: {row['OpSys']}

    Weight: {row['Weight']}

    Price: {row['Price_euros']} Euros
    """

def ingest_data(csv_path):

    global df

    print("Loading dataset...")

    try:

        df = pd.read_csv(
            csv_path,
            encoding="utf-8"
        )

    except UnicodeDecodeError:

        print(
            "UTF-8 failed. Using latin1..."
        )

        df = pd.read_csv(
            csv_path,
            encoding="latin1"
        )

    # Share dataframe
    set_dataframe(df)

    print(df.head())

    print(
        "Total Rows:",
        len(df)
    )

    # Clear old data
    existing_count = collection.count()

    if existing_count > 0:

        all_data = collection.get()

        if all_data["ids"]:

            collection.delete(
                ids=all_data["ids"]
            )

    documents = []
    embeddings = []
    ids = []

    for index, row in df.iterrows():

        document = create_product_document(
            row
        )

        embedding = (
            embedding_model
            .generate_embedding(document)
        )

        documents.append(document)

        embeddings.append(embedding)

        ids.append(str(index))

    print("Adding embeddings...")

    collection.add(

        documents=documents,

        embeddings=embeddings,

        ids=ids
    )

    print(
        "Collection Count:",
        collection.count()
    )

def semantic_search(
    query,
    top_k=5
):

    query_embedding = (
        embedding_model
        .generate_embedding(query)
    )

    results = collection.query(

        query_embeddings=[
            query_embedding
        ],

        n_results=top_k
    )

    return results["documents"][0]