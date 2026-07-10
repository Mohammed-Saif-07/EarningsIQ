import os
import re
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
            raise ValueError(f"No CIK configured for ticker {ticker}")
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        response = requests.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()
        recent = response.json().get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        items = recent.get("items", [])
        candidates = [
            index for index, form in enumerate(forms)
            if form == "8-K" and (
                not items
                or "2.02" in str(items[index])
                or "Results of Operations" in str(items[index])
            )
        ]
        candidates.extend(index for index, form in enumerate(forms) if form == "8-K" and index not in candidates)
        for index in candidates:
            accession = recent["accessionNumber"][index]
            filed = recent["filingDate"][index]
            text = self.fetch_primary_document(cik, accession)
            if len(text.split()) < 50:
                continue
            return {
                "ticker": ticker,
                "cik": cik,
                "accession_number": accession,
                "filed_at": f"{filed}T00:00:00Z",
                "fiscal_year": int(filed[:4]),
                "quarter": ((int(filed[5:7]) - 1) // 3) + 1,
                "text": text,
            }
        raise RuntimeError(f"No usable live SEC 8-K text found for {ticker}")

    def fetch_primary_document(self, cik: str, accession: str) -> str:
        accession_path = accession.replace("-", "")
        index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_path}/index.json"
        response = requests.get(index_url, headers=self.headers, timeout=20)
        response.raise_for_status()
        items = response.json().get("directory", {}).get("item", [])
        html_items = [
            item for item in items
            if item.get("name", "").lower().endswith((".htm", ".html", ".txt"))
            and "index" not in item.get("name", "").lower()
            and not item.get("name", "").lower().startswith(("r1.", "report.", "show."))
            and not item.get("name", "").lower().endswith((".xml", ".xsd"))
        ]
        if not html_items:
            return ""
        exhibit_items = [item for item in html_items if self._document_rank(item)[0] > 0]
        if exhibit_items:
            html_items = exhibit_items
        html_items.sort(key=self._document_rank, reverse=True)
        texts: list[str] = []
        for item in html_items[:2]:
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_path}/{item['name']}"
            doc_response = requests.get(doc_url, headers=self.headers, timeout=20)
            doc_response.raise_for_status()
            text = self.clean_document_text(doc_response.text)
            if len(text.split()) >= 50:
                texts.append(text)
        return "\n\n".join(texts)

    @staticmethod
    def _document_rank(item: dict) -> tuple[int, int]:
        name = item.get("name", "").lower()
        size = int(item.get("size") or 0)
        exhibit = 2 if re.search(r"(ex[-_]?99|ex99|ex991|ex-991)", name) else 0
        primary = 1 if name.endswith((".htm", ".html")) else 0
        return exhibit, primary, size

    @staticmethod
    def clean_document_text(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "ix:header", "xbrl"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

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
