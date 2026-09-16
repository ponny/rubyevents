#!/usr/bin/env python3
"""Fetch Meetup.com events for a group, or one event by id.

The public gql2 endpoint answers unauthenticated. Note the status enum:
upcoming events are ACTIVE (not "UPCOMING"), past ones are PAST, and a
cancelled event keeps its date but reports status CANCELLED.

  ./meetup_events.py ruby-melbourne aucklandruby            # past + upcoming
  ./meetup_events.py --status ACTIVE ruby-melbourne         # upcoming only
  ./meetup_events.py --event 313967951                      # one event, full description
"""
import argparse, json, urllib.request

ENDPOINT = "https://www.meetup.com/gql2"
HEADERS = {"content-type": "application/json", "user-agent": "Mozilla/5.0"}

GROUP_QUERY = """query($urlname:String!,$status:EventStatus,$first:Int){
  groupByUrlname(urlname:$urlname){
    name
    events(status:$status, first:$first, sort:DESC){
      edges{node{ id title dateTime eventUrl status venue{ name address city } }}
    }
  }
}"""

EVENT_QUERY = """query($id:ID!){
  event(id:$id){ id title dateTime eventUrl status description venue{ name address city } }
}"""


def post(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    request = urllib.request.Request(ENDPOINT, data=body, headers=HEADERS)
    return json.load(urllib.request.urlopen(request, timeout=30))


def print_group(urlname, statuses, first):
    print("#" * 20, urlname)
    for status in statuses:
        payload = post(GROUP_QUERY, {"urlname": urlname, "status": status, "first": first})
        if payload.get("errors"):
            print("  [%s] ERROR: %s" % (status, payload["errors"][0].get("message", "")[:200]))
            continue
        group = (payload.get("data") or {}).get("groupByUrlname")
        if not group:
            print("  [%s] group not found" % status)
            continue
        for edge in group["events"]["edges"]:
            node = edge["node"]
            venue = node.get("venue") or {}
            print("  [%s] %s | %s | %s | %s, %s" % (
                node.get("status") or status, node["dateTime"][:16], node["title"],
                node["eventUrl"], venue.get("name", ""), venue.get("address", "")))
    print()


def print_event(event_id):
    payload = post(EVENT_QUERY, {"id": event_id})
    event = (payload.get("data") or {}).get("event")
    if not event:
        # A deleted or merged event id returns null - Meetup reuses one event id
        # when a meetup is postponed into another month.
        print("#" * 10, event_id, "-> NOT FOUND / removed")
        return
    venue = event.get("venue") or {}
    print("#" * 10, event_id, "|", event["dateTime"][:16], "|", event["title"], "| status:", event.get("status"))
    print("   venue:", venue.get("name"), "|", venue.get("address"))
    print("   desc:", (event.get("description") or "").replace("\n", " "))
    print()


parser = argparse.ArgumentParser()
parser.add_argument("urlnames", nargs="*", help="Meetup group urlnames")
parser.add_argument("--event", action="append", default=[], help="Fetch one event id with its full description")
parser.add_argument("--status", action="append", default=[], choices=["PAST", "ACTIVE", "CANCELLED"])
parser.add_argument("--first", type=int, default=8)
args = parser.parse_args()

for event_id in args.event:
    print_event(event_id)
for urlname in args.urlnames:
    print_group(urlname, args.status or ["PAST", "ACTIVE"], args.first)
