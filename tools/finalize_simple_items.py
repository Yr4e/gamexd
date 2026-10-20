"""Validate the complete revised set and create a portable review archive."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import zipfile
from PIL import Image
import numpy as np
from scipy import ndimage as ndi

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
        if e['mode'] == 'keep' and not e.get('pixelate_existing') and not e.get('balanced_fix') and not e.get('restore_before_pixelation') and not e.get('edge_cleanup'):
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
    baseline_path = OUT / 'before-pixelation/baseline.json'
    pixelated = [e['id'] for e in entries if e.get('pixelate_existing')]
    if pixelated:
        baseline = json.loads(baseline_path.read_text(encoding='utf-8'))
        assert len(pixelated) == 38
        for e in entries:
            if e.get('pixelate_existing'):
                before = Image.open(OUT / 'before-pixelation' / f'{e["id"]:02d}.png').convert('RGBA')
                actual = Image.open(OUT / e['file']).convert('RGBA')
                a_box=actual.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
                b_box=before.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
                assert max(abs(a-b) for a,b in zip(a_box,b_box)) <= 10, e['id']
                color=tuple(int(e['outline_hex'][k:k+2],16) for k in (1,3,5))+(255,)
                assert any(c == color for _, c in actual.getcolors(65536)), e['id']
                assert e['sha256'] != baseline[str(e['id'])], e['id']
            else:
                assert e['sha256'] == baseline[str(e['id'])], e['id']
    balanced = [e['id'] for e in entries if e.get('balanced_fix')]
    rolled_back = [e['id'] for e in entries if e.get('restore_before_pixelation')]
    untouched = []
    bounds = {}
    edge_ids = [e['id'] for e in entries if e.get('edge_cleanup')]
    natural_edges = bool(edge_ids) and all(e.get('edge_style')=='natural_no_dark' for e in entries if e.get('edge_cleanup'))
    if balanced and not edge_ids:
        expected_regular = {5,7,8,9,11,12,13,15,16,17,20,23,24,26,27,29,34,38,39,43,45,47,48,49,50,57,62,63,79,80}
        assert set(balanced) == expected_regular | {31,42,51,73}
        assert set(rolled_back) == {2,6,58,60,68,70,71,76}
        latest_baseline = json.loads((OUT / 'before-balanced-fix/baseline.json').read_text(encoding='utf-8'))
        original_baseline = json.loads(baseline_path.read_text(encoding='utf-8'))
        for e in entries:
            if e['id'] in balanced:
                im = Image.open(OUT / e['file']).convert('RGBA')
                box = im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
                longest = max(box[2]-box[0], box[3]-box[1])
                assert 188 <= longest <= 198, (e['id'],longest)
                bounds[e['id']] = [box[2]-box[0],box[3]-box[1]]
                color = tuple(int(e['outline_hex'][k:k+2],16) for k in (1,3,5))+(255,)
                assert any(c == color for _,c in im.getcolors(65536)), e['id']
                assert e['sha256'] != latest_baseline[str(e['id'])], e['id']
            elif e['id'] in rolled_back:
                assert e['sha256'] == original_baseline[str(e['id'])], e['id']
            else:
                assert e['sha256'] == latest_baseline[str(e['id'])], e['id']
                untouched.append(e['id'])
        assert len(untouched) == 43
        assert (OUT / 'raw/73-lightning.png').is_file()
        assert (OUT / 'prompts/73-lightning.txt').is_file()
    if edge_ids and not natural_edges:
        assert set(edge_ids) == {1,2,5,6,7,8,9,12,13,24,27,29,38,47,50,51,63,76,79,80,85}
        assert {e['id'] for e in entries if e.get('slight_pixel_body')} == {1,2,6}
        baseline = json.loads((OUT / 'before-outline-fix/baseline.json').read_text(encoding='utf-8'))
        for e in entries:
            if e['id'] not in edge_ids:
                assert e['sha256'] == baseline[str(e['id'])], e['id']
                untouched.append(e['id'])
                continue
            assert e['sha256'] != baseline[str(e['id'])], e['id']
            image = Image.open(OUT / e['file']).convert('RGBA')
            a = np.asarray(image)
            body = np.asarray(Image.open(OUT / 'edge-masks' / f'{e["id"]:02d}.png')) > 0
            distance = ndi.distance_transform_edt(~body)
            exterior = ~ndi.binary_fill_holes(body)
            dark_band = exterior & (distance>0) & (distance<=1)
            rare_band = exterior & (distance>1) & (distance<=3)
            rgb = tuple(int(e['outline_hex'][k:k+2],16) for k in (1,3,5))
            assert np.all(a[dark_band] == np.array((16,17,24,255))), e['id']
            assert np.all(a[rare_band] == np.array(rgb+(255,))), e['id']
            assert np.array_equal(a[:,:,3]>0, body|dark_band|rare_band), e['id']
            before = Image.open(OUT / 'before-outline-fix' / f'{e["id"]:02d}.png')
            old_box = before.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
            box = image.getchannel('A').getbbox()
            assert max(abs(x-y) for x,y in zip(old_box,box)) <= 7, (e['id'],old_box,box)
        assert len(untouched) == 64
    if natural_edges:
        assert set(edge_ids) == {1,2,5,6,7,8,9,12,13,24,27,29,38,47,50,51,63,76,79,80,85}
        baseline = json.loads((OUT / 'before-no-dark-fix/baseline.json').read_text(encoding='utf-8'))
        for e in entries:
            if e['id'] not in edge_ids:
                assert e['sha256'] == baseline[str(e['id'])], e['id']
                untouched.append(e['id'])
                continue
            assert e['sha256'] != baseline[str(e['id'])], e['id']
            a=np.asarray(Image.open(OUT / e['file']).convert('RGBA'))
            assert not np.any(np.all(a==[16,17,24,255],axis=2)), e['id']
        assert len(untouched)==64
        assert (OUT / 'icons_256/76.png').read_bytes() == (OUT / 'before-outline-fix/76.png').read_bytes()
    clarity_ids = [e['id'] for e in entries if e.get('clarity_restore')]
    clarity_untouched = []
    if clarity_ids:
        assert set(clarity_ids)=={1,2}
        baseline=json.loads((OUT/'before-clarity-fix/baseline.json').read_text(encoding='utf-8'))
        for e in entries:
            if e['id'] in clarity_ids:
                assert (OUT/e['file']).read_bytes()==(OUT/'before-outline-fix'/f'{e["id"]:02d}.png').read_bytes(), e['id']
                assert e['sha256']!=baseline[str(e['id'])], e['id']
            else:
                assert e['sha256']==baseline[str(e['id'])], e['id']
                clarity_untouched.append(e['id'])
        assert len(clarity_untouched)==83
    report = {
        'total': 85, 'unique_pngs': 85, 'rgba_size': [256, 256],
        'transparent_margins': True, 'original_effects_and_rarity_preserved': True,
        'modes': dict(Counter(e['mode'] for e in entries)),
        'generated_ids': generated, 'associative_ids': associative,
        'associative_percent': round(len(associative) / 85 * 100, 2),
        'pixelated_existing_ids': pixelated,
        'other_images_byte_identical_to_previous_revision': len(untouched)==64 if edge_ids else len(untouched)==43 if balanced else bool(pixelated),
        'balanced_fix_ids': balanced,
        'balanced_sprite_bounds': bounds,
        'rolled_back_ids': rolled_back,
        'untouched_ids': untouched,
        'exact_scope_verified': bool(balanced),
        'edge_cleanup_ids': edge_ids,
        'single_separated_outer_rarity_band_verified': bool(edge_ids) and not natural_edges,
        'natural_edges_without_added_dark_separator': natural_edges,
        'latest_clarity_restore_ids': clarity_ids,
        'latest_clarity_untouched_ids': clarity_untouched,
        'grid_size': list(Image.open(OUT / 'items-simple-grid.png').size),
    }
    (OUT / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    archive = ROOT / 'output/items-simple-revised.zip'
    archive.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted(OUT.rglob('*')):
            if path.is_file() and 'raw' not in path.relative_to(OUT).parts:
                z.write(path, 'revision-simple/' + path.relative_to(OUT).as_posix())
        flat_trial=ROOT/'assets/items/flat-2d-attempt'
        if (flat_trial/'preview.html').exists():
            for path in sorted(flat_trial.rglob('*')):
                if path.is_file() and 'raw' not in path.relative_to(flat_trial).parts:
                    z.write(path,'flat-2d-attempt/'+path.relative_to(flat_trial).as_posix())
        for relative in sorted({e[key] for e in entries for key in ('crop_file', 'icon_file')}):
            z.write(OLD / relative, 'individual-redesign/' + relative)
        z.writestr('OPEN.txt', 'Open revision-simple/preview.html for the gallery, or comparison.html for all three versions.\nIndividual transparent PNGs are in revision-simple/icons_256/.\n')
    print(json.dumps(report, ensure_ascii=False))
    print(f'Archive: {archive} ({archive.stat().st_size / 1048576:.2f} MiB)')


if __name__ == '__main__':
    main()
