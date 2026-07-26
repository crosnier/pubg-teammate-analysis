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

## Progress as of 2026-07-25 (part 2, same day - classifier + solo.py wiring)

1. **Kameshki/Stalber resolved.** Re-cropped tight, high-zoom regions of
   the official map image and located each town's real building cluster
   directly - both existing pixel estimates land within ~10px of the
   true centroid, i.e. correctly placed. The lower landing counts are
   real gameplay signal (small, remote, mountainous NE towns - genuinely
   less popular drops), not a data error. `NEEDS_REVIEW` flags removed;
   full reasoning kept in `map_regions_data.py`'s docstring.
2. **Classification module built**: `utils/drop_zone.py`.
   `classify_landing(x, y, poi_coords)` does nearest/second-nearest POI
   lookup and returns a "near X" / "near the edge of X, <compass>" /
   "between X and Y" description depending on how close the two nearest
   candidates are. Ambiguity thresholds (`BETWEEN_RATIO=1.15`,
   `EDGE_RATIO=1.5`) are **not guessed** - calibrated against 15,067 real
   `LogParachuteLanding` events sampled from 204 cached Baltic_Main
   matches (see module docstring for the full ratio percentile
   breakdown). Confirmed ambiguity is genuinely the minority case
   (~75%+ of real landings are unambiguous) before picking the cutoffs.
   `compute_drop_zone_signal()` aggregates per-match reads into a
   most-frequent-zone read, same mode-based pattern as
   `compute_tempo_signal`, gated at `MIN_MATCHES_FOR_SIGNAL=8`.
3. **"Unrecognized map" fallback done**: `MAP_POI_LOOKUP` is the single
   gate for map support; an unsupported `mapName` returns a
   `supported_map: False` reading instead of crashing or guessing, and
   `utils/display_drop_zone.py` renders that as "map not yet supported
   for tracking" rather than showing nothing silently.
4. **12 unit tests** in `tests/test_drop_zone.py` (confident/edge/between
   classification math, compass direction sign convention, unsupported-
   map fallback, min-matches gating, mode-aggregation across matches).
   Full suite (161 tests) still green.
5. **Live-validated against real cached telemetry** (not just unit
   tests): pulled two real accounts' actual Baltic_Main matches and
   inspected per-match + aggregate output by hand. Distances were sane
   (e.g. two School landings at 52.4m/48.6m from the POI center - a
   real hot-drop), the Sosnovka Island/Military Base pair correctly
   reads as "between"/"edge" most of the time (they're genuinely
   adjacent POIs on a small island - the ambiguity model is doing the
   right thing there, not misfiring), and the min-matches gate correctly
   returned no aggregate read for a 7-match account while a separate
   18-match account got a confident "near School" read (6/16 matches).
6. **Wired into `solo.py`**: a new "🪂 Drop Zone" section on the profile,
   computed via `compute_drop_zone_signal` + `format_drop_zone_line`,
   shown only when there's a real read or an explicit "not yet
   supported" note - omitted entirely below the match-count bar, same
   omission convention as the Coaching Note section.

## Progress as of 2026-07-25 (part 3, same day - movement flow + solo.py wiring)

1. **Flow signal built**: `utils/movement_flow.py`. Researched
   `LogPlayerPosition` (fires every ~10 in-game seconds per player while
   alive) and `LogGameStatePeriodic` (same cadence, carries
   `safetyZonePosition` + `safetyZoneRadius`) before designing anything -
   confirmed both are dense and easy to align by `elapsedTime`. Flow is
   **map-agnostic by design**: it only measures a player's distance to
   the safe zone's own center as a fraction of the zone's own radius, so
   unlike Drop Zone it needs no named-POI data and already works on every
   map, including ones Drop Zone can't classify yet.
2. **Thresholds calibrated, not guessed**: sampled 6,570 real
   (player, match) medians across 80 cached matches (any map). Tertile
   split of the real distribution (p33=0.256, p67=0.457) set
   `ZONE_CENTER_MAX_FRACTION=0.26` / `BALANCED_MAX_FRACTION=0.46` -
   same calibration discipline as Drop Zone's ratio thresholds and the
   original range_signal.py tertiles. `compute_flow_signal()` aggregates
   into a most-frequent-bucket tag (Zone Center / Balanced Rotator /
   Zone Edge), same mode-based pattern as tempo/drop-zone, gated at
   `MIN_MATCHES_FOR_SIGNAL=8`.
