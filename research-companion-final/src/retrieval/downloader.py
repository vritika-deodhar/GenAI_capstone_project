import requests, os, hashlib
def download_pdf(url: str, dest_dir: str):
    os.makedirs(dest_dir, exist_ok=True)
    h = hashlib.sha1(url.encode('utf-8')).hexdigest()[:10]
    local_name = f"{h}.pdf"
    dest = os.path.join(dest_dir, local_name)
    if os.path.exists(dest):
        return dest
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return dest
