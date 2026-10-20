"""Extract existing artwork without regenerating it; retain coloured edge emission."""
from pathlib import Path
import csv
import hashlib
import json
import shutil

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r'C:\Users\yr4e\AppData\Local\Temp\codex-clipboard-e227ff83-0ccc-4269-b7f6-84007d14d8f0.png')
OUT = ROOT / 'assets' / 'weapon-icons'
XS = [(19, 206), (226, 414), (432, 619), (637, 823), (843, 1030), (1049, 1235)]
YS = [(94, 281), (312, 501), (532, 724), (754, 951), (982, 1169)]
EN = ['Iron Fang','Ember Scepter','Stormspike','Ashstep','Stone Satellites','Gravebone','Briarstring','Brass Six','Wardstone','Golden Crescent','Halo Engine','Twin Cleaver','Rift Lash','Longwatch','Red Comet','Scrapstorm','Redeye Charge','Ghost Needle','Froststep','Whirlcore','Verdict','Sanguine Heart','Voidwell','Viper Flask','Crimson Arc','Drakefire','Fatecube','Dawnhammer','Voidgrasp','Moonreaper']

def extract(rgb, index):
    values = np.asarray(rgb).astype(np.float32)
    peak = values.max(axis=2)
    # Ignore near-black export noise, while keeping the coloured glow.
    support = peak > 16
    labels, count = ndi.label(support)
    sizes = np.bincount(labels.ravel())
    keep = sizes >= 3
    keep[0] = False
    # Residual frame compression/shadow pixels at the crop edge are not art.
    for label in range(1, count+1):
        yy, xx = np.where(labels == label)
        if len(xx) and (xx.min()==0 or yy.min()==0 or xx.max()==labels.shape[1]-1 or yy.max()==labels.shape[0]-1):
            width, height = xx.max()-xx.min()+1, yy.max()-yy.min()+1
            if max(width,height) > 8*min(width,height):
                keep[label] = False
    support = keep[labels]
    # The physical silhouette stays opaque, including dark internal details.
    solid = support & (peak >= 95)
    solid = ndi.binary_closing(solid, iterations=1)
    if index not in {7, 11, 23}:
        solid = ndi.binary_fill_holes(solid)
    # Recover soft alpha from the black matte for dim edge light. Unpremultiply
    # RGB so that the glow doesn't carry a black halo onto lighter backgrounds.
    glow_items = {2,3,4,11,13,15,18,19,21,22,23,24,25,26,28,29,30}
    if index not in glow_items:
        solid = ndi.binary_fill_holes(support) if index != 7 else support
    # Opaque interior guides for the dark physical bodies. These do not paint
    # pixels: they only stop dark metal/leather from being mistaken for matte.
    guides = {
        4: [(30,150),(48,132),(59,107),(56,87),(62,57),(89,45),(113,55),(118,99),(128,131),(119,162),(86,174),(42,168)],
        26: [(20,38),(62,58),(49,40),(92,70),(100,58),(127,78),(140,77),(152,90),(149,107),(120,110),(94,98),(77,128),(61,159),(42,180),(45,141),(62,111),(27,152),(34,115),(59,89)],
        29: [(65,72),(121,45),(157,66),(160,104),(130,113),(96,142),(42,160),(30,130)],
    }
    if index in guides or index == 21:
        guide = Image.new('1', rgb.size)
        draw = ImageDraw.Draw(guide)
        if index == 21:
            draw.ellipse((86,46,149,110), fill=1)
        else:
            draw.polygon(guides[index], fill=1)
        solid |= np.asarray(guide) & support
    alpha = np.where(solid, 1., np.minimum(1., peak / 255.))
    alpha[~support & ~solid] = 0
    recovered = np.minimum(255, values / np.maximum(alpha[..., None], 1/255))
    rgba = np.dstack([recovered, alpha * 255]).round().astype(np.uint8)
    rgba[rgba[..., 3] == 0, :3] = 0
    item = Image.fromarray(rgba)
    box = item.getbbox()
    if box is None:
        raise ValueError(f'Empty icon {index}')
    # Tighten only empty margins, then place at native size: no artwork crop
    # and no interpolation or redraw of the original pixel geometry.
    item = item.crop(box)
    canvas = Image.new('RGBA', (256, 256))
    canvas.paste(item, ((256-item.width)//2, (256-item.height)//2))
    return canvas

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    icons = OUT / 'icons_256'
    icons.mkdir(exist_ok=True)
    source = OUT / 'source-sheet.png'
    if not source.exists():
        shutil.copyfile(SOURCE, source)
    sheet = Image.open(source).convert('RGB')
    names_source = ROOT/'output/weapons-v3/names.csv'
    if names_source.exists():
        catalog = list(csv.DictReader(names_source.open(encoding='utf-8-sig')))
    else:
        previous = list(csv.DictReader((OUT/'catalog.csv').open(encoding='utf-8-sig')))
        catalog = [{'Megabonk':row['megabonk'], 'Русский':row['russian']} for row in previous]
    entries = []
    preview = Image.new('RGB', (6*256, 5*256))
    for index, row in enumerate(catalog, 1):
        col, line = (index-1) % 6, (index-1) // 6
        left, right = XS[col]
        top, bottom = YS[line]
        icon = extract(sheet.crop((left, top, right, bottom)), index)
        slug = EN[index-1].lower().replace(' ', '-')
        name = f'{index:02d}_{slug}.png'
        replacement = OUT/'revisions'/name
        if replacement.exists():
            revised = Image.open(replacement).convert('RGBA')
            # Generated sprites can have invisible 1/255-alpha specks far
            # outside the art. Exclude those from sizing, retain glow padding.
            visible = revised.getchannel('A').point(lambda a: 255 if a > 2 else 0)
            x0,y0,x1,y1 = visible.getbbox()
            revised = revised.crop((max(0,x0-16),max(0,y0-16),min(revised.width,x1+16),min(revised.height,y1+16)))
            scale = min(208/revised.width, 208/revised.height)
            revised = revised.resize((max(1,round(revised.width*scale)),max(1,round(revised.height*scale))), Image.Resampling.NEAREST)
            icon = Image.new('RGBA',(256,256))
            icon.paste(revised,((256-revised.width)//2,(256-revised.height)//2))
        icon.save(icons/name)
        assert icon.size == (256,256)
        alpha = np.array(icon.getchannel('A'))
        assert alpha.min() == 0 and alpha.max() == 255
        assert not alpha[:12].any() and not alpha[-12:].any()
        assert not alpha[:,:12].any() and not alpha[:,-12:].any()
        tile = Image.new('RGB', (256,256))
        draw = ImageDraw.Draw(tile)
        for y in range(0,256,16):
            for x in range(0,256,16):
                shade = 225 if (x//16+y//16)%2 else 185
                draw.rectangle((x,y,x+15,y+15), fill=(shade,shade,shade))
        tile.paste(icon, mask=icon.getchannel('A'))
        preview.paste(tile, (col*256,line*256))
        entries.append({'id':index,'megabonk':row['Megabonk'],'english':EN[index-1], 'russian':row['Русский'],'file':f'icons_256/{name}'})
    preview.save(OUT/'preview-checker.png')
    (OUT/'catalog.json').write_text(json.dumps(entries, ensure_ascii=False, indent=2),encoding='utf-8')
    with (OUT/'catalog.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=entries[0].keys())
        writer.writeheader()
        writer.writerows(entries)
    cards=''.join(f'<div><img src="{e["file"]}?v={hashlib.sha256((OUT/e["file"]).read_bytes()).hexdigest()[:10]}" alt="{e["english"]}"></div>' for e in entries)
    (OUT/'preview.html').write_text('<!doctype html><meta charset="utf-8"><title>Weapon icons</title><style>body{margin:24px;background:#222}.grid{display:grid;grid-template-columns:repeat(6,128px);gap:12px}.grid>div{background:repeating-conic-gradient(#ddd 0% 25%,#aaa 0% 50%) 0/16px 16px}img{display:block;width:128px;height:128px;image-rendering:pixelated}body.light .grid>div{background:#eee}body.dark .grid>div{background:#181818}button{margin:0 8px 16px 0;padding:8px}</style><button onclick="document.body.className=\'\'">Шахматная подложка</button><button onclick="document.body.className=\'light\'">Светлая</button><button onclick="document.body.className=\'dark\'">Тёмная</button><div class="grid">'+cards+'</div>',encoding='utf-8')
    print(f'Extracted and checked {len(entries)} RGBA icons to {icons}')
    print('Soft-alpha pixels:', sum(np.count_nonzero((np.array(Image.open(icons/Path(e['file']).name).getchannel('A')) > 0) & (np.array(Image.open(icons/Path(e['file']).name).getchannel('A')) < 255)) for e in entries))

if __name__ == '__main__':
    main()