3. **8 unit tests** in `tests/test_movement_flow.py`, including a test
   that specifically pins down the "most recent zone snapshot at or
   before this position's timestamp" selection logic against three
   candidate snapshots that would each produce a different (wrong)
   bucket if the selection logic were off by one. Full suite (169 tests)
   green.
4. **Live-validated against real telemetry**: ran `compute_flow_signal`
   against a real 22-match account - got a non-degenerate spread across
   all three buckets (7/9/6), consistent with tertile-calibrated cutoffs
   by construction, not a crash or an all-one-bucket degenerate result.
5. **Wired into `solo.py`**: merged into the same section as Drop Zone,
   now headed "🪂 Drop Zone + Flow" (matching the capability's original
   name) - full real end-to-end render smoke-tested against real cached
   telemetry (not synthetic fixtures) end to end through
   `render_solo_profile`, output confirmed readable and correctly
   formatted.

## Progress as of 2026-07-25 (part 4, same day - regeneration tool + squad.py wiring)

1. **Regeneration tooling built**: `utils/map_calibration.py` +
   `regenerate_map_data.py` (root-level CLI, same convention as
   `solo.py`/`squad.py`/`doctor.py`). Automates the two mechanical steps
   of the Erangel research process - pixel->world conversion
   (`convert_pixels_to_world`, generalized out of the old
   Erangel-only `erangel_poi_world_coordinates`) and telemetry-density
   validation (`validate_landing_density`, generalized out of the ad hoc
   calibration scripts used earlier this session), plus automatic
   NEEDS_REVIEW flagging (>50% below that map's median POI count - the
   same standard that originally caught Kameshki).
   **Deliberately NOT automated**: reading POI label positions off the
   map image in the first place - that's still a human/vision-capable
   assistant visually locating each town's building cluster, same as
   this session's Erangel work. Auto-detecting label positions via
   OCR/CV was considered and explicitly not attempted - real effort of
   its own, not a few-line addition, and risky to get silently wrong.
   `--map` gates on `MAP_SIZE_CM` having a verified entry (refuses Rondo
   until that's confirmed) rather than guessing a coordinate range.
2. **6 unit tests** in `tests/test_map_calibration.py` (pixel scaling,
   radius inclusion/exclusion, per-map isolation, outlier flagging).
   Smoke-tested the CLI end-to-end with a synthetic map to confirm the
   full pixel -> world -> validation round-trip produces sane output
   before considering it done. Full suite: 175 tests, green.
3. **Wired into `squad.py`**: same per-player `compute_drop_zone_signal`
   / `compute_flow_signal` calls now run once per teammate inside the
   existing per-member loop (same pattern as Headline Number/K/D),
   rendered as each teammate's own "🪂 Drop Zone + Flow" card via
   `render_full_squad_cards`'s new `drop_zone_lines`/`flow_lines`
   params. Live-validated end-to-end against two real cached accounts
   (26 and 18 matches) - each teammate correctly got their own
   independent read (one "near Pochinki", one "near School", both
   "Balanced Rotator"), no cross-contamination between members.

## Progress as of 2026-07-25 (part 5, same day - squad-level consolidation)

1. **"Best fit" / "change it up" designed and built**:
   `utils/squad_drop_zone.py`. Votes are grouped at the POI level (not
   exact ambiguity phrasing) - a member reading "near the edge of
   Pochinki" and another reading "between Pochinki and School" both
   count toward Pochinki, since both are genuinely gravitating there.
   "Best fit" requires `MIN_MEMBERS_FOR_CONSENSUS=2` members to
   independently converge on the same POI before saying anything -
   below that there's no real consensus, so it stays silent rather than
   crowning an arbitrary winner from an all-tied vote (same
   don't-overreach standard as every other signal's confidence gate).
   "Change it up" picks the real named POI farthest from the "best fit"
   POI, restricted to POIs at or above the map's *median* real landing
   count (reusing `ERANGEL_LANDING_VALIDATION_400M`) - so it's a
   genuinely different spot, never a token suggestion of a dead corner
   nobody actually plays.
2. **6 unit tests** in `tests/test_squad_drop_zone.py`, including one
   that specifically confirms Zharki (23 real landings, the map's most
   extreme dead corner) never gets suggested as "change it up" even when
   it would otherwise be the geographically farthest option. Full suite:
   181 tests, green.
3. **Wired into `squad_roster.py`/`squad.py`**: `compute_squad_roster`
   now also returns `drop_zone_best_fit_line` /
   `drop_zone_change_it_up_line`, rendered in the Squad Roster header
   block (alongside the existing coverage summary / bolstered line).
   Live-validated against 3 real cached accounts (26/18/14 matches): 2
   of 3 genuinely converged on Pochinki in their real per-player data,
   correctly detected as "Best fit: Pochinki - 2 of 3 squad members
   already tend to land there," with "Change it up: try Sosnovka
   Military Base" (4,390 real landings, well above median, on the
   opposite side of the map from Pochinki) - not a guess, an emergent
   result of real per-player signals actually overlapping.

