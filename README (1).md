# Research Companion – GenAI Capstone Project
# Research Companion – GenAI Capstone Project

An AI-powered **research assistant** that helps you go from a high-level query to:
- curated arXiv papers,
- cleaned and sectioned full-text PDFs,
- per-paper summaries (problem, methods, datasets, results, limitations),
- cross-paper comparisons,
- heuristic research-gap suggestions,
- and a simple web UI to explore everything.

> **Note:** The codebase is structured so that it can use LLMs (Gemini/OpenAI), but in this snapshot most LLM calls are **commented out**. The system runs end-to-end using **heuristic logic only**, and you can re-enable LLMs by wiring `src/llm/client.py` back to your provider.

---

## 1. High-Level Architecture

The main application lives in `research-companion-final/` and is organized as a pipeline:

1. **Retrieval (`src/retrieval/`)**
   - `client_arxiv.py` queries the public arXiv API using a title/abstract search query.
   - Results are post-processed and re-ranked by how well the title matches the user’s query.
   - Each result includes IDs, title, abstract, PDF URL, authors, and publication date.

2. **Download & Caching (`src/retrieval/downloader.py`, `artifacts/`)**
   - PDFs are downloaded and cached in `./artifacts`.
   - Simple metadata (`metadata.json`) tracks which PDFs have already been downloaded.

3. **Parsing & Cleaning (`src/parsing/`)**
   - `pdf_extractor.py` uses PyMuPDF to extract raw text from the PDF.
   - `cleaner.py` normalizes whitespace, strips boilerplate, etc.
   - `sectioner.py` applies naive rules to split text into sections (e.g., Introduction, Methods, Results).

4. **Chunking (`src/chunking/`)**
   - `section_chunker.py` groups text by section.
   - `tokenizer.py` uses `tiktoken` to estimate token counts; this is mainly used when building prompts (if you enable LLMs).

5. **Agents (`src/agents/`)**
   - `summarizer.py`:
     - Summarizes chunks and builds a per-paper structured summary:
       - `overall_problem`
       - `overall_methods`
       - `overall_datasets`
       - `overall_results`
       - `overall_limitations`
     - Contains both heuristic logic and (commented-out) LLM-based flows.
   - `evaluator.py`:
     - Provides hooks to verify summary factuality and perform numeric checks.
     - LLM-based evaluation is present but disabled; heuristics are used instead.
   - `research_gap.py`:
     - Takes the extracted limitations and attempts to infer **research gaps**.
     - Falls back to a heuristic list if `call_llm` returns `None`.
   - `ranker.py`:
     - Scores papers based on recency, presence of results, and explicit limitations.
     - Produces a ranked list of recommended papers.
   - `aggregator.py`:
     - Merges per-chunk / per-paper outputs into document-level and query-level aggregates.

6. **Analysis & References (`src/analysis/`, `src/utils/`)**
   - `analysis/comparator.py`: builds a **methods comparison table** across papers.
   - `utils/references.py`: builds a clean reference list (title, authors, year, URL) for display/export.

7. **Orchestrator (`src/orchestrator/orchestrator.py`)**
   - `Orchestrator` is the top-level controller:
     - Calls arXiv, downloads PDFs, extracts/cleans/sections text.
     - Calls summarizer, evaluator, comparator, gap detector, ranker, and references builder.
   - Main entrypoint:
     ```python
     from src.orchestrator.orchestrator import Orchestrator

     orc = Orchestrator(tmp_dir="./artifacts")
     result = orc.run(query="graph neural networks for molecular property prediction",
                      max_results=3)
     ```

8. **Web API & UI (`src/api/`, `src/ui/`)**
   - `src/api/fastapi_app.py`: exposes a FastAPI app with:
     - `GET /` – HTML UI.
     - `POST /query` – JSON API: `{ "query": "...", "max_results": 3 }`.
   - `src/ui/templates/index.html` + `src/ui/static/app.js` + `src/ui/static/styles.css`:
     - Minimal single-page interface:
       - input box for query,
       - numeric field for `max_results`,
       - result display showing summaries/comparisons/references.

---

## 2. Project Structure

At the repo root:

```text
GenAI_capstone_project-main/
├── README.md                      # (You can replace/extend with this file)
└── research-companion-final/
    ├── README.md                  # Starter README (short, can be overwritten)
    ├── requirements.txt
    ├── scripts/
    │   └── setup_env.sh           # venv + requirements installer
    ├── artifacts/                 # Cached PDFs, example papers, metadata.json
    ├── src/
    │   ├── __init__.py
    │   ├── agents/
    │   │   ├── aggregator.py
    │   │   ├── evaluator.py
    │   │   ├── ranker.py
    │   │   ├── research_gap.py
    │   │   └── summarizer.py
    │   ├── analysis/
    │   │   └── comparator.py
    │   ├── api/
    │   │   └── fastapi_app.py
    │   ├── chunking/
    │   │   ├── chunker.py (if present)
    │   │   ├── section_chunker.py
    │   │   └── tokenizer.py
    │   ├── llm/
    │   │   └── client.py
    │   ├── orchestrator/
    │   │   └── orchestrator.py
    │   ├── parsing/
    │   │   ├── cleaner.py
    │   │   ├── pdf_extractor.py
    │   │   └── sectioner.py
    │   ├── retrieval/
    │   │   ├── client_arxiv.py
    │   │   └── downloader.py
    │   ├── ui/
    │   │   ├── static/
    │   │   │   ├── app.js
    │   │   │   └── styles.css
    │   │   └── templates/
    │   │       └── index.html
    │   └── utils/
    │       └── references.py
    └── research-companion-*.tar.gz  # Archived versions (not needed for normal use)

An AI-powered research assistant that retrieves arXiv papers, parses PDFs, summarizes insights, compares methods, and suggests research gaps.

## Features
- arXiv retrieval
- PDF parsing and sectioning
- Summarization (heuristic or LLM)
- Cross-paper comparison
- Research gap detection
- FastAPI backend + UI

## Run
```
uvicorn src.api.fastapi_app:app --reload
```

## License
Educational use only.
