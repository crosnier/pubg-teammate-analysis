# Storyboard Profile

Design concept for curated, glanceable player storyboards - not a stats
dump. Two modes, grounded in PUBG's own esports analytics framework
(PEPS+: Battle / Strategy / Player Type categories - Finishing,
Firepower, Landing Position & Drop Timing, Combat Distance, "Warlike"
aggression) rather than invented categories, and in what community/pro
post-match coaching actually values.

## **Features**

- [x] Archetype Tag (headline label: range + tempo + signature weapon) - see `utils/archetype_tag.py`; presented as plain tempo/range/weapon fields plus a short `Range/Temperament` tag rather than an invented flavor-text headline
- [ ] Map Drop Zone + Flow (primary + secondary landing region, per-region flow)
- [x] The Headline Number (one differentiating, confidence-gated stat) - see `utils/headline_number.py`
- [x] Weapon Signature (or honest "Wildcard" framing when there's no clear pattern) - see `utils/weapon_signature.py`
- [x] Last Match Snapshot (extends #13, adds squad-status-at-death) - see `utils/last_match_brief.py`'s `_compute_squad_status_at_death`
- [x] Squad Read (synergy/gap line, bolstered when high-confidence) - see `utils/squad_read.py`; compute module only, not yet wired into a multi-player CLI flow (see the Resolved note below)
- [ ] Squad Roster summary view (Squads mode, 2+ teammates)
- [ ] Mode 2: After-Action Report (conceptual scope only)
- [ ] Solo mode variant (conceptual scope only)
- [x] Data Budget & Fetch Policy - see `utils/match_scope.py` (recency-window + match-count cap, both env-configurable)
- [ ] Trigger & Invocation (Round Start / After Action)
- [ ] Tester Mode (dev-machine feedback loop)

---

## Two modes

**Mode 1 - Pre-Game Round-Start Intel.** Squad loads in, plane's in the
air, rapidly understand each teammate's persona before the round
starts. Forward-looking, coaching-toward-synergy tone. Fully specced
below.

**Mode 2 - After-Action Report.** Post-match, in-depth: my own
performance, my killer's performance, and - if the killer was in a
squad - the killer's teammates and a collective profile of that squad.
Purpose is retrospective self-improvement (what could've gone
differently), not live pre-fight intel - this is where opponent-scouting
framing belongs. Scoped conceptually, not fully slotted; needs its own
design pass later.

**Solo mode** (no squad, or no useful teammate data) is a planned
variant of Mode 1, not Mode 2. Noted for later; doesn't block or
distract from the primary teammate build.

---

## Mode 1: Pre-Game Round-Start Intel

### The 5-slot card

**1. Archetype Tag** (headline) - one flavorful label combining range +
tempo + signature weapon, e.g. "Hot-Drop AR Rusher."

*Tempo formula*: **time-to-first-contact** is the primary signal - elapsed
time from `LogMatchStart` to the player's first `LogPlayerTakeDamage`
event where they're the attacker against a real player (covers both
damage-only pokes and kills, since a kill is damage that finished the
job). Weight by outcome: fast contact that converts to a kill quickly
reads as decisive aggression; fast contact without a quick kill reads as
a probing skirmish. Bucket into a small label set:

- Very fast contact + quick kill -> "Hot-Drop Headhunter"
- Very fast contact, no quick kill -> "Early Skirmisher"
- Short delay (grab gear, then engage) -> "Quick-Gear Striker"
- Moderate delay -> "Calculated Pusher"
- Long delay or rarely engages early -> "Slow-Roll Patient"

Exact minute thresholds between buckets need calibration against real
match-pacing data (varies by map/mode) at implementation time - not
guessed here. This is one clean, well-defined signal, not a
multi-factor blend.

*Data dependency*: buildable today - reuses kill/damage event parsing
already built for #11/#13 (`utils/combat_stats.py`,
`utils/last_match_brief.py`), just needs `LogPlayerTakeDamage` added to
what's parsed (currently only `LogPlayerKillV2` is consumed).

