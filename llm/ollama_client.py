import os
import requests


def ollama_chat(prompt: str) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3")
    try:
        response = requests.post(f"{base_url}/api/generate", json={"model": model, "prompt": prompt, "stream": False}, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.RequestException:
        from llm.groq_client import local_report
        return local_report(prompt)
