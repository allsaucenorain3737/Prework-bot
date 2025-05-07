import os
from datetime import datetime, timedelta

import requests
from icalendar import Calendar

# ─── CONFIG ───────────────────────────────────
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
ONLY_TOMORROW = os.getenv('ONLY_TOMORROW', 'false').lower() in ('1','true','yes')
CAL_URL = "https://bc.instructure.com/feeds/calendars/user_y0uFoVpComnaIImxxnqKFs55uHhotG5n3ozs21Ff.ics"
# ────────────────────────────────────────────────

def fetch_events(ics_url):
    resp = requests.get(ics_url)
    resp.raise_for_status()
    cal = Calendar.from_ical(resp.content)
    evs = []
    for comp in cal.walk():
        if comp.name == 'VEVENT':
            dt = comp.get('DTSTART').dt
            # Normalize to date
            if isinstance(dt, datetime):
                dt = dt.date()
            summary = str(comp.get('SUMMARY'))
            evs.append((dt, summary))
    return evs

def upcoming_prework_dates(events, start_date):
    # unique, sorted dates > start_date where summary contains "Pre-Work"
    dates = {dt for dt, summ in events if dt > start_date and 'Pre-Work' in summ}
    return sorted(dates)

def send_webhook(msg):
    if not WEBHOOK_URL:
        raise RuntimeError("Missing DISCORD_WEBHOOK_URL")
    requests.post(WEBHOOK_URL, json={'content': msg}).raise_for_status()

def main():
    today = datetime.utcnow().date()
    events = fetch_events(CAL_URL)
    ups = upcoming_prework_dates(events, today)

    if ONLY_TOMORROW:
        tomorrow = today + timedelta(days=1)
        if ups and ups[0] == tomorrow:
            send_webhook(f"📝 Reminder: Pre‑Work is due *tomorrow* ({tomorrow.isoformat()}).")
    else:
        if ups:
            next_two = ups[:2]
            dates_str = ', '.join(d.isoformat() for d in next_two)
            send_webhook(f"📝 Upcoming Pre‑Work due on: {dates_str}.")
        else:
            send_webhook("📝 No upcoming Pre‑Work scheduled.")

if __name__ == '__main__':
    main()
