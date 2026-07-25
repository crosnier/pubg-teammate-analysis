# Map Drop Zone + Flow — implementation scope

Captured 2026-07-25 so work can resume from a running start instead of
cold. See "Progress" section near the bottom for current state - this is
now partway built, on branch `map-drop-zone-flow` (not `main`).

## Accuracy requirements (added after initial scope, refines "Why this is
the largest remaining lift" below)

- Ambiguous landings (near a boundary, between two named regions) get
  descriptive phrasing, not a falsely-precise single label - including
  compass-direction qualifiers where intuitive: "landed near the edge of
  Pochinki, northeast" rather than just "landed near Pochinki."
- The per-map region reference dataset must be real, researched, and
  locally cached - never re-fetched/re-derived live at runtime.
- Needs a repeatable regeneration mechanism (script/tool) so the dataset
  can be rebuilt when PUBG ships a new map or overhauls an existing one,
  without re-deriving the whole research process from scratch.
- Graceful, non-breaking fallback when a match's `mapName` isn't in the
  indexed dataset yet (new/unrecognized map) - "map not yet supported",
  never a crash or a silent wrong guess.
- Built with an eye toward a future visual map layer - store/derive
  structured coordinate + region data (see `utils/map_regions_data.py`),
  not just pre-baked sentence strings.

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

## Progress as of 2026-07-25 (end of research session)

Branch: `map-drop-zone-flow` (off `main`, not merged, not pushed).
Issue: #44.

**Confirmed via real research, not guessed:**
- `LogParachuteLanding` events exist in cached telemetry with real
  `character.location.{x,y,z}` in centimeters, exactly matching PUBG's
  documented coordinate system (`utils/map_regions_data.py`'s
  `MAP_SIZE_CM`, sourced from official docs). `LogPlayerPosition` also
  exists for movement-trail mining (not yet used).
- Official, IP-clean, text-labeled map images exist at
  `github.com/pubg/api-assets` (PUBG's own developer asset repo) - the
  Erangel one is saved locally at `docs/design/maps/erangel_official.png`
  (819x819px, covers the full 0-816000cm coordinate range).
- Read every visible POI label off that image directly, converted pixel
  position to real telemetry-space coordinates via linear scaling, and
  **cross-validated against 136,247 real `LogParachuteLanding` events**
  across all 1,047 cached `Baltic_Main` (Erangel) matches - landing
  density within 400m of each estimated POI matches well-established
  PUBG community knowledge closely (School and Pochinki, the two most
  legendary hot-drops in the game, topped the count by a wide margin at
  16,017 and 13,650 respectively; Zharki, a famously dead corner, landed
  at 23 - a strong negative-control signal). This validates both the
  pixel-reading and the assumed coordinate orientation (top-left origin,
  x-right, y-down) without trusting either on faith. Full data + the
  validation counts are committed in `utils/map_regions_data.py`.
- Two POIs (Kameshki, Stalber) show lower validation density than their
  visual prominence as named cities suggests - flagged `NEEDS_REVIEW` in
  the data file, re-examine placement before trusting them.
- PUBG's own in-game grid-letter convention (the callout system players
  use, e.g. "D4") turned out to have genuinely conflicting descriptions
  across sources when researched (one wiki field used two-letter
  sections like "DL", general sources described letter+number like
  "F4") - deliberately NOT building on that ambiguous convention.
  Decision: build our own transparent, empirically-validated region
  system instead (named POI + nearest/between-two + compass direction),
  since the actual requirement is human-readable descriptive text, not
  literal reproduction of PUBG's in-game grid jargon.

**Not yet done** (in priority order for resuming):
1. Fix Kameshki/Stalber placement (flagged above).
2. Write the actual classification module: given a real (x, y) landing
   coordinate, return the nearest POI, or a "between X and Y" /
   "near the edge of X, [compass direction]" description when ambiguous
   (near a boundary between two POIs' zones of influence). No code for
   this exists yet - `map_regions_data.py` is raw material only.
3. Movement-flow mining from `LogPlayerPosition` - not started at all,
   no research done yet on what a useful "flow" summary looks like from
   this event type.
4. The "unrecognized map" graceful-fallback mechanism (check `mapName`
   against `MAP_SIZE_CM`'s keys - cheap, do this early in the
   classification module, not as an afterthought).
5. Repeat the whole research process (official map image + POI reading +
   telemetry-density validation) for the other maps that show up in our
   cache, in priority order by real match volume: `Tiger_Main` (Taego,
   36 of last 300 sampled), `Desert_Main` (Miramar, 31), `Neon_Main`
   (Rondo, 25 - also still needs `MAP_SIZE_CM` verification, see the
   commented-out line in `map_regions_data.py`), `DihorOtok_Main`
   (Vikendi, 17), `Savage_Main` (Sanhok, 8), `Summerland_Main` (Karakin,
   6).
6. The regeneration script/mechanism itself (repeatable process for
   rebuilding a map's dataset when PUBG changes something) - the process
   above was done ad hoc this session; needs to be captured as an
   actual reusable tool, not just repeated by hand each time.
7. Wire into `solo.py` (smallest correct slice, per the original plan).
8. Reuse in `squad.py`'s per-member cards.
9. Squad-level "best fit"/"change it up" consolidation - still fully
   undesigned, per the original scope above.
10. Tests + live validation for whatever ships first (the classification
    module, at minimum, needs unit tests before it's trusted).

No code has been wired into `solo.py`, `squad.py`, or `main.py` yet -
this is all still additive/inert data + research, safe to resume from.
