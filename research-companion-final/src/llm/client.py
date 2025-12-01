import os, requests, json, time
from typing import Optional, Dict
from dotenv import load_dotenv
load_dotenv()

# OPENAI_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')
# GEMINI_ENDPOINT = os.getenv('GEMINI_ENDPOINT')  # must be configured if using Gemini

# def call_gemini(prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> Optional[str]:
#     print("CALL GEMINI")
#     # Minimal generic Gemini call. Requires GEMINI_ENDPOINT set to a supported inference API.
#     if not GEMINI_KEY or not GEMINI_ENDPOINT:
#         return None
#     headers = {'Authorization': f'Bearer {GEMINI_KEY}', 'Content-Type': 'application/json'}
#     payload = {'prompt': prompt, 'max_output_tokens': max_tokens, 'temperature': temperature}
#     try:
#         resp = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload, timeout=60)
#         resp.raise_for_status()
#         j = resp.json()
#         # Try common fields
#         if isinstance(j, dict):
#             # possible keys: 'output', 'candidates', 'text'
#             if 'output' in j and isinstance(j['output'], dict) and 'content' in j['output']:
#                 return j['output']['content']
#             if 'candidates' in j and isinstance(j['candidates'], list) and len(j['candidates'])>0:
#                 return j['candidates'][0].get('content') or j['candidates'][0].get('text')
#             if 'text' in j:
#                 return j['text']
#         return json.dumps(j)
#         print("[LLM DEBUG] Raw response:", response)
#     except Exception as e:
#         print("ERROR", e)

#         return None

from google import genai
import os
from typing import Optional


def call_gemini(prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> Optional[str]:

    print("✅ CALLING GEMINI SDK")

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("❌ Gemini key not found in environment")
        return None

    try:
        client = genai.Client(api_key=key)

        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",   # ✅ correct model
            contents=prompt,
            config={
                "max_output_tokens": max_tokens,
            },
        )

        return response.text

    except Exception as e:
        print("❌ GEMINI ERROR:", e)
        return None

# def call_openai(prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> Optional[str]:
#     if not OPENAI_KEY:
#         return None
#     try:
#         import openai
#         openai.api_key = OPENAI_KEY
#         resp = openai.ChatCompletion.create(
#             model='gpt-4o-mini',
#             messages=[{'role':'user','content':prompt}],
#             max_tokens=max_tokens,
#             temperature=temperature
#         )
#         return resp['choices'][0]['message']['content']
#     except Exception as e:
#         return None

def call_llm(prompt: str, max_tokens: int = 1024, temperature: float = 0.0) -> Optional[str]:
    # prefer Gemini if configured
    # print("CALL LLM")
    out = None
    if GEMINI_KEY:
        out = call_gemini(prompt, max_tokens=max_tokens, temperature=temperature)
    # if out is None and OPENAI_KEY:
    #     out = call_openai(prompt, max_tokens=max_tokens, temperature=temperature)
    # print("OUT : ",out)
    return out