**2. Map Drop Zone + Flow** - primary *and* secondary landing region
(named PUBG callouts, e.g. Pochinki, Military Base - not a pixel
heatmap; no map image assets, no licensing question, works in CLI
today), each with its own flow description, since flow can differ
meaningfully by landing spot.

*Data dependency*: needs new work - `LogParachuteLanding` region
parsing + subsequent `LogPlayerPosition` trail bucketed by landing
region, plus a new static per-map callout-region reference dataset
(region name -> coordinate bounds) that doesn't exist yet. This is the
concrete #8/#9 dependency, now scoped specifically instead of vaguely.

**3. The Headline Number** - one differentiating "so-what" stat, not
raw K/D. Fully programmatic, no LLM - see algorithm below.

**4. Weapon Signature** - phrased as a preference when there's a real
pattern ("Runs AKM up close, switches to SKS past 100m"), but honest
"Wildcard" framing when the split is close rather than forcing a false
narrative: **"Wildcard - no dominant weapon class; splits fairly evenly
between SMGs and DMRs."** Threshold: top weapon class's share of kills
below ~45%, or top two classes within ~10 points of each other ->
Wildcard framing, name the top two classes instead of committing to
one.

*Data dependency*: buildable today - directly reuses `last_match_brief.
py`'s existing weapon-cleaning and tally logic, extended across a
player's match history instead of just the last match.

**5. Last Match Snapshot** - extends #13's existing `last_match_brief`
data:
- Killer's name stays prominent (`death_info.killed_by` - already
  built).
- **New**: if a squad match, list which squadmates were still alive at
  the moment of this player's death (cross-reference team roster via
  `teamId` against each teammate's own elimination timestamp vs. this
  player's death timestamp).
- **New**: explicitly flag any squadmate already eliminated *before*
  this point and not part of the final fight - "dead earlier,
  unrelated" reads differently from "went down in the same engagement."

*Data dependency*: real extension to `utils/last_match_brief.py` beyond
current #13/#23 scope (squad-roster-at-death cross-referencing) - needs
its own follow-up scoping at implementation time, not a small tweak.

### Squad Read (squad-level, not per-player)

A synergy/gap sentence combining profiled teammates' tags, e.g. "You
(Long-Range/Passive) + DanucD (Close-Range/Aggressive) = classic
push-and-cover. Let them open fights, hold your angle."

**Bolstered when high-confidence**: when a specific behavioral pattern
(e.g., "opens the first engagement") holds in at least 5 of the
teammate's last 8 shared matches (~70%+), add a second, more specific,
data-backed sentence beneath the general read - e.g., "High confidence:
DanucD has opened the first engagement in 6 of your last 8 shared
matches — expect him to push first." Below that threshold, only the
general synergy line shows. Reinforcement has value even when it
confirms something already suspected.

### Headline Number: how it's chosen (programmatic, not LLM)

The *values* (avg kills before first death, close-range fight win rate,
revive count, knockdown-to-kill conversion, damage per match, etc.) are
deterministic aggregations over cached telemetry - no LLM involved,
ever.

The real question is *which one* to surface, so it's genuinely
differentiating for this player rather than the same generic stat for
everyone. Naively picking "most statistically unusual" risks a real
failure mode: a small sample can make a fluke look like a pattern
(e.g., "2.1 kills before death" sounds authoritative even from 3
matches). Confidence-gating is built into the algorithm from the start:

1. Define a fixed pool of candidate stat templates (each with a
   fill-in sentence), grounded in the PEPS+ categories (Firepower,
   Finishing, Combat Distance, Warlike/aggression).
2. Compute every candidate for the player, but only make a candidate
   **eligible if it has a minimum sample size behind it** (proposed:
   8-10 matches of underlying data for that specific stat - fewer data
   points excludes it outright, not just down-weights it).
