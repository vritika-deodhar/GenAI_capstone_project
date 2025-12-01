# import requests
# from xml.etree import ElementTree as ET
# from urllib.parse import urlencode
# from typing import List, Dict
# import time
# import os
# ARXIV_BASE = os.getenv('ARXIV_BASE_URL', 'http://export.arxiv.org/api/query')
# def query_arxiv(query: str, max_results: int = 5) -> List[Dict]:
#     params = {'search_query': query, 'start': 0, 'max_results': max_results}
#     url = ARXIV_BASE + '?' + urlencode(params)
#     resp = requests.get(url, timeout=30)
#     resp.raise_for_status()
#     root = ET.fromstring(resp.text)
#     ns = {'atom':'http://www.w3.org/2005/Atom'}
#     entries = []
#     for entry in root.findall('atom:entry', ns):
#         title = entry.find('atom:title', ns).text.strip() if entry.find('atom:title', ns) is not None else ''
#         summary = entry.find('atom:summary', ns).text.strip() if entry.find('atom:summary', ns) is not None else ''
#         pdf_url = None
#         for link in entry.findall('atom:link', ns):
#             if link.attrib.get('type') == 'application/pdf' or link.attrib.get('title') == 'pdf':
#                 pdf_url = link.attrib.get('href')
#         if not pdf_url:
#             id_tag = entry.find('atom:id', ns).text.strip()
#             pdf_url = id_tag.replace('abs','pdf') + '.pdf'
#         authors = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]
#         pub_date = entry.find('atom:published', ns).text if entry.find('atom:published', ns) is not None else None
#         entries.append({'id': entry.find('atom:id', ns).text, 'title': title, 'summary': summary, 'pdf_url': pdf_url, 'authors': authors, 'published': pub_date})
#         time.sleep(0.1)
#     return entries

import requests
from xml.etree import ElementTree as ET
from urllib.parse import urlencode, quote
from typing import List, Dict
import time
import os
import re

ARXIV_BASE = os.getenv('ARXIV_BASE_URL', 'http://export.arxiv.org/api/query')


def _build_search_query(query: str) -> str:
    """
    Build an arXiv search query that searches in title and abstract.
    - Wraps multi-word phrases in quotes for exact matching
    - Searches both ti: (title) and abs: (abstract) fields
    - Uses OR to combine for broader matching, prioritizing title matches
    """
    # Clean the query
    query = query.strip()

    # If the query looks like it could be a paper title (multiple words),
    # search for it as a phrase in the title first, then abstract
    words = query.split()

    if len(words) > 1:
        # For multi-word queries, search as a phrase in title and abstract
        # Quote the phrase for exact matching
        escaped_query = query.replace('"', '')  # Remove any existing quotes
        # Also search for individual words combined with AND for better coverage
        and_query = ' AND '.join([f'ti:{w}' for w in words if len(w) > 2])
        search_query = f'ti:"{escaped_query}" OR ({and_query}) OR abs:"{escaped_query}"'
    else:
        # Single word: search in title and abstract
        search_query = f'ti:{query} OR abs:{query}'

    return search_query


def query_arxiv(query: str, max_results: int = 5) -> List[Dict]:
    # Build a proper search query that prioritizes title matches
    search_query = _build_search_query(query)

    params = {
        'search_query': search_query,
        'start': 0,
        'max_results': max(max_results * 3, 15),  # Fetch more to improve relevance filtering
        'sortBy': 'relevance',  # Sort by relevance instead of default (submittedDate)
        'sortOrder': 'descending'
    }
    url = ARXIV_BASE + '?' + urlencode(params)
    print(f"[arXiv] Query URL: {url}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    ns = {'atom':'http://www.w3.org/2005/Atom'}
    entries = []
    for entry in root.findall('atom:entry', ns):
        title = entry.find('atom:title', ns).text.strip() if entry.find('atom:title', ns) is not None else ''
        summary = entry.find('atom:summary', ns).text.strip() if entry.find('atom:summary', ns) is not None else ''
        pdf_url = None
        for link in entry.findall('atom:link', ns):
            if link.attrib.get('type') == 'application/pdf' or link.attrib.get('title') == 'pdf':
                pdf_url = link.attrib.get('href')
        if not pdf_url:
            id_tag = entry.find('atom:id', ns).text.strip()
            pdf_url = id_tag.replace('abs','pdf') + '.pdf'
        authors = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]
        pub_date = entry.find('atom:published', ns).text if entry.find('atom:published', ns) is not None else None
        entries.append({'id': entry.find('atom:id', ns).text, 'title': title, 'summary': summary, 'pdf_url': pdf_url, 'authors': authors, 'published': pub_date})
        time.sleep(0.1)

    # Re-rank entries by title relevance to the original query
    entries = _rerank_by_relevance(entries, query, max_results)

    return entries


def _rerank_by_relevance(entries: List[Dict], query: str, max_results: int) -> List[Dict]:
    """
    Re-rank entries by how well their title matches the query.
    Prioritizes exact/close title matches over tangential results.
    """
    query_lower = query.lower().strip()
    query_words = set(re.findall(r'\w+', query_lower))
    # Normalize query for comparison (remove punctuation, extra spaces)
    query_normalized = ' '.join(sorted(query_words))

    def relevance_score(entry: Dict) -> float:
        title = entry.get('title', '').lower()
        # Normalize title: collapse whitespace, newlines
        title = ' '.join(title.split())
        title_words = set(re.findall(r'\w+', title))
        title_normalized = ' '.join(sorted(title_words))

        score = 0.0

        # EXACT title match (highest priority) - title equals query
        if query_lower == title or query_normalized == title_normalized:
            score += 1000.0

        # Title contains the exact query phrase
        elif query_lower in title:
            # Penalize if title has many extra words (derivative papers)
            extra_words = len(title_words) - len(query_words)
            if extra_words <= 2:
                score += 500.0  # Very close match
            else:
                score += 200.0 - (extra_words * 5)  # Reduce score for longer derivative titles

        # Check if all query words appear in title
        if query_words.issubset(title_words):
            score += 100.0
            # Bonus if title length is close to query length (not a derivative paper)
            length_ratio = len(query_words) / max(len(title_words), 1)
            score += length_ratio * 50.0

        # Partial word overlap
        overlap = len(query_words & title_words)
        score += overlap * 10.0

        # Small bonus for older/seminal papers (they often have cleaner titles)
        pub_date = entry.get('published', '')
        if pub_date:
            try:
                year = int(pub_date[:4])
                if year <= 2018:  # Likely seminal work
                    score += 20.0
            except:
                pass

        return score

    # Sort by relevance score descending
    entries_scored = [(relevance_score(e), e) for e in entries]
    entries_scored.sort(key=lambda x: x[0], reverse=True)

    # Log top results for debugging
    print(f"[arXiv] Re-ranked results:")
    for score, e in entries_scored[:5]:
        print(f"  - Score {score:.1f}: {e.get('title', 'N/A')[:70]}...")

    # Return top max_results
    return [e for _, e in entries_scored[:max_results]]
 