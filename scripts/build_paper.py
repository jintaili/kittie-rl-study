"""Regenerate analysis, figures and pages using only included data."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
for script in ('analysis.py', 'figures.py', 'timing_figure.py', 'paper.py', 'guide.py'):
    result = subprocess.run([sys.executable, str(ROOT / 'paper/code' / script)],
                            cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(result.returncode)
    print(f'Built {script}')
