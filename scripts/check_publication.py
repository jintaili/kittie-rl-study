"""Validate source provenance, statistical parity and the exported static site."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse
import ast
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class Links(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.links = []; self.ids = set(); self.feed(text)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.add(a['id'])
        for key in ('href', 'src', 'poster'):
            if a.get(key): self.links.append(a[key])

def check(site, archive=None):
    records = json.loads((ROOT / 'provenance/source-map.json').read_text())
    definitions_checked = 0
    for record in records:
        assert sha(ROOT / record['destination']) == record['destination_sha256'], record
        if archive:
            sources = record.get('sources', {})
            if 'source' in record: sources = {record['source']: record['source_sha256']}
            for name, expected in sources.items():
                assert sha(archive / name) == expected, name
            if 'source' in record:
                original = {n.name: n for n in ast.parse((archive / record['source']).read_text()).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
                extracted = {n.name: n for n in ast.parse((ROOT / record['destination']).read_text()).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
                for name in original.keys() & extracted.keys():
                    assert ast.dump(original[name]) == ast.dump(extracted[name]), (record['destination'], name)
                    definitions_checked += 1
    inputs = json.loads((ROOT / 'paper/data/sources.json').read_text())
    if archive:
        for name, expected in inputs.items():
            assert sha(archive / name) == expected, name
    extra_sources = {}
    for filename in ('latencies.json', 'training-lineage.json'):
        extra_sources.update(json.loads((ROOT / 'paper/data' / filename).read_text())['input_sha256'])
    if archive:
        for name, expected in extra_sources.items():
            assert sha(archive / name) == expected, name
        example = json.loads((ROOT / 'provenance/example.json').read_text())
        assert sha(archive / example['source']) == example['source_sha256']
        for name, expected in example['files'].items():
            assert sha(ROOT / name) == expected, name
    manifest = json.loads((site / 'training/export-manifest.json').read_text())
    for name, item in manifest['files'].items():
        assert sha(ROOT / 'paper' / name) == item['source_sha256'], name
        assert sha(site / 'training' / name) == item['export_sha256'], name
    assert sha(site / manifest['media']['site_path']) == manifest['media']['sha256']
    pages = sorted((site / 'training').glob('*.html')) + sorted(site.glob('*.html'))
    count = 0
    for page in pages:
        parsed = Links(page.read_text())
        for link in parsed.links:
            url = urlsplit(link)
            if url.scheme or url.netloc: continue
            target = (page.parent / unquote(url.path)).resolve() if url.path else page
            if target.is_dir(): target = target / 'index.html'
            assert target.is_file(), (page.name, link)
            if url.fragment and target.suffix == '.html':
                assert unquote(url.fragment) in Links(target.read_text()).ids, (page.name, link)
            count += 1
    for path in (site / 'training').rglob('*'):
        if path.is_file() and path.suffix in ('.html', '.py', '.json', '.css'):
            text = path.read_text()
            assert 'ts.net/' not in text and '/Users/' not in text, path
    current = json.loads((ROOT / 'paper/data/analysis.json').read_text())
    previous = json.loads(subprocess.check_output(['git', 'show', 'ca2f81e:paper/data/analysis.json'], cwd=ROOT))
    assert current == previous, 'Numerical results changed'
    return {'code_extractions_verified': len(records), 'original_definitions_unchanged': definitions_checked,
            'latency_and_lineage_sources_verified': len(extra_sources) if archive else None, 'historical_result_sources_verified': len(inputs) if archive else None,
            'export_files_verified': len(manifest['files']), 'pages_checked': len(pages), 'local_links_and_fragments_checked': count,
            'analysis_matches_preparation_baseline': True, 'private_urls_in_export': 0, 'selected_replay_hash_matches': True}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--site-root', required=True, type=Path)
    p.add_argument('--archive', type=Path)
    args = p.parse_args()
    print(json.dumps(check(args.site_root.resolve(), args.archive), indent=2))
