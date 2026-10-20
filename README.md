# Head Goon: behavior cloning → PPO

Training code and paper companion for a Qwen3.5-0.8B policy in real-time native gameplay.
Successful JEV demonstrations supply behavior cloning. PPO then specializes the policy to the Head Goon boss encounter.

## Training

The training implementation is the primary deliverable. The initial extraction includes:

- Weighted BC updates and trajectory weighting.
- The 18-action probability readout and PPO scoring.
- Frame-discounted advantages, clipped PPO updates, KL audits and critic fitting.
- Scientific settings in `configs/` and source provenance in `provenance/`.

These are callable training components. End-to-end model loading, demonstration assets,
native rollout collection, checkpoint orchestration and a GPU environment are still being
packaged. **There is no complete training command yet.** See [training status](docs/training.html).

For the CPU tests of training arithmetic, using synthetic tensors only:

```sh
python -m pip install -e '.[training-core]'
python -m unittest discover -s tests
```

This dependency set covers the extracted training core. It is not the complete historical GPU environment.
The tests do not load a policy, play the game or call a model API.

## Paper and analysis

The [paper](paper/index.html) and [supplement](paper/supplement.html) include all reported outcomes.
Small analysis utilities reproduce the numerical claims from included records:

```sh
python paper/code/analysis.py
python -m unittest discover -s paper/code -p test_study.py
python -m pip install -e '.[figures]'
python paper/code/figures.py
python paper/code/timing_figure.py
python paper/code/paper.py
```

Serve this directory with `python -m http.server 8000` to read the HTML.
Detailed historical reports and videos currently link to the author's private archive.
They are not required for the included numerical analysis and are not publicly distributed yet.

## Reproduction scope

The shortest training path is pretrained Qwen → BC → PPO. The supervised phase has two
stages, specified in the supplement so initialization is reproducible. Historical failed
launches, exploratory branches and monitoring jobs are omitted.

The 50 original and 50 randomized games per primary policy are evaluations of existing
checkpoints. The study uses one training lineage and retrospective checkpoint selection.
Neither the repository nor its tests authorize or automatically launch additional paid computation.

This private repository is under preparation. Checkpoints, demonstrations and native assets
will need versioned downloads and hash verification before a standalone release.
