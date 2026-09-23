import sys
import os
import sqlite3
from app.database.db_manager import DBManager
from app.utils.vector_store import VectorStore
from app.utils.security import hash_password
from app import config

# Add the root directory to path to enable package import if run from terminal
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def clear_sqlite_db():
    """Clears SQLite data for a fresh seeding cycle."""
    try:
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM articles")
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM verification_logs")
        conn.commit()
        conn.close()
        print("[Seed] Local Database: Cleared existing tables.")
    except Exception as e:
        print(f"[Seed] Local Database: Failed to clear SQLite tables: {e}")

def seed():
    print("[Seed] Starting database seeding process...")
    
    # 1. Clear local DB if using SQLite
    db = DBManager()
    if not db.use_supabase:
        clear_sqlite_db()
    
    # 2. Add sample news articles to the corpus
    sample_articles = [
        {
            "title": "Apple's Roadmap: No iPhone 18 planned until 2027",
            "content": "Speculation regarding an iPhone 18 release in 2026 is false. Apple plans to stick to its annual cycle, releasing the iPhone 16 in 2024, iPhone 17 in 2025, and iPhone 18 in late 2027. There will be no July 2026 launch.",
            "source": "TechNews Daily",
            "url": "https://technews.com/iphone-18-roadmap",
            "date": "2026-06-15"
        },
        {
            "title": "Coffee Consumption and Cardiovascular Health: A Long-term Cohort Study",
            "content": "Medical research shows that drinking 2-3 cups of coffee daily can improve longevity indicators. Large-scale cohort studies associate moderate coffee consumption with a significantly lower risk of stroke and cardiovascular disease.",
            "source": "Lancet Health Review",
            "url": "https://lancet.com/coffee-longevity-study",
            "date": "2025-11-20"
        },
        {
            "title": "Apple Valuation Milestone Reached Following Record Q2 Earnings Report",
            "content": "Apple's market value crossed the milestone threshold today. The tech giant recorded unprecedented revenue growth driven by strong cloud services subscription and hardware demand.",
            "source": "Bloomberg Finance",
            "url": "https://bloomberg.com/apple-record-q2",
            "date": "2026-05-10"
        },
        {
            "title": "Local Council Announces Smart Infrastructure Funding Package",
            "content": "A major urban initiative was launched today. The local city council approved a 50 million funding package targeting traffic decongestion, intelligent streetlight matrices, and free community Wi-Fi nodes.",
            "source": "Metro Ledger",
            "url": "https://metroledger.com/smart-city-funding",
            "date": "2026-07-01"
        },
        {
            "title": "Climate Change Accelerated Glacial Melt in Greenland, Study Finds",
            "content": "A multi-year tracking study by geological researchers confirms Greenland's glaciers are melting 15% faster than in the previous decade, threatening global sea level projections by the year 2050.",
            "source": "Scientific Earth",
            "url": "https://scientificearth.org/glacial-melt-greenland",
            "date": "2026-04-18"
        }
    ]
    
    seeded_articles = []
    for art in sample_articles:
        try:
            # Check if using SQLite, check if already exists to prevent duplicate seeding in Supabase
            existing = False
            if db.use_supabase:
                try:
                    res = db.supabase_client.table("articles").select("*").eq("title", art["title"]).execute()
                    if res.data:
                        seeded_articles.append(res.data[0])
                        existing = True
                except Exception:
                    pass
            
            if not existing:
                added = db.add_article(
                    title=art["title"],
                    content=art["content"],
                    source=art["source"],
                    url=art["url"],
                    date=art["date"]
                )
                seeded_articles.append(added)
                print(f"[Seed] Added article: '{art['title']}'")
        except Exception as e:
            print(f"[Seed] Failed to seed article '{art['title']}': {e}")

    # 3. Rebuild the FAISS index with the loaded articles
    print("\n[Seed] Building vector embeddings and creating FAISS index...")
    vs = VectorStore()
    success = vs.build_index(seeded_articles)
    if success:
        print("[Seed] Vector index successfully updated.")
    else:
        print("[Seed] Failed to build vector index.")

    # 4. Seed default test accounts representing different subscription tiers
    test_users = [
        {"username": "user", "password": "password", "role": "user"},
        {"username": "premium", "password": "premium", "role": "premium"},
        {"username": "newsroom", "password": "newsroom", "role": "newsroom_admin"}
    ]
    
    print("\n[Seed] Creating system test accounts...")
    for u in test_users:
        try:
            # Check if user already exists
            existing_user = db.get_user(u["username"])
            if existing_user:
                print(f"[Seed] User '{u['username']}' already exists. Skipping creation.")
                continue

            hashed = hash_password(u["password"])
            db.create_user(u["username"], hashed, u["role"])
            print(f"[Seed] Registered user '{u['username']}' (Role: {u['role']})")
        except Exception as e:
            print(f"[Seed] Failed to register user '{u['username']}': {e}")
            
    print("\n[Seed] Database Seeding Complete!")

if __name__ == "__main__":
    seed()
