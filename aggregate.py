#!/usr/bin/env python3
# =============================================================================
# AI News Aggregator — Main Script
# =============================================================================
# Fetches RSS feeds, categorizes headlines, deduplicates, and generates
# static HTML pages: today's news as index.html, past days as archive pages.
# =============================================================================

import sys
import re
import hashlib
import calendar
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from pathlib import Path

import feedparser
from jinja2 import Environment, FileSystemLoader

from config import (
    FEEDS, TIER2_SOURCES, AI_KEYWORDS, CATEGORIES, DEFAULT_CATEGORY,
    COMPANIES, MAX_HEADLINE_AGE_DAYS, TIMEZONE_OFFSET,
    DEDUP_SIMILARITY_THRESHOLD, DEDUP_ENTITIES, DEDUP_ENTITY_ALIASES,
    BREAKING_TITLE_SIGNALS, MAX_OTHER_ITEMS,
)

CR_TZ = timezone(timedelta(hours=TIMEZONE_OFFSET))
PROJECT_DIR = Path(__file__).parent

# Pre-compile AI keyword regex with word boundaries
_AI_RE = re.compile(
    r'\b(' + '|'.join(re.escape(kw) for kw in AI_KEYWORDS) + r')\b',
    re.IGNORECASE,
)


def parse_published(entry):
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def categorize(title):
    lower = title.lower()
    best_cat = DEFAULT_CATEGORY
    best_score = 0
    for cat in CATEGORIES:
        score = 0
        for kw in cat.get("strong", []):
            if kw in lower:
                score += 3
        for kw in cat.get("weak", []):
            if kw in lower:
                score += 1
        for kw in cat.get("exclude", []):
            if kw in lower:
                score -= 5
        if score > best_score:
            best_score = score
            best_cat = cat["name"]
    return best_cat


def detect_companies(title):
    lower = title.lower()
    matched = []
    for company, keywords in COMPANIES.items():
        for kw in keywords:
            if kw in lower:
                matched.append(company)
                break
    return sorted(matched)


def is_ai_related(title):
    """Check if a headline matches AI keywords using word boundaries."""
    return bool(_AI_RE.search(title))


def dedup_key(url, title):
    if url:
        return url.strip()
    return hashlib.md5(title.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Story deduplication
# ---------------------------------------------------------------------------

# Source priority: lower = preferred when deduplicating
SOURCE_TIER = {}
for _name in FEEDS:
    if _name in TIER2_SOURCES:
        SOURCE_TIER[_name] = 2
    elif _name in ("TechCrunch AI", "The Verge AI", "Wired AI",
                    "The Register AI", "AI News", "InfoQ AI/ML",
                    "The Decoder", "Futurism AI", "ZDNet AI"):
        SOURCE_TIER[_name] = 1
    else:
        SOURCE_TIER[_name] = 0

_STOP = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "about",
    "after", "before", "during", "without", "between", "through",
    "and", "but", "or", "not", "no", "so", "if", "than", "too", "very",
    "just", "that", "this", "it", "its", "new", "says", "said",
    "how", "what", "why", "who", "when", "where", "which",
    "most", "more", "some", "all", "any", "each", "every",
    "up", "out", "over", "also", "now", "here", "there",
    "get", "got", "make", "made", "take", "come", "see", "use",
    "first", "last", "latest", "big", "top", "amid",
    # AI-domain stop words (too common in every headline to be useful for dedup)
    "ai", "artificial", "intelligence", "model", "models",
    "tech", "technology", "data", "digital",
}


def extract_story_key(title):
    tokens = set(re.findall(r'[a-z0-9]+', title.lower()))
    return frozenset(tokens - _STOP)


def extract_entities(title):
    """Extract known entities (companies, people, places) from title.
    Normalizes aliases (e.g. 'chinese' → 'china') for consistent matching."""
    lower = title.lower()
    entities = set()
    for e in DEDUP_ENTITIES:
        if e in lower:
            entities.add(e)
    # Apply aliases: 'chinese' → 'china', etc.
    for alias, canonical in DEDUP_ENTITY_ALIASES.items():
        if alias in lower:
            entities.add(canonical)
    return frozenset(entities)


def story_overlap(key_a, key_b, ent_a, ent_b):
    if not key_a or not key_b:
        return 0.0
    intersection = key_a & key_b
    smaller = min(len(key_a), len(key_b))
    base = len(intersection) / smaller if smaller else 0.0
    # Shared entities provide a small boost (not a floor)
    shared_entities = ent_a & ent_b
    if len(shared_entities) >= 3:
        base += 0.15
    elif len(shared_entities) >= 2:
        base += 0.08
    return base


