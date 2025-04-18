import os
from datasets import load_dataset

def save_subset(n_articles: int = 500, out_dir: str = "data/clean_corpus") -> None:
        os.makedirs(out_dir, exist_ok=True)
        wiki = load_dataset(
            "wikipedia",
            "20220301.en",
            split="train",
            streaming=True,
            trust_remote_code=True
        )
        for i, ex in enumerate(wiki):
            if i >= n_articles:
                break
            text = ex["text"].strip()
            fn = f"article_{i:04d}.txt"
            with open(f"{out_dir}/{fn}", "w", encoding="utf-8") as f:
                f.write(text)

if __name__ == "__main__":
    try:
        save_subset()
        print("Saved 500 articles to data/clean_corpus")
    except Exception as e:
        print(f"Failed to save articles: {e}")
        raise
