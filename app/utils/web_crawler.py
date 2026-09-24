"""
Live Web Crawler Utility for ClaimShield AI.
Uses httpx and BeautifulSoup4 to perform live web search and real-time page content scraping.
Extracts article titles, publisher source domains, main body text, and clickable URLs.

Search strategy (free, no keys):
1. Google News RSS first for time-sensitive queries — fresh headlines with real publish dates.
2. DuckDuckGo Lite as the general fallback (fast; may return cached snippets).
3. Wikipedia OpenSearch as the final fallback for general knowledge.
"""

import time
import re
import datetime
from urllib.parse import quote_plus, urlparse, unquote
from bs4 import BeautifulSoup

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


# Heuristic: does the query look time-sensitive (news/recent events)?
TIME_SENSITIVE_PATTERN = re.compile(
    r"\b(19|20)\d{2}\b"                                  # a year
    r"|\b(?:releas\w*|launch\w*|announc\w*|unveil\w*|reportedly|reported|"
    r"breaking|latest|upcoming|expected|plans|patent|prototype|earnings|"
    r"quarterl\w*|election|verdict|debuted|shipping|shipped|introduc\w*)\b"
    r"|\b(?:this\s+(?:week|month|year|quarter)|yesterday|today|tomorrow)\b",
    re.IGNORECASE,
)

# Headlines that CONFIRM something happened (launch/unveil/debut announcements).
_DEFINITIVE_PATTERN = re.compile(
    r"\b(unveil\w*|launch\w*|debut\w*|announc\w*|official|first\b|introduc\w*|"
    r"releases?\b|join\w* the |enter\w* the |now available|go\w*\s+on sale|"
    r"went\s+on\s+sale|available to|shipping|shipped|released)\b",
    re.IGNORECASE,
)

# Headlines that only PREVIEW/RUMOR something (lead-up framing, not finality).
_RUMOR_PATTERN = re.compile(
    r"\b(rumou?rs?\b|everything\s+we\s+know|what\s+we\s+know|upcoming|expected|"
    r"reportedly|could\b|might\b|maybe\b|when\b|before\b|ahead of|leak\w*|"
    r"teas\w*|hint\w*|wishlist|concept|roundup|guide|recap|overview|"
    r"worst|loved|forgot|mistake|think twice)\b",
    re.IGNORECASE,
)

