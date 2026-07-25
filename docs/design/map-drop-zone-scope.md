# Map Drop Zone + Flow — implementation scope (not started)

Captured 2026-07-25 so the next session can start from a running start
instead of cold. Nothing here is built yet.

## What the user wants

- A drop-zone + movement-flow read on **every player profiled**, not just
  a squad capstone.
  - solo.py: trivial, it's already profiling exactly one player.
  - squad.py: each member gets their own drop-zone/flow read independently
    (same per-player computation solo.py will already have, reused - not
    a separate code path).
- **Additionally**, for squad.py only: a consolidated squad-level read
  proposing how the group might coordinate drops, derived from the
  members' individual patterns. Two angles:
  1. "Best fit" - the most common/preferred landing pattern across the
     squad (whatever that consensus actually looks like from real data).
  2. "Change it up" - a deliberately different suggestion, contrasting
     with what the squad typically does, framed as a variety option.
  - Exact biasing/scoring logic for how to derive these two from N
    players' individual patterns is undecided - needs a real design pass,
    not just glue code.

## Why this is the largest remaining lift (not a quick add)

Three separate pieces of groundwork don't exist yet, unlike every other
capability shipped so far this session (which all reused existing
telemetry parsing):

1. **New telemetry parsing.** Nothing in `utils/` currently parses
   `LogParachuteLanding` or reconstructs a movement trail from
   `LogPlayerPosition`-style events. Needs its own module, its own tests,
   and its own real-data validation - same rigor as tempo_signal.py /
   range_signal.py got originally (their thresholds were calibrated
   against real distributions, not guessed).

2. **A per-map named-region reference dataset that doesn't exist.**
   Landing coordinates are raw (x, y, z) floats - turning "landed at
   (377810, 65856)" into "landed near Pochinki" requires a static mapping
   of named callout regions to in-game coordinate bounds, per map. This
   doesn't exist anywhere in this repo or its data. Options to scope out
   next session:
   - Hand-author a small reference set for the maps this player pool
     actually plays most (check `mapName` distribution across cached
     telemetry first - already have the tooling from the mode-filtering
     investigation this session, see `killer_intel.py`/`solo_coaching.py`
     for the `mapName` field usage pattern).
   - Or use a coarser, non-named grid/quadrant scheme initially (e.g.
     "northwest corner of the map") to avoid needing exact named-region
     boundaries at all - defer full named callouts to a later pass.
   Recommend starting with the coarser scheme - much less upfront data
   work, and can still validate whether it's useful before investing in
   exact named boundaries.

3. **Squad-level consolidation logic is a real design decision, not
   glue.** "Best fit" and "change it up" need actual criteria: is
   consensus by majority landing zone? By some clustering of flow
   patterns? What counts as "radically different" vs. just noise? This
   needs the same "check real data before deciding" pass every other
   signal in this tool got (see squad-output-polish plan's approach to
   the possessive/tense fixes, or this session's mode-filtering
   validation against Shaply/ObiWannCoyote/MAYFAAA- for a model of the
   process to repeat here).

## Suggested next-session approach

1. Validate real data first: pull `mapName` + landing-event availability
   across the cached telemetry pool (same technique used for the mode-
   filtering investigation), confirm `LogParachuteLanding` events are
   actually present and usable before designing around them.
2. Start with the coarse quadrant/grid scheme, not named regions - ship
   a real per-player drop-zone + flow read for solo.py first (smallest
   possible correct slice), get it live-validated.
3. Reuse that same per-player computation inside squad.py's per-member
   cards (same pattern as Coaching Note / K/D - compute once per member,
   render on their card).
4. Only after the per-player version is live and validated, design the
   squad-level "best fit" / "change it up" consolidation as its own
   follow-up - don't build it speculatively before the per-player
   foundation is proven out.
