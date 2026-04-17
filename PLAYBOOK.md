# Newsmarvin Playbook

Operator's manual for Newsmarvin. Read this before making changes. It is the source of truth when the README and code disagree (the README has known inaccuracies, flagged below).

Live site: https://newsmarvin.com
Repo: https://github.com/mzuniga51/newsmarvin (owned by GitHub account `mzuniga51`, NOT `miabogadoai`)
Hosting: Cloudflare Pages project `newsmarvin` (Git Provider: No)

---

## 1. Overview

Newsmarvin is an AI news aggregator. Each run:

1. Pulls ~60 RSS feeds (see `config.py` `FEEDS`)
2. Filters, dedups, and classifies headlines (Claude Haiku + keyword fallback)
3. Renders a static HTML site (`template.html` -> `output/index.html` and per-day archive pages)
4. Generates `sitemap.xml`, `robots.txt`, `_headers`
5. Optionally sends an email digest to subscribers stored in Cloudflare KV, via Resend

There is no database, no server, no build framework. Output is a directory of HTML files shipped to Cloudflare Pages.

---

## 2. Architecture (text diagram)

```
                        +----------------------+
 RSS feeds (~60) -----> |  aggregate.py        |  --- renders --->  output/
 (config.py FEEDS)      |  fetch -> classify   |                    index.html
                        |  -> dedup -> render  |                    YYYY-MM-DD.html
                        +----------+-----------+                    sitemap.xml
                                   |                                robots.txt
                                   | reads subscriber COUNT         _headers
                                   v                                static assets
                          Cloudflare KV (NEWSMARVIN_SUBSCRIBERS)
                                   ^
                                   | reads subscriber LIST
                        +----------+-----------+
                        |  send_digest.py      | ---- Resend ----> Subscribers
                        |  (reuses pipeline)   |   batch API
                        +----------------------+

 output/ --- `wrangler pages deploy` ---> Cloudflare Pages (newsmarvin.com)

 Pages Functions (functions/api/*.js):
   POST /api/subscribe    -> writes email to KV
   GET  /api/unsubscribe  -> deletes email from KV
```

---

## 3. File and directory map

Top-level (absolute paths rooted at `/Users/manuelzuniga/ai/projects/newsmarvin/`):

| Path | What it is |
|---|---|
| `aggregate.py` | Main pipeline (~1088 lines). Entry point `main()` at bottom. Key functions: `fetch_feeds`, `classify_with_haiku`, `dedup_similar`, `build_sections`, `render_page`, `build_calendars`, `get_subscriber_count`. |
| `send_digest.py` | Daily email sender (~322 lines). Reuses `fetch_feeds`, `dedup_similar`, `build_sections` from aggregate. `fetch_subscribers` pages through KV keys. `send_emails` uses Resend batch API (50 per batch, 3 retries, 30s delay). |
| `config.py` | `FEEDS` dict, `TIER2_SOURCES`, `AI_KEYWORDS`, `CATEGORIES`, `COMPANIES`, dedup thresholds, LLM model constant (`claude-haiku-4-5-20251001`), `TIMEZONE_OFFSET = -6`. |
| `template.html` | Jinja2 template (~892 lines). Inline CSS and JS. Contains `.es-banner` (Spanish translate link), calendar, company filter, search, dark mode. |
| `run_daily.sh` | Local daily runner. **HAS A BUG**: cd path is `/Users/manuelzuniga/ai/newsmarvin` which does not exist. Real path is `/Users/manuelzuniga/ai/projects/newsmarvin`. |
| `requirements.txt` | `feedparser`, `jinja2`, `requests`, `anthropic`. |
| `wrangler.toml` | Pages project config. KV binding `NEWSMARVIN_SUBSCRIBERS` -> id `9a4d8965976e4a619e97ce31c7ba842b`. |
| `functions/api/subscribe.js` | Pages Function. POST JSON `{email}` writes to KV. CORS open. |
| `functions/api/unsubscribe.js` | Pages Function. GET `?email=...` deletes KV entry, returns HTML page. |
| `static/` | Assets copied into `output/` on render: `logo.png`, `logo-sm.png`, `logo-email.png`, `logo-email.webp`, `team.html`, team photos, `kill-bill.mp3`, `marvin-motivation.mp4`, `ribbon.png`. |
| `output/` | Generated site. **Gitignored.** Must regenerate before deploy. |
| `.github/workflows/update-site.yml` | GH Actions cron at 06:00 UTC (midnight CST): aggregate + deploy. No email. |
| `.github/workflows/daily-digest.yml` | GH Actions cron at 12:00 UTC (06:00 CST): aggregate + send email + deploy + retry-send job 1h later if email failed. |
| `.env` | Local secrets (gitignored). See section 4. |
| `generate_logo.py`, `logo.png`, `ribbon.png`, `logos/` | One-off asset generation. Not part of the runtime pipeline. |
| `mempalace.yaml` | mempalace config, unrelated to runtime. |
| `SHOW_HN.md`, `README.md` | Docs. README is partially inaccurate - see section 15. |

