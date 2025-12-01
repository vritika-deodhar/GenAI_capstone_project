# import os, json, re
# from typing import Dict, Optional
# from src.llm.client import call_llm
# from src.chunking.tokenizer import count_tokens

# OPENAI_KEY = os.getenv('OPENAI_API_KEY')
# GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# MAX_TOTAL_TOKENS = 4000  # safe upper bound (model dependent). We'll budget conservatively.
# RESP_TOKENS_RESERVED = 400  # reserve for model output

# def build_prompt(text: str) -> str:
#     # prompt instructing the model to output compact JSON and evidence snippets
#     prompt = (
#         "You are an expert academic summarizer. Given the input chunk of a research paper, "
#         "produce ONLY valid JSON with keys: problem (short string), methods (list of short strings), "
#         "datasets (list), results (dict numeric claims if any), limitations (list), evidence (map of field -> list of {chunk_id, snippet}). "
#         "Each snippet must be a direct quote from the input text, no more than 25 words. Do not hallucinate.\n\n"
#         f"INPUT:\n{text}\n\nOUTPUT:"
#     )
#     return prompt

# def summarize_chunk(chunk_text: str, chunk_id: str) -> Dict:
#     # token-budget-aware LLM call with fallback to heuristic summarizer
#     prompt = build_prompt(chunk_text)
#     # count tokens for prompt and estimate
#     try:
#         prompt_tokens = count_tokens(prompt)
#     except Exception:
#         prompt_tokens = len(prompt.split())
#     # decide max tokens for response
#     max_resp = max(128, RESP_TOKENS_RESERVED)
#     # ensure total doesn't exceed MAX_TOTAL_TOKENS
#     if prompt_tokens + max_resp > MAX_TOTAL_TOKENS:
#         # truncate chunk_text proportionally
#         allowed = MAX_TOTAL_TOKENS - max_resp - 200
#         words = chunk_text.split()
#         chunk_text = ' '.join(words[:max(50, allowed)])
#         prompt = build_prompt(chunk_text)
#     # call LLM
#     out = call_llm(prompt, max_tokens=max_resp, temperature=0.0)
#     if out:
#         # try parse JSON block from response
#         try:
#             # extract first {...} block
#             m = re.search(r'\{.*\}', out, flags=re.S)
#             if m:
#                 parsed = json.loads(m.group(0))
#                 return parsed
#         except Exception:
#             pass
#     # fallback heuristic summarizer
#     return heuristic_summarize(chunk_text, chunk_id)

# def heuristic_summarize(text: str, chunk_id: str) -> Dict:
#     # very conservative heuristic: first sentence -> problem; look for 'we propose' ; datasets list common names
#     sents = re.split(r'(?<=[.!?])\s+', text.strip())
#     problem = sents[0] if sents else ''
#     methods = []
#     datasets = []
#     results = {}
#     limitations = []
#     # find 'we propose/present' phrases
#     m = re.search(r'we (?:propose|present|introduce|develop) ([\w\s\-]+)', text, flags=re.I)
#     if m:
#         methods.append(m.group(1).strip())
#     for ds in ['CIFAR-10','CIFAR-100','ImageNet','MNIST','GLUE','SQuAD']:
#         if ds.lower() in text.lower():
#             datasets.append(ds)
#     evidence = {}
#     # collect small quoted snippets if possible
#     if len(problem.split()) > 3:
#         evidence['problem'] = [{'chunk_id': chunk_id, 'snippet': ' '.join(problem.split()[:25])}]
#     return {'problem': problem[:400], 'methods': methods, 'datasets': datasets, 'results': results, 'limitations': limitations, 'evidence': evidence}

import os, json, re
from typing import Dict, List
from src.llm.client import call_llm
from src.chunking.tokenizer import count_tokens

OPENAI_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

MAX_TOTAL_TOKENS = 4000
RESP_TOKENS_RESERVED = 400


# ---------- CHUNK-LEVEL SUMMARIZATION (EXISTING BEHAVIOUR) ----------