def dedup_similar(headlines):
    for h in headlines:
        h["_story_key"] = extract_story_key(h["title"])
        h["_entities"] = extract_entities(h["title"])

    clusters = []
    for h in headlines:
        placed = False
        for cluster in clusters:
            rep = cluster[0]
            if story_overlap(h["_story_key"], rep["_story_key"],
                             h["_entities"], rep["_entities"]) >= DEDUP_SIMILARITY_THRESHOLD:
                cluster.append(h)
                placed = True
                break
        if not placed:
            clusters.append([h])

    result = []
    deduped = 0
    for cluster in clusters:
        cluster.sort(key=lambda h: (SOURCE_TIER.get(h["source"], 2), h["published"]))
        best = cluster[0]
        if len(cluster) > 1:
            best["_also_covered_by"] = [c["source"] for c in cluster[1:]]
            deduped += len(cluster) - 1
        result.append(best)

    if deduped:
        print(f"  ({deduped} duplicate articles merged)")

    # Mark breaking news
    # Breaking = genuinely important stories, not just widely aggregated fluff
    tier0 = {"OpenAI", "Google DeepMind", "Hugging Face", "NVIDIA Blog",
             "Microsoft Research", "Meta Research"}
    tier1_sources = {"TechCrunch AI", "The Verge AI", "Wired AI", "The Register AI",
                     "The Decoder", "MIT Tech Review", "Ars Technica"}
    for h in result:
        h.pop("_story_key", None)
        h.pop("_entities", None)
        score = 0
        also = h.get("_also_covered_by", [])
        all_sources = {h["source"]} | set(also)

        # Coverage by quality outlets (not just Google News reprints)
        quality_sources = all_sources & (tier0 | tier1_sources)
        if len(quality_sources) >= 3:
            score += 2
        elif len(quality_sources) >= 2:
            score += 1

        # Total coverage breadth (including Google News)
        if len(also) >= 4:
            score += 1

        # Official company announcement
        if h["source"] in tier0:
            score += 1

        # Breaking language in title
        lower = h["title"].lower()
        for sig in BREAKING_TITLE_SIGNALS:
            if sig in lower:
                score += 1
                break

        h["_breaking"] = score >= 2

    return result


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_feeds():
    headlines = []
    seen = set()
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_HEADLINE_AGE_DAYS)

    for source_name, feed_url in FEEDS.items():
        print(f"  {source_name}...", end=" ", flush=True)
        try:
            feed = feedparser.parse(feed_url, request_headers={
                "User-Agent": "AI-News-Aggregator/1.0"
            })
            if feed.bozo and not feed.entries:
                print(f"ERR: {feed.bozo_exception}")
                continue

            count = 0
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not title:
                    continue

                if source_name in TIER2_SOURCES and not is_ai_related(title):
                    continue

                key = dedup_key(link, title)
                if key in seen:
                    continue
                seen.add(key)

                published = parse_published(entry)
                if published and published < cutoff:
                    continue
                if not published:
                    published = datetime.now(timezone.utc)

                headlines.append({
                    "title": title,
                    "link": link,
                    "source": source_name,
                    "published": published,
                    "category": categorize(title),
                    "companies": detect_companies(title),
                })
                count += 1

            print(f"{count}")
        except Exception as e:
            print(f"FAIL: {e}")

    return headlines


# ---------------------------------------------------------------------------
# Calendar builder
# ---------------------------------------------------------------------------

def build_calendars(days_with_data, current_day, today_str):
    """Build calendar data for template. Returns list of month dicts."""
    if not days_with_data:
        return []

    # Find which months we need
    all_dates = [datetime.strptime(d, "%Y-%m-%d") for d in days_with_data]
    all_dates.append(datetime.strptime(today_str, "%Y-%m-%d"))
    months = sorted(set((d.year, d.month) for d in all_dates))

    data_set = set(days_with_data)
    current_date = datetime.strptime(current_day, "%Y-%m-%d") if current_day else None
    today_date = datetime.strptime(today_str, "%Y-%m-%d")

    calendars = []
    for year, month in months:
        cal = calendar.Calendar(firstweekday=6)  # Sunday first like Craigslist
        month_name = calendar.month_name[month]
        weeks = []
        for week in cal.monthdayscalendar(year, month):
            row = []
            for day_num in week:
                if day_num == 0:
                    row.append({"day": 0})
                else:
                    d = datetime(year, month, day_num)
                    day_str = d.strftime("%Y-%m-%d")
                    has_data = day_str in data_set
                    is_today = (d.date() == today_date.date())
                    is_current = (current_date and d.date() == current_date.date())

                    href = None
                    if has_data:
                        if day_str == today_str:
                            href = "index.html"
                        else:
                            href = f"{day_str}.html"

                    row.append({
                        "day": day_num,
                        "href": href,
                        "is_today": is_today,
                        "is_current": is_current,
                    })
            weeks.append(row)

        calendars.append({
            "year": year,
            "month_name": month_name,
            "day_labels": ["S", "M", "T", "W", "T", "F", "S"],
            "weeks": weeks,
        })

    return calendars


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def group_by_day(headlines):
    by_day = defaultdict(list)
    for h in headlines:
        local = h["published"].astimezone(CR_TZ)
        h["time_str"] = local.strftime("%H:%M")
        h["date_str"] = local.strftime("%b %d")
        day_key = local.strftime("%Y-%m-%d")
        by_day[day_key].append(h)
    return by_day


