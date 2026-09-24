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
        },
        {
            "title": "Donald Trump Administration and Executive Policy Overview",
            "content": "Following his victory in the 2024 United States presidential election, Donald J. Trump took office as the 47th President of the United States in January 2025. His administration has focused on federal deregulation, energy independence, border policy, and reciprocal international trade agreements.",
            "source": "Associated Press News",
            "url": "https://apnews.com/hub/donald-trump-presidency",
            "date": "2026-02-12"
        },
        {
            "title": "Global Semiconductor Manufacturing Surge as Mega-Foundries Come Online",
            "content": "Leading chip manufacturers have commenced mass production at new semiconductor fabrication plants across the United States and Europe. The new facilities produce 2-nanometer and 3-nanometer wafers aimed at bolstering supply chain resilience and powering generative AI computing clusters.",
            "source": "Reuters Technology",
            "url": "https://reuters.com/technology/semiconductor-foundries-2026",
            "date": "2026-03-05"
        },
        {
            "title": "mRNA Cancer Vaccines Complete Landmark Phase 3 Clinical Trial",
            "content": "Oncology researchers announced positive results from a international Phase 3 trial evaluating personalized mRNA therapeutic vaccines. When combined with immunotherapy, the individualized cancer vaccine reduced the risk of melanoma recurrence by 49% compared to standard care alone.",
            "source": "Nature Medicine Journal",
            "url": "https://nature.com/articles/mrna-cancer-vaccine-trial",
            "date": "2026-01-28"
        },
        {
            "title": "James Webb Space Telescope Discovers Most Distant Cosmic Structure Ever Seen",
            "content": "Astronomers utilizing the James Webb Space Telescope have spectroscopically confirmed a massive proto-cluster of galaxies existing just 320 million years after the Big Bang. The discovery challenges existing cosmological models regarding the speed of early star formation and black hole growth.",
            "source": "Astrophysical Journal",
            "url": "https://astrophysics.org/jwst-early-universe-discovery",
            "date": "2026-06-02"
        },
        {
            "title": "Federal Reserve Cuts Interest Rates Following Sustained Inflation Target Achievement",
            "content": "The Federal Open Market Committee lowered benchmark lending rates by 25 basis points after core consumer price index data demonstrated inflation had stabilized near the 2.0 percent annual target. Central bank officials noted labor market strength and balanced economic growth.",
            "source": "Wall Street Journal",
            "url": "https://wsj.com/economy/fed-rate-cut-decision-2026",
            "date": "2026-05-18"
        },
        {
            "title": "Quantum Computing Milestone: Fault-Tolerant Logical Qubits Demonstrated",
            "content": "Physics research consortiums have achieved quantum error correction thresholds with over 100 fault-tolerant logical qubits operating simultaneously. The demonstration marks a crucial transition from noisy intermediate-scale quantum devices toward commercially viable quantum algorithms in materials science.",
            "source": "MIT Technology Review",
            "url": "https://technologyreview.com/quantum-error-correction-milestone",
            "date": "2026-03-22"
        },
        {
            "title": "Renewable Electricity Surpasses Coal Generation Globally for First Time",
            "content": "The International Energy Agency reported that combined solar, wind, and hydroelectric generation accounted for more than 33% of global electricity in 2025, eclipsing coal-fired generation for the first time in industrial history. Rapid solar panel manufacturing scaling drove record additions.",
            "source": "IEA Clean Energy Report",
            "url": "https://iea.org/reports/global-electricity-renewables-2026",
            "date": "2026-04-09"
        },
        {
            "title": "NASA Artemis III Moon Landing Mission Timeline and Gateway Assembly",
            "content": "NASA and international space partners completed testing of the lunar human landing system and finalized launch readiness for Artemis lunar surface exploration. The Lunar Gateway space station modules are scheduled for orbital insertion to support sustained human presence on the South Pole of the Moon.",
            "source": "NASA Space Flight Daily",
            "url": "https://nasa.gov/artemis/lunar-landing-update",
            "date": "2026-07-14"
        },
        {
            "title": "European Union Enforces Full Compliance with Comprehensive Artificial Intelligence Act",
            "content": "Regulatory bodies across the European Union have initiated statutory auditing for high-risk AI deployments under the EU AI Act. Technology providers must demonstrate transparency in foundation model training datasets, rigorous safety benchmarks, and mandatory watermarking for synthetic audiovisual media.",
            "source": "Financial Times",
            "url": "https://ft.com/tech/eu-ai-act-compliance-enforcement",
            "date": "2026-02-25"
        },
        {
            "title": "Solid-State Battery Breakthrough Enables 10-Minute EV Fast Charging",
            "content": "Automotive battery scientists published verification of a solid-electrolyte cell delivering 1,000 charging cycles with zero dendrite formation. The solid-state technology promises 800-kilometer electric vehicle range alongside 10-minute fast charging from 10% to 80% capacity.",
            "source": "Automotive Engineering Journal",
            "url": "https://autoengineering.org/solid-state-battery-breakthrough",
            "date": "2026-05-30"
        },
        {
            "title": "Mediterranean Diet Confirmed to Lower Dementia and Cognitive Decline Risk",
            "content": "A twenty-year observational study tracking 25,000 adults confirmed that high adherence to an olive oil and whole-grain Mediterranean diet correlates with a 30% reduction in dementia progression, attributed to polyphenols and anti-inflammatory vascular benefits.",
            "source": "British Medical Journal",
            "url": "https://bmj.com/content/mediterranean-diet-cognition",
            "date": "2026-01-15"
        },
        {
            "title": "Post-Quantum Cryptography: NIST Releases Finalized Data Encryption Standards",
            "content": "The National Institute of Standards and Technology officially released finalized post-quantum cryptographic algorithms designed to withstand future quantum computer decrypting capabilities. Government agencies and financial institutions are mandated to begin protocol migration immediately.",
            "source": "Cyber Defense Magazine",
            "url": "https://cyberdefensemag.com/nist-pqc-standards-finalized",
            "date": "2026-04-29"
        },
        {
            "title": "Urban Vertical Farming Reduces Agricultural Water Consumption by 95%",
            "content": "Controlled-environment vertical agriculture facilities across metropolitan centers have achieved commercial scale, producing leafy greens and produce using closed-loop aeroponic systems that require 95% less water and zero chemical pesticides compared to conventional farming.",
            "source": "AgriTech Innovations",
            "url": "https://agritech.com/vertical-farming-water-efficiency",
            "date": "2026-06-20"
        },
        {
            "title": "Commercial Transatlantic Flight Successfully Powered by 100% Sustainable Biofuel",
            "content": "A major passenger airliner completed a scheduled commercial flight across the Atlantic using 100% drop-in sustainable aviation fuel derived from waste lipids. Exhaust monitoring demonstrated a 70% lifecycle greenhouse gas emission reduction compared to conventional fossil jet kerosene.",
            "source": "Aviation International News",
            "url": "https://ainonline.com/aviation-news/100-percent-saf-transatlantic",
            "date": "2026-03-14"
        },
        {
            "title": "Deep-Ocean Hydrothermal Ecosystems Unveil New Extremophile Microorganisms",
            "content": "Oceanographic expedition submersibles exploring Mariana Trench seafloor volcanic vents discovered previously catalogued extremophile bacterial colonies utilizing chemosynthesis in superheated mineral-rich fluids, offering new avenues for industrial enzyme synthesis.",
            "source": "Deep Sea Research",
            "url": "https://deepsearesearch.org/hydrothermal-extremophiles",
            "date": "2026-07-08"
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
        {"username": "pro", "password": "password", "role": "pro"},
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
