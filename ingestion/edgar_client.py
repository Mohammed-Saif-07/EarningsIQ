import os
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup


CIK_BY_TICKER = {
    "AAPL": "0000320193", "MSFT": "0000789019", "AMZN": "0001018724",
    "GOOGL": "0001652044", "META": "0001326801", "NVDA": "0001045810",
    "TSLA": "0001318605", "JPM": "0000019617", "GS": "0000886982", "JNJ": "0000200406",
}


class EdgarClient:
    def __init__(self) -> None:
        self.user_agent = os.getenv("SEC_USER_AGENT", "Saif Mohammed smohammed8@seattleu.edu")
        self.headers = {"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate"}

    def latest_8k(self, ticker: str) -> dict:
        ticker = ticker.upper()
        if os.getenv("USE_LIVE_EDGAR", "false").lower() not in {"1", "true", "yes"}:
            return self.sample_filing(ticker)
        cik = CIK_BY_TICKER.get(ticker, "")
        if not cik:
            return self.sample_filing(ticker)
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        try:
            payload = requests.get(url, headers=self.headers, timeout=15).json()
            recent = payload.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            for index, form in enumerate(forms):
                if form == "8-K":
                    accession = recent["accessionNumber"][index]
                    filed = recent["filingDate"][index]
                    return {
                        "ticker": ticker,
                        "cik": cik,
                        "accession_number": accession,
                        "filed_at": f"{filed}T00:00:00Z",
                        "fiscal_year": int(filed[:4]),
                        "quarter": ((int(filed[5:7]) - 1) // 3) + 1,
                        "text": self.fetch_primary_document(cik, accession) or self.sample_filing(ticker)["text"],
                    }
        except requests.RequestException:
            return self.sample_filing(ticker)
        return self.sample_filing(ticker)

    def fetch_primary_document(self, cik: str, accession: str) -> str:
        accession_path = accession.replace("-", "")
        index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_path}/index.json"
        try:
            items = requests.get(index_url, headers=self.headers, timeout=15).json().get("directory", {}).get("item", [])
            html_name = next((item["name"] for item in items if item["name"].endswith((".htm", ".html", ".txt"))), "")
            if not html_name:
                return ""
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_path}/{html_name}"
            html = requests.get(doc_url, headers=self.headers, timeout=15).text
            return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        except requests.RequestException:
            return ""

    def sample_filing(self, ticker: str) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "ticker": ticker.upper(),
            "cik": CIK_BY_TICKER.get(ticker.upper(), ""),
            "accession_number": f"LOCAL-{ticker.upper()}-{now:%Y%m%d%H%M%S}",
            "filed_at": now.isoformat(),
            "fiscal_year": now.year,
            "quarter": ((now.month - 1) // 3) + 1,
            "text": (
                f"{ticker.upper()} earnings call transcript. The CEO said demand remains healthy and execution is improving. "
                "The CFO said gross margin was pressured by input costs and foreign exchange. "
                "Management noted cautious enterprise spending, longer sales cycles, and disciplined expense control. "
                "Free cash flow improved, but inventory normalization is taking longer than expected. "
                "The CFO said margin recovery should accelerate if volume returns in the second half."
            ),
        }


def get_recent_filings(ticker: str = "AAPL") -> list[dict]:
    """Return recent filing metadata using the same SEC client as the agents."""
    filing = EdgarClient().latest_8k(ticker)
    return [filing]


def fetch_transcript_text(ticker: str = "AAPL") -> str:
    """Return filing/transcript text for compatibility with smoke tests."""
    return EdgarClient().latest_8k(ticker).get("text", "")