3. Among eligible candidates, require the pattern to be **stable, not a
   one-hit wonder**: check it holds directionally across two halves of
   the sample window, not driven by one or two outlier games.
4. Score remaining eligible candidates by deviation from baseline
   (self-relative variance across the player's own history - no
   external population dataset needed for a first pass) and surface the
   highest-scoring one.
5. **If nothing clears the eligibility bar**, fall back to the safest,
   most basic aggregate (plain kill count or K/D) rather than force a
   shaky "notable" stat.
6. **Always state the sample size inline** ("...over your last 14
   matches") so reliability is transparent rather than asserted with
   false confidence.

Same confidence-first principle as the Squad Read bolstering rule -
both gated by real sample-size and stability checks before sounding
confident. Standard outlier/z-score "most notable metric" selection,
well-understood and debuggable. Matches `docs/vision.md`'s existing
decision to keep LLM narration out of scope until core capabilities are
stable.

### Mockup - Duos (you + 1 teammate)

```
╔═══════════════════════════════════════════════════╗
║  🔥 DanucD — "Hot-Drop AR Rusher"                  ║
╚═══════════════════════════════════════════════════╝

🗺️  Erangel Drop Zone (last 12 games)
    Primary landing   : Pochinki (5/12 games)
       → Pushes toward the nearest circle edge, rarely rotates wide
    Secondary landing : Military Base (3/12 games)
       → Holds position early, rotates late via the coastline

⚔️  Combat Signature
    Runs AKM up close, switches to SKS past 100m
    Wins close-range fights: engages inside 30m in 62% of kills

📊 The Number That Matters
    Averages 2.1 kills before first death — when they get
    rolling, they don't stop early

🕒 Last Time Out
    8th place · squad match · died to JB_Cruz (AUG) at 21m
    Squad status at the time: 7h3Cr0 still alive · Vacency had
    already gone down earlier, unrelated to this fight

────────────────────────────────────────────────────
🤝 Squad Read: You (Long-Range/Passive) + DanucD
   (Close-Range/Aggressive) = classic push-and-cover.
   Let them open fights, hold your angle.

   High confidence: DanucD has opened the first engagement in
   6 of your last 8 shared matches — expect him to push first.
```

### Mockup - Squads (you + 3 teammates)

Roster summary up top for the true at-a-glance need, full cards after
for depth without requiring interactivity CLI doesn't have:

```
═══════════════════════════════════════════════════════
🎮 SQUAD ROSTER — At a Glance
═══════════════════════════════════════════════════════
  You         "Silent Ridge-Line Sniper"     Long-Range / Passive
  DanucD      "Hot-Drop AR Rusher"           Close-Range / Aggressive
  Vacency     "Wildcard SMG/DMR"             Mid-Range / Balanced
  7h3Cr0      "Support Anchor"               Mid-Range / Passive

🤝 Squad Read: Balanced squad — one entry fragger (DanucD), one
   support anchor (7h3Cr0), you and Vacency cover mid-to-long.
   No overlapping blind spots.

   High confidence: DanucD has opened the first engagement in
   6 of your last 8 shared matches — expect him to push first,
   be ready to flank or clean up.
═══════════════════════════════════════════════════════

[full 5-slot card for DanucD]

[full 5-slot card for Vacency]

[full 5-slot card for 7h3Cr0]
```

Duos skips the roster table (one teammate doesn't need a summary of
itself) and goes straight to the single full card + Squad Read.

---

## Mode 2: After-Action Report (conceptual scope, not fully slotted)

Purpose: after a match ends, understand what happened in the fight that
ended it, and whether anything could've gone differently.

Content categories, grounded in what community/pro post-match coaching
actually values (researched, not assumed) rather than in mechanics the
API can't back up:

- **My own performance this match** - deeper than the Mode 1 teaser:
  full engagement sequence leading to death or victory, not just the
  final blow.
- **My killer's profile** - same archetype/signature framing as Mode 1,
  applied to whoever killed me.
- **If the killer was in a squad**: killer's teammates + a collective
  squad profile, same shape as the Mode 1 Squad Read but describing
  *their* squad.
- **Tactical replay angle** - every item here is a real inference from
  a real telemetry field, never a guess at something the API doesn't
  emit:
  - **Engagement range vs. weapon fit** - was the weapon suited to the
    distance it was used at (e.g., DMR/sniper used inside 15m, or an
    SMG used past 100m)? Distance and weapon already parsed (#13's
    `killerDamageInfo`). Community/pro guidance consistently flags
    range-weapon mismatch as a top self-correctable mistake.
  - **Positioning/elevation** - z-coordinate delta between the player
    and their killer at the moment of the fight, directly from
    `location.z`.
  - **Zone/rotation timing** - was the player already in the blue zone,
    or caught rotating late (`isInBlueZone`/`isInRedZone` flags plus
    `LogPhaseChange` timestamps, both already present in telemetry).
  - **Numbers advantage/disadvantage at the fight** - how many of the
    player's squad vs. the killer's squad were still alive at that
    moment - reuses the same squad-status-at-death cross-reference
    built for Mode 1's Last Match Snapshot slot.
  - **Push vs. hold read** - was the player closing distance
    aggressively into the fight or holding position beforehand, from
    `LogPlayerPosition` deltas leading up to the engagement.
  - **Who fired first** - from `LogPlayerAttack` timestamps for both
    sides in the same engagement window.
- **Explicitly NOT attempted**: stance (crouch/prone), lean direction,
  or specific cover-object usage. Confirmed empirically that PUBG's
  telemetry schema has no stance field anywhere (checked
  `LogPlayerPosition`, `LogPlayerAttack`, `LogPlayerTakeDamage` -
  character objects only carry location/health/zone/vehicle flags).
  This was a lower-priority idea to begin with, not a requirement - so
  it's dropped rather than approximated. The line to hold, consistently:
  derive confidently from real fields, never infer something with zero
  data behind it.

Not mocked up in ASCII yet - needs its own dedicated design pass once
Mode 1 is built and the underlying engagement-sequence parsing
(who-shot-first, distance-over-time) exists to build on.

Sources grounding the category list: [PUBG positioning
analysis](https://gosu.ai/blog/pubg/pubg-positioning-analysis/), [PUBG
Coach - AI match analysis](https://thepubgcoach.com) (an existing
product validating this space - confirms range-vs-weapon fit,
positioning/cover, zone timing, and rotation/fight review are the
categories real post-match coaching centers on).

---

## Solo mode (planned, not detailed here)

When there's no useful teammate to profile (solo queue, or a squad
match where teammates never loaded in), the same Mode 1 slot shapes
apply to the player's own profile instead of a teammate's - Archetype
Tag, Map Drop Zone + Flow, Headline Number, Weapon Signature, Last
Match Snapshot all work unchanged when the subject is "you."

