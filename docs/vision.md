# Vision

## The problem

Squads in PUBG load in on the plane. From that point until
the match ends, you're playing with strangers whose habits, skill level, and
tendencies you know nothing about. There's a short window, while flying to
the island, where the roster is effectively final but the round hasn't
started yet — that's the moment this tool is built around.

## North star

While a match is loading and the squad is on the plane:

1. Detect that a new round has started.
2. Read the player names on screen (own name excluded).
3. Query the PUBG API for each detected teammate.
4. Build a short profile per teammate: playstyle indicators (drop zones,
   weapon preferences, aggression vs. survival tendencies), summary of their
   last match, and any notable patterns or standout events from recent
   history — this is a starting list, not a ceiling. As telemetry gets mined
   more deeply, the profile should grow to include whatever signal turns out
   to be genuinely worth surfacing.
5. Surface those profiles before the plane reaches the drop zone.

The PUBG API only exposes a match after it's finished processing (roughly
2-10 minutes post-match, per PUBG's own guidance). There's no live, in-round
data. That's not a blocker: every profile is built from each teammate's most
recent *completed* matches, which naturally includes last round if you were
already playing with them.

Own-name exclusion above is specific to the auto-detection step — it's a
teammate scanner, not a mirror. Seeing my own profile, built the exact same
way as everyone else's, is a separate and genuinely useful capability: it's
the only way to know what my own persona looks like from the outside.

The goal isn't just stat-checking — it's understanding the profile of each
player in your squad well enough to predict their behavior and playstyle
patterns, adapt your own play to theirs, and have something real to talk
about. A good profile should make it easy to strike up a conversation with a
teammate, not just judge their K/D.

## How the pieces fit together

The current CLI is the foundation, not the end state. Rough phases, in
order:

1. **Stats & telemetry foundation** (current) — query, cache, and display
   player stats and match history from the CLI.
2. **Match-level insight** — mine telemetry for behavioral signal (drop
   zones, weapon usage, engagement patterns, bot detection, and more) instead
   of just raw stat totals. The specific signals worth extracting are still
   an open question — expect this list to mature as prototyping against real
   telemetry surfaces better, more "wow factor" storyboards.
3. **Automatic squad detection** — recognize when a new round has loaded and
   identify teammates from on-screen player names, without manual input.
4. **Delivery surface** — move profile output from console text to a web
   app, so profiles render as an actual UI instead of ASCII tables. Docker
   packaging follows once the app has a stable shape.

Live status and sequencing for all of this lives on the
[Project board](https://github.com/users/crosnier/projects/2) — this doc
explains the *why*, the board tracks the *what's next*.

## Explicitly out of scope for now

Attaching an LLM to narrate or extrapolate insights from the collected stats
and telemetry is a compelling future enhancement, but it's a layer on top of
a working profiling pipeline, not a prerequisite for one. It stays in the
backlog until the core capabilities above are built and stable.
