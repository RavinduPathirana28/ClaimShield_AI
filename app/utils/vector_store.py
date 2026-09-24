import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from app import config

class VectorStore:
    def __init__(self):
        # Using a highly-optimized, fast local model for text embedding
        print("Vector Store: Initializing SentenceTransformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.mapping = {}  # FAISS index_id -> database article_id
        self.load()

    def load(self):
        """Loads FAISS index and database key mapping if they exist."""
        if os.path.exists(config.FAISS_INDEX_PATH):
            try:
                self.index = faiss.read_index(config.FAISS_INDEX_PATH)
                mapping_path = config.FAISS_INDEX_PATH + ".json"
                if os.path.exists(mapping_path):
                    with open(mapping_path, 'r') as f:
                        # JSON stores keys as strings; convert keys back to integers
                        self.mapping = {int(k): v for k, v in json.load(f).items()}
                # Guard against a stale or wrong-model index: a dimension mismatch
                # would make every search raise silently inside FAISS. When it is
                # detected we drop the index so retrieval degrades to DB/web instead
                # of crashing the pipeline.
                get_dim = getattr(self.model, "get_embedding_dimension", None) or self.model.get_sentence_embedding_dimension
                expected_dim = get_dim()
                if self.index is not None and self.index.d != expected_dim:
                    print(f"[Warning] Vector Store: FAISS index dimension {self.index.d} does not match model "
                          f"dimension {expected_dim}. Discarding stale index; run 'python seed_database.py' to rebuild it.")
                    self.index = None
                    self.mapping = {}
                    return
                print(f"Vector Store: Loaded FAISS index from {config.FAISS_INDEX_PATH}")
            except Exception as e:
                print(f"[Warning] Vector Store: Failed to load existing index: {e}")

    def build_index(self, articles: list) -> bool:
        """Builds a FAISS index using article text and saves to disk."""
        if not articles:
            print("Vector Store: No articles provided for indexing.")
            return False

        texts = []
        mapping = {}
        for idx, art in enumerate(articles):
            # Package title and body content for richer semantic comparison
            text = f"Title: {art['title']}\nContent: {art['content']}"
            texts.append(text)
            mapping[idx] = art['id']

        try:
            # Generate embeddings
            embeddings = self.model.encode(texts, show_progress_bar=False)
            embeddings = np.array(embeddings).astype('float32')
            
            # Normalize embeddings for Cosine Similarity (via Inner Product)
            faiss.normalize_L2(embeddings)
            
            dimension = embeddings.shape[1]
            # Use Flat Inner Product index for Cosine Similarity
            index = faiss.IndexFlatIP(dimension)
            index.add(embeddings)
            
            # Persist FAISS index and mappings to data directory
            faiss.write_index(index, config.FAISS_INDEX_PATH)
            mapping_path = config.FAISS_INDEX_PATH + ".json"
            with open(mapping_path, 'w') as f:
                json.dump(mapping, f)
                
            self.index = index
            self.mapping = mapping
            print(f"Vector Store: Successfully built and indexed {len(articles)} documents.")
            return True
        except Exception as e:
            print(f"[Warning] Vector Store: Failed to build index: {e}")
            return False

    def search_index(self, query: str, limit: int = 3) -> list:
        """Searches the index for query text and returns matching article ids and similarity scores."""
        if self.index is None or not self.mapping:
            print("[Warning] Vector Store: Attempted search, but FAISS index is not built or loaded.")
            return []

        try:
            # Encode and normalize query vector
            query_vector = self.model.encode([query])
            query_vector = np.array(query_vector).astype('float32')
            faiss.normalize_L2(query_vector)
            
            # Perform FAISS inner-product search
            scores, indices = self.index.search(query_vector, limit)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:
                    continue
                article_id = self.mapping.get(int(idx))
                if article_id is not None:
                    # Inner Product of normalized vectors yields standard Cosine Similarity [-1.0, 1.0]
                    results.append((article_id, float(score)))
            return results
        except Exception as e:
            print(f"[Warning] Vector Store: Error during index search: {e}")
            return []
