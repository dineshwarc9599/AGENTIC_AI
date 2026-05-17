from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    BASE_DIR / "data" / "laptop_price.csv"
)

CHROMA_DB_PATH = (
    BASE_DIR / "chroma_storage"
)

COLLECTION_NAME = "laptop_products"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "llama-3.3-70b-versatile"
)

TOP_K_RESULTS = 5