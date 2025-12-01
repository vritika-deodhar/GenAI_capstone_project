from typing import List, Dict
from datetime import datetime

def _score_paper(p: Dict) -> float:
    ps = p.get("paper_summary") or {}
    score = 0.0

    # recency boost
    pub = ps.get("published") or p.get("published")
    if pub:
        try:
            year = int(str(pub)[:4])
            score += max(0, year - 2000) * 0.5
        except Exception:
            pass

    # more methods = richer methodology
    score += len(ps.get("overall_methods", [])) * 1.0

    # results presence
    if ps.get("overall_results"):
        score += 2.0

    # limitations presence (honesty)
    if ps.get("overall_limitations"):
        score += 1.0

    return score


def rank_papers(papers: List[Dict]) -> List[Dict]:
    scored = []
    for p in papers:
        s = _score_paper(p)
        scored.append({
            "paper_id": p.get("paper_id"),
            "title": p.get("title"),
            "published": (p.get("paper_summary") or {}).get("published") or p.get("published"),
            "score": round(s, 2),
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored

def build_ranking_prompt(papers: List[Dict]) -> str:
    return f"""
        You are a scientific ranking agent.

        Your task is to assign a numeric score to each paper based on:
        1. Recency (newer papers score higher)
        2. Richness of methodology (more methods → higher score)
        3. Presence of experimental results (papers with results → +2)
        4. Presence of limitations (transparent papers → +1)

        These rules mirror the scoring logic:

        score =
        0.5 * max(0, year - 2000)
        + 1.0 * len(overall_methods)
        + 2.0 * (has overall_results)
        + 1.0 * (has overall_limitations)

        ### INPUT PAPERS (JSON)
        {papers}

        ### TASK:
        Return a STRICT JSON array where each element has:
        {{
        "paper_id": "...",
        "title": "...",
        "published": "...",
        "score": number
        }}

        ### RULES
        - Use ONLY the information inside the provided JSON.
        - Use the scoring formula above EXACTLY.
        - The output must be a JSON array only. No explanations.
        """

import json
import re
from src.llm.client import call_llm

def rank_papers_llm(papers: List[Dict]) -> List[Dict]:
    prompt = build_ranking_prompt(papers)
    out = call_llm(prompt, max_tokens=2000, temperature=0)

    # Extract JSON
    m = re.search(r"\[.*\]", out, flags=re.S)
    parsed = json.loads(m.group(0))

    # Validate structure
    for item in parsed:
        if "paper_id" not in item:
            raise ValueError("Missing paper_id")
        if "title" not in item:
            raise ValueError("Missing title")
        if "published" not in item:
            raise ValueError("Missing published")
        if "score" not in item:
            raise ValueError("Missing score")

    return parsed

