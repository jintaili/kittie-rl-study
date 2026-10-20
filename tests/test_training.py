import copy
import random
import unittest

import numpy as np
import torch

from head_goon_study.actions import log_probabilities
from head_goon_study.advantages import gae, weights
from head_goon_study.bc import train_epoch
from head_goon_study.ppo import loss_terms


class ToyActor(torch.nn.Module):
    """A local tensor fixture, not a gameplay checkpoint."""
    def __init__(self):
        super().__init__()
        self.logits = torch.nn.Parameter(torch.arange(18, dtype=torch.float64) / 20)

    def forward(self, ids, facings):
        return self.logits.log_softmax(-1).expand(len(ids), -1)


class TrainingTests(unittest.TestCase):
    def test_bc_accumulation_and_short_batch_denominator(self):
        rows = [{"ids": [1], "facing": 0, "target": i, "weight": i + 1,
                 "split": "train"} for i in range(3)]
        for denominator in ("actual_batch", "effective_batch"):
            a = ToyActor()
            b = copy.deepcopy(a)
            expected = copy.deepcopy(a)
            for actor, micro in [(a, 1), (b, 3)]:
                opt = torch.optim.SGD(actor.parameters(), lr=.1)
                records = train_epoch(actor, rows, opt, random.Random(2), effective_batch=4,
                                      microbatch=micro, max_grad_norm=100,
                                      loss_denominator=denominator)
                self.assertEqual(sum(r["examples"] for r in records), 3)
            opt = torch.optim.SGD(expected.parameters(), lr=.1)
            divisor = 3 if denominator == "actual_batch" else 4
            loss = -(expected.logits.log_softmax(-1)[:3] * torch.arange(1, 4)).sum() / divisor
            loss.backward()
            opt.step()
            torch.testing.assert_close(a.logits, b.logits)
            torch.testing.assert_close(a.logits, expected.logits)

    def test_bc_rejects_heldout_rows(self):
        actor = ToyActor()
        with self.assertRaises(ValueError):
            train_epoch(actor, [{"split": "test"}], torch.optim.SGD(actor.parameters(), lr=.1), random.Random(0))

    def test_facing_conditionals_normalize(self):
        logits = torch.zeros(2, 12)
        logits[:, 7] = 5  # left-facing flat throw
        logits[:, 11] = 5  # right-facing lob
        p = log_probabilities(logits, torch.tensor([0, 1])).exp().reshape(2, 6, 3)
        torch.testing.assert_close(p.sum((1, 2)), torch.ones(2))
        self.assertEqual(int(p[0, 0].argmax()), 1)
        self.assertEqual(int(p[1, 0].argmax()), 2)
        torch.testing.assert_close(p[0, 2:], p[1, 2:])

    def test_frame_discounting_and_terminal_unapplied_weight(self):
        rows = [dict(episode_id="a", decision=0, done=False, request_frame=0,
                     end_frame=2, frames=2, reward_discounted=1, executed=True, stage="head_goon"),
                dict(episode_id="a", decision=1, done=True, request_frame=2,
                     end_frame=3, frames=1, reward_discounted=2, executed=False, stage="head_goon")]
        adv, target = gae(rows, [0., 0.], {"gamma_per_frame": .5, "lambda_per_20_frames": 1.})
        np.testing.assert_allclose(target, [1.5, 2.])
        np.testing.assert_allclose(weights(rows, ["head_goon"]), [2., 0.])
        rows[-1]["done"] = False
        with self.assertRaises(ValueError):
            gae(rows, [0., 0.], {"gamma_per_frame": .5, "lambda_per_20_frames": 1.})

    def test_ppo_clips_positive_and_negative_advantages(self):
        old = torch.tensor([[.5, .5], [.5, .5]]).log()
        new = torch.tensor([[.9, .1], [.1, .9]]).log()
        loss, _ = loss_terms(new, old, torch.tensor([0, 0]), torch.tensor([1., -1.]),
                             torch.ones(2), {"clip_epsilon": .2, "entropy_coefficient": 0.})
        self.assertAlmostEqual(float(loss), -.4, places=6)


if __name__ == "__main__":
    unittest.main()
