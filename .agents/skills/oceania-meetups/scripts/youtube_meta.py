#!/usr/bin/env python3
"""Read YouTube metadata without an API key.

The rubyevents MCP youtube_* tools need a YouTube API key that is not
configured locally, so use this instead.

  ./youtube_meta.py --channel UCr38SHAvOKMDyX3-8lhvJHA   # 15 most recent uploads via RSS
  ./youtube_meta.py VIDEO_ID [VIDEO_ID ...]              # title, published_at, description

published_at is printed in the exact format videos.yml wants
(%Y-%m-%dT%H:%M:%SZ), which the schema requires for youtube entries.
"""
import argparse, json, re, urllib.request
from datetime import datetime, timezone

HEADERS = {"user-agent": "Mozilla/5.0", "accept-language": "en-US,en"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=25).read().decode("utf8", "ignore")


def channel_feed(channel_id):
    feed = get("https://www.youtube.com/feeds/videos.xml?channel_id=%s" % channel_id)
    entries = re.findall(r"<entry>(.*?)</entry>", feed, re.S)
    for entry in entries:
        video_id = re.search(r"<yt:videoId>(.*?)</yt:videoId>", entry).group(1)
        title = re.search(r"<title>(.*?)</title>", entry).group(1)
        published = re.search(r"<published>(.*?)</published>", entry).group(1)
        stamp = datetime.fromisoformat(published).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        print("%s | %s | %s" % (video_id, stamp, title))


def video(video_id):
    page = get("https://www.youtube.com/watch?v=%s" % video_id)
    match = re.search(r"var ytInitialPlayerResponse = (\{.*?\});</script>", page)
    if not match:
        print("### %s | could not parse player response" % video_id)
        return
    data = json.loads(match.group(1))
    details = data.get("videoDetails", {})
    micro = data.get("microformat", {}).get("playerMicroformatRenderer", {})
    published = micro.get("publishDate")
    stamp = datetime.fromisoformat(published).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if published else "?"
    print("### %s | %s" % (video_id, details.get("title")))
    print("    published_at: %s | length: %ss" % (stamp, details.get("lengthSeconds")))
    print("    description: %s" % (details.get("shortDescription") or "").replace("\n", "\n                 "))


parser = argparse.ArgumentParser()
parser.add_argument("video_ids", nargs="*")
parser.add_argument("--channel", help="Channel id - lists the 15 most recent uploads")
args = parser.parse_args()

if args.channel:
    channel_feed(args.channel)
for video_id in args.video_ids:
    video(video_id)
