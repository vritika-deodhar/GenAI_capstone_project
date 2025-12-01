from typing import List, Dict
from src.llm.client import call_llm


def detect_research_gaps(paper_summaries: List[Dict]) -> Dict:
    """
    paper_summaries: list of paper-level summaries from summarize_paper_from_chunks
    Returns: {"text": "..."} with a short list of gaps / future work
    """
    if not paper_summaries:
        return {"text": "No papers found, so no research gaps could be identified."}

    # LLM-based gap analysis if available
    try:
        import json
        compact = []
        for ps in paper_summaries:
            compact.append({
                "title": ps.get("title"),
                "problem": ps.get("overall_problem"),
                "methods": ps.get("overall_methods"),
                "datasets": ps.get("overall_datasets"),
                "limitations": ps.get("overall_limitations"),
            })

        prompt = (
            "You are an expert in recommender systems and academic survey writing.\n"
            "Given the following list of papers (with their problems, methods, datasets, and limitations), "
            "identify key research gaps, unresolved issues, and promising directions for future work.\n\n"
            "Return a short Markdown-formatted section, with bullet points, under headings like "
            "'Open Problems', 'Under-explored Settings', 'Methodological Gaps'.\n\n"
            f"PAPERS (JSON):\n{json.dumps(compact, ensure_ascii=False)}\n\n"
            "OUTPUT:"
        )
        out = call_llm(prompt, max_tokens=1024, temperature=0.0)
        if out:
            return {"text": out}
    except Exception:
        pass

    # Heuristic fallback: aggregate limitations
    limitations = []
    for ps in paper_summaries:
        for lim in ps.get("overall_limitations", []):
            limitations.append(f"- {lim}")

    if not limitations:
        return {"text": "No explicit limitations were extracted; research gaps could not be inferred reliably."}

    return {
        "text": "### Research Gaps (heuristic)\n\n" + "\n".join(limitations)
    }
