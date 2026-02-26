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

FROM_EMAIL = "Marvin AI News <morning@mzuniga.com>"
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


# ---------------------------------------------------------------------------
# Build email content
# ---------------------------------------------------------------------------

LOGO_URL = "https://newsmarvin.com/logo-email.png"


def _html_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_email(sections, today_str, total_headlines, total_sources):
    """Build plain text and HTML email matching the website design."""
    display_date = datetime.strptime(today_str, "%Y-%m-%d").strftime("%b %d, %Y")
    subject = f"Marvin AI News — {display_date}"

    # Plain text version
    text_lines = [f"marvin ai news — {display_date}", f"{total_headlines} headlines · {total_sources} sources", ""]

    for cat_name, headlines in sections:
        text_lines.append(f"{cat_name} ({len(headlines)})")
        text_lines.append("-" * 40)
        for h in headlines:
            prefix = "** " if h.get("_breaking") else ""
            also = f" +{len(h['_also_covered_by'])}" if h.get("_also_covered_by") else ""
            text_lines.append(f"  {h['time_str']}  {prefix}{h['title']}")
            text_lines.append(f"         {h['link']}")
            text_lines.append(f"         ({h['source']}{also})")
            text_lines.append("")
        text_lines.append("")

    text_lines.append("—")
    text_lines.append("newsmarvin.com · Your AI news, served raw")
    text_lines.append("")
    text_lines.append("Unsubscribe: %%UNSUB_URL%%")
    text_body = "\n".join(text_lines)

    # HTML version
    logo_img = (
        f'<img src="{LOGO_URL}" '
        f'alt="Marvin" width="60" height="60" '
        f'style="display:inline-block;vertical-align:middle;border-radius:50%;">'
    )

    # Build sections
    sections_html = []
    for cat_name, headlines in sections:
        anchor = cat_name.lower().replace(" & ", "-").replace(" ", "-")
        rows = []
        for h in headlines:
            weight = "font-weight:bold;" if (h.get("_breaking") or cat_name == "Top News") else ""
            also = f" +{len(h['_also_covered_by'])}" if h.get("_also_covered_by") else ""
            title_esc = _html_escape(h["title"])
            source_esc = _html_escape(h["source"])
            rows.append(
                f'<tr><td style="color:#999;font-size:12px;white-space:nowrap;'
                f'vertical-align:baseline;padding:3px 8px 3px 0;font-family:Verdana,Geneva,sans-serif;">'
                f'{h["time_str"]}</td>'
                f'<td style="padding:3px 0;font-size:13px;line-height:1.4;font-family:Verdana,Geneva,sans-serif;{weight}">'
                f'<a href="{h["link"]}" style="color:#00c;text-decoration:none;" target="_blank">'
                f'{title_esc}</a> '
                f'<span style="color:#999;font-size:11px;white-space:nowrap;">'
                f'({source_esc}{also})</span>'
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
<html lang="en"><head><meta charset="UTF-8">
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
<a href="https://newsmarvin.com" style="color:#fff;text-decoration:none;">marvin ai news</a>
</div>
<div style="color:rgba(255,255,255,0.55);font-size:11px;margin-top:2px;font-family:Verdana,Geneva,sans-serif;">
Your AI news, served raw &middot; {display_date} &middot; {total_headlines} headlines &middot; {total_sources} sources
</div>
</td>
</tr></table>
</div>

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
<a href="%%UNSUB_URL%%" style="display:inline-block;padding:10px 28px;background:#826eb4;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold;">Unsubscribe</a>
</div>
</div>

</div>
<!--[if mso]></td></tr></table><![endif]-->
</body></html>"""

    return subject, text_body, html_body


# ---------------------------------------------------------------------------
# Send via Resend
# ---------------------------------------------------------------------------

def send_emails(subscribers, subject, text_body, html_body):
    """Send digest to all subscribers using Resend batch API."""
    if not RESEND_API_KEY:
        print("ERROR: Missing RESEND_API_KEY")
        sys.exit(1)

    total_sent = 0

    for i in range(0, len(subscribers), BATCH_SIZE):
        batch = subscribers[i:i + BATCH_SIZE]

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
            print(f"  Sent batch {i // BATCH_SIZE + 1}: {len(batch)} emails")
        else:
            print(f"  ERROR batch {i // BATCH_SIZE + 1}: {resp.status_code} {resp.text}")

    return total_sent


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
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

    # Build email
    from config import FEEDS
    subject, text_body, html_body = build_email(sections, today_str, len(recent_hl), len(FEEDS))
    print(f"Subject: {subject}")

    # Fetch subscribers
    print("\nFetching subscribers...")
    subscribers = fetch_subscribers()
    print(f"Subscribers: {len(subscribers)}")

    if not subscribers:
        print("No subscribers. Done.")
        sys.exit(0)

    # Send
    print("\nSending...")
    sent = send_emails(subscribers, subject, text_body, html_body)
    print(f"\nDone. Sent to {sent}/{len(subscribers)} subscribers.\n")


if __name__ == "__main__":
    main()
