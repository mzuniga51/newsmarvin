# Show HN Draft

**Title:** Show HN: NewsMarvin – AI news aggregator with LLM-based classification

**Body:**

I read AI news every day across dozens of sources and got tired of the fragmentation — so I built NewsMarvin to solve it for myself. It pulls from 60+ RSS feeds, deduplicates stories, and categorizes everything automatically.

The interesting part: keyword-based classification kept failing in obvious ways ("DMEC Releases Policy Brief" → Releases, "AIs happy to launch nukes" → Releases because of "launch"). So I switched to Claude Haiku as the primary classifier — all articles go through one batched API call that returns categories and company tags. Keywords remain as fallback if the API is down. The LLM classification costs about $0.01/run.

How it works:

- **60+ RSS feeds** — company blogs (OpenAI, Google, Anthropic), news sites (TechCrunch, Ars Technica, The Register), research (Nature, arXiv), newsletters, Google News searches
- **Entity-aware dedup** — title similarity + entity extraction catches "OpenAI releases GPT-5" and "GPT-5 is here from OpenAI" as the same story
- **Haiku classification** — one API call classifies all articles into Releases, Business, Research, Policy, People, Vibe Coding, etc. with context awareness keywords can't match
- **Dynamic company filters** — Haiku also tags companies, so new players show up as filter buttons automatically
- **Paywall filtering** — paywalled sources are detected and excluded automatically, both by feed source and by LLM content analysis
- **Breaking news detection** — stories covered by 3+ quality outlets get promoted to Top News
- **Source gating** — only trusted sources (universities, labs, journals) can contribute to Research

No database, no JS framework. Python + feedparser + Jinja2 → static HTML on Cloudflare Pages. Updates every 4 hours via GitHub Actions. Free daily email digest at 6 AM.

If this is useful to you too, I'd love to hear about it. Suggestions welcome at zuniga.manuel@gmail.com.

Live: https://newsmarvin.com | Code: https://github.com/mzuniga51/newsmarvin
