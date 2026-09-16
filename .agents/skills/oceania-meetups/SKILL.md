---
name: oceania-meetups
description: |-
  Run the recurring update of the Australian and New Zealand Ruby meetup data — Melbourne, Sydney, BrisRails, Perth, Adelaide, Auckland, Wellington and Christchurch. Use when asked to update, refresh or catch up the AU/NZ (Oceania) meetups, when new recordings or announced meetups need adding to data/{ruby-melbourne,ruby-sydney,brisrails,ruby-perth,adelaide-rb,auckland-ruby,ruby-wellington,christchurch-ruby}/, or on a "monthly meetup update" for those series.
---

# Updating the Oceania meetup series

Each series keeps every edition in **one** event folder: one top-level entry per
month inside `data/{series}/{series}-meetup/videos.yml`. There is no per-month
`event.yml`. A month that has talks uses `video_provider: "children"` with the
talks nested underneath; a month with nothing to show keeps `talks: []`.

Read `.agents/skills/event-data/SKILL.md` first for the generators and the
repo-wide data rules. This skill covers what that one does not: where the
Oceania data comes from, and how to decide what each entry should say.

## 1. Survey what needs resolving

```bash
.agents/skills/oceania-meetups/scripts/pending.py
```

Lists, per series, the entries whose date has passed but that still claim to be
`scheduled`, the talks waiting on a recording, and how far the announced
coverage runs. That output is the to-do list for the round. Work on a branch
named for the month, e.g. `au-nz-meetup-update-2026-09`.

## 2. Fetch the sources

