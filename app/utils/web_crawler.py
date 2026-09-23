"""
Live Web Crawler Utility for ClaimShield AI.
Uses httpx and BeautifulSoup4 to perform live web search and real-time page content scraping.
Extracts article titles, publisher source domains, main body text, and clickable URLs.
"""

import time
import re
from urllib.parse import quote_plus, urlparse, unquote
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 ClaimShieldAI/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }

    def search_and_crawl(self, query: str, limit: int = 3) -> list:
        """
        Executes a live web search for the query, crawls target web pages,
        and returns clean article objects.
        """
        if not query.strip() or not HTTPX_AVAILABLE:
            return []

        search_candidates = []  # list of tuples: (url, title, snippet)

        # 1. DuckDuckGo Lite search (fast, reliable, no javascript or bot challenges)
        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                resp = client.post("https://lite.duckduckgo.com/lite/", data={"q": query})
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    link_tags = soup.select(".result-link")
                    snippet_tags = soup.select(".result-snippet")
                    
                    for i in range(len(link_tags)):
                        raw_href = link_tags[i].get("href", "")
                        clean_url = self._extract_clean_url(raw_href)
                        title = link_tags[i].get_text(strip=True)
                        snippet = snippet_tags[i].get_text(strip=True) if i < len(snippet_tags) else ""
                        
                        if clean_url and clean_url.startswith("http") and not clean_url.endswith(".pdf"):
                            if not any(c[0] == clean_url for c in search_candidates):
                                search_candidates.append((clean_url, title, snippet))
                                if len(search_candidates) >= limit * 2:
                                    break
        except Exception as e:
            print(f"[Web Crawler] DuckDuckGo search note: {e}")

        # 2. Google News RSS search fallback if candidates are insufficient
        if len(search_candidates) < limit:
            try:
                news_rss = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
                with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                    resp = client.get(news_rss)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "xml")
                        for item in soup.find_all("item")[:limit]:
                            title = item.title.text.strip() if item.title else ""
                            link = item.link.text.strip() if item.link else ""
                            desc = BeautifulSoup(item.description.text, "html.parser").get_text(strip=True) if item.description else ""
                            if link and not any(c[0] == link for c in search_candidates):
                                search_candidates.append((link, title, desc))
            except Exception as e:
                print(f"[Web Crawler] Google News RSS note: {e}")

        # 3. Wikipedia OpenSearch API fallback if still empty
        if not search_candidates:
            try:
                wiki_api = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote_plus(query)}&limit={limit}&namespace=0&format=json"
                with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                    resp = client.get(wiki_api)
                    if resp.status_code == 200:
                        data = resp.json()
                        titles = data[1] if len(data) > 1 else []
                        snippets = data[2] if len(data) > 2 else []
                        urls = data[3] if len(data) > 3 else []
                        for i in range(len(urls)):
                            u = urls[i]
                            t = titles[i] if i < len(titles) else query
                            s = snippets[i] if i < len(snippets) else ""
                            search_candidates.append((u, t, s))
            except Exception as e:
                print(f"[Web Crawler] Wikipedia search note: {e}")

        # Crawl target pages with snippet fallback
        articles = []
        for idx, (url, initial_title, snippet) in enumerate(search_candidates[:limit]):
            article_data = self._crawl_page(url, idx + 1, fallback_snippet=snippet, fallback_title=initial_title)
            if article_data:
                articles.append(article_data)

        return articles

    def _extract_clean_url(self, raw_url: str) -> str:
        """Cleans DuckDuckGo redirect URL parameters."""
        if "uddg=" in raw_url:
            match = re.search(r"uddg=([^&]+)", raw_url)
            if match:
                return unquote(match.group(1))
        if raw_url.startswith("//"):
            return "https:" + raw_url
        if raw_url.startswith("http"):
            return raw_url
        return ""

    def _crawl_page(self, url: str, item_id: int, fallback_snippet: str = "", fallback_title: str = "") -> dict:
        """Scrapes and extracts main text from a web page with fallback to snippet."""
        domain = urlparse(url).netloc.replace("www.", "").capitalize() or "Web Source"
        date_str = time.strftime("%Y-%m-%d", time.gmtime())
        title = fallback_title or f"Web Article ({domain})"
        body_text = ""

        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")

                    # Remove non-content elements
                    for elem in soup(["script", "style", "nav", "header", "footer", "aside"]):
                        elem.decompose()

                    # Extract title
                    title_tag = soup.find("h1") or soup.find("title")
                    if title_tag and title_tag.get_text().strip():
                        title = re.sub(r"\s+", " ", title_tag.get_text().strip())[:120]

                    # Extract main content paragraphs
                    paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 30]
                    extracted = " ".join(paragraphs[:6])
                    body_text = re.sub(r"\s+", " ", extracted)

                    if len(body_text) < 50:
                        raw_body = soup.get_text()
                        body_text = re.sub(r"\s+", " ", raw_body)[:500]
        except Exception as e:
            print(f"[Web Crawler] Deep crawl note on '{url}': {e}")

        # If live deep crawl was empty, blocked, or timed out, use the search snippet
        if not body_text or len(body_text) < 30:
            if fallback_snippet and len(fallback_snippet) >= 20:
                body_text = fallback_snippet
            else:
                return None

        return {
            "id": 9000 + item_id,
            "title": title,
            "content": body_text[:700] + ("..." if len(body_text) >= 700 else ""),
            "source": f"Live Web ({domain})",
            "url": url,
            "date": date_str,
            "score": 0.85
        }
