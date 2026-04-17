#!/usr/bin/env python3
# =============================================================================
# Newsmarvin - Spanish availability announcement (one-off)
# =============================================================================
# Sends a bilingual (EN+ES) email to subscribers announcing that Newsmarvin
# is now available in Spanish, with a unique one-click link to switch their
# preference to Spanish. The daily digest reads the preference from KV.
#
# Usage:
#   python send_announcement.py --test manuel@mzuniga.com     # send to one
#   python send_announcement.py --dry-run                     # preview only
#   python send_announcement.py                               # send to all
#
# Same env vars as send_digest.py.
# =============================================================================

import os
import sys
import argparse
import requests

from send_digest import fetch_subscribers, RESEND_API_KEY, FROM_EMAIL, BATCH_SIZE


def build_announcement(email):
    """Build the Spanish-only announcement email for one subscriber."""
    switch_url = f"https://newsmarvin.com/api/set-language?email={email}&lang=es"
    unsub_url = f"https://newsmarvin.com/api/unsubscribe?email={email}"

    subject = "Newsmarvin, ahora también en Español"

    text_body = f"""Newsmarvin, ahora también en Español

Aviso rápido: Newsmarvin ya está disponible en español. Si prefieres
recibir tu resumen diario de noticias de IA en español a partir de
mañana, haz clic en el enlace de abajo. Un solo toque y listo.

  Cambiar a Español:  {switch_url}

No tienes que hacer nada si prefieres seguir en inglés. Puedes cambiar
cuando quieras desde cualquier futuro resumen.

Gracias por leer,
Manuel y Marvin

---
newsmarvin.com
Cancelar suscripción: {unsub_url}
"""

    html_body = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Newsmarvin, ahora también en Español</title></head>
<body style="margin:0;padding:0;background:#f6f6f0;color:#222;font-family:Verdana,Geneva,sans-serif;font-size:15px;line-height:1.6;">
<div style="max-width:560px;margin:0 auto;">

<div style="background:#826eb4;padding:18px 22px;">
  <table cellpadding="0" cellspacing="0" border="0" style="width:100%;"><tr>
    <td style="width:70px;vertical-align:middle;">
      <img src="https://newsmarvin.com/logo-email.png" alt="Marvin" width="60" height="60" style="display:inline-block;vertical-align:middle;border-radius:50%;">
    </td>
    <td style="vertical-align:middle;padding-left:14px;">
      <div style="color:#fff;font-size:20px;font-weight:bold;letter-spacing:2px;">Newsmarvin</div>
      <div style="color:rgba(255,255,255,0.65);font-size:11px;margin-top:2px;">Tus noticias de IA, sin filtros</div>
    </td>
  </tr></table>
</div>

<div style="background:linear-gradient(90deg,#f4ebcc 0%,#ecdfb0 100%);border-bottom:2px solid #826eb4;padding:12px 22px;color:#4a3d6b;font-weight:600;font-size:14px;">
  <table cellpadding="0" cellspacing="0" border="0" style="display:inline-table;vertical-align:middle;margin-right:10px;border:1px solid rgba(74,61,107,0.3);border-radius:2px;overflow:hidden;">
    <tr><td style="width:30px;height:5px;background:#AA151B;font-size:0;line-height:0;">&nbsp;</td></tr>
    <tr><td style="width:30px;height:10px;background:#F1BF00;font-size:0;line-height:0;">&nbsp;</td></tr>
    <tr><td style="width:30px;height:5px;background:#AA151B;font-size:0;line-height:0;">&nbsp;</td></tr>
  </table>
  <span style="vertical-align:middle;">Ahora también en Español</span>
</div>

<div style="padding:24px;">

<p style="margin:0 0 16px;color:#222;">
Aviso rápido: Newsmarvin ya está disponible en español. Si prefieres
recibir tu resumen diario de noticias de IA en español a partir de
mañana, haz clic abajo. Un solo toque y listo.
</p>

<div style="text-align:center;margin:28px 0;">
  <a href="{switch_url}" style="display:inline-block;padding:13px 32px;background:#826eb4;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold;">
    <table cellpadding="0" cellspacing="0" border="0" style="display:inline-table;vertical-align:middle;margin-right:10px;border:1px solid rgba(255,255,255,0.5);border-radius:2px;overflow:hidden;">
      <tr><td style="width:22px;height:4px;background:#AA151B;font-size:0;line-height:0;">&nbsp;</td></tr>
      <tr><td style="width:22px;height:7px;background:#F1BF00;font-size:0;line-height:0;">&nbsp;</td></tr>
      <tr><td style="width:22px;height:4px;background:#AA151B;font-size:0;line-height:0;">&nbsp;</td></tr>
    </table>
    <span style="vertical-align:middle;">Sí, quiero recibirlo en Español &rarr;</span>
  </a>
</div>

<p style="margin:0 0 14px;color:#666;font-size:13px;">
No tienes que hacer nada si prefieres seguir en inglés. Puedes cambiar
cuando quieras desde cualquier futuro resumen.
</p>

<p style="margin:28px 0 0;color:#826eb4;font-size:13px;">
Gracias por leer,<br>Manuel y Marvin
</p>

</div>

<div style="border-top:1px solid #ddd;padding:14px 20px;color:#999;font-size:12px;text-align:center;">
<a href="https://newsmarvin.com" style="color:#826eb4;text-decoration:none;">newsmarvin.com</a>
 &middot;
<a href="{unsub_url}" style="color:#999;text-decoration:underline;">cancelar suscripción</a>
</div>

</div>
</body></html>"""

    return subject, text_body, html_body


def send_one(email, dry_run=False):
    subject, text_body, html_body = build_announcement(email)
    if dry_run:
        print(f"\n--- DRY RUN for {email} ---")
        print(f"Subject: {subject}")
        print(f"Switch URL: https://newsmarvin.com/api/set-language?email={email}&lang=es")
        print(f"(text length: {len(text_body)} chars; html length: {len(html_body)} chars)")
        return True

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": FROM_EMAIL,
            "to": [email],
            "subject": subject,
            "text": text_body,
            "html": html_body,
        },
    )
    if resp.status_code == 200:
        print(f"  Sent: {email}")
        return True
    print(f"  ERROR sending to {email}: {resp.status_code} {resp.text}")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", help="Send to a single test email address only")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be sent without sending")
    args = parser.parse_args()

    if args.test:
        recipients = [args.test.strip().lower()]
        print(f"TEST MODE - sending only to: {recipients[0]}")
    else:
        recipients = fetch_subscribers()
        print(f"Found {len(recipients)} subscribers")

    if not recipients:
        print("No recipients.")
        return

    if not args.dry_run and not RESEND_API_KEY:
        print("ERROR: RESEND_API_KEY not set")
        sys.exit(1)

    if not args.test and not args.dry_run:
        confirm = input(f"Send announcement to {len(recipients)} subscribers? [y/N] ")
        if confirm.strip().lower() != "y":
            print("Aborted.")
            return

    sent = 0
    for email in recipients:
        if send_one(email, dry_run=args.dry_run):
            sent += 1

    print(f"\nDone. Sent: {sent}/{len(recipients)}")


if __name__ == "__main__":
    main()
