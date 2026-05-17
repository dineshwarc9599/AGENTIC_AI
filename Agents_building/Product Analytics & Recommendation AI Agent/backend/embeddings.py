from sentence_transformers import (
    SentenceTransformer
)

class EmbeddingModel:

    def __init__(self):

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    def generate_embedding(self, text):

        embedding = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return embedding.tolist()

embedding_model = EmbeddingModel()