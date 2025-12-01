import re
def clean_text(text: str) -> str:
    text = re.sub(r'\\cite\{.*?\}', '', text)
    text = re.sub(r'\\ref\{.*?\}', '', text)
    text = re.sub(r'\[(?:[0-9]{1,3},?\s?)+\]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
