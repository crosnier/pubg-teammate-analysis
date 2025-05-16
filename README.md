# PUBG Teammate Analysis

*Analyze and visualize stats of your PUBG teammate(s) to make smarter squad decisions.*

As I join a round I like to know who I'm playing with. This project leverages the PUBG APIs to parse and analyze teammate performance, match history, and player statistics. It's designed to help players make informed decisions about who they team up with (or not).

---

## 🚀 Getting Started

1. Clone the repo and set up a virtual environment:

```bash
git clone https://github.com/crosnier/pubg-teammate-analysis.git
cd pubg-teammate-analysis
python3 -m venv .venv
source .venv/bin/activate
```

2. Install required packages from `requirements.txt`:

```bash
pip install -r requirements.txt  # includes requests, python-dotenv, aiohttp
```

3. Set up a `.env` file with your PUBG API key:

```
PUBG_API_KEY=your_api_key_here
```

4. Run the CLI with a player name:

```bash
python main.py PlayerName
```

---

## 🧭 System Flow

Just run `main.py` with a player name and let the automation do the rest.

```text
main.py
 ├──▶ Step 1: Load player name from CLI and reference player-index.json
 ├──▶ Step 2: Fetch player stats via PUBG API
 │       └── utils/io_helpers.py → stores to ./playerstats/
 ├──▶ Step 3: Display match history
 │       └── utils/display_match_history.py
 ├──▶ Step 4: (Optional) Fetch match telemetry files
 └──▶ Step 5: Display categorized stat tables by mode
         └── utils/display_stats_by_mode.py
```

---

## 📂 File Structure Overview

```
├── main.py
├── match-telemetry/                # Raw telemetry JSON files
├── matches/                        # Future match-level reports
├── playerstats/                    # Cached player stat data
├── player-index.json               # List of tracked players
├── requirements.txt
├── tests/
│   └── test_player_stats.py
├── utils/
│   ├── display_match_history.py
│   ├── display_stats_by_mode.py
│   ├── io_helpers.py
│   └── suppress_warnings.py
└── README.md
```

---

## 🔧 Features (Built So Far)

- ✅ Player Stats Query (lifetime stats by name)
- ✅ Display player stats by game mode
- ✅ Match ID history display
- ✅ Telemetry file lookup and fetch queue
- ✅ Console UI: Table display of stats per category
- ⚠️ Bot detection prototype (matches with few real players)
- ⚙️ Player index to preload common teammate names

---

## 🛠 Notes

- Only telemetry files are required to analyze bot/player behavior.
- Match IDs pulled from cached stats, not fresh API calls (avoids rate limits). Match json doesn't change once generated.

---

## 📸 Sample Console Output

