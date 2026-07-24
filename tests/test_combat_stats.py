##########
# Unit Test for Combat Stats parsing
# from root of project: `python -m unittest discover tests`
##########

import unittest
from utils.combat_stats import compute_combat_stats_from_events

ME = "account.me"
RIVAL_A = "account.rival_a"
RIVAL_B = "account.rival_b"


def kill_event(killer_id, killer_name, victim_id, victim_name, is_suicide=False,
               killer_type="user", victim_type="user"):
    return {
        "_T": "LogPlayerKillV2",
        "isSuicide": is_suicide,
        "killer": {"accountId": killer_id, "name": killer_name, "type": killer_type},
        "victim": {"accountId": victim_id, "name": victim_name, "type": victim_type},
    }


class TestCombatStats(unittest.TestCase):

    def test_tallies_eliminations_and_deaths_by_opponent(self):
        documents = [[
            kill_event(ME, "Me", RIVAL_A, "RivalA"),
            kill_event(ME, "Me", RIVAL_A, "RivalA"),
            kill_event(RIVAL_B, "RivalB", ME, "Me"),
        ]]

        stats = compute_combat_stats_from_events(ME, documents)

        self.assertEqual(stats["total_eliminations"], 2)
        self.assertEqual(stats["total_deaths"], 1)
        self.assertEqual(stats["eliminations_breakdown"], {"RivalA": 2})
        self.assertEqual(stats["deaths_breakdown"], {"RivalB": 1})

    def test_excludes_suicides(self):
        documents = [[kill_event(ME, "Me", ME, "Me", is_suicide=True)]]

        stats = compute_combat_stats_from_events(ME, documents)

        self.assertEqual(stats["total_eliminations"], 0)
        self.assertEqual(stats["total_deaths"], 0)

    def test_excludes_non_user_killers_and_victims(self):
        # Environmental deaths (bluezone, falls) have no real opposing player.
        documents = [[kill_event(ME, "Me", "npc.bluezone", "BlueZone", killer_type="npc")]]

        stats = compute_combat_stats_from_events(ME, documents)

        self.assertEqual(stats["total_deaths"], 0)
        self.assertEqual(stats["deaths_breakdown"], {})

    def test_breakdown_sorted_descending(self):
        documents = [[
            kill_event(ME, "Me", RIVAL_A, "RivalA"),
            kill_event(ME, "Me", RIVAL_B, "RivalB"),
            kill_event(ME, "Me", RIVAL_B, "RivalB"),
        ]]

        stats = compute_combat_stats_from_events(ME, documents)

        self.assertEqual(list(stats["eliminations_breakdown"].items()), [("RivalB", 2), ("RivalA", 1)])


if __name__ == '__main__':
    unittest.main()
