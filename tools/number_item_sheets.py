"""Add consistent item IDs to four existing sheets, without regenerating art."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = [ROOT/'assets/items/style-passes/passes-01-04-combined.png', ROOT/'assets/items/style-passes/pass-07.png', ROOT/'assets/items/pixelated/items-01.png', ROOT/'assets/items/pixelated/items-02.png']
OUT = ROOT/'assets/items/numbered'

def line_bands(values):
    labels,_ = ndi.label(values)
    return [(s[0].start,s[0].stop) for s in ndi.find_objects(labels)]

def number_sheet(path, index):
    original = Image.open(path).convert('RGB')
    pixels = np.asarray(original).astype(np.int16)
    neutral = (pixels.max(2)-pixels.min(2)<8)&(pixels.mean(2)>50)&(pixels.mean(2)<200)
    xs = line_bands(neutral.sum(0)>original.height*.45)
    ys = line_bands(neutral.sum(1)>original.width*.35)
    assert len(xs)==20 and len(ys)==18, (path,len(xs),len(ys))
    overlay = Image.new('RGBA',original.size)
    draw = ImageDraw.Draw(overlay)
    labels = []
    for item_id in range(1,86):
        column,row = (item_id-1)%10,(item_id-1)//10
        left,right = xs[column*2][1],xs[column*2+1][0]
        top,bottom = ys[row*2][1],ys[row*2+1][0]
        size = round(min(right-left,bottom-top)*.12)
        font = ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',size)
        inset = max(4,round((right-left)*.025))
        position = (left+inset,top+inset)
        stroke = max(1,round(size/14))
        draw.text(position,str(item_id),font=font,anchor='lt',fill='white',stroke_width=stroke,stroke_fill='black')
        box = draw.textbbox(position,str(item_id),font=font,anchor='lt',stroke_width=stroke)
        assert left<=box[0] and top<=box[1] and box[2]<right and box[3]<bottom
        labels.append({'id':item_id,'bounds':box})
    result = Image.alpha_composite(original.convert('RGBA'),overlay).convert('RGB')
    changed = np.any(np.asarray(result)!=np.asarray(original),axis=2)
    assert not np.any(changed & (np.asarray(overlay.getchannel('A'))==0))
    assert changed.mean()<.04
    output = OUT/f'numbered-{index:02d}.png'
    result.save(output)
    return {'image':index,'file':output.name,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':original.size,'count':len(labels),'labels':labels}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('sources',nargs='*',type=Path)
    args = parser.parse_args()
    sources = args.sources or DEFAULTS
    assert len(sources)==4
    OUT.mkdir(parents=True,exist_ok=True)
    records = [number_sheet(path,i) for i,path in enumerate(sources,1)]
    (OUT/'numbering.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    cards=''.join(f'<section><h2>{r["image"]}</h2><a href="{r["file"]}"><img src="{r["file"]}" alt="Лист {r["image"]}, номера 1–85"></a></section>' for r in records)
    (OUT/'preview.html').write_text('<!doctype html><meta charset="utf-8"><title>Предметы — нумерация</title><style>body{background:#111;color:#eee;font:16px system-ui;margin:24px}section{margin-bottom:32px}img{max-width:100%;height:auto;display:block}h2{font-size:18px}</style>'+cards,encoding='utf-8')
    print('Saved 4 sheets, 85 IDs each; all pixel changes confined to number overlays.')

if __name__=='__main__':
    main()
