# Teammate Stats

## **Features**  
- [ ] Data Query + manually enter target player
- [ ] Player Stats by Game Mode  
- [ ] Player Match History

- [ ] list of 'players killed' with count
- [ ] list of 'killed by players' with count

---

## **Player Stats**  

requirements:  
- ASCII formatting for headers
- data columns for each game mode, in this order from left to right:
  - solo-fpp    duo-fpp     squad-fpp  |  solo    duo     squad

```
=========================
🎯 COMBAT PERFORMANCE
=========================
                    solo-fpp    duo-fpp     squad-fpp  |  solo    duo     squad
Kills             : 591
Assists           : 166
Headshot Kills    : 153
Knockdowns (DBNOs): 481
Round Most Kills  : 10
Kill Streak Max   : 3
Team Kills        : 5
Suicides          : 12

=========================
🛡️ SURVIVAL OUTCOMES
=========================
                    solo-fpp    duo-fpp     squad-fpp  |  solo    duo     squad
Wins              : 18
Losses            : 828
Top 10 Finishes   : 178
Rounds Played     : 843
Time Survived     : 532,572.5 sec
Longest Survival  : 1,797 sec
Most Survival Time: 1,797 sec
Daily Wins        : 1
Weekly Wins       : 3

=========================
💉 SUPPORT ACTIONS
=========================
                    solo-fpp    duo-fpp     squad-fpp  |  solo    duo     squad
Heals             : 1,095
Revives           : 168
Boosts            : 1,256

=========================
🏃 MOVEMENT STATS
=========================
                    solo-fpp    duo-fpp     squad-fpp  |  solo    duo     squad
Walked Distance   : 573,472 m
Driven Distance   : 926,628 m
Swam Distance     : 2,195 m
Longest Kill Shot : 570 m
Road Kills        : 11

=========================
🔧 EQUIPMENT & VEHICLES
=========================
                    solo-fpp    duo-fpp     squad-fpp  |  solo    duo     squad
Weapons Acquired  : 3,571
Vehicles Destroyed: 8

=========================
📆 ACTIVITY OVER TIME
=========================
                    solo-fpp    duo-fpp     squad-fpp  |  solo    duo     squad
Days Played       : 101
Daily Kills       : 14
Weekly Kills      : 56

```

---

## **Player Match History**  

requirements:  
- ASCII formatting for headers
- display game mode headers (sections) ONLY when there's match IDs available. 
- modes without match data are grouped underneath a section named 'Other Modes'

```
=======================================
🕹️ SOLO - FPP Matches (Most Recent First)
=======================================
Total Matches: 6

  • Match ID: 921c2ded-24cf-4ea1-b6cb-c8da722f3dd7
  • Match ID: 9f92cbd0-8cbb-4a7f-a471-9c77e42aa08b
  • Match ID: 6d201eaa-b3d3-4c4b-82be-3f483f98c705
  • Match ID: 4003af73-a00f-4d12-87cc-acc2a524230e
  • Match ID: 4c5a546c-9e0c-4f50-a6b1-e06015cadc4e
  • Match ID: a108a369-4743-4aad-bb39-e52179cdb1b5

=======================================
🎮 DUO - FPP Matches (Most Recent First)
=======================================
Total Matches: 33

  • Match ID: 919fe898-67da-4fb9-8bdd-0fe2cb796478
  • Match ID: 66c63e6a-74cc-4839-9b07-b373f93ef62c
  • Match ID: ee003f8d-a814-4cc4-aa93-a53bfca8f59f
  • Match ID: 64de0184-c985-44b9-a7c8-ef8b75c8cf38
  • Match ID: b0277217-cfb4-438a-93db-43ba200cdc08
  • Match ID: 96017a6b-89cd-4e0a-ad59-03588ec026a4
  • Match ID: 3bc73df9-ebf5-4bca-b543-5b13baf8cbff
  • Match ID: 8a1d85cb-c05b-4691-bb9c-8fbeeb5eae5e
  • Match ID: e91ae678-e50a-4b4a-ab1c-105fbc70d53b
  • Match ID: 7db019bc-7db4-4c3f-977c-402ace31a5f4
  • Match ID: d0d1d900-1e77-4997-ba44-79b48c38dbea
  ... (22 more)

=======================================
⛔ Other Modes
=======================================
solo         → No matches
duo          → No matches
squad        → No matches
squad-fpp    → No matches
```

---

## **Combat Stats by Player**

```
=============================
🎯 Summary – Combat Stats
=============================
Eliminations : 78
Deaths       : 64

=============================
🔫 Eliminations Breakdown
=============================
PlayerName_7   : 16
PlayerName_2   : 13
PlayerName_5   : 12
PlayerName_9   : 10
PlayerName_4   : 8
PlayerName_1   : 7
PlayerName_3   : 6
PlayerName_6   : 4
PlayerName_8   : 2

=============================
💀 Deaths Breakdown
=============================
PlayerName_3   : 14
PlayerName_4   : 11
PlayerName_7   : 10
PlayerName_6   : 9
PlayerName_1   : 7
PlayerName_2   : 6
PlayerName_8   : 4
PlayerName_9   : 2
PlayerName_5   : 1
```

---

## **Samples for Inspiration**  

![stats sample 1](../../images/pubg-player-stats-sample.png)
