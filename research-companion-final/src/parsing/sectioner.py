import re
HEADING_PATTERNS = [r'^(Abstract)\b', r'^(Introduction)\b', r'^(Related Work)\b', r'^(Background)\b', r'^(Method|Methods)\b', r'^(Experiments|Results)\b', r'^(Conclusion|Conclusions)\b', r'^(References)\b']
def find_headings(text: str):
    headings=[]
    lines = text.split('\n')
    for i,ln in enumerate(lines):
        s = ln.strip()
        for pat in HEADING_PATTERNS:
            if re.match(pat, s, flags=re.IGNORECASE):
                headings.append((i,s))
                break
    return headings
def naive_section_split(text: str):
    lines = text.split('\n')
    headings = find_headings(text)
    if not headings:
        return [{'title':'full_text','text':text}]
    sections=[]
    for idx, (line_no, title) in enumerate(headings):
        start = line_no
        end = headings[idx+1][0] if idx+1 < len(headings) else len(lines)
        sec_text = '\n'.join(lines[start+1:end]).strip()
        sections.append({'title': title.strip(), 'text': sec_text})
    return sections
