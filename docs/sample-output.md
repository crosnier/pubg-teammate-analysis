# Sample Output

Example run of `python main.py DanucD`, showing lifetime stats by game mode
followed by match history grouped by mode.

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
  ... (29 more)

======================================
🕹️ DUO-FPP Matches (Most Recent First)
======================================
Total Matches: 32

  • Match ID: 6de4decf-c2f2-43a0-9e74-f060188b1edb
  • Match ID: 665aba55-2573-4cad-8290-427815d0e7f4
  • Match ID: f68ffb05-ff11-4869-8eb7-e67d05cc82f4
  ... (29 more)

========================================
🕹️ SQUAD-FPP Matches (Most Recent First)
========================================
Total Matches: 32

  • Match ID: 27c0ef2a-116a-451c-8907-42cbe75858a9
  • Match ID: 217cada8-a9ea-4569-8a82-7b98991c1135
  • Match ID: 6ffd1ca7-78f9-4127-ba6c-d880615a11bd
  ... (29 more)

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
