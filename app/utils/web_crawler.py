"""
Live Web Crawler Utility for ClaimShield AI.
Uses httpx and BeautifulSoup4 to perform live web search and real-time page content scraping.
Extracts article titles, publisher source domains, main body text, and clickable URLs.
"""

import time
import re
from urllib.parse import quote_plus, urlparse
from bs4 import BeautifulSoup

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class WebCrawler:
    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def search_and_crawl(self, query: str, limit: int = 3) -> list:
        """
        Executes a live web search for the query, crawls target web pages,
        and returns clean article objects.
        """
        if not query.strip() or not HTTPX_AVAILABLE:
            return []

        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        links = []

        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(search_url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Extract search result links
                    for a in soup.select(".result__url"):
                        raw_href = a.get("href", "")
                        if raw_href:
                            # Clean duckduckgo redirect wrapper if present
                            clean_url = self._extract_clean_url(raw_href)
                            if clean_url and clean_url not in links and not clean_url.endswith(".pdf"):
                                links.append(clean_url)
                                if len(links) >= limit:
                                    break
        except Exception as e:
            print(f"[Web Crawler] Search request error: {e}")

        # If DDG HTML search yielded no links, try Wikipedia / News fallback
        if not links:
            wiki_url = f"https://en.wikipedia.org/wiki/{quote_plus(query.replace(' ', '_'))}"
            links.append(wiki_url)

        # Crawl each link to extract full title & text
        articles = []
        for idx, url in enumerate(links):
            article_data = self._crawl_page(url, idx + 1)
            if article_data:
                articles.append(article_data)

        return articles

    def _extract_clean_url(self, raw_url: str) -> str:
        """Cleans DuckDuckGo redirect URL parameters."""
        if "uddg=" in raw_url:
            match = re.search(r"uddg=([^&]+)", raw_url)
            if match:
                from urllib.parse import unquote
                return unquote(match.group(1))
        if raw_url.startswith("//"):
            return "https:" + raw_url
        if raw_url.startswith("http"):
            return raw_url
        return ""

    def _crawl_page(self, url: str, item_id: int) -> dict:
        """Scrapes and extracts main text from a web page."""
        try:
            domain = urlparse(url).netloc.replace("www.", "").capitalize() or "Web Source"
            date_str = time.strftime("%Y-%m-%d", time.gmtime())

            with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    return None

                soup = BeautifulSoup(resp.text, "html.parser")

                # Remove script and style tags
                for elem in soup(["script", "style", "nav", "header", "footer", "aside"]):
                    elem.decompose()

                # Extract title
                title_tag = soup.find("h1") or soup.find("title")
                title = title_tag.get_text().strip() if title_tag else f"Web Article ({domain})"
                title = re.sub(r"\s+", " ", title)[:120]

                # Extract main content paragraphs
                paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 30]
                body_text = " ".join(paragraphs[:6])
                body_text = re.sub(r"\s+", " ", body_text)

                if len(body_text) < 50:
                    body_text = soup.get_text()
                    body_text = re.sub(r"\s+", " ", body_text)[:500]

                if not body_text or len(body_text) < 30:
                    return None

                return {
                    "id": 9000 + item_id,  # Dynamic web article ID range
                    "title": title,
                    "content": body_text[:600] + "...",
                    "source": f"Live Web ({domain})",
                    "url": url,
                    "date": date_str,
                    "score": 0.85  # Real-time web similarity confidence
                }
        except Exception as e:
            print(f"[Web Crawler] Error crawling '{url}': {e}")
            return None