---

## 4. Environment variables

All read from process env. Local values live in `.env` (gitignored). Same names are set as GitHub Actions secrets for the workflows.

| Var | Purpose |
|---|---|
| `RESEND_API_KEY` | Auth for Resend batch email API. Used by `send_digest.py`. |
| `CF_ACCOUNT_ID` | Cloudflare account id `d9cace2c6112e8c6b46b5d2d95a98525`. Used for KV list, Pages deploy. |
| `CF_API_TOKEN` | Cloudflare API token with KV read and Pages deploy permissions. |
| `CF_DNS_TOKEN` | DNS edit token. Not used by the runtime pipeline; kept for manual DNS work. |
| `KV_NAMESPACE_ID` | `9a4d8965976e4a619e97ce31c7ba842b` - NEWSMARVIN_SUBSCRIBERS KV namespace. |
| `ANTHROPIC_API_KEY` | Claude Haiku for classify + dedup. If missing or credits depleted, the pipeline warns and falls back to keyword-only classification. Site still builds. |

Never commit `.env`. Secrets must be rotated through both `.env` and the `mzuniga51/newsmarvin` GitHub secrets.

---

## 5. Local development

```bash
cd /Users/manuelzuniga/ai/projects/newsmarvin
pip install -r requirements.txt

# Load env
export $(grep -v '^#' .env | xargs)

# Rebuild site into output/
python3 aggregate.py

# Preview
open output/index.html
```

To test the email build without sending, comment out `send_emails(...)` in `send_digest.py` `main()` or run it against a KV namespace with a single test email. There is no dry-run flag.

Template changes take effect on the next `aggregate.py` run. JS and CSS are inline in `template.html`.

---

## 6. Deploy end-to-end

Cloudflare Pages for this project is **not** linked to git. Pushing to GitHub does NOT ship the site by itself - the GitHub Actions workflow has to run (or you deploy manually with wrangler). The README's claim that "pushing to main triggers deployment from the output directory" is wrong.

### Manual deploy from laptop

```bash
cd /Users/manuelzuniga/ai/projects/newsmarvin

# 1. Edit template.html / aggregate.py / config.py / static/* as needed

# 2. Regenerate output/
export $(grep -v '^#' .env | xargs)
python3 aggregate.py

# 3. Switch GitHub identity (repo is under mzuniga51, not miabogadoai)
gh auth switch -u mzuniga51

# 4. Commit and push template/code changes. output/ is gitignored so it's not in the push.
git add -A
git commit -m "description"
git push

# 5. THIS is what actually ships the site:
npx wrangler pages deploy output/ --project-name=newsmarvin --branch=main
```

Step 5 is the only step that updates the live site from a laptop. Skipping it means the site stays stale.

### Via GitHub Actions

Either workflow (`update-site.yml` or `daily-digest.yml`) runs `python aggregate.py` and then `npx wrangler pages deploy output --project-name=newsmarvin`. Trigger manually with:

```bash
gh auth switch -u mzuniga51
gh workflow run update-site.yml -R mzuniga51/newsmarvin
# or
gh workflow run daily-digest.yml -R mzuniga51/newsmarvin
```

---

## 7. Daily pipeline

Two automated paths exist:

1. **GitHub Actions** - `update-site.yml` runs at 06:00 UTC (midnight CST) daily, aggregate + deploy only. `daily-digest.yml` runs at 12:00 UTC (06:00 CST), aggregate + email + deploy, with a `retry-send` job that waits 1 hour and retries email if the first send failed. This is the primary mechanism in production.

2. **Local `run_daily.sh`** - wraps aggregate + send_digest. **Known bug**: first line is `cd /Users/manuelzuniga/ai/newsmarvin` which does not exist. Should be `/Users/manuelzuniga/ai/projects/newsmarvin`. Fix before wiring to launchd/cron. There is currently no launchd or crontab entry on the MacBook that invokes it; laptop runs are on-demand only.

---

## 8. Subscribers and email

