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
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · Kittie Has Other Plans</title><link rel="stylesheet" href="assets/site.css"></head><body><main class="article"><header><a href="{SITE}">Kittie Has Other Plans</a><nav class="site-nav" aria-label="Main navigation">{nav}</nav></header>{body}<footer><span>Jintai Li · 2026</span><span><a href="methods.html">Methods and code</a> · <a href="methods.html#licenses">Licenses</a></span></footer></main></body></html>'''

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
