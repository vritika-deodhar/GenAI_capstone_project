import re
from typing import Dict, List, Tuple

def find_snippet_in_chunks(snippet: str, chunks: List[Dict]) -> Tuple[bool, str]:
    # returns (found, chunk_id) where snippet found (exact substring match)
    for idx, c in enumerate(chunks):
        if snippet.strip() and snippet in c.get('text',''):
            return True, f"chunk_{idx}"
    return False, ''

def extract_numbers(s: str) -> List[float]:
    nums = re.findall(r'[-+]?[0-9]*\.?[0-9]+(?:e[-+]?\d+)?', s)
    out = []
    for n in nums:
        try:
            out.append(float(n))
        except:
            continue
    return out

def verify_summary_factuality(summary: Dict, chunks: List[Dict]) -> Dict:
    # summary: has fields 'problem','methods','datasets','results','evidence'
    issues = []
    # 1) evidence snippets presence
    evidence = summary.get('evidence', {})
    for field, items in evidence.items():
        for it in items:
            snippet = it.get('snippet','').strip()
            found, cid = find_snippet_in_chunks(snippet, chunks)
            if not found:
                issues.append({'type':'missing_evidence', 'field':field, 'snippet': snippet})
    # 2) numeric claim verification: ensure numbers mentioned in results appear in chunks
    results = summary.get('results', {})
    for k,v in results.items():
        # check v appears in chunk text (as number)
        v_str = str(v)
        found_any = False
        for c in chunks:
            if v_str in c.get('text',''):
                found_any = True
                break
        if not found_any:
            issues.append({'type':'numeric_mismatch','key':k,'value':v})
    return {'ok': len(issues)==0, 'issues': issues}

import json
import re
from src.llm.client import call_llm

def build_evaluator_prompt(summary, chunk_text):
    return f"""
        You are a strict verification agent.

        Your task is to compare the SUMMARY against the ORIGINAL TEXT
        and determine if the summary is fully grounded, factual, and consistent.

        ### ORIGINAL TEXT
        \"\"\"{chunk_text}\"\"\"

        ### SUMMARY
        {summary}

        ### CHECK FOR:
        - hallucinated methods, datasets, metrics
        - missing factual details
        - incorrect numeric values
        - mismatched metric names
        - claims not supported by the text

        ### RETURN STRICT JSON:
        {{
        "ok": true/false,
        "issues": [
            "description of issue 1",
            "description of issue 2"
        ]
        }}
        """


from src.llm.client import call_llm
import json
import re

def evaluate_summary_llm(summary, chunk_text):
    prompt = build_evaluator_prompt(chunk_text, summary)
    out = call_llm(prompt, max_tokens=2000, temperature=0)

    try:
        # Extract the JSON object from LLM output
        match = re.search(r"\{.*\}", out, flags=re.S)
        parsed = json.loads(match.group(0))

        # Ensure both fields exist even if LLM forgets
        if "ok" not in parsed:
            parsed["ok"] = False
        if "issues" not in parsed:
            parsed["issues"] = ["LLM returned incomplete evaluation"]

        return parsed

    except Exception:
        # Fallback if LLM output parsing fails
        return {
            "ok": False,
            "issues": [
                "LLM evaluator failed to parse output"
            ]
        }