Open design question: what replaces the Squad Read capstone line when
there's no squad. Proposed direction (not locked in): a **Personal
Trend** line in the same "bolstered when confident" shape - e.g., "Your
close-range win rate has climbed from 41% to 58% over your last 20
matches" - momentum/reinforcement coaching about yourself instead of
squad synergy. Flagged for its own design pass later; doesn't block or
reshape Mode 1's primary teammate build.

---

## Cross-cutting: Data Budget & Fetch Policy

Applies to both modes - how much telemetry gets pulled to build a
profile, and how the API budget is managed.

- **No fixed match-count target.** Pull whatever's needed to satisfy
  the confidence-gating rules already defined (Headline Number, Squad
  Read bolstering) - if a player only has 10 matches ever, use all 10;
  don't invent an arbitrary minimum that can't be met.
- **Rate-limit ceiling: never exceed 85% of whatever limit the PUBG API
  states** (`api/rate_limiter.py`'s existing `RateLimitedQueue` already
  reads live `X-RateLimit-*` headers - this is a policy tightening of
  the ceiling it throttles to, not new infrastructure).
- **Fetch smart, not just fast**: never re-pull data already cached
  (existing convention); batch/paginate requests where the API allows
  it, rather than one-at-a-time when a batch endpoint exists.
- **Queue, paginate, never drop.** If building a full profile takes a
  while under the rate limit, show a progress/countdown indicator and
  let it run to completion rather than silently truncating or returning
  partial data. No manual re-invocation should ever be needed just to
  top up data that got cut short.
