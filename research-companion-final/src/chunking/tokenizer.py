try:
    import tiktoken
    def count_tokens(text: str, model: str = 'gpt-4o-mini'):
        try:
            enc = tiktoken.encoding_for_model(model)
        except Exception:
            enc = tiktoken.get_encoding('cl100k_base')
        return len(enc.encode(text))
except Exception:
    def count_tokens(text: str, model: str = None):
        return max(1, len(text.split()))
