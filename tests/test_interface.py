"""Check the extracted interface against retained inputs and native event records."""
import copy
import json
from pathlib import Path
import unittest

from head_goon_study.observations import build_input, messages, NAMES, OPTIONS
from head_goon_study.rewards import EpisodeMetrics
from head_goon_study.event_rewards import RewardState, RewardTracker
from head_goon_study.reward_config import RewardConfig
from head_goon_study.ball_physics import physics, hit_reward

ROOT = Path(__file__).resolve().parents[1]

class InterfaceTests(unittest.TestCase):
    def test_retained_observation_and_causal_boundary(self):
        wire = json.loads((ROOT / 'paper/examples/observation.json').read_text())
        expected = json.loads((ROOT / 'paper/examples/qwen-messages.json').read_text())
        self.assertEqual(messages(build_input(wire, 'head_goon')), expected)
        # Archive labels and measured future timings cannot enter the input.
        wire.update(outcome='win', action=17, measured_future_latency=12345)
        self.assertEqual(messages(build_input(wire, 'head_goon')), expected)
        bad = copy.deepcopy(wire)
        bad['questions']['throw_right']['instructions']['shot_feedback'] = {'future': True}
        with self.assertRaises(ValueError):
            build_input(bad, 'head_goon')

    def test_physical_button_map(self):
        self.assertEqual(len(NAMES), 18)
        self.assertEqual(OPTIONS['right_hold_a_lob'], ['right', 'a', 'b', 'up'])
        self.assertEqual(OPTIONS['neutral_release_a_none'], [])
        for action in NAMES:
            buttons = OPTIONS[action]
            self.assertEqual('a' in buttons, '_hold_a_' in action)
            self.assertEqual('b' in buttons, not action.endswith('_none'))
            self.assertEqual('up' in buttons, action.endswith('_lob'))
            self.assertFalse('left' in buttons and 'right' in buttons)

    def test_recorded_reward_events(self):
        fixture = json.loads((ROOT / 'tests/fixtures/recorded-rewards.json').read_text())
        for pair in fixture['pairs']:
            metrics = EpisodeMetrics(pair['before'], 480, True)
            actual = metrics.sample(pair['after'], 1, pair['events'])
            self.assertEqual(actual, pair['reward'])
            self.assertEqual(metrics.reward.total, pair['reward'])
            for event in pair['events']:
                if event['kind'] == 'boss_hit':
                    self.assertEqual(event['reward'], hit_reward(event['bounces']))
        damaged = next(p for p in fixture['pairs'] if p['events'])
        with self.assertRaises(ValueError):
            EpisodeMetrics(damaged['before'], 480, True).sample(damaged['after'], 1, [])

    def test_terminal_rewards_and_no_double_counting(self):
        initial = RewardState(30, True, 3, 1, 1, 0, 3)
        tracker = RewardTracker(initial, 480, True, RewardConfig())
        dead = RewardState(30, True, 0, 1, 1, 0, 3, dead=True)
        terms = tracker.update(dead, 1, timeout=True)
        self.assertEqual(terms['damage'], -12)
        self.assertEqual(terms['death'], -30)
        self.assertNotIn('timeout', terms)
        with self.assertRaises(RuntimeError):
            tracker.update(dead, 1)
        tracker = RewardTracker(initial, 480, True, RewardConfig())
        self.assertEqual(tracker.update(initial, 0, timeout=True)['timeout'], -5)

    def test_surface_rebound_not_apex_or_rest(self):
        ball = dict(state=0, vx=0, vy=-2, cooldown=2, x=1000, y=1000, armed=1)
        _, events = physics(ball, False, 2)
        self.assertEqual(events, [])
        ball.update(y=1984, vy=0)
        _, events = physics(ball, False, 2)
        self.assertEqual(events, [])
        ball.update(y=1980, vy=20)
        after, events = physics(ball, False, 2)
        self.assertEqual(events, ['floor'])
        self.assertLess(after['vy'], 0)

if __name__ == '__main__':
    unittest.main()