- **Idea to vet, not a directive yet**: if the first batch (or two) of
  queued/paginated requests comes back quickly with enough content to
  generate profile output already, show that profile immediately and
  update it in place as remaining queued data arrives, rather than
  blocking the whole render on the slowest request.
- **A cap on how many historical matches get telemetry pulled per
  player is required** - unbounded pulls could be excessive for a
  player with a long match history. The exact cap is not known yet and
  needs empirical investigation before implementation - a testing spike
  weighing both (a) API request volume/response timeline under the 85%
  rate-limit ceiling, and (b) actual processing time to mine and curate
  profile content from that much telemetry.
- **Telemetry caching is already shared across players today** -
  confirmed, not a new design decision: `match-telemetry/*.json` files
  are keyed by match ID globally (see `api/telemetry_fetcher.py`'s
  `_is_cached`/`fetch_and_save_telemetry`), not per-player, so a match
  already cached from looking up one player is reused automatically
  when it shows up in a different player's history - likely often,
  since many players share the same matches.
- **Future stretch (not building now)**: an opt-in "gather more data to
  increase profile accuracy" mode, for when someone wants a deeper pull
  than the default confidence-gated minimum.
- **Ad-hoc lookup already works today** - confirmed, not a design
  change: `main.py <playername>` already accepts any player name,
  whether or not the person running it is currently playing with them.

## Cross-cutting: Trigger & Invocation (Round Start / After Action)

Both modes need to fire at the right moment without false triggers -
a hard requirement, not a nice-to-have.

- **Automatic invocation is Phase 3 territory** (`docs/vision.md`'s
  "Automatic squad detection," via on-screen player-name reading) and
  hasn't been started - no OpenCV, screen-capture, or OCR code exists
  anywhere in the repo yet. Nothing to vet or simulate yet because
  nothing's built - needs its own dedicated design/implementation pass
  (screen-read reliability, false-positive avoidance, exactly when
  "plane load-in" and "match end" get detected) before Mode 1/Mode 2
  can auto-fire. Not attempting to design that detection mechanism in
  this doc.
- **Anti-false-trigger requirement carries forward as a hard
  constraint** on whatever that future detection design turns out to
  be: it must not fire Round Start or After Action speculatively - a
  missed trigger (falls back to manual) is far better than a false one.
- **Manual failsafe hotkey**, buildable independently of auto-detection
  and worth having regardless of how reliable detection ends up being:
  a global hotkey combination (unclaimed by the game or Windows,
  specific combo TBD at implementation time) to manually fire "Round
  Start" and a separate one for "After Action." Practical fallback for
  both false negatives and for testing/dev use before auto-detection
  exists at all.

## Cross-cutting: Tester Mode (dev-machine feedback loop)

Separate from the storyboard content itself, but directly relevant to
building Phase 3 reliably given the macOS-dev / Windows-live-test split
already documented in this project's local CLAUDE.md: a **Tester Mode
toggle** that, when enabled, logs objective diagnostic detail that
wouldn't otherwise be logged - detection attempts, confidence scores,
timing, trigger fires and near-misses - to a local file on the Windows
machine. That log can be handed back after a play session instead of
manually relaying everything from memory, so issues get diagnosed from
real data rather than reconstructed secondhand. Scoped for whenever
Phase 3 detection work actually starts - not designed in detail yet
since there's no detection code to log from.

