const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

export const api = {
  transcripts: () => fetchJson<Array<Record<string, unknown>>>("/transcripts"),
  transcript: (ticker: string) => fetchJson<Record<string, unknown>>(`/transcripts/${ticker}`),
  sentiment: (ticker: string) => fetchJson<Record<string, unknown>>(`/sentiment/${ticker}`),
  signals: () => fetchJson<Array<Record<string, unknown>>>("/signals"),
  signal: (ticker: string) => fetchJson<Record<string, unknown>>(`/signals/${ticker}`),
  ask: (ticker: string, question: string) =>
    fetchJson<Record<string, unknown>>("/qa", { method: "POST", body: JSON.stringify({ ticker, question }) })
};
