import os
import pickle
from typing import List, Tuple

import numpy as np
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter


EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_NAME")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")

if not EMBEDDING_MODEL:
    raise ValueError("EMBEDDING_MODEL_NAME environment variable not set.")
if not GOOGLE_PROJECT_ID:
    raise ValueError("GOOGLE_PROJECT_ID environment variable not set.")


if EMBEDDING_MODEL == "text-embedding-004":
    EMB_DIM = 768
else:
    EMB_DIM = 768
    print(f"Warning: Unknown embedding model '{EMBEDDING_MODEL}', assuming dimension {EMB_DIM}")


def load_texts(folder: str) -> Tuple[List[str], List[str]]:
    texts, ids = [], []
    for fn in sorted(os.listdir(folder)):
        path = os.path.join(folder, fn)
        if os.path.isfile(path) and fn.lower().endswith(".txt"):
            with open(path, "r", encoding="utf-8") as f:
                texts.append(f.read())
                ids.append(fn)
    return texts, ids


def build_faiss_index(
    corpus_folder: str,
    index_path: str,
    ids_path: str
) -> None:
    store_path = index_path.replace(".index", "")
    os.makedirs(store_path, exist_ok=True)

    texts, ids = load_texts(corpus_folder)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2_000_000, 
        chunk_overlap=0      
    )
    docs, metadatas = [], []
    for doc_id, text in zip(ids, texts):
        chunks = splitter.split_text(text)
        for i, chunk in enumerate(chunks):
            docs.append(chunk)
            metadatas.append({"source": doc_id, "chunk": i})

    embedder = VertexAIEmbeddings(
        model_name=EMBEDDING_MODEL,
        project=GOOGLE_PROJECT_ID
    )
    db = FAISS.from_texts(
        texts=docs,
        embedding=embedder,
        metadatas=metadatas
    )

    db.save_local(store_path)
    with open(ids_path, "wb") as f:
        pickle.dump(ids, f)

    print(f"Built chunked FAISS store ({len(docs)} chunks) -> {store_path}")
    print(f"Saved document IDs -> {ids_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Build a chunked FAISS index from a folder of .txt files."
    )
    parser.add_argument(
        "--corpus_folder",
        type=str,
        default="data/clean_corpus",
        help="Folder containing .txt documents"
    )
    parser.add_argument(
        "--index_path",
        type=str,
        default="data/clean.index",
        help="Path to save the FAISS store (suffix .index stripped)"
    )
    parser.add_argument(
        "--ids_path",
        type=str,
        default="data/clean.ids.pkl",
        help="Path to save the original document ID list"
    )
    args = parser.parse_args()

    build_faiss_index(
        corpus_folder=args.corpus_folder,
        index_path=args.index_path,
        ids_path=args.ids_path
    )