```text
[SUCCESS] Stats saved for 'DanucD' (account ID: account.74c87c9ee413407894c9ec17063ea023)


╔═════════════════════════════════════════════╗
║                DanucD Stats                 ║
╚═════════════════════════════════════════════╝

=========================
🎯 COMBAT PERFORMANCE
=========================
                         solo-fpp    duo-fpp     squad-fpp   |  solo    duo     squad 
Kills                        51,548      80,046      24,270  |     109     404     250  
Assists                         663      18,513       5,408  |       2      81      40  
Headshot Kills               16,120      21,064       5,733  |      26     120      65  
Knockdowns (DBNOs)              498      47,291      20,101  |       0     249     272  
Round Most Kills                 23          29          24  |      16      19      13  
Kill Streak Max                   5           6           5  |       2       5       4  
Team Kills                       24         123          71  |       0       3       1  
Suicides                         88         184          82  |       0       2       0  

=========================
🛡️ SURVIVAL OUTCOMES
=========================
                         solo-fpp    duo-fpp     squad-fpp   |  solo    duo     squad 
Wins                            901       2,139         637  |       4       5       3  
Losses                       12,236      17,894       6,290  |      32      80      98  
Top 10 Finishes               1,947       5,038       2,042  |       6      23      12  
Rounds Played                13,090      19,699       6,835  |      36      85     100  
Time Survived (min)          7,324k     12,546k      4,331k  |  24,184  53,565  42,576  
Longest Survival (min)           36          33          35  |      31      32      32  
Most Survival Time (min)      2,165       2,036       2,101  |   1,916   1,930   1,940  
Daily Wins                        1           0           0  |       0       1       1  
Weekly Wins                       1           0           7  |       0       1       1  

=========================
💉 SUPPORT ACTIONS
=========================
                         solo-fpp    duo-fpp     squad-fpp   |  solo    duo     squad 
Heals                        39,743      85,219      26,035  |      51     272     218  
Revives                          63       9,877       2,978  |       0      31      22  
Boosts                       38,678      69,347      20,310  |      80     274     208  

=========================
🏃 MOVEMENT STATS
=========================
                         solo-fpp    duo-fpp     squad-fpp   |  solo    duo     squad 
Walked Distance              9,790k     17,317k      6,581k  |  32,508  75,926  34,682  
Driven Distance             19,704k     30,033k      7,631k  |  50,462    143k  85,268  
Swam Distance                 6,075      14,984       8,396  |      66       0      14  
Longest Kill Shot               669         919         901  |     219     446     336  
Road Kills                      342         350          90  |       0       4       5  

=========================
🔧 EQUIPMENT & VEHICLES
=========================
                         solo-fpp    duo-fpp     squad-fpp   |  solo    duo     squad 
Weapons Acquired             68,791        115k      34,600  |     133     400     608  
Vehicles Destroyed              231         613         139  |       0       2       1  

=========================
📆 ACTIVITY OVER TIME
=========================
                         solo-fpp    duo-fpp     squad-fpp   |  solo    duo     squad 
Days Played                   1,460       1,435         946  |      19      23      30  
Daily Kills                      54          12           7  |       3      19      41  
Weekly Kills                     54          12         107  |       3      19      46  




╔═════════════════════════════════════════════╗
║            DanucD Match History             ║
╚═════════════════════════════════════════════╝

=======================================
🕹️ SOLO-FPP Matches (Most Recent First)
=======================================
Total Matches: 32

  • Match ID: d575aa3e-b627-45b9-9879-3d6a789026ad
  • Match ID: 01381014-b404-4fbb-9979-56a1fb38a7cc
  • Match ID: 6738a645-cb57-4ada-8670-0b3709d5dc8d
  • Match ID: 7e8e0d19-cc82-4ab3-bcdb-3be9d9f3ad6e
  • Match ID: 66064397-341f-49c9-a828-a3f19299411f
  • Match ID: cbd1bb35-5664-4604-8954-e4e6ee14551d
  • Match ID: 73ca1748-8426-4a8d-ae78-9a0aca839f72
  • Match ID: 69536c62-3712-43f9-9200-5dc6890a1131
  • Match ID: 3eaa7d48-4cb1-4e0f-948d-413b2c9bc6e2
  • Match ID: 2d103083-a4a7-4265-afbd-0b52b185e346
  • Match ID: 04d0faa4-6b36-430c-9605-69260aa9e6c2
  • Match ID: 26aab18e-228c-4c93-8f33-db6c819da59d
  • Match ID: 371bdf3e-8dd7-40e1-bf2b-8cb47f9c8725
  • Match ID: 407840f9-7a21-4651-82ae-fe846e453d8a
  • Match ID: 34a74de3-2a63-433f-9f6a-f87a1e12aa85
  • Match ID: 0cb4a64a-55f1-4c9e-a898-70c279b015c7
  • Match ID: b778c351-6253-4cd9-ab12-c5b41791137a
  • Match ID: 9faaa093-74c8-40fa-b811-6b68d2be100e
  • Match ID: 52078b23-424d-4f06-86b4-99dcd2c91c06
  • Match ID: b836c02e-49d1-4a3b-8546-d6c8c388e1c3
  • Match ID: 42282af7-f8fc-4690-859a-22499c32c0cd
  • Match ID: cd02861d-4191-413c-9204-24566f651d50
  • Match ID: 2ed05415-ae9d-4072-9fe3-b400951f00f3
  • Match ID: 2a701430-a6a6-47b5-a451-e19dcc21825a
  • Match ID: de0a1dca-0ed7-4fae-a2db-c836bf578aa3
  • Match ID: b4947e05-9bca-43b9-ace2-fbbc5ece2763
  • Match ID: 9bc3e166-4f92-4a69-bd1e-c9b65361ac7a
  • Match ID: b0469f40-fa90-4151-aa69-1e476ffaf0f9
  • Match ID: 0fca0b9d-c500-480a-8ea2-a87ea5fd1c11
  • Match ID: 9962b736-7c2b-47c8-b60c-c51ce5e69738
  • Match ID: c4f67bbf-336c-46bd-8d5b-94ca7d2fd732
  • Match ID: 5e253ff1-1c9d-4818-9835-ed376d95b8de

======================================
🕹️ DUO-FPP Matches (Most Recent First)
======================================
Total Matches: 32

  • Match ID: 6de4decf-c2f2-43a0-9e74-f060188b1edb
  • Match ID: 665aba55-2573-4cad-8290-427815d0e7f4
  • Match ID: f68ffb05-ff11-4869-8eb7-e67d05cc82f4
  • Match ID: 305b4d64-e8c5-4fd5-b16c-4b436aa277e4
  • Match ID: efe358ec-df2b-414d-b8e6-5f56b914f52a
  • Match ID: 65759780-4cf6-4644-b605-fc42f13d560a
  • Match ID: 80f7eaa4-9a5b-497f-b5ab-04b07a351046
  • Match ID: 68a18cc6-496f-444b-adcb-e0e1057034c6
  • Match ID: 351fc51c-9567-414e-8fdd-187238533494
  • Match ID: 49548aa5-d5a6-427e-a83d-035a9d065695
  • Match ID: afd0ba8f-a2b1-4b53-9421-b6d1fa7768f1
  • Match ID: dc65c0ec-ba87-48df-9f8b-8eebc30877c9
  • Match ID: 24a39e89-e998-496b-8fb1-0a8a34a51d44
  • Match ID: 6d1eccbf-2b25-4703-9fe5-17382823adb8
  • Match ID: 63dac5f9-5bc6-4e75-8a27-1931ba27667f
  • Match ID: d6230de5-95ba-4ddc-99ac-513b930767e4
  • Match ID: f64cefea-80b2-40b1-83ca-9011a43c56e8
  • Match ID: 5e28f3a0-9bec-485b-a878-7d608a983d76
  • Match ID: 7b452c46-71e2-4762-9deb-e699476a6694
  • Match ID: f7a60987-85bd-4d4f-9a18-678dcb481325
  • Match ID: e44ef65a-feb1-4dd8-80f9-c7a6c68a76c2
  • Match ID: 9d3e6619-c9ab-42e2-b318-ce9e53693d3b
  • Match ID: 7b6211b2-cf9d-4bca-b73a-c144bd2c16d4
  • Match ID: 61a80aad-8c6e-4119-8b61-a7eac489eb40
  • Match ID: 528050fd-6728-42e2-8e88-7a3f07df621e
  • Match ID: c55b0cba-9062-4409-b862-33ac15a698a3
  • Match ID: 991b51a5-30ea-4fab-87dc-2b1794938afd
  • Match ID: 1ed988c0-5b80-4456-8c12-8422763409a1
  • Match ID: 27249ffe-93ac-4cbc-98b6-7d57fbe03069
  • Match ID: 4dd79c66-0945-430b-9792-769f7bbcb7ee
  • Match ID: 87f8ea36-4dad-40ac-b94f-0c69ac6ec305
  • Match ID: bf64ec4f-d40c-4414-a0aa-0fe04d089b9e

========================================
🕹️ SQUAD-FPP Matches (Most Recent First)
========================================
Total Matches: 32

  • Match ID: 27c0ef2a-116a-451c-8907-42cbe75858a9
  • Match ID: 217cada8-a9ea-4569-8a82-7b98991c1135
  • Match ID: 6ffd1ca7-78f9-4127-ba6c-d880615a11bd
  • Match ID: 2117b8e6-01ec-470e-8b57-487b73dbddb3
  • Match ID: c25740ac-6e80-43bc-b044-6a1c66485a8a
  • Match ID: 24339006-72bc-4036-88f5-e6343017ac54
  • Match ID: a121b722-5426-49d3-9b31-2bf3ee372ab6
  • Match ID: b5883225-e661-42bc-9863-7bc52f3350b5
  • Match ID: eefe30d5-1b81-4ffe-a036-82ab345ed8ac
  • Match ID: 157e0d18-f0de-4066-85f9-b6db6fefefde
  • Match ID: 0932d962-0faa-4d13-bc66-2e1816b12397
  • Match ID: 989da2c9-9957-446f-92de-8038a64d519d
  • Match ID: c39cf33c-8cc6-4cec-ab5d-f9742d3750bb
  • Match ID: 2753f8fe-0f07-4b00-9ceb-9a8ce228bbd1
  • Match ID: f0680bd9-2b83-4310-afed-9ca103948547
  • Match ID: c7d58f99-7402-41b0-a2e9-ac3d14f6ed3b
  • Match ID: 18b10e80-1e32-4467-8305-c65773f3e266
  • Match ID: 2867b3e3-7042-4b6a-9842-5cbb47ce475e
  • Match ID: 68cb8334-43d2-44c2-b8dd-f7ba6d6b0bff
  • Match ID: 4f846e34-6960-4601-869f-e5de18501145
  • Match ID: 25e1aeda-d496-44a2-944e-f8c6ce9accdf
  • Match ID: c62fe03a-2779-4fc7-b6a4-8cfa48e90237
  • Match ID: b3b8dfed-9fd0-4b6e-8ef6-9fb2c69205ea
  • Match ID: f3eee5c6-58c2-4dab-a373-2269e18fbde4
  • Match ID: abfaabe2-a221-4494-8cc7-b34252245a2e
  • Match ID: 94497f2d-a625-4e7c-8660-6e505505e12e
  • Match ID: 3a8af7e6-9a0c-4b28-8f6e-65ea0f423863
  • Match ID: 55b8d964-c6b0-440f-841c-852c0ee9a306
  • Match ID: 6ae0f8ad-9687-4cdb-a924-cdf6109d0d3d
  • Match ID: ad5f4757-bb98-413d-b41b-5eba2e6511d5
  • Match ID: 480b53d5-d5f4-4816-884a-8a57c6a262a6
  • Match ID: 1921b6aa-6342-4ede-a2c1-fcbae22c9696

========================================
⛔ Other Modes
========================================
solo           → No matches
duo            → No matches
squad          → No matches


[INFO] Fetching telemetry for 96 matches...

╔════════════════════════════════════════╗
║         Telemetry Fetch Summary        ║
╚════════════════════════════════════════╝
✅ Saved: 0     ⏭️  Skipped: 96    ❌ Failed: 0  

```