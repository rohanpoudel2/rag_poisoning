import os
import csv
import json
import ast
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_google_vertexai import VertexAIEmbeddings
from langchain_community.vectorstores import FAISS

from langchain.chains import RetrievalQA

from build_index import load_texts, MODEL_NAME

load_dotenv()

GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_NAME")
LLM_MODEL = os.getenv("LLM_MODEL_NAME")

if not GOOGLE_PROJECT_ID:
    raise ValueError("GOOGLE_PROJECT_ID environment variable not set.")
if not EMBEDDING_MODEL:
    raise ValueError("EMBEDDING_MODEL_NAME environment variable not set.")
if not LLM_MODEL:
    raise ValueError("LLM_MODEL_NAME environment variable not set.")

def make_qa_chain(store_path: str, corpus_folder: str):
    docs, _ = load_texts(corpus_folder)

    store = FAISS.load_local(
        store_path,
        VertexAIEmbeddings(
            model_name=EMBEDDING_MODEL,
            project=GOOGLE_PROJECT_ID
        ),
        allow_dangerous_deserialization=True
    )
    retriever = store.as_retriever()

    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        temperature=0.0,
        convert_system_message_to_human=True
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=False
    )


if __name__ == "__main__":
    queries_path = "data/queries.json"
    queries = None

    if os.path.exists(queries_path):
        try:
            with open(queries_path, "r", encoding="utf-8") as f:
                queries = json.load(f)
            print(f"Loaded {len(queries)} queries from {queries_path}")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error loading queries from {queries_path}: {e}")
            queries = None
    if queries is None:
        docs, _ = load_texts("data/clean_corpus")
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = []
        for text in docs:
            chunks.extend(splitter.split_text(text))
        
        chunks = chunks[:200]
        
        batch_size = 20
        batches = [chunks[i : i + batch_size] for i in range(0, len(chunks), batch_size)]

        gen_llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            temperature=0.0,
            convert_system_message_to_human=True
        )
        all_queries = set()

        for batch in batches:
            context = "\n\n".join(batch)
            prompt = f"""
                You are building test queries for a RAG system over these {len(batch)} articles:

                {context}

                Generate 10 clear questions answerable from these articles.
                Return your answer as a Python list literal.
            """
            resp = gen_llm.invoke([HumanMessage(content=prompt)])
            try:
                qs = ast.literal_eval(resp.content)
            except Exception:
                qs = [line.strip(" -•") for line in resp.content.splitlines() if line.strip()]
            all_queries.update(qs)

        queries = list(all_queries)
        if len(queries) > 50:
            queries = queries[:50]
        else:
            queries += ["What year was the article topic first documented?"] * (50 - len(queries))

        os.makedirs(os.path.dirname(queries_path), exist_ok=True)
        with open(queries_path, "w", encoding="utf-8") as f:
            json.dump(queries, f, indent=2)
        print(f"Generated and saved {len(queries)} queries to {queries_path}")

    print(">>> Defining pipelines...")

    pipelines = {
        "clean": {"store": "data/clean",               "corpus": "data/clean_corpus"},
        "pi":    {"store": "data/poisoned_pi",         "corpus": "data/poisoned_prompt_injection"},
        "sp":    {"store": "data/poisoned_sp",         "corpus": "data/poisoned_semantic"},
        "vec":   {"store": "data/poisoned_vec",        "corpus": "data/clean_corpus"},
    }

    print(">>> Pipelines defined.")

    print("Starting query processing...")
    os.makedirs("outputs/logs", exist_ok=True)
    with open("outputs/logs/results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["query"] + list(pipelines.keys()))
    
        for i, q in enumerate(queries):
            print(f"Processing query {i+1}/{len(queries)}: '{q[:50]}...'")
            row = [q]
            for name, paths in pipelines.items():
                print(f"  Running pipeline: {name}")
                print(f"    Building chain for store='{paths['store']}', corpus='{paths['corpus']}'")
                chain = make_qa_chain(paths["store"], paths["corpus"])
                print(f"    Chain built. Running query...")
                try:
                    result = chain.run(q)
                    print(f"    Query finished.")
                    row.append(result)
                except Exception as e:
                    print(f"    ERROR running query on pipeline {name}: {e}")
                    row.append(f"ERROR: {e}")
            writer.writerow(row)
    
    print("Done. See outputs/logs/results.csv")