def build_prompt(text: str) -> str:
    # prompt = (
    #     "You are an expert academic summarizer. Given the input chunk of a research paper, "
    #     "produce ONLY valid JSON with keys: problem (short string), methods (list of short strings), "
    #     "datasets (list), results (dict numeric claims if any), limitations (list), "
    #     "evidence (map of field -> list of {chunk_id, snippet}). "
    #     "Each snippet must be a direct quote from the input text, no more than 25 words. "
    #     "Do not hallucinate.\n\n"
    #     f"INPUT:\n{text}\n\nOUTPUT:"
    # )
    prompt = """
            You are an expert research assistant.

            Analyze the following research paper chunk and extract ONLY factual information explicitly stated.

            DO NOT summarize generally.
            DO NOT guess or infer.
            DO NOT hallucinate.
            Keep the summary technical and to the point.

            ### RULES:
            - The extracted summary should contain the methodology, results atleast.
            - Extract the metric and their corresponding values with the method as well as a part of results.
            - Include dataset names near reported metrics.
            - Do not copy unrelated text.
            - Include metric names exactly.
            - Evidence snippets MUST be copied verbatim from the text.

            ### CHUNK:
            {text}
            """

    return prompt

import re
from typing import Dict, List


def heuristic_summarize(text: str, chunk_id: str) -> Dict:
    sents = re.split(r'(?<=[.!?])\s+', text.strip())

    # ---------- PROBLEM ----------
    problem = sents[0] if sents else ''

    # ---------- METHODS ----------
    methods = []
    method_patterns = [
        r'we (?:propose|present|introduce|develop|design) ([\w\- ]+)',
        r'our (?:method|model|approach|framework|algorithm) ([\w\- ]+)',
        r'the proposed ([\w\- ]+)',
    ]

    for pat in method_patterns:
        for m in re.findall(pat, text, re.I):
            methods.append(m.strip())

    methods = list(set(methods))

    # ---------- DATASETS (auto-detect) ----------
    dataset_patterns = [
        r'on the ([A-Z][A-Za-z0-9\- ]+ dataset)',
        r'evaluated on ([A-Z][A-Za-z0-9\- ]+)',
        r'tested on ([A-Z][A-Za-z0-9\- ]+)',
        r'using the ([A-Z][A-Za-z0-9\- ]+)',
        r'we use ([A-Z][A-Za-z0-9\- ]+)',
    ]

    datasets = set()
    for pat in dataset_patterns:
        for match in re.findall(pat, text):
            datasets.add(match.strip())

    # ---------- RESULTS (metric extraction) ----------
    results = {}
    result_patterns = [
        r'(accuracy|acc|f1-score|bleu|rouge|ndcg|map|recall|precision)[:= ]+([0-9]+(?:\.[0-9]+)?)',
        r'([0-9]+(?:\.[0-9]+)?)\s*%(?:\s+)?(accuracy|acc|f1|f1-score|precision|recall)',
        r'outperform(?:s)? .* by ([0-9]+(?:\.[0-9]+)?)%',
    ]

    for pat in result_patterns:
        for m in re.findall(pat, text, re.I):
            if isinstance(m, tuple):
                metric = m[0].lower()
                value = m[1]
                results[metric] = value
    # ---------- RESULTS (better metric extraction) ----------
    # results = {}

    # RESULT_PATTERNS = [
    #     r'(ndcg[:= ]+([0-9]+\.[0-9]+))',
    #     r'(map[:= ]+([0-9]+\.[0-9]+))',
    #     r'(recall[:= ]+([0-9]+\.[0-9]+))',
    #     r'(precision[:= ]+([0-9]+\.[0-9]+))',
    #     r'(accuracy[:= ]+([0-9]+\.[0-9]+))',
    #     r'(f1-score[:= ]+([0-9]+\.[0-9]+))',
    #     r'(hit@k[:= ]+([0-9]+\.[0-9]+))',
    #     r'(hit@10[:= ]+([0-9]+\.[0-9]+))',
    #     r'outperform(?:s)? .* by ([0-9]+(?:\.[0-9]+)?)%',
    #     r'(improve(?:d)? by ([0-9]+(?:\.[0-9]+)?)%)',
    # ]

    # for pat in RESULT_PATTERNS:
    #     for m in re.findall(pat, text, re.I):
    #         if isinstance(m, tuple):
    #             metric = m[0].split()[0].lower()
    #             value = m[-1]
    #             results[metric] = value


    # ---------- LIMITATIONS ----------
    limitations = []
    limitation_patterns = [
        r'limitation[s]?:? (.*?)[\.\n]',
        r'however[,]?(.*?)[\.\n]',
        r'drawback[s]?:? (.*?)[\.\n]',
        r'future work (.*?)[\.\n]',
    ]

    for pat in limitation_patterns:
        for m in re.findall(pat, text, re.I):
            limitations.append(m.strip())

    # ---------- EVIDENCE ----------
    evidence = {}

    if len(problem.split()) > 5:
        evidence['problem'] = [{
            'chunk_id': chunk_id,
            'snippet': ' '.join(problem.split()[:25])
        }]

    if methods:
        evidence['methods'] = [{
            'chunk_id': chunk_id,
            'snippet': methods[0]
        }]

    if datasets:
        evidence['datasets'] = [{
            'chunk_id': chunk_id,
            'snippet': d
        } for d in list(datasets)[:3]]

    if results:
        for k, v in list(results.items())[:3]:
            evidence.setdefault("results", []).append({
                'chunk_id': chunk_id,
                'snippet': f"{k}: {v}"
            })

    if limitations:
        evidence['limitations'] = [{
            'chunk_id': chunk_id,
            'snippet': limitations[0][:100]
        }]

    return {
        'problem': problem[:400],
        'methods': methods,
        'datasets': list(datasets),
        'results': results,
        'limitations': limitations[:3],
        'evidence': evidence,
    }