---

## Open questions for implementation

- Exact sample size N for map tendency
- Region-boundary reference data source per map (callout name ->
  coordinate bounds)
- Mode 2's full slot design (this doc only scopes it conceptually)
- The specific failsafe hotkey combination
- Multi-player CLI wiring so Squad Read/Squad Roster are runnable
  end-to-end (today `main.py` only profiles one player per run) - planned
  as a combined follow-up for both slots: a separate entry point reusing
  the existing single-player functions untouched, one deduplicated
  telemetry fetch across all squad members instead of one per player, and
  concurrent player-stats fetches (safe today - `api/rate_limiter.py`'s
  queue already serializes via an `asyncio.Lock` regardless of caller
  count).

Resolved: Archetype tempo bucket thresholds and range-axis thresholds are
both calibrated against real telemetry (1,636 cached matches, including
top-30 ranked PC-NA leaderboard players) - see `utils/tempo_signal.py` and
`utils/range_signal.py`. The per-player historical-match cap is
implemented in `utils/match_scope.py`, currently set low (50 matches)
pending a dedicated performance pass, not yet the intended production
default (250).

Resolved: The Headline Number's candidate pool, eligibility gate,
stability check, and scoring are implemented in `utils/headline_number.py`.
Five candidates cover the PEPS+ categories the doc calls out (Firepower,
Finishing, Combat Distance, plus a team-support read via revives): avg
kills before first death, close-range fight win rate, knockdown-to-kill
conversion rate, revives per match, damage per match. Eligibility requires
`MIN_MATCHES_FOR_CANDIDATE = 8` matches of underlying data, matching the
threshold used across the other Archetype Tag signals. Stability is a
chronological first-half/second-half check requiring the same direction
of deviation from a neutral reference in both halves, with neither half's
deviation dwarfing the other's. Scoring uses two standard, self-relative
statistical tests rather than one blended formula, since a single formula
turned out to blow up for count-type stats at large magnitudes: rate-type
candidates (win rate, conversion rate) use a one-sample z-test for a
proportion against a neutral 50/50 split; magnitude-type candidates
(kills, revives, damage) use a one-sample t-statistic against a neutral
zero. Falls back to a plain kill count when nothing clears the bar.

Resolved: Last Match Snapshot's squad-status-at-death cross-reference is
implemented in `utils/last_match_brief.py` (`_compute_squad_status_at_death`).
Each teammate (same `teamId`, real player) is classified as still alive,
went down in the same fight, or eliminated earlier and unrelated, by
comparing their own first real death timestamp against this player's death
timestamp. The same-fight cutoff (`SAME_ENGAGEMENT_WINDOW_SECONDS = 30`) is
grounded in real data - checked against 10,744 real teammate-death-gap
timings across 250 cached squad matches, which showed no clean bimodal
split, but whose p60 (~29s) lines up closely with `tempo_signal.py`'s
independently-calibrated `QUICK_KILL_WINDOW_SECONDS` (30s), so the same
window is reused rather than introducing a second, unrelated constant for
a similar "quick/connected" question.

Resolved: Squad Read's general synergy line is implemented in
`utils/squad_read.py` as compositional logic (range-bucket delta +
temperament delta between two players), not a hand-authored lookup table
of named roles - scales to any pairing without maintaining a combo table,
and stays consistent with how the other signals derive behavior from raw
data rather than fixed categories. The bolstered "opens first" line reuses
`tempo_signal.py`'s own time-to-first-contact reading for each player and
compares them within the same shared match; the confidence bar is the
doc's own literal worked example - most recent 8 shared matches, at least
5 needed to name a leader (the doc's parenthetical "~70%+" doesn't match
5/8 exactly, so the concrete numeric example was treated as authoritative
over the loose gloss). Compute module only for now - see the open
question above on multi-player CLI wiring.
