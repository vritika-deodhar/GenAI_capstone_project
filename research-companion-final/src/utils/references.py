from typing import List, Dict

def build_references(papers: List[Dict]) -> List[Dict]:
    """
    Build a simple reference list for UI / export.
    Each entry: {paper_id, title, authors, published, url}
    """
    refs = []
    for p in papers:
        meta = p.get("paper_summary") or {}
        refs.append({
            "paper_id": p.get("paper_id"),
            "title": meta.get("title") or p.get("title"),
            "authors": meta.get("authors") or p.get("authors") or [],
            "published": meta.get("published") or p.get("published"),
            "url": p.get("pdf_url") or p.get("id"),
        })
    return refs