# def heuristic_summarize(text: str, chunk_id: str) -> Dict:
#     sents = re.split(r'(?<=[.!?])\s+', text.strip())
#     problem = sents[0] if sents else ''
#     methods: List[str] = []
#     datasets: List[str] = []
#     results: Dict[str, float] = {}
#     limitations: List[str] = []

#     m = re.search(r'we (?:propose|present|introduce|develop) ([\w\-\s]+)', text, flags=re.I)
#     if m:
#         methods.append(m.group(1).strip())

#     for ds in ['CIFAR-10', 'CIFAR-100', 'ImageNet', 'MNIST', 'GLUE', 'SQuAD']:
#         if ds.lower() in text.lower():
#             datasets.append(ds)

#     evidence: Dict[str, List[Dict]] = {}
#     if len(problem.split()) > 3:
#         evidence['problem'] = [{
#             'chunk_id': chunk_id,
#             'snippet': ' '.join(problem.split()[:25])
#         }]

#     return {
#         'problem': problem[:400],
#         'methods': methods,
#         'datasets': datasets,
#         'results': results,
#         'limitations': limitations,
#         'evidence': evidence,
#     }


def summarize_chunk(chunk_text: str, chunk_id: str) -> Dict:
    print("IN Summarize chunk")
    prompt = build_prompt(chunk_text)

    try:
        prompt_tokens = count_tokens(prompt)
    except Exception:
        prompt_tokens = len(prompt.split())

    max_resp = max(128, RESP_TOKENS_RESERVED)
    if prompt_tokens + max_resp > MAX_TOTAL_TOKENS:
        allowed = MAX_TOTAL_TOKENS - max_resp - 200
        words = chunk_text.split()
        chunk_text = ' '.join(words[:max(50, allowed)])
        prompt = build_prompt(chunk_text)

    out = call_llm(prompt, max_tokens=max_resp, temperature=0.0)
    if out:
        try:
            m = re.search(r'\{.*\}', out, flags=re.S)
            if m:
                parsed = json.loads(m.group(0))
                return parsed
        except Exception:
            pass

    return heuristic_summarize(chunk_text, chunk_id)


# ---------- PAPER-LEVEL SUMMARIZATION (NEW) ----------

