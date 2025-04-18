# RAG Poisoning Experiment Setup and Execution

## Setup

1.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    *   Create a file named `.env` in the project root.
    *   Add the following lines, replacing the placeholder model names if necessary:
    ```dotenv
    EMBEDDING_MODEL_NAME=
    OLLAMA_LLM_MODEL=
    # OLLAMA_BASE_URL=http://localhost:11434 # Optional: Uncomment if Ollama runs elsewhere
    ```

4.  **Set up and run Ollama (in a separate terminal):**
    *   Install Ollama: [https://ollama.com/](https://ollama.com/)
    *   Pull the required model:
        ```bash
        ollama pull ***Model of choice* 
        ```
    *   Run the Ollama server (leave this terminal running):
        ```bash
        ollama serve
        ```

## Data Preparation and Indexing

6.  **Fetch base corpus data:**
    ```bash
    python src/fetch_wiki.py
    ```

7.  **Generate poisoned text corpora:**
    ```bash
    python src/poison_corpus.py
    ```

8.  **Build FAISS indices:**
    ```bash
    # Clean
    python src/build_index.py --corpus_folder data/clean_corpus --index_path data/clean --ids_path data/clean.ids.pkl
    # Prompt Injection
    python src/build_index.py --corpus_folder data/poisoned_prompt_injection --index_path data/poisoned_pi --ids_path data/poisoned_pi.ids.pkl
    # Semantic Poisoning
    python src/build_index.py --corpus_folder data/poisoned_semantic --index_path data/poisoned_sp --ids_path data/poisoned_sp.ids.pkl
    # Vector Poisoning (Base)
    python src/build_vector_poisoned_index.py
    ```

## Run Experiment

9.  **Execute the RAG analysis:**
    ```bash
    python src/run_rag.py
    ```

10. **View Results:**
    *   Check the output file: `outputs/logs/results.csv`
