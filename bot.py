#!/usr/bin/env python3
import os
import requests
from icalendar import Calendar
from datetime import datetime, timedelta

# ─── CONFIG ───────────────────────────────────
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
CAL_URL     = (
    "https://bc.instructure.com/feeds/calendars/"
    "user_y0uFoVpComnaIImxxnqKFs55uHhotG5n3ozs21Ff.ics"
)
# ────────────────────────────────────────────────

def fetch_events(ics_url):
    resp = requests.get(ics_url)
    resp.raise_for_status()
    cal = Calendar.from_ical(resp.content)
    evs = []
    for comp in cal.walk():
        if comp.name == 'VEVENT':
            dt = comp.get('DTSTART').dt
            # normalize to date
            if isinstance(dt, datetime):
                dt = dt.date()
            summary = str(comp.get('SUMMARY'))
            evs.append((dt, summary))
    return evs

def send_discord(msg: str):
    if not WEBHOOK_URL:
        raise RuntimeError("Missing DISCORD_WEBHOOK_URL")
    requests.post(WEBHOOK_URL, json={"content": msg}).raise_for_status()

def main():
    # Shift “today” back one so that UTC scheduling aligns with PST intent
    today    = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    in_three = today + timedelta(days=3)

    events = fetch_events(CAL_URL)
    messages = []

    # 1) Pre-Work → only tomorrow
    for dt, summ in events:
        if dt == tomorrow and 'Pre-Work' in summ:
            messages.append(f"📝 Pre-Work due tomorrow ({dt.isoformat()}): {summ}")

    # 2) Extra Credit → in 3 days & today
    for dt, summ in events:
        if '(Extra Credit)' in summ:
            if dt == in_three:
                messages.append(f"⭐ Extra Credit due in 3 days ({dt.isoformat()}): {summ}")
            elif dt == today:
                messages.append(f"⭐ Extra Credit due today ({dt.isoformat()}): {summ}")

    # 3) Python Coding → tomorrow & today
    for dt, summ in events:
        if 'Python Coding' in summ:
            if dt == tomorrow:
                messages.append(f"🐍 Python Coding due tomorrow ({dt.isoformat()}): {summ}")
            elif dt == today:
                messages.append(f"🐍 Python Coding due today ({dt.isoformat()}): {summ}")

    # If we have any reminders, send each as its own message
    for msg in messages:
        send_discord(msg)

if __name__ == "__main__":
    main()
