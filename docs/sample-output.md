# Sample Output

Two real examples: a single-player run (`python main.py <player>`) and a
two-player squad run (`python squad.py <you> <teammate>`). Player-stats
tables and rate-limiter log lines are trimmed for brevity where noted -
everything else is the actual console output.

## Single player: `python main.py 7h3Cr0`

```text
[SUCCESS] Stats saved for '7h3Cr0' (account ID: account.4d62f321d9e7461a8cd7a29006d31ce2)


╔═════════════════════════════════════════════╗
║                7h3Cr0 Stats                 ║
╚═════════════════════════════════════════════╝

=========================
🎯 COMBAT PERFORMANCE
=========================
                         solo-fpp    duo-fpp     squad-fpp   |  solo    duo     squad 
Kills                         2,351         785         414  |      12       0       2  
Assists                          86         203          87  |       0       0       0  
Headshot Kills                  628         198          96  |       5       0       1  
Knockdowns (DBNOs)               35         614         437  |       0       0       2  
Round Most Kills                 13          13          12  |       3       0       1  
Kill Streak Max                   5           3           3  |       2       0       1  
Team Kills                       42           5           9  |       1       0       0  
Suicides                         79          16          13  |       1       0       0  

=========================
🛡️ SURVIVAL OUTCOMES
=========================
                         solo-fpp    duo-fpp     squad-fpp   |  solo    duo     squad 
Wins                             32          24          15  |       0       0       0  
Losses                        2,474       1,002         620  |      13       0      10  
Top 10 Finishes                 443         223         190  |       0       0       1  
Rounds Played                 2,506       1,023         630  |      13       0      10  
Time Survived (min)          31,241      11,162       7,244  |     109       0     107  
Longest Survival (min)           32          29          28  |      15       0      23  
Most Survival Time (min)      1,933       1,797       1,698  |     943       0   1,393  
Daily Wins                        0           0           0  |       0       0       0  
Weekly Wins                       0           0           0  |       0       0       0  

  ... (Support Actions / Movement Stats / Equipment & Vehicles / Activity
       Over Time follow the same per-mode table format)

╔═════════════════════════════════════════════╗
║            7h3Cr0 Match History             ║
╚═════════════════════════════════════════════╝

======================================
🕹️ DUO-FPP Matches (Most Recent First)
======================================
Total Matches: 14

  • Match ID: d988278f-dea5-45e4-ac34-d9dbfe836f7d
  • Match ID: 22ec554a-4708-4318-9f5c-9558e4cf4116
  ... (12 more)

========================================
⛔ Other Modes
========================================
squad-fpp      → No matches
solo           → No matches
duo            → No matches
squad          → No matches


[INFO] Fetching telemetry for 15 matches...

╔════════════════════════════════════════╗
║         Telemetry Fetch Summary        ║
╚════════════════════════════════════════╝
✅ Saved: 0     ⏭️  Skipped: 15    ❌ Failed: 0  


=============================
🎯 Summary - Combat Stats
=============================
Eliminations : 14
Deaths       : 14
K/D Ratio    : 1.00
(from 15 cached matches with telemetry)

=============================
🔫 Eliminations Breakdown
=============================
Celsius          : 1
wetee777         : 1
SurvivalAvocado  : 1
Dbl_cheezeburger : 1
drjakespeare     : 1
... (9 more, one kill each)

=============================
💀 Deaths Breakdown
=============================
LordFancypants : 1
FURTLECRESCENT : 1
N1GHT_737      : 1
... (11 more, one death each)


=============================
🏷️  Archetype Tag
=============================
Tempo  : Slow-Roll Patient  (11/15 matches with contact)
Range  : Mid-Range  (median 32.3m over 14 kills)
Weapon : Wildcard - no dominant class; splits between SMG and DMR  (14 classifiable kills)

Short tag: Mid-Range/Passive
(from 15 matches analyzed)


=============================
📊 The Number That Matters
=============================
Averages 147 damage per match over your last 15 matches


=============================
📋 Last Match Brief - 7h3Cr0
=============================
Match ID   : d988278f-dea5-45e4-ac34-d9dbfe836f7d
Round Rank : 8
Time Alive : 18m 40s
Kills      : 0
Top Weapon : -
Died To    : JB_Cruz (AUG) from 20.9m
In your last shared match: No

=============================
🤖 Bot Detection - Last Match
=============================
Match ID: bad84eae-bb95-433d-8efe-da3bea2513ee
Bots Detected: 4

  • Acapitalist  (ai.340)
  • Ajudging  (ai.339)
  • Faabyhop97  (ai.338)
  • Osunog94  (ai.337)
```

## Squad: `python squad.py VALL-__- af0nso`

```text
[SUCCESS] Stats saved for 'VALL-__-' (account ID: account.1e7b85df46e94898b7e1d60397fa57c6)
[SUCCESS] Stats saved for 'af0nso' (account ID: account.77a6d0650f844af6a640bcc7d9e28715)

[INFO] Fetching telemetry for 79 unique matches across 2 players...
[INFO] 27 new matches found; fetching 25 this run to stay conservative on telemetry requests. Re-run later to continue backfilling.

╔════════════════════════════════════════╗
║         Telemetry Fetch Summary        ║
╚════════════════════════════════════════╝
✅ Saved: 25    ⏭️  Skipped: 52    ❌ Failed: 0  


=============================================
🎮 SQUAD ROSTER - At a Glance
=============================================
  You           Hot-Drop Headhunter     Mid-Range/Aggressive
  af0nso        Hot-Drop Headhunter     Mid-Range/Aggressive

🤝 Squad Read: All-Aggressive squad: you (aggressive skirmisher), af0nso (aggressive skirmisher). No one covers close-range, long-range - you may be exposed there.

High confidence: af0nso has opened the first engagement in 5 of your last 8 shared matches - expect af0nso to push first.
=============================================

--- af0nso ---
=============================
🏷️  Archetype Tag
=============================
Tempo  : Hot-Drop Headhunter  (47/50 matches with contact)
Range  : Mid-Range  (median 26.5m over 155 kills)
Weapon : AR  (148 classifiable kills)

Short tag: Mid-Range/Aggressive
(from 50 matches analyzed)
=============================
📊 The Number That Matters
=============================
Averages 418 damage per match over your last 50 matches
```

Notice the telemetry fetch above: 79 unique matches across two players who
share a lot of match history, but only 27 were new - the other 52 were
already cached from looking either player up before. A match two teammates
played together only ever gets pulled once, no matter how many times
either of them shows up in a future squad lookup.
