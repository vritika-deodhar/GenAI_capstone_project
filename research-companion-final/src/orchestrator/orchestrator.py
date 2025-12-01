import os, json, time
from typing import Dict
from pathlib import Path

from src.retrieval.client_arxiv import query_arxiv
from src.retrieval.downloader import download_pdf
from src.parsing.pdf_extractor import extract_text_from_pdf
from src.parsing.cleaner import clean_text
from src.parsing.sectioner import naive_section_split
# from src.chunking.chunker import chunk_text_by_tokens
from src.chunking.section_chunker import section_chunker
from src.agents.summarizer import summarize_chunk, summarize_paper_from_chunks
from src.agents.evaluator import verify_summary_factuality
from src.agents.evaluator import evaluate_summary_llm
from src.agents.aggregator import aggregate_summaries
from src.analysis.comparator import build_method_comparison
from src.agents.research_gap import detect_research_gaps
from src.agents.ranker import rank_papers
from src.agents.ranker import rank_papers_llm
from src.utils.references import build_references


class Orchestrator:
    def __init__(self, tmp_dir: str = './artifacts'):
        os.makedirs(tmp_dir, exist_ok=True)
        self.tmp_dir = tmp_dir
        self.cache_meta = Path(tmp_dir) / "metadata.json"
        if not self.cache_meta.exists():
            self._write_meta({'papers': {}})

    def _read_meta(self):
        return json.loads(self.cache_meta.read_text())

    def _write_meta(self, obj):
        self.cache_meta.write_text(json.dumps(obj, indent=2))

    def run(self, query: str, max_results: int = 3) -> Dict:
        start_time = time.time()
        print("\n============================")
        print("🚀 ORCHESTRATOR STARTED")
        print("📌 Query:", query)
        print("📄 Max papers:", max_results)
        print("============================\n")

        # 1) Retrieval
        print("🔍 Querying arXiv...")
        try:
            papers_meta = query_arxiv(query, max_results=max_results)
            print(f"✅ Retrieved {len(papers_meta)} papers")
        except Exception as e:
            print("❌ arXiv FAILED:", e)
            return {"error": "arXiv query failed", "details": str(e)}

        outputs = []

        for p_idx, p in enumerate(papers_meta):
            print(f"\n===============================")
            print(f"📄 PROCESSING PAPER {p_idx+1}/{len(papers_meta)}")
            print("📝 Title:", p.get("title", "N/A"))
            print("===============================\n")

            pdf_url = p.get('pdf_url')
            pid = p.get('id') or pdf_url
            title = p.get('title')
            authors = p.get('authors')
            published = p.get('published')

            meta_cache = self._read_meta()
            cached = meta_cache['papers'].get(pid)

            # 2) download / cache
            print("⬇️  Downloading / using cached PDF...")
            if cached and Path(cached.get('local_path', '')).exists():
                pdf_path = cached['local_path']
                print("✅ Using cached PDF:", pdf_path)
            else:
                try:
                    pdf_path = download_pdf(pdf_url, self.tmp_dir)
                    meta_cache['papers'][pid] = {'local_path': pdf_path, 'title': title, 'pdf_url': pdf_url}
                    self._write_meta(meta_cache)
                    print("✅ Downloaded:", pdf_path)
                except Exception as e:
                    print("❌ PDF download failed:", e)
                    pdf_path = None

            # 3) extract text
            print("📖 Extracting PDF text...")
            if pdf_path:
                try:
                    raw = extract_text_from_pdf(pdf_path)
                    print(f"✅ Extracted {len(raw)} characters")
                except Exception as e:
                    print("❌ PDF extraction failed:", e)
                    raw = p.get('summary', '')
            else:
                raw = p.get('summary', '')
                print("⚠️ Using abstract instead")

            # 4) clean + section
            print("🧹 Cleaning + sectioning...")
            cleaned = clean_text(raw)
            sections = naive_section_split(cleaned)
            combined = '\n'.join(s.get('text', '') for s in sections)

            # 5) chunking
            print("🧩 Chunking...")
            # chunks = chunk_text_by_tokens(combined, max_tokens=800, overlap=100)
            # chunks = chunk_text_by_tokens(combined)
            chunks = section_chunker(combined, max_tokens=3000)

            print(f"✅ Total chunks: {len(chunks)}")

            # 6) per-chunk summaries + verification
            chunk_summaries = []
            verifications = []
            # for idx, c in enumerate(chunks[:3]):
            #     print(f"🧠 Summarizing chunk {idx+1}/{min(3, len(chunks))}")
            # for idx, c in enumerate(chunks):
            #     print(f"🧠 Summarizing chunk {idx+1}/{len(chunks)}")
            #     summ = summarize_chunk(c['text'], f"{pid}_chunk_{idx}")
            #     try :
            #         v = evaluate_summary_llm(summ, chunks)
            #     except:
            #         v = verify_summary_factuality(summ, chunks)
            #     chunk_summaries.append(summ)
            #     verifications.append(v)
            MAX_RETRIES = 1   # run summarization again if evaluation fails

            for idx, c in enumerate(chunks):
                print(f"🧠 Summarizing chunk {idx+1}/{len(chunks)}")

                retries = 0
                while True:
                    # 1. Run summarizer
                    summ = summarize_chunk(c['text'], f"{pid}_chunk_{idx}")

                    # 2. Run evaluator (LLM first, fallback to rule-based)
                    try:
                        v = evaluate_summary_llm(c['text'], summ)
                    except:
                        v = verify_summary_factuality(summ, c['text'])

                    if v.get("ok", False) is True:
                        break

                    print(f"⚠️ Evaluation failed for chunk {idx+1}, retrying summarization...")

                    retries += 1
                    if retries > MAX_RETRIES:
                        print(f"❌ Summary failed after {MAX_RETRIES+1} attempts — keeping last version.")
                        break

                chunk_summaries.append(summ)
                verifications.append(v)


            # 7) paper-level summary
            print("📚 Aggregating chunk summaries into paper-level summary...")
            paper_summary = summarize_paper_from_chunks(
                chunk_summaries,
                {
                    "paper_id": pid,
                    "title": title,
                    "authors": authors,
                    "published": published,
                },
            )

            outputs.append({
                'paper_id': pid,
                'title': title,
                'authors': authors,
                'published': published,
                'pdf_url': pdf_url,
                'chunk_summaries': chunk_summaries,
                'verifications': verifications,
                'paper_summary': paper_summary,
            })
        # print("\n============================")
        # print("OUTPUT : ", outputs)
        # print("\n============================")
        # 8) corpus-level aggregation
        all_chunk_summaries = [s for p in outputs for s in p['chunk_summaries']]
        aggregate = aggregate_summaries(all_chunk_summaries)
        comparison = build_method_comparison(outputs)
        research_gaps = detect_research_gaps([p['paper_summary'] for p in outputs])
        try:
            ranking = rank_papers_llm(outputs)
        except:
            ranking = rank_papers(outputs)
        references = build_references(outputs)

        elapsed = round(time.time() - start_time, 2)
        print("\n============================")
        print("✅ ORCHESTRATOR FINISHED")
        print("⏱ Elapsed time:", elapsed, "seconds")
        print("============================\n")

        return {
            'query': query,
            'runtime_seconds': elapsed,
            'papers': outputs,
            'aggregate': aggregate,
            'comparison': comparison,
            'research_gaps': research_gaps,
            'ranking': ranking,
            'references': references,
        }