def build_sections(headlines):
    by_cat = defaultdict(list)
    for h in headlines:
        by_cat[h["category"]].append(h)
    for cat in by_cat:
        by_cat[cat].sort(key=lambda h: h["published"], reverse=True)

    # Cap the catch-all category — keep best items by coverage & source tier
    if DEFAULT_CATEGORY in by_cat and len(by_cat[DEFAULT_CATEGORY]) > MAX_OTHER_ITEMS:
        others = by_cat[DEFAULT_CATEGORY]
        # Rank by: multi-source coverage first, then source tier, then recency
        others.sort(key=lambda h: (
            -len(h.get("_also_covered_by", [])),
            SOURCE_TIER.get(h["source"], 2),
            -h["published"].timestamp(),
        ))
        by_cat[DEFAULT_CATEGORY] = others[:MAX_OTHER_ITEMS]

    category_order = [c["name"] for c in CATEGORIES] + [DEFAULT_CATEGORY]
    return [(cat, by_cat[cat]) for cat in category_order if cat in by_cat]


def render_page(sections, headlines, display_date, filename, calendars,
                global_companies=None, all_headlines=None):
    import json
    env = Environment(loader=FileSystemLoader(PROJECT_DIR))
    template = env.get_template("template.html")

    # Use global company list (all days) if provided, else fall back to page-only
    all_companies = global_companies or sorted({c for h in headlines for c in h["companies"]})
    now_cr = datetime.now(CR_TZ)

    # Serialize all headlines as JSON for cross-day company filtering
    all_hl_json = "[]"
    if all_headlines:
        all_hl_json = json.dumps([{
            "title": h["title"],
            "link": h["link"],
            "source": h["source"],
            "time": h["time_str"],
            "date": h.get("date_str", ""),
            "day": h["published"].astimezone(CR_TZ).strftime("%Y-%m-%d"),
            "companies": h["companies"],
            "category": h["category"],
            "breaking": h.get("_breaking", False),
            "also": len(h.get("_also_covered_by", [])),
        } for h in all_headlines], ensure_ascii=False)

    html = template.render(
        sections=sections,
        all_companies=all_companies,
        display_date=display_date,
        generated_at=now_cr.strftime("%Y-%m-%d %H:%M CST"),
        total_headlines=len(headlines),
        total_sources=len(FEEDS),
        calendars=calendars,
        all_headlines_json=all_hl_json,
    )

    output_dir = PROJECT_DIR / "output"
    output_dir.mkdir(exist_ok=True)
    (output_dir / filename).write_text(html)
    return output_dir / filename


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n=== AI News Aggregator ===\n")
    print("Fetching:")
    headlines = fetch_feeds()

    if not headlines:
        print("\nNo headlines fetched.")
        sys.exit(1)

    print(f"\nTotal: {len(headlines)} headlines (before dedup)")
    headlines = dedup_similar(headlines)
    print(f"After dedup: {len(headlines)} headlines")

    by_day = group_by_day(headlines)
    sorted_days = sorted(by_day.keys(), reverse=True)
    today_cr = datetime.now(CR_TZ).strftime("%Y-%m-%d")

    # Compute global company list from ALL headlines (past 30 days)
    global_companies = sorted({c for h in headlines for c in h["companies"]})

    # Sort all headlines by published time (newest first) for JSON embed
    all_sorted = sorted(headlines, key=lambda h: h["published"], reverse=True)

    # Render today
    if today_cr in by_day:
        today_hl = by_day[today_cr]
        sections = build_sections(today_hl)
        cals = build_calendars(sorted_days, today_cr, today_cr)
        dt = datetime.strptime(today_cr, "%Y-%m-%d")
        display = f"Today, {dt.strftime('%B %d')}"
        path = render_page(sections, today_hl, display, "index.html", cals,
                           global_companies, all_sorted)
        print(f"  {path} ({len(today_hl)} headlines)")
    else:
        cals = build_calendars(sorted_days, today_cr, today_cr)
        dt = datetime.strptime(today_cr, "%Y-%m-%d")
        display = f"Today, {dt.strftime('%B %d')}"
        render_page([], [], display, "index.html", cals, global_companies,
                    all_sorted)
        print("  index.html (0 headlines)")

    # Render archive days
    for day in sorted_days:
        if day == today_cr:
            continue
        day_hl = by_day[day]
        sections = build_sections(day_hl)
        cals = build_calendars(sorted_days, day, today_cr)
        dt = datetime.strptime(day, "%Y-%m-%d")
        display = dt.strftime("%A, %B %d")
        path = render_page(sections, day_hl, display, f"{day}.html", cals,
                           global_companies, all_sorted)
        print(f"  {path} ({len(day_hl)} headlines)")

    print("Done.\n")


if __name__ == "__main__":
    main()
