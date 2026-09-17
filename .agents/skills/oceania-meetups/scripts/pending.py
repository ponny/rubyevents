#!/usr/bin/env python3
"""Survey the Oceania meetup files and list what this update round has to resolve.

Run from the repo root. Reports, per series: entries whose date has passed but
that still claim to be scheduled, talks still waiting on a recording, how far
the upcoming coverage runs, and how long a dormant series has been quiet.

  ./pending.py                 # all series
  ./pending.py ruby-melbourne  # one series
"""
import re, sys, glob
from datetime import date

SERIES = [
    "ruby-melbourne", "ruby-sydney", "brisrails", "ruby-perth",
    "adelaide-rb", "auckland-ruby", "ruby-wellington", "christchurch-ruby",
]

TODAY = date.today()


def entries(path):
    """Yield (id, date, provider, status, [(talk_id, provider)]) per top-level entry."""
    for block in re.split(r"\n(?=- id:)", open(path).read()):
        entry_id = re.match(r'- id: "([^"]+)"', block)
        if not entry_id:
            continue
        entry_date = re.search(r'^  date: "([\d-]+)"', block, re.M)
        provider = re.search(r'^  video_provider: "(\w+)"', block, re.M)
        status = re.search(r'^  status: "(\w+)"', block, re.M)
        talks = re.findall(r'^    - id: "([^"]+)"(?:.(?!\n    - id:))*?\n      video_provider: "(\w+)"',
                           block, re.M | re.S)
        yield (entry_id.group(1),
               entry_date.group(1) if entry_date else "?",
               provider.group(1) if provider else "?",
               status.group(1) if status else None,
               talks)


for slug in (sys.argv[1:] or SERIES):
    paths = glob.glob("data/%s/*/videos.yml" % slug)
    if not paths:
        print("%-20s no videos.yml found" % slug)
        continue
    rows = list(entries(paths[0]))
    notes = []
    upcoming = []
    for entry_id, entry_date, provider, status, talks in rows:
        past = entry_date != "?" and date.fromisoformat(entry_date) < TODAY
        if not past:
            upcoming.append((entry_date, entry_id, provider))
        if past and status != "cancelled":
            if provider == "scheduled":
                notes.append("  RESOLVE  %s (%s) is past but still scheduled" % (entry_id, entry_date))
            for talk_id, talk_provider in talks:
                if talk_provider == "scheduled":
                    notes.append("  RESOLVE  %s (%s) talk still scheduled" % (talk_id, entry_date))
                elif talk_provider == "not_published":
                    notes.append("  CHECK    %s (%s) waiting on a recording" % (talk_id, entry_date))
    last = max((row[1] for row in rows if row[1] != "?"), default="?")
    print("%s  (%d entries, last %s)" % (slug, len(rows), last))
    for note in notes:
        print(note)
    if upcoming:
        print("  upcoming: " + ", ".join("%s %s" % (d, p) for d, _, p in sorted(upcoming)))
    else:
        print("  upcoming: none announced" + (" - dormant since %s" % last if last != "?" else ""))
    print()
