from typing import List, Dict


# def build_method_comparison(papers: List[Dict]) -> Dict:
#     """
#     papers: list of dicts with keys:
#       - paper_id
#       - title
#       - published
#       - paper_summary (from summarize_paper_from_chunks)
#     """
#     by_method: Dict[str, List[str]] = {}
#     rows: List[Dict] = []

#     for p in papers:
#         meta = p.get("paper_summary") or {}
#         paper_id = p.get("paper_id")
#         title = p.get("title")
#         published = meta.get("published") or p.get("published")
#         methods = meta.get("overall_methods", [])
#         datasets = meta.get("overall_datasets", [])
#         results = meta.get("overall_results", {})

#         # build cross-table rows
#         if not methods:
#             rows.append({
#                 "paper_id": paper_id,
#                 "title": title,
#                 "published": published,
#                 "method": None,
#                 "datasets": datasets,
#                 "results": results,
#             })
#         else:
#             for m in methods:
#                 by_method.setdefault(m, []).append(paper_id)
#                 rows.append({
#                     "paper_id": paper_id,
#                     "title": title,
#                     "published": published,
#                     "method": m,
#                     "datasets": datasets,
#                     "results": results,
#                 })

#     return {
#         "by_method": by_method,
#         "rows": rows,
#     }

def build_method_comparison(papers):
    rows = []

    for p in papers:
        ps = p.get("paper_summary") or {}
        paper_id = p.get("paper_id")
        title = ps.get("title") or p.get("title")
        published = ps.get("published") or p.get("published")
        methods = ps.get("overall_methods", [])
        datasets = ps.get("overall_datasets", [])
        results = ps.get("overall_results", {})

        rows.append({
            "paper_id": paper_id,
            "title": title,
            "published": published,
            "method": ", ".join(methods) if methods else "N/A",
            "datasets": datasets,
            "results": results,
        })

    return {
        "rows": rows
    }