| Series | Upcoming + past editions | Talks and recordings |
| --- | --- | --- |
| `ruby-melbourne` | `meetup_events.py ruby-melbourne` | Talk → month mapping from the [melbourne-ruby](https://github.com/rubyaustralia/melbourne-ruby) milestones; recordings on the RubyAustralia channel `UCr38SHAvOKMDyX3-8lhvJHA` |
| `ruby-sydney` | `meetup_events.py ruby-on-rails-oceania-sydney` | Speaker line-up is in the event description; Sydney does not record |
| `brisrails` | `luma_events.py` (moved off Meetup in Dec 2023) | Occasional whole-meetup recordings, also on the RubyAustralia channel |
| `ruby-perth` | `meetup_events.py ruby-perth-meetup` | Not recorded |
| `adelaide-rb` | `meetup_events.py adelaiderb` | Not recorded |
| `auckland-ruby` | `meetup_events.py aucklandruby` | Talk titles and abstracts are in the event description |
| `ruby-wellington` | `meetup_events.py rubywellington` + `wellington.ruby.nz/meetups/{year}/{date}-meetup/` | `wellington.ruby.nz/recordings/` and channel `UC97hWMRsq2rmpCo3p950NSQ`; the site also links slides |
| `christchurch-ruby` | `christchurch.ruby.nz/events/{year}/{date}-meetup/` | Not recorded |

```bash
S=.agents/skills/oceania-meetups/scripts
$S/meetup_events.py ruby-melbourne ruby-on-rails-oceania-sydney ruby-perth-meetup adelaiderb aucklandruby rubywellington
$S/meetup_events.py --event 313967951          # one event with its full description
$S/luma_events.py --period future
$S/youtube_meta.py --channel UCr38SHAvOKMDyX3-8lhvJHA
$S/youtube_meta.py VIDEO_ID VIDEO_ID           # title, published_at, description
gh api "repos/rubyaustralia/melbourne-ruby/issues?state=all&per_page=100" \
  -q '.[] | select(.milestone != null) | "\(.milestone.title) | \(.title) | @\(.user.login)"' | sort -r
```

Each series' channel ids are recorded in its `series.yml` under
`youtube_channels`. The Melbourne **milestones are authoritative** for which month a talk belongs
to — RubyAustralia often uploads two months of recordings in one batch, so
publish dates group talks wrongly. Resolve each proposal's `@handle` to a real
name with `gh api users/<handle>`.

## 3. Decide what each entry should say

| Situation | Entry |
| --- | --- |
| Announced, still to come | `video_provider: "scheduled"`, `talks: []` — or `children` once speakers are known, with each talk `scheduled` |
| Happened, no recording expected | `not_recorded` |
| Happened, recording expected but not up yet | talks `not_published` — the next round picks them up |
| Happened, recording published | parent `children`, each talk `youtube` with `published_at`, `video_id` and the five thumbnails |
| Cancelled | `status: "cancelled"`, `video_provider: "not_recorded"`, title suffixed `(Cancelled)` |
| Postponed into another month | cancel the original month, say so in its description, and move the talk to the new month keeping `old_id` (below) |

Add roughly three months of announced meetups. Sydney publishes recurring
placeholders a year out — do not import them all.

### Shapes

A recorded month, talks in running order (not publish order):

```yaml
- id: "ruby-melbourne-meetup-june-2026"
  title: "Ruby Melbourne Meetup June 2026"
  event_name: "Ruby Melbourne Meetup June 2026"
  date: "2026-06-25"
  video_provider: "children"
  video_id: "ruby-melbourne-meetup-june-2026"
  description: |-
    Hosted at Ferocia, Level 7/271 Collins Street, Melbourne.
    https://www.meetup.com/ruby-melbourne/events/313408452/
  talks:
    - id: "pat-allan-ruby-melbourne-meetup-june-2026"
      title: "Music Services and UPnP with Ruby"
      raw_title: "Music Services and UPnP with Ruby - Pat Allan"
      event_name: "Ruby Melbourne Meetup June 2026"
      date: "2026-06-25"
      published_at: "2026-07-17T06:38:17Z"
      video_provider: "youtube"
      video_id: "61ZxS68y1OQ"
      thumbnail_xs: "https://img.youtube.com/vi/61ZxS68y1OQ/default.jpg"
      thumbnail_sm: "https://img.youtube.com/vi/61ZxS68y1OQ/mqdefault.jpg"
      thumbnail_md: "https://img.youtube.com/vi/61ZxS68y1OQ/mqdefault.jpg"
      thumbnail_lg: "https://img.youtube.com/vi/61ZxS68y1OQ/hqdefault.jpg"
      thumbnail_xl: "https://img.youtube.com/vi/61ZxS68y1OQ/hqdefault.jpg"
      description: |-
        A bit of a recap on what I've learnt from using Ruby to interact with Sonos speakers and music service APIs.
      speakers:
        - Pat Allan
```

Field order is `id`, `old_id`, `title`, `kind`, `raw_title`, `event_name`,
`date`, `published_at`, `video_provider`, `video_id`, thumbnails,
`description`, `slides_url`, `speakers`. Keep the meetup or site URL as the
last line of every month's `description`. Talk ids are
`{speaker-slug}-{month-entry-id}`; keep the speaker's canonical accented name in
`speakers` but strip accents in the id.

When a scheduled talk turns out recorded, keep the announced `title` and put
the YouTube title in `raw_title`. When a talk moves to another month, rename its
id and carry the previous one so the production record migrates:

```yaml
    - id: "yuri-vyatkin-auckland-ruby-meetup-september-2026"
      old_id: "yuri-vyatkin-auckland-ruby-meetup-august-2026"
```

Deleting a month or a talk outright instead needs its id listed under
`removed_talk_ids` in the series' `event.yml`, or `bin/rails validate:videos`
fails.

## 4. Speakers

Every speaker in a talk needs a `data/speakers.yml` record, and the GitHub
handle is what deduplicates them. Confirm a handle really is that person
(`gh api users/<handle>` — location and bio) before attaching it, and leave
`github: ""` when the search is ambiguous rather than guessing. Ask before
merging a new handle into an existing record that already has talks, because
two people can share a name.

```bash
bin/rails runner '
file = Static::SpeakersFile.new
file.find_by(name: "Anton Katunin")["github"] = "antulik"
file.add(name: "Ben Tillman", github: "")
file.save! if file.changed?'
```

## 5. Finish

```bash
bin/rails validate:all
bundle exec yerba apply
bin/rails db:seed:event_series[ruby-melbourne]   # per touched series
bin/dev                                          # review at localhost:3000/events/{series}-meetup
```

Screenshot the affected event pages, then open the PR. The nested meetup
structure is why this skill hand-edits YAML: `bin/rails g talk` appends at the
top level and cannot set `video_id` or `published_at`, so it only helps for a
brand new unrecorded talk. Say so in the PR description, per the event-data
skill.

## Gotchas

- The `youtube_*` MCP tools need an API key that is not configured here; use
  `youtube_meta.py`.
- Meetup's status enum calls upcoming events `ACTIVE`, not `UPCOMING`.
- A postponed meetup keeps its Meetup event id and the later month's event is
  deleted — an id that returns "NOT FOUND" usually means it was merged, not
  cancelled. Check the group's event list before concluding anything.
- Two separate Meetup organiser accounts hold these groups (`ruby-melbourne`,
  `ruby-perth-meetup`, `adelaiderb` under one; `ruby-on-rails-oceania-sydney`,
  `brisruby` under the other), so there is no single Pro network to query.
- Adelaide's fortnightly "Ruby Burgers" socials are deliberately left out; only
  the talk meetups are tracked.
- Perth and Adelaide go quiet for months at a time. A dormant series is not a
  missing-data bug.
- Wellington and Christchurch publish their own sites, which carry abstracts and
  slides that Meetup does not.
