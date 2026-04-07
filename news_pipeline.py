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

# news_pipeline.py must be run from the TSGPortfolio folder alongside utils.py
# i.e.: cd C:\Users\TSGDW\OneDrive\Documents\TSGPortfolio && python news_pipeline.py
try:
    from utils import get_engine
except ImportError:
    raise ImportError(
        "Cannot find utils.py. Run news_pipeline.py from the TSGPortfolio folder:\n"
        "  cd C:\\Users\\TSGDW\\OneDrive\\Documents\\TSGPortfolio\n"
        "  python news_pipeline.py"
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("news_pipeline")

# Search terms per company.
# Use the most specific query possible — include brand descriptor, sector,
# or parent company name to avoid false positives on ambiguous names.
# Format: "Company Name": ("search query", ["required keywords"], ["exclude keywords"])
#   - search query:       what to send to Google News RSS
#   - required keywords:  at least ONE must appear in title OR summary (empty = no filter)
#   - exclude keywords:   if ANY appear in title OR summary, article is dropped
# ─────────────────────────────────────────────────────────────────────────────
# COMPANY_NEWS_CONFIG
# Each entry: (search_query, required_keywords, exclude_keywords)
#   search_query:      Sent to Google News RSS. Use quotes + descriptors for precision.
#   required_keywords: At least ONE must appear in title+summary. Empty = no requirement.
#   exclude_keywords:  ANY match drops the article. Be specific to avoid over-filtering.
#
# STRATEGY:
#   1. Make the search query as specific as possible (quoted brand name + sector descriptor)
#   2. required_keywords ensure the result is actually about the right company/industry
#   3. exclude_keywords block known false positives (other companies with same name)
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# COMPANY_NEWS_CONFIG
# Each entry: (search_query, required_keywords, exclude_keywords)
#
# STRATEGY FOR TIGHT FILTERING:
#   1. search_query: Always quote the FULL brand name. Add sector descriptor.
#   2. required_keywords: Use the MOST specific terms (exact brand name preferred).
#      At least one MUST appear — this is the primary relevance gate.
#   3. exclude_keywords: Block all known false-positive company names and topics.
#
# KEY RULE: If the company name is ambiguous (ATI, Legacy, Endeavor, etc.),
# the FULL brand name must appear as a required keyword — not just sector words.
# ─────────────────────────────────────────────────────────────────────────────
COMPANY_NEWS_CONFIG = {

    # ── HIGH AMBIGUITY — full brand name required ─────────────────────────────

    "ATI": (
        # Use full brand name only — never bare "ATI"
        '"ATI Aesthetics"',
        # REQUIRED: full brand name must appear — rejects ATI Physical Therapy, AMD, etc.
        ["ati aesthetics"],
        # Belt-and-suspenders exclusions for anything that slips through
        ["physical therapy", "allegheny technologies", "amd", "radeon", "gpu",
         "graphics card", "semiconductor", "orthopedic", "rehabilitation",
         "sports medicine", "pt clinic", "ati inc", "ati metals"]
    ),

    "Legacy": (
        '"Legacy.com" obituaries',
        # Must contain "legacy.com" — rejects Legacy Health, Legacy Housing, etc.
        ["legacy.com"],
        ["legacy health", "legacy emanuel", "legacy good samaritan", "legacy hospital",
         "legacy housing", "legacy reserves", "legacy christian", "legacy financial",
         "legacy real estate", "legacy fund"]
    ),

    "Endeavor": (
        '"Endeavor Schools"',
        # Must contain "endeavor schools" — rejects WME/Endeavor, NASA, etc.
        ["endeavor schools"],
        ["endeavor group", "wme", "ufc", "talent agency", "ari emanuel",
         "hollywood", "img", "nasa", "space shuttle", "endeavor air",
         "endeavor streaming", "endeavor content"]
    ),

    "Core Power": (
        '"CorePower Yoga"',
        ["corepower yoga", "corepower"],
        ["nuclear", "energy", "power plant", "reactor", "electricity", "utility",
         "renewable energy", "solar", "grid", "molten salt", "core power systems"]
    ),

    "EoS": (
        '"EoS Fitness"',
        ["eos fitness"],
        ["eos cryptocurrency", "eos camera", "canon eos", "eos token",
         "blockchain", "eos network", "eos coin", "crypto", "eos coin"]
    ),

    "Mavis": (
        '"Mavis Discount Tire" OR "Mavis Tires"',
        ["mavis discount tire", "mavis tires", "mavis tire"],
        ["mavis beacon", "typing", "software", "keyboard"]
    ),

    "Trinity Solar": (
        '"Trinity Solar"',
        ["trinity solar"],
        ["trinity college", "trinity university", "trinity health", "trinity church",
         "trinity river", "trinity industries", "trinity broadcasting", "holy trinity"]
    ),

    "Thrive Pet Healthcare": (
        '"Thrive Pet Healthcare" OR "Thrive Pet"',
        # Must contain "thrive pet" — rejects Thrive Market, Thrive Global, etc.
        ["thrive pet"],
        ["thrive market", "thrive global", "thrive capital", "thrive causemetics",
         "thrive financial", "thrive supplement", "thrive diet", "thrive wellness"]
    ),

    "Wrench Group": (
        '"Wrench Group"',
        ["wrench group"],
        []
    ),

    "Radiance Holdings": (
        '"Radiance Holdings" OR "Sola Salons" OR "Woodhouse Spa"',
        # Any of these three brand names is acceptable
        ["radiance holdings", "sola salons", "woodhouse spa", "woodhouse day spa"],
        ["radiance solar", "radiance capital", "radiance technologies",
         "radiance health", "radiance skin clinic"]
    ),

    # ── MODERATE AMBIGUITY — brand name + sector required ────────────────────

    "Revolut": (
        '"Revolut" fintech OR banking OR neobank',
        ["revolut"],  # Revolut is distinctive enough — just require the name
        []
    ),

    "Cadogan Tate": (
        '"Cadogan Tate"',
        ["cadogan tate"],
        []
    ),

    "Phlur": (
        '"Phlur" fragrance OR perfume',
        ["phlur"],
        []
    ),

    "Hempz": (
        '"Hempz" skincare OR beauty OR lotion',
        ["hempz"],
        ["marijuana", "cannabis dispensary", "hemp farm", "hemp legislation", "weed"]
    ),

    "Summer Fridays": (
        '"Summer Fridays" skincare OR beauty',
        ["summer fridays"],
        []
    ),

    "Dude Wipes": (
        '"Dude Wipes"',
        ["dude wipes"],
        []
    ),

    "BrewDog": (
        '"BrewDog" beer OR brewery OR pub',
        ["brewdog"],
        []
    ),

    "Crumbl": (
        '"Crumbl Cookies" OR "Crumbl" cookie',
        ["crumbl"],
        []
    ),

    "PowerStop": (
        '"PowerStop" brake OR automotive',
        ["powerstop"],
        []
    ),

    "Rough Country": (
        '"Rough Country" lift kit OR truck OR off-road',
        ["rough country"],
        []
    ),

    # ── UNIQUE NAMES — exact name sufficient ─────────────────────────────────

    "Pura Vida": (
        '"Pura Vida Bracelets" OR "Pura Vida" jewelry bracelet',
        ["pura vida"],
        ["pura vida beach", "pura vida costa rica", "pura vida hotel",
         "pura vida restaurant", "pura vida meaning"]
    ),

    "Super Star": (
        '"Super-Star" car wash OR "SuperStar" car wash',
        ["super-star", "superstar car wash", "super star car wash"],
        []
    ),

}

# For any company not in COMPANY_NEWS_CONFIG, use bare company name as query
# with no keyword filters — works fine for unique names like "Crumbl", "BrewDog"

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
    """Fetch up to 15 recent articles for a company via Google News RSS.

    Uses COMPANY_NEWS_CONFIG for:
      - search_query:      what to send Google News
      - required_keywords: at least ONE must appear in title+summary (case-insensitive)
      - exclude_keywords:  if ANY appear in title+summary, article is dropped
    Falls back to bare company name with no filters for unconfigured companies.
    """
    cfg = COMPANY_NEWS_CONFIG.get(company_name)
    if cfg:
        search_query, required_kws, exclude_kws = cfg
    else:
        search_query  = f'"{company_name}"'
        required_kws  = []
        exclude_kws   = []

    required_lower = [k.lower() for k in required_kws]
    exclude_lower  = [k.lower() for k in exclude_kws]

    url = (
        f"https://news.google.com/rss/search"
        f"?q={search_query.replace(' ', '+')}"
        f"&hl=en-US&gl=US&ceid=US:en"
    )

    cutoff   = datetime.now(timezone.utc) - timedelta(days=DAYS_LOOKBACK)
    articles = []

    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:30]:  # over-fetch to allow for filtering
            pub_date = parse_date(entry)
            if pub_date < cutoff:
                continue

            title   = (entry.title   or "").strip()
            summary = clean_html(entry.get("summary", ""))
            title_lower   = title.lower()
            haystack      = (title + " " + summary).lower()

            # Drop if any exclude keyword found anywhere in title or summary
            if exclude_lower and any(ex in haystack for ex in exclude_lower):
                logger.info("  [EXCLUDED] %s — %s: %s", company_name,
                            next(ex for ex in exclude_lower if ex in haystack), title[:80])
                continue

            # Drop if required keywords defined but none appear in title+summary
            if required_lower and not any(rk in haystack for rk in required_lower):
                logger.info("  [NO MATCH] %s — no required keyword in: %s", company_name, title[:80])
                continue

            # Secondary gate: for high-ambiguity companies, the first required keyword
            # (which is always the full brand name) must appear in the TITLE specifically.
            # This catches articles that merely mention the brand in passing in the body.
            if required_lower:
                primary_kw = required_lower[0]  # always the most specific term
                if len(primary_kw) > 6 and primary_kw not in title_lower:
                    logger.info("  [TITLE MISS] %s — '%s' not in title: %s",
                                company_name, primary_kw, title[:80])
                    continue

            source = entry.get("source", {}).get("title", "") if hasattr(entry, "source") else ""
            articles.append({
                "company_name": company_name,
                "entity_id":    entity_id,
                "title":        title[:1000],
                "summary":      summary[:2000],
                "published":    pub_date.replace(tzinfo=None),
                "link":         (entry.link or "")[:2000],
                "source":       source[:200],
            })

            if len(articles) >= 15:
                break

    except Exception as exc:
        logger.warning("  Failed to fetch news for %s: %s", company_name, exc)

    logger.info("  %-30s → %d articles (after filtering)", company_name, len(articles))
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
