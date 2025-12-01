# import re
# from .tokenizer import count_tokens

# # Common academic section patterns
# SECTION_PATTERNS = [
#     r'^\d+\s+introduction',
#     r'^\d+\.\s+introduction',
#     r'^introduction',
#     r'^\d+\s+related work',
#     r'^related work',
#     r'^\d+\s+background',
#     r'^background',
#     r'^\d+\s+method',
#     r'^method',
#     r'^\d+\s+methodology',
#     r'^methodology',
#     r'^\d+\s+approach',
#     r'^approach',
#     r'^\d+\s+model',
#     r'^model',
#     r'^\d+\s+experiments?',
#     r'^experiments?',
#     r'^\d+\s+evaluation',
#     r'^evaluation',
#     r'^\d+\s+results?',
#     r'^results?',
#     r'^\d+\s+discussion',
#     r'^discussion',
#     r'^\d+\s+analysis',
#     r'^analysis',
#     r'^\d+\s+conclusion',
#     r'^conclusion',
#     r'^\d+\s+limitations?',
#     r'^limitations?',
#     r'acknowledg(e)?ments?',
#     r'references'
# ]

# SECTION_RE = re.compile("|".join(SECTION_PATTERNS), re.I)


# def section_chunker(text: str, max_tokens: int = 3000):
#     """
#     Split paper into chunks by detecting semantic sections.
#     Large sections are further split if they exceed max_tokens.
#     """
#     lines = text.splitlines()

#     sections = []
#     current_title = "unknown"
#     current_body = []

#     for line in lines:
#         if SECTION_RE.match(line.strip()):
#             if current_body:
#                 sections.append((current_title, "\n".join(current_body)))
#                 current_body = []
#             current_title = line.strip()
#         else:
#             current_body.append(line)

#     if current_body:
#         sections.append((current_title, "\n".join(current_body)))

#     # ---- handle large sections (sub-chunk if needed) ----
#     chunks = []
#     for title, body in sections:
#         tokens = count_tokens(body)
#         if tokens <= max_tokens:
#             chunks.append({
#                 "section": title,
#                 "text": body,
#                 "tokens": tokens
#             })
#         else:
#             # fallback to token chunking inside large section
#             words = body.split()
#             step = max_tokens // 2
#             for i in range(0, len(words), step):
#                 part = " ".join(words[i:i+step])
#                 chunks.append({
#                     "section": f"{title} (part {i//step+1})",
#                     "text": part,
#                     "tokens": count_tokens(part)
#                 })

#     return chunks
import re
from .tokenizer import count_tokens

# ✅ Valuable sections
KEEP_SECTIONS = [
    r'^abstract',
    r'^\d+\s+method',
    r'^method',
    r'^\d+\s+methodology',
    r'^methodology',
    r'^\d+\s+model',
    r'^model',
    r'^\d+\s+approach',
    r'^approach',
    r'^\d+\s+experiments?',
    r'^experiments?',
    r'^\d+\s+evaluation',
    r'^evaluation',
    r'^\d+\s+results?',
    r'^results?',
    r'^\d+\s+analysis',
    r'^analysis',
    r'^\d+\s+discussion',
    r'^discussion',
    r'^\d+\s+limitations?',
    r'^limitations?',
    r'^\d+\s+conclusion',
    r'^conclusion',
]

# ❌ Sections to ignore
DROP_SECTIONS = [
    r'^introduction',
    r'^\d+\s+introduction',
    r'^related work',
    r'^\d+\s+related work',
    r'^background',
    r'^\d+\s+background',
    r'^acknowledg(e)?ments?',
    r'^references'
]

KEEP_RE = re.compile("|".join(KEEP_SECTIONS), re.I)
DROP_RE = re.compile("|".join(DROP_SECTIONS), re.I)


def section_chunker(text: str, max_tokens: int = 3000):
    """
    Split paper into semantic chunks.
    Keeps only informative sections and drops noise.
    """

    lines = text.splitlines()

    sections = []
    current_title = "abstract"    # assume start is abstract
    current_body = []

    for line in lines:
        stripped = line.strip()

        # if it is a garbage section → close and skip
        if DROP_RE.match(stripped):
            current_body = []
            current_title = "SKIP"
            continue

        # if it's a useful section → start new
        if KEEP_RE.match(stripped):
            if current_body and current_title != "SKIP":
                sections.append((current_title, "\n".join(current_body)))
            current_body = []
            current_title = stripped
            continue

        # collect text if it belongs to good section
        if current_title != "SKIP":
            current_body.append(line)

    # flush last collected section
    if current_body and current_title != "SKIP":
        sections.append((current_title, "\n".join(current_body)))

    # ---------- split large sections ----------
    chunks = []
    for title, body in sections:
        tokens = count_tokens(body)

        if tokens <= max_tokens:
            chunks.append({
                "section": title,
                "text": body,
                "tokens": tokens
            })
        else:
            # split large sections only if needed
            words = body.split()
            step = max_tokens // 2

            for i in range(0, len(words), step):
                part = " ".join(words[i:i+step])
                chunks.append({
                    "section": f"{title} (part {i//step+1})",
                    "text": part,
                    "tokens": count_tokens(part)
                })

    return chunks
