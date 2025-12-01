# Research Companion — Enhanced (Gemini, Token Budgeting, Evaluator, Web UI)

This enhanced starter includes:
- LLM client that prefers Gemini (if configured) otherwise OpenAI; configurable via env.
- Token budgeting using tiktoken to size prompts and cap responses.
- Improved evaluator performing factuality checks and numeric claim verification.
- A simple web UI served by FastAPI that displays returned summaries and evidence snippets.

Quickstart:
1. Copy `.env.example` to `.env` and set keys: GEMINI_API_KEY (preferred) or OPENAI_API_KEY.
2. Run `./scripts/setup_env.sh` and activate venv.
3. Start the app: `uvicorn src.api.fastapi_app:app --reload`
4. Open http://localhost:8000 in your browser and submit a query.

If no LLM keys present, the system falls back to a heuristic summarizer and remains fully runnable.
