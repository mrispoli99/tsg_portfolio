"""
news_pipeline.py
================
Fetches recent news for each portfolio company via Google News RSS
and stores results in dbo.ts_company_news.

Run daily via Windows Task Scheduler AFTER the main pipeline:
    python news_pipeline.py

SQL table required (run once):
    CREATE TABLE dbo.ts_company_news (
        news_id         BIGINT IDENTITY(1,1) PRIMARY KEY,
        company_name    NVARCHAR(500),
        entity_id       NVARCHAR(100),
        title           NVARCHAR(1000),
        summary         NVARCHAR(MAX),
        published       DATETIME2,
        link            NVARCHAR(2000),
        source          NVARCHAR(200),
        fetched_at      DATETIME2 DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX IX_ts_company_news_company ON dbo.ts_company_news(company_name, published DESC);
"""

import feedparser
import logging
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

from sqlalchemy import text
from db import get_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("news_pipeline")

# Search terms per company — add brand names, ticker symbols etc.
# If a company isn't listed here it falls back to the company name itself
COMPANY_SEARCH_OVERRIDES = {
    "Rough Country":         "Rough Country truck accessories",
    "Radiance Holdings":     "Radiance Holdings beauty",
    "Summer Fridays":        "Summer Fridays skincare",
    "Revolut":               "Revolut fintech",
    "Thrive Pet Healthcare": "Thrive Pet Healthcare",
    "Wrench Group":          "Wrench Group auto repair",
    "Trinity Solar":         "Trinity Solar energy",
    "BrewDog":               "BrewDog brewery",
    "Mavis":                 "Mavis Discount Tire",
    "PowerStop":             "PowerStop brakes",
    "Endeavor":              "Endeavor Education Schools",
    "Core Power":            "Core Power Yoga",
    "Hempz":                 "Hempz beauty",
    "Cadogan Tate":          "Cadogan Tate removals",
    "Legacy":                "Legacy.com",
    "ATI":                   "ATI physical therapy",
}

DAYS_LOOKBACK = 30  # Only keep articles from last 30 days


def clean_html(text: str) -> str:
    """Strip HTML tags from RSS summary."""
    return re.sub(r"<[^>]+>", "", text or "").strip()


def parse_date(entry) -> datetime:
    """Parse RSS date to UTC datetime."""
    try:
        if hasattr(entry, "published"):
            return parsedate_to_datetime(entry.published).astimezone(timezone.utc)
    except Exception:
        pass
    return datetime.now(timezone.utc)


def fetch_news_for_company(company_name: str, entity_id: str) -> list:
    """Fetch up to 15 recent articles for a company via Google News RSS."""
    search_term = COMPANY_SEARCH_OVERRIDES.get(company_name, company_name)
    url = f"https://news.google.com/rss/search?q={search_term.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"

    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_LOOKBACK)
    articles = []

    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:15]:
            pub_date = parse_date(entry)
            if pub_date < cutoff:
                continue
            source = entry.get("source", {}).get("title", "") if hasattr(entry, "source") else ""
            articles.append({
                "company_name": company_name,
                "entity_id":    entity_id,
                "title":        (entry.title or "")[:1000],
                "summary":      clean_html(entry.get("summary", ""))[:2000],
                "published":    pub_date.replace(tzinfo=None),  # strip tz for SQL Server
                "link":         (entry.link or "")[:2000],
                "source":       source[:200],
            })
    except Exception as exc:
        logger.warning("  Failed to fetch news for %s: %s", company_name, exc)

    return articles


def run():
    engine = get_engine()
    logger.info("=== News Pipeline START ===")

    # Load portfolio companies from DB
    with engine.connect() as conn:
        companies = conn.execute(text(
            "SELECT entity_id, name FROM dbo.ts_entities WHERE type = 'Portfolio Company' AND status = 'ACTIVE'"
        )).fetchall()

    logger.info("Fetching news for %d companies ...", len(companies))
    total_inserted = 0

    with engine.begin() as conn:
        for entity_id, company_name in companies:
            articles = fetch_news_for_company(company_name, entity_id)

            if not articles:
                logger.info("  %-30s → 0 articles", company_name)
                continue

            # Delete existing articles for this company before re-inserting
            conn.execute(text(
                "DELETE FROM dbo.ts_company_news WHERE company_name = :name"
            ), {"name": company_name})

            # Insert fresh articles
            for a in articles:
                conn.execute(text("""
                    INSERT INTO dbo.ts_company_news
                        (company_name, entity_id, title, summary, published, link, source)
                    VALUES
                        (:company_name, :entity_id, :title, :summary, :published, :link, :source)
                """), a)

            total_inserted += len(articles)
            logger.info("  %-30s → %d articles", company_name, len(articles))

    logger.info("=== News Pipeline DONE — %d total articles stored ===", total_inserted)


if __name__ == "__main__":
    run()