- Storage: Cloudflare KV namespace `NEWSMARVIN_SUBSCRIBERS` (id `9a4d8965976e4a619e97ce31c7ba842b`). Key = email (lowercased), value = JSON `{subscribed_at: ISO timestamp}`.
- Subscribe endpoint: `POST /api/subscribe` with JSON `{email}`. Implemented at `functions/api/subscribe.js`. Validates `@` and `.` only; no confirmation email.
- Unsubscribe endpoint: `GET /api/unsubscribe?email=...`. Implemented at `functions/api/unsubscribe.js`. Deletes KV entry, returns HTML confirmation page.
- Digest sender: `send_digest.py`. From address `Newsmarvin <morning@mzuniga.com>`. Subject line: `Newsmarvin - <Month DD, YYYY>` (see `build_email`, `send_digest.py` line ~95).
- Batch size: 50 per Resend batch call.
- Retry: 3 attempts per batch with 30s delay in-script. If 0 sends succeed the script exits code 2, which signals the workflow `retry-send` job to kick in 1h later.
- Known outage: 2026-04-10 Resend returned `405 method_not_allowed` for `/emails/batch`, 0/29 sent. Transient. Retry logic was added in response (commit `05e410a`).
- Subscriber count as of last check: ~29.

---

## 9. AI classification

- Model: `claude-haiku-4-5-20251001` (see `config.py` `LLM_MODEL`).
- Two passes, both via batch of 100 headlines (`classify_with_haiku`, `aggregate.py`):
  - Pass 1: assigns `category` + `companies`.
  - Pass 2: assigns a `story` slug (for LLM-driven dedup clustering) + `importance` (1-3).
- Junk pre-filter: regex in `classify_with_haiku` drops obvious listicles, subscriber-only content, "I asked ChatGPT" pieces before spending tokens.
- Post-LLM keyword dedup fallback handles anything the LLM didn't cluster, plus a merge pass that combines LLM clusters whose reps overlap at or above 0.45 similarity.
- Graceful degradation: if `ANTHROPIC_API_KEY` is missing, the `anthropic` package is not installed, or an API call fails, the pipeline logs `WARNING` and keeps keyword classifications. The site still renders. If Anthropic credits are depleted, expect the same behavior - site builds, categorization quality drops.

---

## 10. Known issues and watch-outs

- **`run_daily.sh` has a broken cd path** - `/Users/manuelzuniga/ai/newsmarvin` vs real `/Users/manuelzuniga/ai/projects/newsmarvin`. Fix before relying on it.
- **GitHub account switch** - Default `gh` session on this machine is usually `miabogadoai`. Pushing to `mzuniga51/newsmarvin` without `gh auth switch -u mzuniga51` returns 403.
- **output/ is gitignored** - `git push` never ships the site. Always regenerate with `aggregate.py` and then `wrangler pages deploy`.
- **Pages is not git-linked** - dashboard shows "Git Provider: No". This is intentional because there is nothing for Pages to build from (output is gitignored). Deploys are manual via wrangler or via the GH Actions workflows that invoke wrangler.
- **Traffic numbers are inflated by crawlers** - Cloudflare's 10K pageviews figure is HTTP requests including bots. Real humans tracked by the web analytics beacon: ~200/month (Mar 2026). AI crawl volume up 518% period-over-period. All currently set to Allow.
- **Anthropic credit depletion** is silent-ish: pipeline prints a warning and continues. Watch the log for "WARNING: classify batch ... failed".
- **Tier 2 (traditional media) sources are filtered by AI keyword match in title or description**; if `AI_KEYWORDS` is edited, a lot of content can vanish.

---

## 11. Design constraints (non-negotiable)

- **The Marvin logo stays.** Marvin was Manuel's Pomeranian, who passed away in March 2026 from Cushing's disease. The project is a tribute. When performance issues involve the logo (e.g. LCP complaints), optimize - never remove or hide. Prior fixes have been compression + WebP (`logo-email.webp`).
- **No em dashes or en dashes** anywhere in code comments, UI copy, commit messages, or any user-facing content. Regular hyphens only.
- **Brutalist aesthetic** - inline CSS/JS, Verdana, no framework. Keep it that way.

---

## 12. Costa Rica timezone

All display times are in CST (UTC-6). `TIMEZONE_OFFSET = -6` in `config.py`, `CR_TZ = timezone(timedelta(hours=TIMEZONE_OFFSET))` in `aggregate.py`. Day boundaries, archive page filenames (`YYYY-MM-DD.html`), and the "Last 24 hours" cutoff all anchor to this tz. Do not change the constant without understanding that archive URLs are date-stamped.

---

## 13. Shipped features of note

- **WebP logo** (`logo-email.webp`, commit `3cedef4`) - faster sidebar loading, used alongside PNG fallback.
- **Google News redirect resolution** (commit `697d5f8`) - `fetch_feeds` does a HEAD request against `news.google.com` links to resolve to the real publisher URL. 5s timeout, falls back silently.
- **Spanish translation banner** (`.es-banner` in `template.html` around line 591) - sits between `</header>` and `<div class="page">`. Cream-to-gold gradient, deep purple text, inline SVG Spain flag, reads "Ahora también en Español". Links to `https://translate.google.com/translate?sl=auto&tl=es&u=https://newsmarvin.com{canonical_path}` - Google Translate proxy, zero cost. Preserves wrapper on outbound article clicks. An alternative (Workers AI `@cf/meta/m2m100-1.2b` at build time for real pre-translated titles) is not implemented.
- **Retry logic for digest** (commit `05e410a`) - 3 attempts per Resend batch plus a workflow-level retry job 1h later.
- **Static site with client-side filtering** - full archive indexed as a JSON blob in the page so company filter and search work across days without a backend.

