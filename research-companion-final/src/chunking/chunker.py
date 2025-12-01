# from typing import List, Dict
# from .tokenizer import count_tokens
# def chunk_text_by_tokens(text: str, max_tokens: int = 800, overlap: int = 50):
#     words = text.split()
#     chunks = []
#     i=0; n=len(words)
#     while i < n:
#         j = min(n, i + max_tokens)
#         chunk = ' '.join(words[i:j])
#         chunks.append({'text': chunk, 'start': i, 'end': j})
#         i = j - overlap
#     return chunks

import spacy
from .tokenizer import count_tokens
from itertools import accumulate

nlp = spacy.load("en_core_web_sm")

def chunk_text_by_tokens(text, max_tokens=1000):
    doc = nlp(text)
    sents = [s.text for s in doc.sents]

    token_sizes = list(map(count_tokens, sents))
    cum = list(accumulate(token_sizes))

    cuts = [0]
    for i, total in enumerate(cum):
        if total > max_tokens:
            cuts.append(i)
            cum = list(accumulate(token_sizes[i:]))
    cuts.append(len(sents))

    return [{"text": " ".join(sents[cuts[i]:cuts[i+1]])}
            for i in range(len(cuts)-1)]