class WebCrawler:
    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 ClaimShieldAI/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }

    @staticmethod
    def is_time_sensitive(query: str) -> bool:
        """True when a query is about recent news, launches, or reported events."""
        return bool(query.strip()) and bool(TIME_SENSITIVE_PATTERN.search(query))

    @staticmethod
    def _headline_signal(title: str, snippet: str) -> int:
        """+1 for confirmed-event headlines, -1 for rumor/preview framing, else 0."""
        text = f"{title or ''} {snippet or ''}"
        boost = 1 if bool(_DEFINITIVE_PATTERN.search(text)) else 0
        demote = 1 if bool(_RUMOR_PATTERN.search(text)) else 0
        return boost - demote

    def search_and_crawl(self, query: str, limit: int = 3) -> list:
        """
        Executes a live web search for the query, crawls target web pages,
        and returns clean article objects. Articles are newest-first.
        """
        if not query.strip() or not HTTPX_AVAILABLE:
            return []

        search_candidates = self._gather_candidates(query, limit)  # (url, title, snippet, published_date_iso, source_hint_url)

        # Finality-aware ranking: heads-ups that already happened (unveils, launches)
        # win the evidence slots; rumor/preview roundups only fill gaps. Newest first
        # within each group; unknown dates sink to the bottom.
        search_candidates.sort(
            key=lambda c: (self._headline_signal(c[1], c[2]), c[3] or "0000-00-00"),
            reverse=True,
        )
        search_candidates = search_candidates[:limit]

        articles = []
        for idx, (url, initial_title, snippet, published_date, source_hint) in enumerate(search_candidates):
            article_data = self._crawl_page(
                url, idx + 1,
                fallback_snippet=snippet,
                fallback_title=initial_title,
                published_date=published_date,
                source_hint_url=source_hint,
            )
            if article_data:
                articles.append(article_data)

        return articles

    def _gather_candidates(self, query: str, limit: int) -> list:
        """Collects raw search results across sources before any page crawling.

        For time-sensitive queries, searches Google News with both the raw query
        and a 'launch release news' variant so a definitive article reliably lands
        in the pool even when headline framing varies. Deduplicates by URL and by
        near-identical headlines.
        """
        out = []
        time_sensitive = WebCrawler.is_time_sensitive(query)

        if time_sensitive:
            variants = [query]
            if not query.rstrip().lower().endswith(("launch", "release", "news")):
                variants.append(f"{query} launch release news")
            for variant in variants:
                if len(out) >= limit:
                    break
                self._search_google_news(variant, max(limit, 3), out)
            if len(out) < limit:
                self._search_duckduckgo(query, limit, out)
        else:
            self._search_duckduckgo(query, limit, out)
            if len(out) < limit:
                self._search_google_news(query, max(limit, 3), out)

        if not out:
            self._search_wikipedia(query, limit, out)

        # Drop near-identical headlines (same story surfaced by both variants).
        seen_titles = set()
        deduped = []
        for cand in out:
            norm_title = (cand[1] or "").lower().strip()
            if not norm_title:
                deduped.append(cand)
                continue
            key = norm_title[:60]
            if key in seen_titles:
                continue
            seen_titles.add(key)
            deduped.append(cand)
        return deduped

    def _search_google_news(self, query: str, limit: int, out: list) -> None:
        """Fresh news headlines with real publish dates via Google News RSS."""
        try:
            rss_url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
            with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                resp = None
                for attempt in (0, 1):  # one retry to ride out transient throttling
                    try:
                        resp = client.get(rss_url)
                        if resp.status_code == 200:
                            break
                    except Exception:
                        resp = None
                    if attempt == 0:
                        time.sleep(0.5)
                if resp is None or resp.status_code != 200:
                    print(f"[Web Crawler] Google News RSS unavailable ({resp.status_code if resp else 'error'}) for '{query}'. Falling back.")
                    return
                soup = BeautifulSoup(resp.text, "xml")
                for item in soup.find_all("item")[: limit * 2]:
                    title = item.title.text.strip() if item.title else ""
                    link = item.link.text.strip() if item.link else ""
                    desc = BeautifulSoup(item.description.text, "html.parser").get_text(strip=True) if item.description else ""
                    pub_date = ""
                    if item.pubDate:
                        try:
                            parsed = datetime.datetime.strptime(
                                item.pubDate.text.strip(), "%a, %d %b %Y %H:%M:%S %Z")
                            pub_date = parsed.strftime("%Y-%m-%d")
                        except Exception:
                            pass
                    if not pub_date:
                        pub_date = time.strftime("%Y-%m-%d", time.gmtime())

                    # Real publisher URL (used for labelling when deep crawl is blocked)
                    source_hint = ""
                    if hasattr(item, "source") and item.source is not None:
                        src_url = item.source.get("url", "")
                        if src_url and src_url.startswith("http"):
                            source_hint = src_url

                    if not link:
                        continue
                    if not any(c[0] == link for c in out):
                        out.append((link, title, desc, pub_date, source_hint))
                        if len(out) >= limit * 2:
                            break
        except Exception as e:
            print(f"[Web Crawler] Google News RSS note: {e}")

    def _search_duckduckgo(self, query: str, limit: int, out: list) -> None:
        """DuckDuckGo Lite search fallback (no javascript / bot challenges)."""
        try:
            today = time.strftime("%Y-%m-%d", time.gmtime())
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
                            if not any(c[0] == clean_url for c in out):
                                out.append((clean_url, title, snippet, today, ""))
                                if len(out) >= limit * 2:
                                    break
        except Exception as e:
            print(f"[Web Crawler] DuckDuckGo search note: {e}")

    def _search_wikipedia(self, query: str, limit: int, out: list) -> None:
        """Wikipedia OpenSearch fallback for general knowledge."""
        try:
            today = time.strftime("%Y-%m-%d", time.gmtime())
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
                        if not any(c[0] == u for c in out):
                            out.append((u, t, s, today, ""))
        except Exception as e:
            print(f"[Web Crawler] Wikipedia search note: {e}")

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

    def _crawl_page(self, url: str, item_id: int, fallback_snippet: str = "",
                    fallback_title: str = "", published_date: str = "",
                    source_hint_url: str = "") -> dict:
        """Scrapes and extracts main text from a web page with fallback to snippet."""
        date_str = published_date or time.strftime("%Y-%m-%d", time.gmtime())
        final_url = url
        title = fallback_title or f"Web Article ({urlparse(url).netloc.replace('www.', '').capitalize() or 'Web Source'})"
        body_text = ""
        deep_crawl_ok = False

        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    final_url = str(resp.url)
                    deep_crawl_ok = True
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
        used_snippet = False
        if not body_text or len(body_text) < 30:
            if fallback_snippet and len(fallback_snippet) >= 20:
                body_text = fallback_snippet
                used_snippet = True
            else:
                return None

        # When we fell back to the snippet, trust the search engine's headline
        # (e.g. Google News' "Headline - Publisher") over an interstitial title.
        if used_snippet and fallback_title:
            title = fallback_title[:120]

        # Prefer the resolved publisher domain; fall back to the Google News
        # <source url=...> hint when the deep crawl was blocked or unresolved.
        label_url = final_url if deep_crawl_ok and "news.google.com" not in urlparse(final_url).netloc else source_hint_url or final_url
        domain = urlparse(label_url).netloc.replace("www.", "").capitalize() or "News"
        return {
            "id": 9000 + item_id,
            "title": title,
            "content": body_text[:700] + ("..." if len(body_text) >= 700 else ""),
            "source": f"Live Web ({domain})",
            "url": final_url,
            "date": date_str,
            "score": 0.85
        }