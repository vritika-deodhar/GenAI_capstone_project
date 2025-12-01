import fitz, re
def extract_text_by_page(path: str):
    doc = fitz.open(path)
    pages = []
    for page in doc:
        pages.append(page.get_text('text'))
    return pages
def remove_headers_footers(pages):
    top_lines=[]; bottom_lines=[]
    for p in pages:
        lines=[ln.strip() for ln in p.splitlines() if ln.strip()]
        if not lines: continue
        top_lines.append(lines[0]); bottom_lines.append(lines[-1])
    from collections import Counter
    top_common = Counter(top_lines).most_common(1)
    bot_common = Counter(bottom_lines).most_common(1)
    top = top_common[0][0] if top_common else None
    bot = bot_common[0][0] if bot_common else None
    cleaned=[]
    for p in pages:
        lines = p.splitlines()
        if top and lines and lines[0].strip()==top:
            lines = lines[1:]
        if bot and lines and lines[-1].strip()==bot:
            lines = lines[:-1]
        cleaned.append('\n'.join(lines))
    return cleaned
def extract_text_from_pdf(path: str):
    pages = extract_text_by_page(path)
    pages = remove_headers_footers(pages)
    text = '\n'.join(pages)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
