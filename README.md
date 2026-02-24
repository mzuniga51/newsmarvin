# NewsMarvin

AI news aggregator that fetches 29 RSS feeds, deduplicates headlines, categorizes them, and generates a static HTML site. Updated daily.

**Live at [newsmarvin.com](https://newsmarvin.com)**

Named after Marvin, a 6-year-old black and tan pomeranian who serves as the project's mascot.

## What It Does

- Pulls from 29 RSS sources across official company blogs (OpenAI, DeepMind, Meta, NVIDIA), AI-focused outlets (TechCrunch, The Verge, Ars Technica, Wired), traditional media (NYT, WSJ, BBC, Bloomberg), and community sources (Hacker News, Google News)
- **Entity-aware deduplication** removes the same story covered by multiple outlets, keeping the earliest published version
- **Keyword categorization** scores headlines into 10 topic categories using strong/weak/exclude keyword matching
- **Breaking news detection** identifies stories covered by multiple quality outlets
- **Tier-based filtering** — traditional media articles only appear if they match AI-specific keywords
- Generates static HTML with no JavaScript framework, no build step, no server required

## Categories

Releases, Products & Tools, Rumors & Speculation, Fun & Weird, Business & Money, Policy & Regulation, Research, Vibe Coding, Ethics & Philosophy, Other

## Features

- Company filter buttons with 30-day rolling window
- Full-text search across all days (client-side)
- Date range picker integrated with filters
- Calendar navigation with daily archive pages
- Sidebar with section navigation

## Setup

```bash
pip install -r requirements.txt
python aggregate.py
open output/index.html
```

Requirements: Python 3.9+, `feedparser`, `jinja2`.

## How It Works

```
RSS Feeds (29) → feedparser → AI keyword filter → dedup → categorize → Jinja2 → static HTML
```

1. **Fetch** — `feedparser` pulls all configured RSS feeds
2. **Filter** — Tier 2 sources (traditional media) are filtered for AI keyword matches
3. **Dedup** — URL-based exact dedup + title similarity scoring (0.35 threshold) with entity awareness
4. **Categorize** — Headlines scored against category keyword lists (strong +3, weak +1, exclude -5)
5. **Detect breaking** — Stories covered by 3+ quality outlets get flagged
6. **Render** — Jinja2 template generates `index.html` (today) + date archive pages

## Project Structure

```
aggregate.py     — main script: fetch, dedup, categorize, render
config.py        — feeds, categories, companies, dedup settings
template.html    — Jinja2 template with inline CSS + JS
output/          — generated static HTML (not tracked in git)
```

## Deployment

Hosted on Cloudflare Pages. Pushing to `main` triggers deployment from the `output/` directory.

## License

MIT
