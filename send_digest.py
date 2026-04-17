#!/usr/bin/env python3
# =============================================================================
# NewsMarvin — Daily Email Digest Sender
# =============================================================================
# Runs after aggregate.py. Fetches today's articles from the same pipeline,
# builds a brutalist email (plain text + minimal HTML), fetches subscriber
# list from Cloudflare KV, and sends via Resend batch API.
#
# Usage:
#   python send_digest.py
#
# Environment variables:
#   RESEND_API_KEY        — Resend API key
#   CF_ACCOUNT_ID         — Cloudflare account ID
#   CF_API_TOKEN          — Cloudflare API token (KV read access)
#   KV_NAMESPACE_ID       — KV namespace ID for NEWSMARVIN_SUBSCRIBERS
# =============================================================================

import os
import sys
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from aggregate import fetch_feeds, dedup_similar, group_by_day, build_sections, CR_TZ
from config import CATEGORIES, DEFAULT_CATEGORY

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
KV_NAMESPACE_ID = os.environ.get("KV_NAMESPACE_ID", "")

FROM_EMAIL = "Newsmarvin <morning@mzuniga.com>"
BATCH_SIZE = 50  # Resend batch limit


# ---------------------------------------------------------------------------
# Fetch subscribers from Cloudflare KV
# ---------------------------------------------------------------------------

def fetch_subscribers():
    """List all subscriber emails from Cloudflare KV."""
    if not CF_ACCOUNT_ID or not CF_API_TOKEN or not KV_NAMESPACE_ID:
        print("ERROR: Missing Cloudflare env vars (CF_ACCOUNT_ID, CF_API_TOKEN, KV_NAMESPACE_ID)")
        sys.exit(1)

    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{KV_NAMESPACE_ID}/keys"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}

    emails = []
    cursor = None

    while True:
        params = {"limit": 1000}
        if cursor:
            params["cursor"] = cursor

        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()

        if not data.get("success"):
            print(f"ERROR: KV list failed: {data.get('errors')}")
            sys.exit(1)

        for key in data.get("result", []):
            emails.append(key["name"])

        cursor = data.get("result_info", {}).get("cursor")
        if not cursor:
            break

    return emails


def fetch_subscriber_lang(email):
    """Fetch a single subscriber's lang preference from KV. Returns 'es' or 'en'."""
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{KV_NAMESPACE_ID}/values/{email}"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return "en"
        data = json.loads(resp.text)
        return "es" if data.get("lang") == "es" else "en"
    except Exception:
        return "en"


# ---------------------------------------------------------------------------
# Translation (Cloudflare Workers AI via Pages Function)
# ---------------------------------------------------------------------------

TRANSLATE_SECRET = os.environ.get("TRANSLATE_SECRET", "")
TRANSLATE_ENDPOINT = "https://newsmarvin.com/api/translate"


def translate_batch(texts, target_lang="spanish"):
    """Translate a list of strings via Workers AI. Returns list same length; '' for any failed item."""
    if not texts:
        return []
    if not TRANSLATE_SECRET:
        print("  WARNING: TRANSLATE_SECRET not set; skipping translation")
        return list(texts)
    try:
        resp = requests.post(
            TRANSLATE_ENDPOINT,
            headers={
                "X-Translate-Key": TRANSLATE_SECRET,
                "Content-Type": "application/json",
            },
            json={"texts": texts, "source_lang": "english", "target_lang": target_lang},
            timeout=120,
        )
        if resp.status_code != 200:
            print(f"  WARNING: translate {resp.status_code}: {resp.text[:200]}")
            return list(texts)
        data = resp.json()
        translations = data.get("translations", [])
        return [t or orig for t, orig in zip(translations, texts)]
    except Exception as e:
        print(f"  WARNING: translate failed: {e}")
        return list(texts)


# Domains that reject Google Translate's proxy fetcher (usually because of
# Cloudflare or similar bot-protection). For these, we link direct to the
# English article and let the reader use their browser's built-in translation.
# Grow this list as failures are reported.
PROXY_UNFRIENDLY_DOMAINS = {
    "axios.com",
    "bloomberg.com",
    "wsj.com",
    "nytimes.com",
    "ft.com",
    "reuters.com",
    "forbes.com",
    "barrons.com",
}


