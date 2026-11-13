import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from .ingestion import load_pdf
from .chunking import fixed_size, by_paragraph
from .embeddings import MyEmbedder
from .store import PgVectorStore
from .evaluation import evaluate_query, summarize
def main() -> None:
    """Run strategies A, B, C and save benchmark results."""

    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")

    # 1. Load corpus and benchmark
    manifest = json.loads(
        (root / "data/manifest.json").read_text(encoding="utf-8")
    )
    benchmark = json.loads(
        (root / "data/questions.json").read_text(encoding="utf-8")
    )

    pdf_path = root / "data" / manifest["local_filename"]
    pages = load_pdf(
        pdf_path, manifest["source_id"],
        manifest["source_path_or_url"]
    )

    selected = {p["pdf_page"]: p for p in manifest["pages"]}
    pages = [p for p in pages if p.page in selected]

    for page in pages:
        page.metadata["chapter"] = selected[page.page]["chapter"]

    if len(pages) < 30:
        raise ValueError("Corpus must have at least 30 content pages")

    questions = benchmark["questions"]
    if (len(questions) < 20
            or sum(q["split"] == "dev" for q in questions) < 15
            or sum(q["split"] == "test" for q in questions) < 5):
        raise ValueError("Benchmark needs 15 dev and 5 test questions")

    if sum(bool(q.get("metadata_filter")) for q in questions) < 3:
        raise ValueError("Benchmark needs at least 3 filter questions")
    if not any(q["split"] == "test" and q.get("metadata_filter")
               for q in questions):
        raise ValueError("Test split needs a filter question")

    # Verify gold evidence before API calls
    page_map = {(p.document_id, p.page): p.text for p in pages}
    for q in questions:
        for gold in q["gold_evidence"]:
            text = page_map.get(
                (gold["source_id"], gold["pdf_page"]), ""
            )
            anchor = gold["evidence_anchor"]
            if " ".join(anchor.split()) not in " ".join(text.split()):
                raise ValueError(f"Invalid gold evidence: {q['question_id']}")

    # 2. Initialize model and vector store
    model = MyEmbedder(
        os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    )
    store = PgVectorStore(str(root / "chroma_db"), model.dimensions)
    store.create_schema()

    traces, stats = [], {}
    query_vectors = {
        q["question_id"]: model.embed_query(q["question"])
        for q in questions
    }

    # 3. Run three strategies
    for strategy in ("A", "B", "C"):
        start = time.perf_counter()

        chunks = [
            chunk
            for page in pages
            for chunk in (
                fixed_size(page, 500, 50)
                if strategy == "A"
                else by_paragraph(page, 700)
            )
        ]

        vectors = model.embed_documents([c.text for c in chunks])
        store.upsert(strategy, chunks, vectors)

        stats[strategy] = {
            "chunks": len(chunks),
            "characters": sum(len(c.text) for c in chunks),
            "ingest_seconds": round(time.perf_counter() - start, 2)
        }

        # 4. Retrieve and evaluate top-3
        for q in questions:
            filters = (
                q.get("metadata_filter") if strategy == "C" else None
            )

            hits = store.search(
                strategy, query_vectors[q["question_id"]],
                top_k=3, filters=filters
            )

            trace = evaluate_query(q, hits)
            trace["strategy"] = strategy
            traces.append(trace)

        print(f"Strategy {strategy}: {len(chunks)} chunks")

    # 5. Save results
    output = root / "results"
    output.mkdir(exist_ok=True)

    for name, data in {
        "traces.json": traces,
        "metrics.json": summarize(traces),
        "ingestion_stats.json": stats
    }.items():
        (output / name).write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    print("Finished! Results saved in results/")

if __name__ == "__main__":
    main()
