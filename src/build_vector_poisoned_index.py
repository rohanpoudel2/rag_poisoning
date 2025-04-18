import os
import numpy as np
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from build_index import EMB_DIM

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_NAME")

if not EMBEDDING_MODEL:
    raise ValueError("EMBEDDING_MODEL_NAME environment variable not set.")

def build_vector_poisoned_index(
    clean_corpus_folder: str  = "data/clean_corpus",
    clean_store_path: str     = "data/clean",
    poisoned_store_path: str  = "data/poisoned_vec",
    num_adv: int              = 5,
    noise_scale: float        = 1e-3
) -> None:
    embedder = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    db = FAISS.load_local(
        clean_store_path,
        embedder,
        allow_dangerous_deserialization=True
    )

    emb_dim = EMB_DIM

    n = num_adv

    noise = np.random.normal(
        loc=0.0,
        scale=noise_scale,
        size=(n, emb_dim)
    ).astype("float32")

    adv_texts = [f"poisoned_vector_{i}" for i in range(n)]
    adv_metadatas = [{"source": "poison", "chunk": i} for i in range(n)]

    db.add_embeddings(list(zip(adv_texts, noise.tolist())), metadatas=adv_metadatas)

    os.makedirs(poisoned_store_path, exist_ok=True)
    db.save_local(poisoned_store_path)
    print(f">>> Built vector‑poisoned vectorstore → {poisoned_store_path}")

if __name__ == "__main__":
    # Increase the number of adversarial vectors significantly
    build_vector_poisoned_index(num_adv=100)