def _domain_of(url):
    from urllib.parse import urlparse
    try:
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def wrap_google_translate(url, target="es"):
    """Wrap an article URL through Google Translate's web proxy for read-time
    translation. For known-blocked domains, return the URL unwrapped so the
    reader gets the English article directly instead of a Google error page."""
    host = _domain_of(url)
    for bad in PROXY_UNFRIENDLY_DOMAINS:
        if host == bad or host.endswith("." + bad):
            return url
    from urllib.parse import quote
    return f"https://translate.google.com/translate?sl=auto&tl={target}&u={quote(url, safe='')}"


ES_MONTHS = {
    "Jan": "ene", "Feb": "feb", "Mar": "mar", "Apr": "abr", "May": "may", "Jun": "jun",
    "Jul": "jul", "Aug": "ago", "Sep": "sep", "Oct": "oct", "Nov": "nov", "Dec": "dic",
}


def spanish_date(en_date_str):
    """Convert 'Apr 16, 2026' -> '16 abr 2026'."""
    parts = en_date_str.replace(",", "").split()
    if len(parts) == 3:
        mon, day, year = parts
        return f"{int(day)} {ES_MONTHS.get(mon, mon.lower())} {year}"
    return en_date_str


# ---------------------------------------------------------------------------
# Build email content
# ---------------------------------------------------------------------------

LOGO_URL = "https://newsmarvin.com/logo-email.png"


