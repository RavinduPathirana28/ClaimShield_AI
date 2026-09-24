from app.agents.base_agent import BaseAgent
from app.database.db_manager import DBManager
from app.utils.vector_store import VectorStore
from app.utils.web_crawler import WebCrawler

class RetrievalAgent(BaseAgent):
    """
    Information Retrieval (IR) Agent. Integrates FAISS vector indexing with database
    queries and live web crawling to fetch related news articles to back up or dispute claims.
    """
    def __init__(self, db: DBManager = None, vector_store: VectorStore = None):
        super().__init__("retrieval_agent")
        self.db = db if db is not None else DBManager()
        self.vector_store = vector_store if vector_store is not None else VectorStore()
        self.web_crawler = WebCrawler()

    def handle_message(self, message: dict) -> dict:
        action = message.get("action")
        data = message.get("data", {})
        
        if action == "retrieve":
            return self._retrieve(data)
        else:
            return {
                "sender": self.name,
                "status": "error",
                "message": f"Unknown action: {action}"
            }

    def _retrieve(self, data: dict) -> dict:
        query = data.get("query", "").strip()
        try:
            limit = int(data.get("limit", 3))
        except (TypeError, ValueError):
            limit = 3

        if not query:
            return {
                "sender": self.name,
                "status": "error",
                "message": "Empty query text supplied to Retrieval Agent."
            }

        try:
            # 1. Query local FAISS Vector Store index
            results = self.vector_store.search_index(query, limit=limit)
            articles_list = self.db.get_all_articles()
            articles_map = {art["id"]: art for art in articles_list}
            
            retrieved_articles = []
            top_score = 0.0
            
            if results:
                for art_id, score in results:
                    article = articles_map.get(art_id)
                    if article:
                        enriched = article.copy()
                        enriched["score"] = score
                        retrieved_articles.append(enriched)
                if retrieved_articles:
                    top_score = retrieved_articles[0].get("score", 0.0)

            # 2. Launch the live web crawler when the query is time-sensitive (news,
            #    launches, reports), asks who currently holds an office/role, OR when
            #    local results are insufficient — so fresh evidence always reaches
            #    the verifier instead of unrelated vector matches.
            query_is_news = WebCrawler.is_time_sensitive(query) or WebCrawler.is_office_holder(query)
            if query_is_news or not retrieved_articles or top_score < 0.30:
                print(f"[Retrieval Agent] {'Time-sensitive query -> ' if query_is_news else 'Local FAISS score (' + f'{top_score:.2f}' + ') insufficient -> '}Launching Live Web Crawler for '{query}'...")
                web_results = self.web_crawler.search_and_crawl(query, limit=limit)
                
                if web_results:
                    # Check which articles already exist so repeated queries do not
                    # re-insert duplicate rows into the local database on every run.
                    existing = self.db.get_all_articles()
                    existing_urls = {str(a.get("url", "")).strip() for a in existing if a.get("url")}
                    existing_titles = {str(a.get("title", "")).strip().lower() for a in existing if a.get("title")}

                    saved_web_articles = []
                    for web_art in web_results:
                        url = str(web_art.get("url", "")).strip()
                        title = str(web_art.get("title", "")).strip()
                        is_duplicate = bool(url and url in existing_urls) or bool(title and title.lower() in existing_titles)
                        try:
                            # Save to local database so it can be vector indexed in the future
                            if not is_duplicate:
                                db_saved = self.db.add_article(
                                    title=web_art["title"],
                                    content=web_art["content"],
                                    source=web_art["source"],
                                    url=web_art["url"],
                                    date=web_art["date"]
                                )
                                web_art["id"] = db_saved.get("id", web_art.get("id", 9000))
                        except Exception as save_err:
                            print(f"[Warning] Failed to save web article to DB: {save_err}")
                            web_art.setdefault("id", 9000)

                        saved_web_articles.append(web_art)
                    
                    # Prepend live web articles so they take priority over low-score local articles
                    retrieved_articles = saved_web_articles + [a for a in retrieved_articles if a.get("score", 0.0) >= 0.30]

            return {
                "sender": self.name,
                "status": "success",
                "articles": retrieved_articles[:limit],
                "web_crawled": any("Live Web" in a.get("source", "") for a in retrieved_articles)
            }
        except Exception as e:
            return {
                "sender": self.name,
                "status": "error",
                "message": f"Retrieval failed: {e}"
            }