---

## 14. Common tasks

### Add a feed
Edit `config.py` `FEEDS` dict. If it's a noisy general-tech source, add it to `TIER2_SOURCES` so it gets AI-keyword-filtered. Regenerate with `python3 aggregate.py`. Deploy.

### Remove a source
Delete the entry from `FEEDS` in `config.py`, delete from `TIER2_SOURCES` if present. Regenerate. Deploy. Example commit: `156a3d2` removed Wired and Times of India.

### Change the digest subject line
`send_digest.py` `build_email`, around line 95: `subject = f"Newsmarvin - {display_date}"`. Edit and redeploy. Purely a send-time change, no site rebuild needed.

### Regenerate archive for a specific day
Archive pages are rebuilt every `aggregate.py` run from the last 30 days of fetched headlines (controlled by `MAX_HEADLINE_AGE_DAYS` in `config.py`). There is no selective-day rebuild. Run `aggregate.py` and deploy; the target day will be refreshed if it's within the 30-day window.

### Force a redeploy (same content)
```bash
cd /Users/manuelzuniga/ai/projects/newsmarvin
npx wrangler pages deploy output/ --project-name=newsmarvin --branch=main
```
Or trigger the GH Actions workflow:
```bash
gh auth switch -u mzuniga51
gh workflow run update-site.yml -R mzuniga51/newsmarvin
```

### Add a category
Edit `CATEGORIES` in `config.py`. Also update the LLM prompt in `classify_with_haiku` (aggregate.py ~line 455) so Haiku knows the new category exists - otherwise it will never classify anything into it.

### Test changes without shipping
Build locally, open `output/index.html` in a browser. There is no staging/preview environment.

---

## 15. Troubleshooting

### Site is blank / missing headlines
- Check last workflow run: `gh run list -R mzuniga51/newsmarvin -L 5`
- Re-run aggregate locally with env vars set. Inspect `output/index.html`. Look for feed fetch failures in stdout - feeds that 403 or 404 just print `FAIL:` and are skipped.
- If all feeds failed, check network / DNS.

### aggregate.py crashed mid-run
- Look for `WARNING: classify batch ... failed` - LLM issue, likely credits. Pipeline should still complete.
- Unicode errors on `.write_text(html)` (render_page) - rare, rerun.
- `ImportError: anthropic` - `pip install anthropic` and rerun.

### Emails not sending
- First check: did aggregate run? Digest won't build if `fetch_feeds()` returns empty.
- Resend 405 - known transient issue (Apr 10). Retry will happen automatically 1h later via the `retry-send` job. For manual retry: `gh workflow run daily-digest.yml -R mzuniga51/newsmarvin`.
- Any other 4xx/5xx from Resend - check API key validity, check From domain `mzuniga.com` is still verified in Resend.
- 0 subscribers fetched - KV token scope issue. Verify `CF_API_TOKEN` has Workers KV read on the right account/namespace.

### Pages deploy failing
- `gh auth switch -u mzuniga51` first if this is a laptop deploy that needs to push too.
- `wrangler pages deploy` auth uses `CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_API_TOKEN`. Local-only deploys rely on `wrangler`'s own OAuth login (`wrangler login`) unless those env vars are set.
- Project name must be exactly `newsmarvin` with `--branch=main`.

### Subscribers not showing in count
- `get_subscriber_count` in `aggregate.py` hits the KV list API and reads `result_info.count`. If CF env vars are missing, it silently returns 0. The site still builds.

### "It deployed but the site didn't change"
- Did you regenerate `output/` before `wrangler pages deploy`? The deploy uploads whatever's in the directory. No regen = same site.
- Cloudflare cache: `_headers` sets 1h cache on index.html, 24h on other html. Use a cache-bust query string to verify.

---

## 16. Quick reference

- Cloudflare account ID: `d9cace2c6112e8c6b46b5d2d95a98525`
- KV namespace id: `9a4d8965976e4a619e97ce31c7ba842b`
- Cloudflare dashboard login: zuniga.manuel@gmail.com
- Pages project: `newsmarvin` (branch: `main`)
- Repo: `mzuniga51/newsmarvin`
- From email: `Newsmarvin <morning@mzuniga.com>`
- LLM: `claude-haiku-4-5-20251001`
- Timezone: CST (UTC-6)