def _html_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_email(sections, today_str, total_headlines, total_sources, subscriber_count=0, lang="en"):
    """Build plain text and HTML email matching the website design.

    lang: "en" (default) or "es". For "es": translates headline titles and category
    names via Workers AI, localizes UI labels, and wraps article links through
    Google Translate proxy so readers can read full articles in Spanish.
    """
    display_date_en = datetime.strptime(today_str, "%Y-%m-%d").strftime("%b %d, %Y")

    # Translate headlines + category names in one batch if needed
    is_es = (lang == "es")
    if is_es:
        titles_in = [h["title"] for _, hs in sections for h in hs]
        cats_in = [c for c, _ in sections]
        batch_in = titles_in + cats_in
        if batch_in:
            batch_out = translate_batch(batch_in)
            titles_out = batch_out[:len(titles_in)]
            cats_out = batch_out[len(titles_in):]
        else:
            titles_out, cats_out = [], []
        # Map back into sections (deep copy to avoid mutating caller's data)
        translated_sections = []
        idx = 0
        for (cat, hs), cat_es in zip(sections, cats_out):
            new_hs = []
            for h in hs:
                nh = dict(h)
                nh["title"] = titles_out[idx] or h["title"]
                idx += 1
                new_hs.append(nh)
            translated_sections.append((cat_es or cat, new_hs))
        sections = translated_sections
        display_date = spanish_date(display_date_en)
        subject = f"Newsmarvin — {display_date}"
        L = {
            "tagline": "Tus noticias de IA, sin filtros",
            "headlines": "titulares",
            "sources": "fuentes",
            "unsubscribe": "Cancelar suscripción",
            "html_lang": "es",
        }
    else:
        display_date = display_date_en
        subject = f"Newsmarvin — {display_date}"
        L = {
            "tagline": "Your AI news, served raw",
            "headlines": "headlines",
            "sources": "sources",
            "unsubscribe": "Unsubscribe",
            "html_lang": "en",
        }

    # Plain text version
    sub_text = f" · {subscriber_count}s" if subscriber_count else ""
    text_lines = [f"Newsmarvin — {display_date}", f"{total_headlines} {L['headlines']} · {total_sources} {L['sources']}{sub_text}", ""]

    for cat_name, headlines in sections:
        text_lines.append(f"{cat_name} ({len(headlines)})")
        text_lines.append("-" * 40)
        for h in headlines:
            prefix = "** " if h.get("_breaking") else ""
            also = f" +{len(h['_also_covered_by'])}" if h.get("_also_covered_by") else ""
            link = wrap_google_translate(h["link"]) if is_es else h["link"]
            text_lines.append(f"  {h['time_str']}  {prefix}{h['title']}")
            text_lines.append(f"         {link}")
            text_lines.append(f"         ({h['source']}{also})")
            text_lines.append("")
        text_lines.append("")

    text_lines.append("—")
    text_lines.append(f"newsmarvin.com - {L['tagline']}")
    text_lines.append("")
    text_lines.append(f"{L['unsubscribe']}: %%UNSUB_URL%%")
    text_body = "\n".join(text_lines)

    # HTML version
    logo_img = (
        f'<img src="{LOGO_URL}" '
        f'alt="Marvin" width="60" height="60" '
        f'style="display:inline-block;vertical-align:middle;border-radius:50%;">'
    )

    # Spanish-only strip announcing the translation provenance
    if is_es:
        es_strip = (
            '<div style="background:linear-gradient(90deg,#f4ebcc 0%,#ecdfb0 100%);'
            'border-bottom:2px solid #826eb4;padding:10px 20px;color:#4a3d6b;'
            'font-weight:600;font-size:13px;font-family:Verdana,Geneva,sans-serif;">'
            '<table cellpadding="0" cellspacing="0" border="0" style="width:100%;"><tr>'
            # Spain flag
            '<td style="width:30px;vertical-align:middle;">'
            '<table cellpadding="0" cellspacing="0" border="0" style="border:1px solid rgba(74,61,107,0.3);border-radius:2px;overflow:hidden;">'
            '<tr><td style="width:24px;height:4px;background:#AA151B;font-size:0;line-height:0;">&nbsp;</td></tr>'
            '<tr><td style="width:24px;height:8px;background:#F1BF00;font-size:0;line-height:0;">&nbsp;</td></tr>'
            '<tr><td style="width:24px;height:4px;background:#AA151B;font-size:0;line-height:0;">&nbsp;</td></tr>'
            '</table></td>'
            # label + sub
            '<td style="vertical-align:middle;padding-left:10px;">'
            'Ahora también en Español '
            '<span style="font-weight:400;opacity:0.7;font-size:11px;">&middot; traducido por Google</span>'
            '</td>'
            # Google Translate icon
            '<td style="width:26px;vertical-align:middle;text-align:right;">'
            '<svg width="18" height="18" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="display:inline-block;vertical-align:middle;">'
            '<rect x="0" y="0" width="14" height="14" rx="2" fill="#4285F4"/>'
            '<text x="7" y="11" font-family="Arial,Helvetica,sans-serif" font-size="10" fill="#fff" text-anchor="middle" font-weight="700">&#25991;</text>'
            '<rect x="9" y="9" width="14" height="14" rx="2" fill="#fff" stroke="#4285F4" stroke-width="1.4"/>'
            '<text x="16" y="20" font-family="Arial,Helvetica,sans-serif" font-size="10" fill="#4285F4" text-anchor="middle" font-weight="700">A</text>'
            '</svg>'
            '</td>'
            '</tr></table>'
            '</div>'
        )
    else:
        es_strip = ""

    # Build sections
    sections_html = []
    for cat_name, headlines in sections:
        anchor = cat_name.lower().replace(" & ", "-").replace(" ", "-")
        rows = []
        for h in headlines:
            weight = "font-weight:bold;" if h.get("_breaking") else ""
            also = f" +{len(h['_also_covered_by'])}" if h.get("_also_covered_by") else ""
            title_esc = _html_escape(h["title"])
            source_esc = _html_escape(h["source"])
            link = wrap_google_translate(h["link"]) if is_es else h["link"]
            # Show (original) fallback only when the primary link is going through the proxy
            show_fallback = is_es and link != h["link"]
            original_link = (
                f' <a href="{h["link"]}" style="color:#bbb;font-size:10px;text-decoration:underline;" target="_blank">(original)</a>'
                if show_fallback else ""
            )
            rows.append(
                f'<tr><td style="color:#999;font-size:12px;white-space:nowrap;'
                f'vertical-align:baseline;padding:3px 8px 3px 0;font-family:Verdana,Geneva,sans-serif;">'
                f'{h["time_str"]}</td>'
                f'<td style="padding:3px 0;font-size:13px;line-height:1.4;font-family:Verdana,Geneva,sans-serif;{weight}">'
                f'<a href="{link}" style="color:#00c;text-decoration:none;" target="_blank">'
                f'{title_esc}</a> '
                f'<span style="color:#999;font-size:11px;white-space:nowrap;">'
                f'({source_esc}{also})</span>{original_link}'
                f'</td></tr>'
            )
        sections_html.append(
            f'<div id="cat-{anchor}" style="margin:20px 0;">'
            f'<div style="font-size:14px;font-weight:bold;color:#826eb4;'
            f'padding:6px 0 4px;border-bottom:2px solid #826eb4;margin-bottom:6px;'
            f'font-family:Verdana,Geneva,sans-serif;">'
            f'{_html_escape(cat_name)} '
            f'<span style="color:#999;font-weight:normal;font-size:13px;">({len(headlines)})</span>'
            f'</div>'
            f'<table cellpadding="0" cellspacing="0" border="0" style="width:100%;">'
            f'{"".join(rows)}</table></div>'
        )

    html_body = f"""<!DOCTYPE html>
<html lang="{L['html_lang']}"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ai news — {display_date}</title></head>
<body style="margin:0;padding:0;background:#f6f6f0;color:#222;font-family:Verdana,Geneva,sans-serif;font-size:15px;line-height:1.6;">

<!--[if mso]><table width="700" cellpadding="0" cellspacing="0" border="0" align="center"><tr><td><![endif]-->
<div style="max-width:700px;margin:0 auto;">

<!-- Header with Marvin -->
<div style="background:#826eb4;padding:16px 20px;">
<table cellpadding="0" cellspacing="0" border="0" style="width:100%;"><tr>
<td style="width:70px;vertical-align:middle;">{logo_img}</td>
<td style="vertical-align:middle;padding-left:14px;">
<div style="color:#fff;font-size:20px;font-weight:bold;letter-spacing:2px;font-family:Verdana,Geneva,sans-serif;">
<a href="https://newsmarvin.com" style="color:#fff;text-decoration:none;">Newsmarvin</a>
</div>
<div style="color:rgba(255,255,255,0.55);font-size:11px;margin-top:2px;font-family:Verdana,Geneva,sans-serif;">
{L['tagline']} &middot; {display_date} &middot; {total_headlines} {L['headlines']} &middot; {total_sources} {L['sources']}{f" &middot; {subscriber_count}s" if subscriber_count else ""}
</div>
</td>
</tr></table>
</div>

{es_strip}

<!-- Body -->
<div style="padding:16px 24px;">

<!-- Headlines -->
{"".join(sections_html)}

</div>

<!-- Footer -->
<div style="border-top:1px solid #ddd;padding:14px 20px;color:#999;font-size:13px;text-align:center;font-family:Verdana,Geneva,sans-serif;">
<a href="https://newsmarvin.com" style="color:#826eb4;text-decoration:none;">newsmarvin.com</a>
 &middot; {datetime.now(CR_TZ).strftime("%Y-%m-%d %H:%M CST")}
<div style="margin-top:16px;">
<a href="%%UNSUB_URL%%" style="display:inline-block;padding:10px 28px;background:#826eb4;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold;">{L['unsubscribe']}</a>
</div>
</div>

</div>
<!--[if mso]></td></tr></table><![endif]-->
</body></html>"""

    return subject, text_body, html_body


