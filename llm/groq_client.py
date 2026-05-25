import os
import requests


def groq_chat(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY", "")
    model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    if not api_key:
        return local_report(prompt)
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def local_report(prompt: str) -> str:
    signal = "WATCH" if "negative" in prompt.lower() or "pressure" in prompt.lower() else "NEUTRAL"
    return (
        f"SIGNAL: {signal}\nCONFIDENCE: 72\nKEY QUOTES: margin pressure; disciplined expense control; recovery in second half\n"
        "REASONING: The transcript contains language that can move investor expectations, especially around margins and demand quality. "
        "The signal should be treated as decision support, not a stock prediction."
    )
