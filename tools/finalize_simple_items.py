"""Validate the complete revised set and create a portable review archive."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/items/revision-simple'
OLD = ROOT / 'assets/items/individual-redesign'


def main():
    entries = json.loads((OUT / 'catalog.json').read_text(encoding='utf-8'))
    previous = {e['id']: e for e in json.loads((OLD / 'catalog.json').read_text(encoding='utf-8'))}
    assert [e['id'] for e in entries] == list(range(1, 86))
    hashes = []
    generated = []
    for e in entries:
        assert e['status'] == 'complete', e['id']
        path = OUT / e['file']
        with Image.open(path) as im:
            assert im.mode == 'RGBA' and im.size == (256, 256), e['id']
            assert im.getchannel('A').getextrema() == (0, 255), e['id']
            bbox = im.getchannel('A').getbbox()
            assert bbox and min(bbox) > 0 and max(bbox) < 256, e['id']
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == e['sha256'], e['id']
        hashes.append(digest)
        for field in ('original_name', 'effect_summary_ru', 'outline_hex', 'page_url'):
            assert e[field] == previous[e['id']][field], (e['id'], field)
        if e['mode'] == 'keep':
            assert path.read_bytes() == (OLD / e['icon_file']).read_bytes(), e['id']
        if e['mode'] in ('generate', 'edit'):
            generated.append(e['id'])
            for suffix in ('.png', '.json'):
                assert (OUT / 'raw' / f'{e["id"]:02d}{suffix}').is_file(), e['id']
            assert (OUT / 'prompts' / f'{e["id"]:02d}.txt').is_file(), e['id']
    assert len(set(hashes)) == 85
    assert len(generated) == 47
    assert len(list((OUT / 'icons_256').glob('*.png'))) == 85
    associative = [e['id'] for e in entries if e['associative']]
    assert len(associative) == 22
    report = {
        'total': 85, 'unique_pngs': 85, 'rgba_size': [256, 256],
        'transparent_margins': True, 'original_effects_and_rarity_preserved': True,
        'modes': dict(Counter(e['mode'] for e in entries)),
        'generated_ids': generated, 'associative_ids': associative,
        'associative_percent': round(len(associative) / 85 * 100, 2),
        'unchanged_images_byte_identical': True,
        'grid_size': list(Image.open(OUT / 'items-simple-grid.png').size),
    }
    (OUT / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    archive = ROOT / 'output/items-simple-revised.zip'
    archive.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted(OUT.rglob('*')):
            if path.is_file() and 'raw' not in path.relative_to(OUT).parts:
                z.write(path, 'revision-simple/' + path.relative_to(OUT).as_posix())
        for relative in sorted({e[key] for e in entries for key in ('crop_file', 'icon_file')}):
            z.write(OLD / relative, 'individual-redesign/' + relative)
        z.writestr('OPEN.txt', 'Open revision-simple/preview.html for the gallery, or comparison.html for all three versions.\nIndividual transparent PNGs are in revision-simple/icons_256/.\n')
    print(json.dumps(report, ensure_ascii=False))
    print(f'Archive: {archive} ({archive.stat().st_size / 1048576:.2f} MiB)')


if __name__ == '__main__':
    main()
