#!/usr/bin/env python3
"""List events on a Luma calendar (BrisRails moved off Meetup in Dec 2023).

  ./luma_events.py                      # BrisRails past events
  ./luma_events.py --period future
  ./luma_events.py --calendar cal-xxxx  # any other Luma calendar

Luma's public calendar API answers unauthenticated. Event descriptions are
not included in the listing; open the lu.ma/<slug> page for those.
"""
import argparse, json, urllib.request

BRISRAILS = "cal-cELXJWvMwJuG17i"

parser = argparse.ArgumentParser()
parser.add_argument("--calendar", default=BRISRAILS)
parser.add_argument("--period", default="past", choices=["past", "future"])
parser.add_argument("--limit", type=int, default=12)
args = parser.parse_args()

url = ("https://api.lu.ma/calendar/get-items?calendar_api_id=%s&period=%s&pagination_limit=%d"
       % (args.calendar, args.period, args.limit))
payload = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"user-agent": "Mozilla/5.0"}), timeout=25))

for entry in payload.get("entries", []):
    event = entry.get("event", {})
    address = (event.get("geo_address_info") or {}).get("address", "")
    print("%s | %s | https://lu.ma/%s | %s" % (
        event.get("start_at", "")[:10], event.get("name"), event.get("url"), address))