# ---------------------------------------------------------------------------
# Send via Resend
# ---------------------------------------------------------------------------

SEND_MAX_RETRIES = 3
SEND_RETRY_DELAY = 30  # seconds between retries


def send_emails(subscribers, subject, text_body, html_body):
    """Send digest to all subscribers using Resend batch API."""
    if not RESEND_API_KEY:
        print("ERROR: Missing RESEND_API_KEY")
        sys.exit(1)

    total_sent = 0

    for i in range(0, len(subscribers), BATCH_SIZE):
        batch = subscribers[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        emails = []
        for email in batch:
            unsub_url = f"https://newsmarvin.com/api/unsubscribe?email={email}"
            emails.append({
                "from": FROM_EMAIL,
                "to": [email],
                "subject": subject,
                "text": text_body.replace("%%UNSUB_URL%%", unsub_url),
                "html": html_body.replace("%%UNSUB_URL%%", unsub_url),
            })

        for attempt in range(1, SEND_MAX_RETRIES + 1):
            resp = requests.post(
                "https://api.resend.com/emails/batch",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=emails,
            )

            if resp.status_code == 200:
                total_sent += len(batch)
                print(f"  Sent batch {batch_num}: {len(batch)} emails")
                break
            else:
                print(f"  ERROR batch {batch_num} (attempt {attempt}/{SEND_MAX_RETRIES}): {resp.status_code} {resp.text}")
                if attempt < SEND_MAX_RETRIES:
                    import time
                    print(f"  Retrying in {SEND_RETRY_DELAY}s...")
                    time.sleep(SEND_RETRY_DELAY)

    return total_sent


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", help="Send only to this email address (dev)")
    parser.add_argument("--force-lang", choices=["en", "es"], help="Override the test recipient's lang preference")
    args = parser.parse_args()

    print("\n=== NewsMarvin Daily Digest ===\n")

    # Reuse the same pipeline as aggregate.py
    print("Fetching feeds...")
    headlines = fetch_feeds()

    if not headlines:
        print("No headlines. Skipping digest.")
        sys.exit(0)

    headlines = dedup_similar(headlines)

    # Last 24 hours of headlines (not calendar "today")
    now = datetime.now(CR_TZ)
    cutoff_24h = now - timedelta(hours=24)
    recent_hl = [h for h in headlines if h["published"].astimezone(CR_TZ) >= cutoff_24h]

    if not recent_hl:
        print("No headlines in the last 24h. Skipping digest.")
        sys.exit(0)

    # Add time_str for display
    for h in recent_hl:
        local = h["published"].astimezone(CR_TZ)
        h["time_str"] = local.strftime("%H:%M")

    sections = build_sections(recent_hl)
    today_str = now.strftime("%Y-%m-%d")

    print(f"\nLast 24h: {len(recent_hl)} headlines in {len(sections)} sections")

    # Fetch subscribers
    if args.test:
        subscribers = [args.test.strip().lower()]
        print(f"\nTEST MODE - only sending to: {subscribers[0]}")
    else:
        print("\nFetching subscribers...")
        subscribers = fetch_subscribers()
        print(f"Subscribers: {len(subscribers)}")

    if not subscribers:
        print("No subscribers. Done.")
        sys.exit(0)

    # Split by language preference
    en_subs, es_subs = [], []
    for email in subscribers:
        if args.test and args.force_lang:
            lang = args.force_lang
        else:
            lang = fetch_subscriber_lang(email)
        (es_subs if lang == "es" else en_subs).append(email)
    print(f"  EN: {len(en_subs)}  ES: {len(es_subs)}")

    from config import FEEDS
    total_sent = 0

    if en_subs:
        print("\nBuilding English digest...")
        subject, text_body, html_body = build_email(sections, today_str, len(recent_hl), len(FEEDS), len(subscribers), lang="en")
        print(f"  Subject: {subject}")
        print(f"Sending to {len(en_subs)} EN subscriber(s)...")
        total_sent += send_emails(en_subs, subject, text_body, html_body)

    if es_subs:
        print("\nBuilding Spanish digest (translating headlines + categories)...")
        subject, text_body, html_body = build_email(sections, today_str, len(recent_hl), len(FEEDS), len(subscribers), lang="es")
        print(f"  Subject: {subject}")
        print(f"Sending to {len(es_subs)} ES subscriber(s)...")
        total_sent += send_emails(es_subs, subject, text_body, html_body)

    print(f"\nDone. Sent to {total_sent}/{len(subscribers)} subscribers.\n")

    if total_sent == 0 and len(subscribers) > 0:
        sys.exit(2)  # signal failure for workflow retry


if __name__ == "__main__":
    main()