def _build_paper_prompt(chunk_summaries: List[Dict], meta: Dict) -> str:
    """
    chunk_summaries: list of dicts from summarize_chunk()
    meta: {title, authors, published, paper_id}
    """
    compact_chunks = []
    for idx, cs in enumerate(chunk_summaries):
        compact_chunks.append({
            "chunk_index": idx,
            "problem": cs.get("problem", ""),
            "methods": cs.get("methods", []),
            "datasets": cs.get("datasets", []),
            "results": cs.get("results", {}),
            "limitations": cs.get("limitations", []),
        })

    title = meta.get("title") or ""
    authors = ", ".join(meta.get("authors") or [])
    published = meta.get("published") or ""
    prompt = """
    You are a scientific editor combining structured research findings.

    Aggregate the following extracted chunk-level summaries into a single global paper summary.

    Merge only factual fields that are repeated or consistent.

    ### RULES:
    - Summary should contain the methodology and the results.
    - Deduplicate metrics by (metric + dataset).
    - Prefer consistent values reported multiple times.
    - Discard conflicting values unless ALL are reported.
    - Report comparisons of methods explicitly.
    - Report dataset + metric pairs.
    - Keep evidence.
    - Do not summarize vaguely.

    ### CHUNK RESULTS:
    {chunk_summaries}

    """

    # prompt = (
    #     "You are summarizing an academic paper from multiple chunk-level summaries.\n"
    #     "You will receive: metadata (title, authors, year) and a list of chunk_summaries.\n\n"
    #     "Return ONLY valid JSON with keys:\n"
    #     " - title (string)\n"
    #     " - authors (list of strings)\n"
    #     " - published (string or year)\n"
    #     " - overall_problem (string)\n"
    #     " - overall_methods (list of strings)\n"
    #     " - overall_datasets (list of strings)\n"
    #     " - overall_results (dict of metric_name -> numeric or short string)\n"
    #     " - overall_limitations (list of strings)\n\n"
    #     "Be concise, do NOT hallucinate new datasets or methods; only merge what appears in the chunk summaries.\n\n"
    #     f"METADATA:\nTitle: {title}\nAuthors: {authors}\nPublished: {published}\n\n"
    #     f"CHUNK_SUMMARIES (JSON):\n{json.dumps(compact_chunks, ensure_ascii=False)}\n\n"
    #     "OUTPUT JSON:"
    # )
    return prompt


def summarize_paper_from_chunks(chunk_summaries: List[Dict], meta: Dict) -> Dict:
    """
    Aggregate chunk-level summaries into a single paper-level summary.
    Uses LLM if available, otherwise falls back to a deterministic merge.
    """
    # Try LLM-based aggregation
    prompt = _build_paper_prompt(chunk_summaries, meta)
    out = call_llm(prompt, max_tokens=512, temperature=0.0)

    if out:
        try:
            m = re.search(r'\{.*\}', out, flags=re.S)
            if m:
                return json.loads(m.group(0))
        except Exception:
            pass

    # -------- Heuristic fallback: merge fields --------
    overall_problem = ""
    methods_set = set()
    datasets_set = set()
    results_agg: Dict[str, float] = {}
    limitations_set = set()

    for cs in chunk_summaries:
        if not overall_problem and cs.get("problem"):
            overall_problem = cs["problem"]

        for mtd in cs.get("methods", []):
            methods_set.add(mtd)

        for ds in cs.get("datasets", []):
            datasets_set.add(ds)

        for k, v in (cs.get("results") or {}).items():
            # simple override / or last one wins (you can make smarter later)
            results_agg[k] = v

        for lim in cs.get("limitations", []):
            limitations_set.add(lim)

    return {
        "title": meta.get("title"),
        "authors": meta.get("authors") or [],
        "published": meta.get("published"),
        "overall_problem": overall_problem,
        "overall_methods": sorted(methods_set),
        "overall_datasets": sorted(datasets_set),
        "overall_results": results_agg,
        "overall_limitations": sorted(limitations_set),
    }
