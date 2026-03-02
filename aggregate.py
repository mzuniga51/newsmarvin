#!/usr/bin/env python3
# =============================================================================
# AI News Aggregator — Main Script
# =============================================================================
# Fetches RSS feeds, categorizes headlines, deduplicates, and generates
# static HTML pages: today's news as index.html, past days as archive pages.
# =============================================================================

import sys
import os
import re
import json
import hashlib
import calendar
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from pathlib import Path

import requests
import feedparser
from jinja2 import Environment, FileSystemLoader

from config import (
    FEEDS, TIER2_SOURCES, AI_KEYWORDS, CATEGORIES, DEFAULT_CATEGORY,
    COMPANIES, MAX_HEADLINE_AGE_DAYS, TIMEZONE_OFFSET,
    DEDUP_SIMILARITY_THRESHOLD, DEDUP_ENTITIES, DEDUP_ENTITY_ALIASES,
    BREAKING_TITLE_SIGNALS, MAX_ITEMS_PER_CATEGORY,
    PAYWALLED_PUBLISHERS, PAYWALLED_FEEDS,
    GOOGLE_NEWS_BLOCKED_PUBLISHERS, RESEARCH_QUALITY_SOURCES,
    TOP_NEWS_COVERAGE_THRESHOLD, TOP_NEWS_MAX_ITEMS,
    MIN_CLASSIFICATION_SCORE,
    LLM_CLASSIFY, LLM_MODEL,
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


def categorize(title, description=""):
    """Two-pass classification: title is primary signal, description adds context.

    Scoring:
      - Strong keyword in title    = +3
      - Strong keyword in desc     = +2
      - Weak keyword in title      = +1
      - Weak keyword in desc       = +0.5
      - Exclude keyword in either  = -5
    """
    title_low = title.lower()
    desc_low = description.lower() if description else ""

    best_cat = DEFAULT_CATEGORY
    best_score = 0
    for cat in CATEGORIES:
        score = 0
        for kw in cat.get("strong", []):
            if kw in title_low:
                score += 3
            elif kw in desc_low:
                score += 2
        for kw in cat.get("weak", []):
            if kw in title_low:
                score += 1
            elif kw in desc_low:
                score += 0.5
        for kw in cat.get("exclude", []):
            if kw in title_low or kw in desc_low:
                score -= 5
        if score > best_score:
            best_score = score
            best_cat = cat["name"]
    # Require minimum confidence to classify
    if best_score < MIN_CLASSIFICATION_SCORE:
        return DEFAULT_CATEGORY
    return best_cat


def categorize_excluding(title, description="", exclude_cat=None):
    """Categorize but skip a specific category. Used for source gating."""
    title_low = title.lower()
    desc_low = description.lower() if description else ""

    best_cat = DEFAULT_CATEGORY
    best_score = 0
    for cat in CATEGORIES:
        if cat["name"] == exclude_cat:
            continue
        score = 0
        for kw in cat.get("strong", []):
            if kw in title_low:
                score += 3
            elif kw in desc_low:
                score += 2
        for kw in cat.get("weak", []):
            if kw in title_low:
                score += 1
            elif kw in desc_low:
                score += 0.5
        for kw in cat.get("exclude", []):
            if kw in title_low or kw in desc_low:
                score -= 5
        if score > best_score:
            best_score = score
            best_cat = cat["name"]
    if best_score < MIN_CLASSIFICATION_SCORE:
        return DEFAULT_CATEGORY
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


def is_ai_related(title, description=""):
    """Check if a headline matches AI keywords using word boundaries.
    Pass 1: checks both title and RSS description for relevance."""
    return bool(_AI_RE.search(title)) or bool(_AI_RE.search(description))


def extract_google_news_publisher(title):
    """Extract publisher name from Google News title format: 'Headline - Publisher Name'."""
    if " - " in title:
        return title.rsplit(" - ", 1)[-1].strip().lower()
    return ""


def is_paywalled(source_name, title):
    """Check if an article is from a paywalled publisher."""
    if source_name in PAYWALLED_FEEDS:
        return True
    if source_name.startswith("Google News"):
        pub = extract_google_news_publisher(title)
        return any(pw in pub for pw in PAYWALLED_PUBLISHERS)
    return False


def is_blocked_google_news(source_name, title):
    """Check if a Google News article is from a blocked low-quality publisher."""
    if not source_name.startswith("Google News"):
        return False
    pub = extract_google_news_publisher(title)
    return any(blocked in pub for blocked in GOOGLE_NEWS_BLOCKED_PUBLISHERS)


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
    if _name in TIER2_SOURCES or _name.startswith("Google News"):
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
    # Company/product names: tracked by entity system, not useful for story differentiation
    "anthropic", "claude", "openai", "chatgpt", "gpt", "google", "gemini",
    "meta", "microsoft", "apple", "amazon", "nvidia", "deepmind",
    "code", "llm", "chatbot", "copilot",
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


def dedup_similar(headlines, llm_clusters=None):
    for h in headlines:
        h["_story_key"] = extract_story_key(h["title"])
        h["_entities"] = extract_entities(h["title"])

    # Build clusters: LLM groups first, then keyword fallback for ungrouped
    if llm_clusters:
        # Group by LLM cluster ID
        from collections import OrderedDict
        llm_groups = OrderedDict()
        ungrouped = []
        for i, h in enumerate(headlines):
            cid = llm_clusters.get(i)
            if cid is not None:
                llm_groups.setdefault(cid, []).append(h)
            else:
                ungrouped.append(h)

        clusters = list(llm_groups.values())

        # Post-LLM merge: merge clusters whose representatives are clearly the same story
        # Only compares cluster representatives (best article) with a higher threshold
        POST_MERGE_THRESHOLD = 0.45
        merged_any = True
        while merged_any:
            merged_any = False
            i = 0
            while i < len(clusters):
                j = i + 1
                while j < len(clusters):
                    rep_i = clusters[i][0]
                    rep_j = clusters[j][0]
                    overlap = story_overlap(rep_i["_story_key"], rep_j["_story_key"],
                                            rep_i["_entities"], rep_j["_entities"])
                    if overlap >= POST_MERGE_THRESHOLD:
                        clusters[i].extend(clusters[j])
                        clusters.pop(j)
                        merged_any = True
                    else:
                        j += 1
                i += 1

        # Try to place ungrouped into existing clusters via keyword similarity
        for h in ungrouped:
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
    else:
        # Pure keyword fallback
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
        cluster.sort(key=lambda h: (SOURCE_TIER.get(h.get("_feed_source", h["source"]), 2), h["published"]))
        best = cluster[0]
        if len(cluster) > 1:
            best["_also_covered_by"] = list({c["source"] for c in cluster[1:]} - {best["source"]})
            deduped += len(cluster) - 1
        result.append(best)

    if deduped:
        print(f"  ({deduped} duplicate articles merged)")

    # Mark breaking news
    # Breaking = genuinely important stories, not just widely aggregated fluff
    tier0 = {"OpenAI", "Google DeepMind", "Hugging Face", "NVIDIA Blog",
             "Microsoft Research", "Meta Research"}
    tier1_sources = {"TechCrunch AI", "The Verge AI", "Wired AI", "The Register AI",
                     "The Decoder", "MIT Tech Review", "Ars Technica",
                     "Axios", "Fortune", "CNBC Tech", "BBC Tech", "Guardian Tech",
                     "VentureBeat AI", "ZDNet AI", "Futurism AI", "InfoQ AI/ML"}
    # Google News articles use the publisher name as source, so check against
    # known quality publishers that may appear via Google News feeds
    google_news_quality = {
        "reuters", "ap news", "associated press", "cbs news", "nbc news",
        "abc news", "cnbc", "bbc", "the guardian", "pcmag", "defense one",
        "politico", "the hill", "bloomberg", "time",
    }

    for h in result:
        h.pop("_story_key", None)
        h.pop("_entities", None)
        score = 0
        also = h.get("_also_covered_by", [])
        all_sources = {h["source"]} | set(also)

        # Coverage by quality outlets (not just Google News reprints)
        # Check both direct feed names AND Google News publisher names
        quality_sources = all_sources & (tier0 | tier1_sources)
        # Also count Google News publishers that are quality outlets
        for s in all_sources:
            if s.lower() in google_news_quality:
                quality_sources.add(s)
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

        # LLM importance boost: major stories get a point
        if (h.get("_importance") or 2) >= 3:
            score += 1

        h["_breaking"] = score >= 2

    return result


# ---------------------------------------------------------------------------
# LLM Classification
# ---------------------------------------------------------------------------

def classify_with_haiku(headlines):
    """Reclassify articles using Claude Haiku for context-aware categorization.
    Falls back to keyword classification if API call fails."""
    if not LLM_CLASSIFY:
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  WARNING: ANTHROPIC_API_KEY not set, keeping keyword classifications")
        return

    try:
        import anthropic
    except ImportError:
        print("  WARNING: anthropic package not installed, keeping keyword classifications")
        return

    # Pre-filter obvious junk before wasting LLM tokens
    JUNK_PATTERNS = re.compile(
        r'(?i)\b('
        r'county board agenda|faculty senate|campus event|'
        r'stocks? to (?:buy|consider|watch)|stock pick|'
        r'side hustle|make money with|earn \$|'
        r'what is ai\??|introduction to ai|ai for beginners|'
        r'how to use chatgpt to|i asked chatgpt|chatgpt says|'
        r'artificial intelligence in (?:cancer|healthcare|nursing|dental)|'
        r'sign in to read|for subscribers only|premium content'
        r')\b'
    )
    for h in headlines:
        title = h["title"]
        desc = h.get("_description", "")
        if JUNK_PATTERNS.search(title) or JUNK_PATTERNS.search(desc[:200]):
            h["_skip_llm"] = True
            h["category"] = None  # will be dropped

    # Build known companies list
    known_companies = sorted(COMPANIES.keys())
    companies_text = ", ".join(known_companies)

    # ---- PASS 1: Classification (category + companies) ----
    classify_prompt = f"""Classify AI/tech news articles. Return JSON array with "id", "category", "companies".

Categories (pick ONE):
- Releases: product/model/API/feature shipped or made available, new tools, new open-source projects
- People: specific individuals hired, fired, resigned, appointed (NOT interviews or opinions BY people)
- Vibe Coding: AI-assisted coding, "I built X with AI", code generation tools, developer workflow with AI
- Rumors & Speculation: unconfirmed reports, leaks, "reportedly", "expected to"
- Business & Money: funding, revenue, layoffs, market analysis, enterprise trends, datacenter/cloud infrastructure, corporate strategy
- Policy & Regulation: government actions, laws, military/defense AI use, bans, regulatory moves
- Security & Privacy: hacking, exploits, breaches, surveillance, scams, privacy concerns, ads tracking users
- Research: scientific papers, studies, datasets, benchmarks from labs/universities
- Ethics & Philosophy: moral debates, societal impact, existential risk, bias, job displacement fears
- Fun & Weird: bizarre, humorous, unexpected AI stories, memes, unusual use cases
- Other: AI news that doesn't fit above — use ONLY as last resort, prefer a specific category
- null: not about AI/tech, or pure ads/spam/paywall

Known companies: {companies_text}

Examples:
{{"title":"Trump bans Anthropic from government","category":"Policy & Regulation","companies":["anthropic"]}}
{{"title":"OpenAI launches GPT-5","category":"Releases","companies":["openai"]}}
{{"title":"I built a SaaS in a weekend with Claude","category":"Vibe Coding","companies":["anthropic"]}}
{{"title":"Block cuts half its staff in AI pivot","category":"Business & Money","companies":["block"]}}
{{"title":"Dario Amodei on AI red lines (interview)","category":"Ethics & Philosophy","companies":["anthropic"]}}
{{"title":"AWS datacenter hit in Middle East strikes","category":"Business & Money","companies":["amazon"]}}
{{"title":"AI-generated film pulled from theaters","category":"Fun & Weird","companies":[]}}
{{"title":"OpenAI hires iPhone designer Jony Ive","category":"People","companies":["openai"]}}
{{"title":"Hackers exploit GitHub Actions with AI bot","category":"Security & Privacy","companies":["microsoft"]}}
{{"title":"ElevenLabs tops speech-to-text benchmark","category":"Releases","companies":["elevenlabs","google"]}}
{{"title":"Cancel ChatGPT movement grows after Pentagon deal","category":"Business & Money","companies":["openai"]}}
{{"title":"SaaS-pocalypse: AI disrupting enterprise software","category":"Business & Money","companies":[]}}
{{"title":"Why XML tags matter for Claude prompts","category":"Vibe Coding","companies":["anthropic"]}}
{{"title":"New dataset for animating drawings","category":"Research","companies":["meta"]}}

Return ONLY a JSON array of {{"id","category","companies"}}. No other text."""

    # ---- PASS 2: Story dedup + importance ----
    dedup_prompt = """Group these articles by real-world event. Return JSON array with "id", "story", "importance".

- "story": 2-5 word lowercase slug for the event. Same event = same slug across ALL articles.
- "importance": 1=trivial/listicle/SEO, 2=normal news, 3=major breaking news

Examples of consistent slugs:
- "Pentagon bans Anthropic" / "Trump orders Anthropic ban" / "Anthropic stock drops after ban" → "anthropic-pentagon-ban"
- "OpenAI launches GPT-5" / "GPT-5 benchmarks released" → "openai-gpt5-launch"
- Articles reacting to the same event get the same slug.

Return ONLY a JSON array of {"id","story","importance"}. No other text."""

    # Prepare article data (skip junk-filtered articles)
    articles = []
    article_idx_map = {}  # maps position in articles list → headline index
    for i, h in enumerate(headlines):
        if h.get("_skip_llm"):
            continue
        article_idx_map[len(articles)] = i
        articles.append({
            "id": i,
            "title": h["title"],
            "description": h.get("_description", "")[:200],
        })

    batch_size = 100  # simpler output = can handle bigger batches
    results = {}
    client = anthropic.Anthropic(api_key=api_key)

    # Pass 1: Classification
    for start in range(0, len(articles), batch_size):
        batch = articles[start:start + batch_size]
        user_msg = json.dumps(batch, ensure_ascii=False)

        try:
            response = client.messages.create(
                model=LLM_MODEL,
                max_tokens=4096,
                system=classify_prompt,
                messages=[{"role": "user", "content": user_msg}],
            )

            text = response.content[0].text
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                classifications = json.loads(json_match.group())
                for item in classifications:
                    article_id = item.get("id")
                    if article_id is not None:
                        results[article_id] = {
                            "category": item.get("category"),
                            "companies": item.get("companies", []),
                        }
        except Exception as e:
            print(f"  WARNING: classify batch {start}-{start+len(batch)} failed: {e}")
            continue

    # Pass 2: Story dedup + importance
    for start in range(0, len(articles), batch_size):
        batch = articles[start:start + batch_size]
        user_msg = json.dumps(batch, ensure_ascii=False)

        try:
            response = client.messages.create(
                model=LLM_MODEL,
                max_tokens=4096,
                system=dedup_prompt,
                messages=[{"role": "user", "content": user_msg}],
            )

            text = response.content[0].text
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                dedup_results = json.loads(json_match.group())
                for item in dedup_results:
                    article_id = item.get("id")
                    if article_id is not None and article_id in results:
                        results[article_id]["importance"] = item.get("importance", 2)
                        results[article_id]["story"] = item.get("story")
        except Exception as e:
            print(f"  WARNING: dedup batch {start}-{start+len(batch)} failed: {e}")
            continue

    # Apply Haiku classifications, company tags, and importance
    valid_categories = {cat["name"] for cat in CATEGORIES}
    reclassified = 0
    nulled = 0
    trivial = 0
    for i, h in enumerate(headlines):
        if i in results:
            r = results[i]
            new_cat = r["category"]
            importance = r.get("importance", 2)
            h["_importance"] = importance
            h["_story_key_llm"] = r.get("story")

            if new_cat is None:
                if h["category"] is not None:
                    nulled += 1
                h["category"] = DEFAULT_CATEGORY
            elif new_cat in valid_categories:
                if new_cat != h["category"]:
                    reclassified += 1
                h["category"] = new_cat
            else:
                # Haiku returned an invalid category name — use Other
                h["category"] = DEFAULT_CATEGORY
            # Override companies with Haiku's tags (more context-aware)
            if r["companies"]:
                h["companies"] = sorted(set(r["companies"]))
            # Mark trivial articles — they'll be deprioritized in section building
            if importance == 1:
                trivial += 1
        else:
            h["_importance"] = 2  # default for unclassified
            # Ensure keyword-only articles also get a category
            if h["category"] is None:
                h["category"] = DEFAULT_CATEGORY

    skipped = sum(1 for h in headlines if h.get("_skip_llm"))
    print(f"  LLM: {reclassified} reclassified, {nulled} dropped, {trivial} trivial, "
          f"{skipped} pre-filtered, {len(headlines) - len(results) - skipped} unchanged")


def apply_research_gating(headlines):
    """Research source gating: only trusted sources can contribute to Research."""
    gated = 0
    for h in headlines:
        if h["category"] == "Research" and h.get("_feed_source", h["source"]) not in RESEARCH_QUALITY_SOURCES:
            new_cat = categorize_excluding(
                h["title"], h.get("_description", ""), "Research")
            h["category"] = new_cat
            gated += 1
    if gated:
        print(f"  Research gating: {gated} articles moved to other categories")


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
            resp = requests.get(feed_url, headers={"User-Agent": "AI-News-Aggregator/1.0"}, timeout=15)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            if feed.bozo and not feed.entries:
                print(f"ERR: {feed.bozo_exception}")
                continue

            count = 0
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not title:
                    continue

                # Extract description/summary from RSS for two-pass classification
                desc = (entry.get("summary") or entry.get("description") or "").strip()
                # Strip HTML tags from description
                desc = re.sub(r'<[^>]+>', ' ', desc)
                # Remove bare URLs (common in HN, Reddit feeds — wastes token budget)
                desc = re.sub(r'https?://\S+', '', desc)
                # Collapse whitespace
                desc = re.sub(r'\s+', ' ', desc).strip()
                # Truncate to first ~500 chars (enough for classification, not wasteful)
                desc = desc[:500]

                # Filter: paywall check
                if is_paywalled(source_name, title):
                    continue

                # Filter: Google News quality check
                if is_blocked_google_news(source_name, title):
                    continue

                # Pass 1: Relevance check (title + description)
                if source_name in TIER2_SOURCES and not is_ai_related(title, desc):
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

                # Pass 2: Keyword classification (may be overridden by LLM)
                category = categorize(title, desc)

                # For Google News: extract real publisher and clean title
                display_source = source_name
                display_title = title
                if source_name.startswith("Google News") and " - " in title:
                    pub = title.rsplit(" - ", 1)[-1].strip()
                    if pub:
                        display_source = pub
                        display_title = title.rsplit(" - ", 1)[0].strip()

                headlines.append({
                    "title": display_title,
                    "link": link,
                    "source": display_source,
                    "_feed_source": source_name,
                    "published": published,
                    "category": category,
                    "companies": detect_companies(title),
                    "_description": desc,
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
        # Drop uncategorized headlines (DEFAULT_CATEGORY is None)
        if h["category"] is None:
            continue
        by_cat[h["category"]].append(h)

    # --- Top News: extract breaking + viral stories from ALL categories ---
    # These appear in Top News ONLY and are removed from their category.
    top_news = []
    for cat in list(by_cat.keys()):
        remaining = []
        for h in by_cat[cat]:
            is_breaking = h.get("_breaking", False)
            is_viral = len(h.get("_also_covered_by", [])) >= TOP_NEWS_COVERAGE_THRESHOLD
            if is_breaking or is_viral:
                h["_promoted_from"] = cat
                top_news.append(h)
            else:
                remaining.append(h)
        by_cat[cat] = remaining

    # Rank top news: coverage breadth first, then source tier, then recency
    top_news.sort(key=lambda h: (
        -len(h.get("_also_covered_by", [])),
        SOURCE_TIER.get(h.get("_feed_source", h["source"]), 2),
        -h["published"].timestamp(),
    ))
    top_news = top_news[:TOP_NEWS_MAX_ITEMS]

    # Cap every category: rank by importance + coverage + source tier + recency, keep top N
    for cat in by_cat:
        items = by_cat[cat]
        items.sort(key=lambda h: (
            -(h.get("_importance") or 2),  # Major stories first
            -len(h.get("_also_covered_by", [])),
            SOURCE_TIER.get(h.get("_feed_source", h["source"]), 2),
            -h["published"].timestamp(),
        ))
        by_cat[cat] = items[:MAX_ITEMS_PER_CATEGORY]

    # Build final sections: Top News first, then categories in order
    sections = []
    if top_news:
        sections.append(("Top News", top_news))
    category_order = [c["name"] for c in CATEGORIES]
    for cat in category_order:
        if cat in by_cat and by_cat[cat]:
            sections.append((cat, by_cat[cat]))
    return sections


def render_page(sections, headlines, display_date, filename, calendars,
                global_companies=None, all_headlines=None,
                page_title=None, page_description=None):
    import json
    env = Environment(loader=FileSystemLoader(PROJECT_DIR))
    template = env.get_template("template.html")

    # Use global company list (all days) if provided, else fall back to page-only
    all_companies = global_companies or sorted({c for h in headlines for c in h["companies"]})
    now_cr = datetime.now(CR_TZ)

    # SEO defaults
    if not page_title:
        page_title = "AI News Today — NewsMarvin"
    if not page_description:
        page_description = f"{len(headlines)} AI headlines from {len(FEEDS)} sources, deduplicated and ranked."
    canonical_path = "" if filename == "index.html" else filename

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
        page_title=page_title,
        page_description=page_description,
        canonical_path=canonical_path,
    )

    output_dir = PROJECT_DIR / "output"
    output_dir.mkdir(exist_ok=True)
    (output_dir / filename).write_text(html)

    # Copy static assets to output if missing
    import shutil
    for asset in ("logo.png", "logo-sm.png", "logo-email.png", "team.html",
                   "team-marvin.jpg", "team-oreo.jpg", "team-papato.jpg",
                   "team-bella.jpg", "team-panda.jpg", "team-choco.jpg",
                   "kill-bill.mp3", "marvin-motivation.mp4",
                   "team-panko.jpg"):
        src = PROJECT_DIR / "static" / asset
        dst = output_dir / asset
        if src.exists():
            shutil.copy2(src, dst)

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

    # LLM classification (overrides keyword-based categories)
    print(f"\nClassifying with {LLM_MODEL}...")
    classify_with_haiku(headlines)
    apply_research_gating(headlines)

    # Clean up internal description field
    for h in headlines:
        h.pop("_description", None)

    print(f"\nTotal: {len(headlines)} headlines (before dedup)")

    # Build LLM clusters from story keys assigned during classification
    # Story keys from different batches may use slightly different slugs for the same story
    # (e.g., "pentagon-anthropic-dispute" vs "anthropic-pentagon-standoff")
    # Normalize by fuzzy-matching keys that share 50%+ of their words
    raw_keys = {}
    for i, h in enumerate(headlines):
        sk = h.get("_story_key_llm")
        if sk:
            raw_keys[i] = sk.lower().strip()

    # Normalize: group similar story keys
    key_groups = {}  # canonical key → set of variant keys
    for sk in set(raw_keys.values()):
        words = set(re.findall(r'[a-z0-9]+', sk))
        placed = False
        for canonical, variants in key_groups.items():
            canon_words = set(re.findall(r'[a-z0-9]+', canonical))
            shared = words & canon_words
            smaller = min(len(words), len(canon_words))
            if smaller > 0 and len(shared) >= 2 and len(shared) / smaller >= 0.5:
                variants.add(sk)
                placed = True
                break
        if not placed:
            key_groups[sk] = {sk}

    # Build normalize map: variant → canonical
    normalize = {}
    for canonical, variants in key_groups.items():
        for v in variants:
            normalize[v] = canonical

    llm_clusters = {}
    for i, sk in raw_keys.items():
        llm_clusters[i] = normalize.get(sk, sk)

    if llm_clusters:
        unique_stories = len(set(llm_clusters.values()))
        print(f"  LLM story keys: {unique_stories} unique stories from {len(llm_clusters)} headlines")

    headlines = dedup_similar(headlines, llm_clusters)
    print(f"After dedup: {len(headlines)} headlines")

    by_day = group_by_day(headlines)
    sorted_days = sorted(by_day.keys(), reverse=True)
    today_cr = datetime.now(CR_TZ).strftime("%Y-%m-%d")

    # Compute global company list from ALL headlines (past 30 days)
    global_companies = sorted({c for h in headlines for c in h["companies"]})

    # Sort all headlines by published time (newest first) for JSON embed
    all_sorted = sorted(headlines, key=lambda h: h["published"], reverse=True)

    # Render index — rolling 24h window
    now_cr = datetime.now(CR_TZ)
    cutoff_24h = now_cr - timedelta(hours=24)
    recent_hl = [h for h in headlines if h["published"].astimezone(CR_TZ) >= cutoff_24h]
    # Ensure time_str is set for recent headlines
    for h in recent_hl:
        if "time_str" not in h:
            local = h["published"].astimezone(CR_TZ)
            h["time_str"] = local.strftime("%H:%M")
            h["date_str"] = local.strftime("%b %d")
    sections = build_sections(recent_hl)
    cals = build_calendars(sorted_days, today_cr, today_cr)
    display = f"Last 24 hours"
    path = render_page(sections, recent_hl, display, "index.html", cals,
                       global_companies, all_sorted,
                       page_title="AI News Today — NewsMarvin",
                       page_description=f"Today's {len(recent_hl)} AI headlines from {len(FEEDS)} sources. Deduplicated, ranked, and updated every 4 hours.")
    print(f"  {path} ({len(recent_hl)} headlines)")

    # Render archive days
    archive_pages = []
    for day in sorted_days:
        if day == today_cr:
            continue
        day_hl = by_day[day]
        sections = build_sections(day_hl)
        cals = build_calendars(sorted_days, day, today_cr)
        dt = datetime.strptime(day, "%Y-%m-%d")
        display = dt.strftime("%A, %B %d")
        day_title = f"AI News — {dt.strftime('%B %d, %Y')} — NewsMarvin"
        day_desc = f"{len(day_hl)} AI headlines from {display}. Curated from {len(FEEDS)} sources."
        path = render_page(sections, day_hl, display, f"{day}.html", cals,
                           global_companies, all_sorted,
                           page_title=day_title, page_description=day_desc)
        archive_pages.append(day)
        print(f"  {path} ({len(day_hl)} headlines)")

    # Generate sitemap.xml
    output_dir = PROJECT_DIR / "output"
    now_iso = now_cr.isoformat()
    sitemap_urls = [
        f'  <url><loc>https://newsmarvin.com/</loc><lastmod>{now_iso}</lastmod><changefreq>hourly</changefreq><priority>1.0</priority></url>',
    ]
    for day in sorted(archive_pages, reverse=True):
        sitemap_urls.append(
            f'  <url><loc>https://newsmarvin.com/{day}.html</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>'
        )
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(sitemap_urls) + '\n</urlset>\n'
    (output_dir / "sitemap.xml").write_text(sitemap)

    # Generate robots.txt
    robots = "User-agent: *\nAllow: /\nSitemap: https://newsmarvin.com/sitemap.xml\n"
    (output_dir / "robots.txt").write_text(robots)

    # Generate _headers (Cloudflare Pages)
    headers = """/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: SAMEORIGIN
  Referrer-Policy: strict-origin-when-cross-origin

/index.html
  Cache-Control: public, max-age=3600

/*.html
  Cache-Control: public, max-age=86400

/logo.png
  Cache-Control: public, max-age=604800

/logo-sm.png
  Cache-Control: public, max-age=604800
"""
    (output_dir / "_headers").write_text(headers)

    print("Done.\n")


if __name__ == "__main__":
    main()
