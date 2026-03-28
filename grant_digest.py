#!/usr/bin/env python3
"""
GrowZA Client Grant Digest
Scrapes grant RSS feeds for 4 clients and emails a weekly digest.
Runs every Monday & Thursday at 7AM SAST via GitHub Actions.
"""

import smtplib
import feedparser
import datetime
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# --- CONFIG ---
SENDER_EMAIL    = "craigkensley@gmail.com"
RECIPIENT_EMAIL = "craig@growza.co.za"
EMAIL_PASSWORD  = os.environ.get("GMAIL_APP_PASSWORD", "")
TODAY           = datetime.date.today().strftime("%-d %B %Y")

# --- CLIENT PROFILES ---
CLIENTS = {
    "GrowZA": {
        "emoji": "🌱",
        "keywords": ["social investment", "NPO", "NGO", "community development",
                     "social impact", "South Africa", "CSI", "social enterprise"],
    },
    "Afrika Tikkun": {
        "emoji": "🤝",
        "keywords": ["ECD", "early childhood", "youth employment", "youth skills",
                     "after-school", "nutrition", "psychosocial", "youth development",
                     "education", "child poverty", "skills development"],
    },
    "Smile Foundation": {
        "emoji": "😊",
        "keywords": ["child health", "healthcare", "paediatric", "facial", "cleft",
                     "craniofacial", "burns", "reconstructive", "medical",
                     "children hospital", "surgical", "disability"],
    },
    "Philanthrostrat": {
        "emoji": "🌍",
        "keywords": ["international donor", "cross-border", "family foundation",
                     "African NGO", "strategic philanthropy", "overseas",
                     "USA", "UK", "Europe", "global fund", "international grant"],
    },
}

# --- RSS FEEDS ---
FEEDS = [
    "https://africanngos.org/feed/",
    "https://fundingfinder.co.za/feed/",
    "https://opportunitiesforafricans.com/feed/",
]

# --- SCRAPER ---
def fetch_grants():
    seen = set()
    grants = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                if title and title not in seen:
                    seen.add(title)
                    grants.append({
                        "title":   title,
                        "summary": entry.get("summary", "")[:400],
                        "link":    entry.get("link", ""),
                        "source":  feed.feed.get("title", url),
                    })
        except Exception as e:
            print(f"Feed error ({url}): {e}")
    return grants

def match_client(grant, keywords):
    text = (grant["title"] + " " + grant["summary"]).lower()
    return any(kw.lower() in text for kw in keywords)

def build_section(name, emoji, grants, keywords):
    matches = [g for g in grants if match_client(g, keywords)]
    header = f'<h3 style="color:#1b5e20;margin:16px 0 8px;border-bottom:2px solid #c8e6c9;padding-bottom:6px;">{emoji} {name} <span style="font-weight:normal;font-size:13px;color:#777;">— {len(matches)} match{"es" if len(matches)!=1 else ""}</span></h3>'
    if not matches:
        return header + '<p style="color:#999;font-style:italic;font-size:13px;">No new matches this week. Check back next digest.</p>'
    rows = ""
    for i, g in enumerate(matches[:8], 1):
        summary = g["summary"].replace("<[^>]+>", "")[:200]
        rows += f"""
        <div style="border-left:3px solid #4caf50;padding:8px 12px;margin:8px 0;background:#f9fbe7;">
            <strong style="font-size:14px;">{i}. {g['title']}</strong><br>
            <span style="color:#555;font-size:12px;">{summary}...</span><br>
            <a href="{g['link']}" style="color:#1565c0;font-size:12px;text-decoration:none;">Read more → <em>({g['source']})</em></a>
        </div>"""
    return header + rows

def build_email(grants):
    total = sum(len([g for g in grants if match_client(g, p["keywords"])]) for p in CLIENTS.values())
    sections = "".join(build_section(n, p["emoji"], grants, p["keywords"]) for n, p in CLIENTS.items())
    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:680px;margin:0 auto;color:#333;padding:20px;">
        <div style="background:#1b5e20;padding:20px;border-radius:8px;margin-bottom:20px;">
            <h1 style="color:white;margin:0;font-size:22px;">🌱 GrowZA Client Grant Digest</h1>
            <p style="color:#c8e6c9;margin:6px 0 0;">{TODAY} &nbsp;|&nbsp; {total} opportunities across 4 clients</p>
        </div>
        {sections}
        <div style="margin-top:24px;padding-top:16px;border-top:1px solid #eee;font-size:11px;color:#aaa;">
            Sources: AfricanNGOs.org | FundingFinder.co.za | OpportunitiesForAfricans.com<br>
            Clients: GrowZA · Afrika Tikkun · Smile Foundation · Philanthrostrat<br>
            Delivered Mon & Thu 7AM SAST — GrowZA Grant Scraper
        </div>
    </body></html>"""

def send_email(html, count):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🌱 GrowZA Client Grants — {count} Opportunities | {TODAY}"
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(SENDER_EMAIL, EMAIL_PASSWORD)
        s.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print(f"Digest sent to {RECIPIENT_EMAIL} — {count} opportunities")

if __name__ == "__main__":
    print("Fetching grants...")
    grants = fetch_grants()
    print(f"Total entries: {len(grants)}")
    html  = build_email(grants)
    total = sum(len([g for g in grants if match_client(g, p["keywords"])]) for p in CLIENTS.values())
    send_email(html, total)