**This closes the original ask from the top of this doc.** Both per-
player halves (Drop Zone naming, zone-relative Flow) and the squad-level
consolidation are built, calibrated against real data (never guessed
thresholds), unit-tested, and live-validated end-to-end in both `solo.py`
and `squad.py`.

## Progress as of 2026-07-26 (map data completed, cross-map bug fixed)

1. **All 4 ranked-rotation maps done**: Erangel, Miramar, Taego, and Rondo
   all have real, validated POI data. Vikendi and Sanhok are done too - 6
   of 9 currently-playable maps total (per PUBG's official Map Service
   Report, Update 41.2). Rondo needed its own coordinate-range
   verification pass first (no official source states it in cm; confirmed
   empirically against 112 real cached matches instead - see
   `docs/design/map-poi-discovery-procedure.md`, which documents the full
   repeatable process for any future map).
2. **Karakin, Deston, Paramo intentionally not started** - deprioritized
   in favor of bug fixes on the existing capability (see below), not
   forgotten. Camp Jackal and Haven are discontinued (not in PUBG's
   current rotation) and are permanently out of scope - annotated in
   `map_regions_data.py`, no POI work planned ever.
3. **Real bug found and fixed: POI names collide across maps.** "School"
   exists on both Erangel and Taego; "Ruins" and "Quarry" exist on both
   Erangel and Sanhok; "Prison" exists on both Erangel and Miramar. Before
   this fix, `zone_key` was just the bare POI name, so a player's
   aggregate `zone_counts` (and a squad's consensus vote) could silently
   merge two physically different locations on two different maps into
   one count just because the names matched - a real correctness bug,
   not hypothetical, present since Taego was added and worse with every
   map since. Fixed by having `compute_landing_read_from_events`
   (drop_zone.py) qualify every `zone_key` as `"<map_name>||<rest>"`;
   `squad_drop_zone.py`'s voting now keys on `(map_name, poi)` pairs
   instead of bare POI names. Covered by new tests in both
   `test_drop_zone.py` and `test_squad_drop_zone.py` that specifically
   construct the collision scenario and assert it's no longer merged.
4. **`squad_drop_zone.py` generalized off Erangel-only.** "Best fit"
   already worked for any map by construction (it just tallies whichever
   POI name a member's read converged on); "Change it up" was the
   actually-hardcoded half (`erangel_poi_world_coordinates()` /
   `ERANGEL_LANDING_VALIDATION_400M` called directly). Fixed by adding
   `MAP_LANDING_VALIDATION_400M` (map_regions_data.py) as a per-map
   registry paralleling drop_zone.py's `MAP_POI_LOOKUP`, and having the
   consolidation look up whichever map the winning vote actually came
   from. New test confirms "change it up" now produces a real suggestion
   for a non-Erangel map (Rondo) instead of silently returning `None`.

**What's left, not urgent:** Karakin/Deston/Paramo POI data (mechanical,
per the discovery procedure doc, once prioritized); nothing else open on
this capability's design or engineering.

`solo.py` and `squad.py` both call into Drop Zone + Flow, including the
squad-level consolidation now; `main.py` is untouched (by design - it's
the raw-stats view, narrative signals live in solo.py/squad.py only).
