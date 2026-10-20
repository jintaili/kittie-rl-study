"""Export the generated article into an existing Kittie static-site checkout."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = 'https://jintaili.github.io/kittie-game/'

def export(site: Path, video: Path | None = None) -> dict:
    site = site.resolve()
    if not (site / 'index.html').is_file() or not (site / 'analytics.js').is_file():
        raise ValueError('Expected the existing Kittie docs directory')
    media = json.loads((ROOT / 'provenance/media.json').read_text())
    target_video = site / media['site_path']
    source_video = video or target_video
    if not source_video.is_file():
        raise ValueError('First export needs --video pointing to the selected replay')
    if hashlib.sha256(source_video.read_bytes()).hexdigest() != media['sha256']:
        raise ValueError('Replay does not match the retained selected example')
    target_video.parent.mkdir(parents=True, exist_ok=True)
    if source_video.resolve() != target_video:
        shutil.copyfile(source_video, target_video)
    target = site / 'training'
    target.mkdir(exist_ok=True)
    files = ['LICENSE.txt', 'index.html', 'supplement.html', 'methods.html', 'reproduction.html',
             'performance.png', 'performance.svg', 'latency-distributions.png',
             'latency-distributions.svg', 'study.json']
    for folder in ('data', 'examples', 'images', 'assets', 'reference'):
        files += [str(p.relative_to(ROOT / 'paper')) for p in (ROOT / 'paper' / folder).rglob('*') if p.is_file()]
    files += ['code/' + name for name in ('analysis.py', 'figures.py', 'timing.py',
              'timing_figure.py', 'test_study.py')]
    manifest = {}
    for name in sorted(files):
        source = ROOT / 'paper' / name
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = source.read_bytes()
        if name.endswith('.html'):
            text = data.decode().replace(PUBLIC + 'training/', './').replace(PUBLIC, '../')
            text = text.replace('</head>', '<script defer src="../analytics.js"></script></head>')
            data = text.encode()
        if b'ts.net' in data or b'tailscale' in data.lower():
            raise ValueError(f'Private URL in export: {name}')
        dest.write_bytes(data)
        manifest[name] = {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                          'export_sha256': hashlib.sha256(data).hexdigest()}
    # The article is generated; only this exporter maintains the integration card/nav.
    nav = '<a href="training/">Training</a>'
    for p in site.glob('*.html'):
        text = p.read_text()
        if 'class="site-nav"' in text and nav not in text:
            needle = '<a href="methods.html"'
            text = text.replace(needle, nav + needle, 1)
        if p.name == 'index.html' and 'id="training-experiment"' not in text:
            card = '''<section class="experiment" id="training-experiment"><div><h2><a href="training/">Teaching a small language model to play</a></h2><p>Can demonstrations and reinforcement learning teach a 0.8B model to play Head Goon? I trained Qwen with behavior cloning, then PPO.</p><p><a href="training/">Watch the gameplay and read the study →</a></p></div><div class="table-wrap"><table><caption>Original encounter · 50 games per policy</caption><thead><tr><th>Policy</th><th>Wins</th></tr></thead><tbody><tr><th>Pretrained Qwen</th><td>0/50</td></tr><tr><th>Behavior cloning</th><td>39/50</td></tr><tr><th>PPO15</th><td>47/50</td></tr></tbody></table><p class="fine">A separate study from the earlier API comparison. Randomized scenarios and limitations are reported in the article.</p></div></section>'''
            marker = '<section class="evidence-section"'
            if marker not in text:
                raise ValueError('Overview evidence section changed; inspect card placement')
            text = text.replace(marker, card + marker, 1)
        if p.name == 'index.html':
            text = text.replace('Watch all 190 attempts', 'Watch all 190 API-evaluation attempts')
            text = text.replace('<h2>Methods and data</h2>', '<h2>API comparison methods and data</h2>')
        p.write_text(text)
    output = {'files': manifest, 'media': media, 'destination': 'docs/training/',
              'note': 'Generated from the research repository. Edit its source, then re-export.'}
    (target / 'export-manifest.json').write_text(json.dumps(output, indent=2) + '\n')
    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site-root', type=Path, required=True)
    parser.add_argument('--video', type=Path)
    args = parser.parse_args()
    result = export(args.site_root, args.video)
    print(f"Exported {len(result['files'])} article files and verified the selected replay")
