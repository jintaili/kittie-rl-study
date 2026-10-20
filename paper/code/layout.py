"""Shared article shell and generated copies of the small reference components."""
from pathlib import Path
import html
import shutil

PAPER = Path(__file__).resolve().parents[1]
REPO = PAPER.parent
SITE = "https://jintaili.github.io/kittie-game/"

def page(title: str, body: str) -> str:
    nav = ''.join(f'<a href="{SITE}{path}">{label}</a>' for path, label in [
        ('index.html', 'Overview'), ('courtyard.html', 'Courtyard'),
        ('head-goon.html', 'Head Goon'), ('training/', 'Training'), ('methods.html', 'Methods')])
    description = "Fine-tuning a 0.8B language model with behavior cloning and PPO for real-time Game Boy gameplay, with results, limitations and reference code."
    route = {'Teaching a small language model to play': '', 'Methods and code': 'methods.html'}.get(title, 'supplement.html')
    metadata = (f'<meta name="description" content="{description}">'
                f'<meta property="og:title" content="{html.escape(title, quote=True)}">'
                f'<meta property="og:description" content="{description}">'
                '<meta property="og:type" content="article">'
                f'<meta property="og:url" content="{SITE}training/{route}">'
                f'<meta property="og:image" content="{SITE}training/images/game-frame.png">'
                '<meta property="og:image:alt" content="Kittie facing Head Goon in the Game Boy game">')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{metadata}<title>{html.escape(title)} · Kittie Has Other Plans</title><link rel="stylesheet" href="assets/site.css"></head><body><main class="article"><header><a href="{SITE}">Kittie Has Other Plans</a><nav class="site-nav" aria-label="Main navigation">{nav}</nav></header>{body}<footer><span>Jintai Li · 2026</span><span><a href="methods.html">Methods and code</a></span></footer></main></body></html>'''

def materialize_reference() -> None:
    """Generated for browsing/export; editable implementations stay under src/."""
    target = PAPER / 'reference'
    target.mkdir(exist_ok=True)
    for source in (REPO / 'src/head_goon_study').glob('*.py'):
        shutil.copyfile(source, target / source.name)
    for name in ('LICENSE', 'LICENSE-CONTENT', 'NOTICE', 'THIRD_PARTY_NOTICES'):
        shutil.copyfile(REPO / name, target / name)
    for name in ('source-map.json', 'example.json', 'media.json'):
        shutil.copyfile(REPO / 'provenance' / name, target / name)
    for source in (REPO / 'configs').glob('*.json'):
        shutil.copyfile(source, target / ('config-' + source.name))
