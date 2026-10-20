"""Build the separate five-item matte 2D experiment without replacing the main set."""
from pathlib import Path
import json, html, hashlib, zipfile
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
MAIN=ROOT/'assets/items/revision-simple'
OUT=ROOT/'assets/items/flat-2d-attempt'
IDS=[17,20,23,27,29]


def sprite(path,color):
    im=Image.open(path).convert('RGBA')
    assert im.getchannel('A').getextrema()[0]==0
    box=im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
    im=im.crop(box)
    scale=48/max(im.size)
    small=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.BOX)
    alpha=small.getchannel('A').point(lambda a:255 if a>=128 else 0)
    rgb=small.convert('RGB').quantize(colors=16,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGBA')
    rgb.putalpha(alpha)
    rgb=rgb.resize((rgb.width*4,rgb.height*4),Image.Resampling.NEAREST)
    canvas=Image.new('RGBA',(256,256));canvas.paste(rgb,((256-rgb.width)//2,(256-rgb.height)//2))
    a=np.array(canvas);solid=a[:,:,3]>=128
    distance=ndi.distance_transform_edt(~solid)
    band=(distance>0)&(distance<=3)&~ndi.binary_fill_holes(solid)
    color=tuple(int(color[k:k+2],16) for k in (1,3,5))
    a[band,:3]=color;a[band,3]=255
    a[a[:,:,3]==0,:3]=0
    return Image.fromarray(a)


def main():
    entries=json.loads((MAIN/'catalog.json').read_text(encoding='utf-8'))
    old_hashes=json.loads((OUT/'baseline-main.json').read_text(encoding='utf-8'))
    for e in entries:
        digest=hashlib.sha256((MAIN/e['file']).read_bytes()).hexdigest()
        if e['id'] not in (1,2):
            assert digest==old_hashes[str(e['id'])],e['id']
    completed=[]
    for item_id in IDS:
        raw=OUT/'raw'/f'{item_id:02d}.png'
        if not raw.exists():continue
        e=entries[item_id-1].copy()
        image=sprite(raw,e['outline_hex'])
        target=OUT/'icons_256'/f'{item_id:02d}.png';image.save(target)
        assert image.size==(256,256) and image.mode=='RGBA'
        assert image.getchannel('A').getextrema()==(0,255)
        box=image.getchannel('A').getbbox()
        assert min(box)>0 and max(box)<256,item_id
        assert len(image.convert('RGB').getcolors(65536))<=18,item_id
        assert (OUT/'prompts'/f'{item_id:02d}.txt').is_file()
        assert (OUT/'raw'/f'{item_id:02d}.json').is_file()
        assert hashlib.sha256((OUT/'before'/f'{item_id:02d}.png').read_bytes()).hexdigest()==old_hashes[str(item_id)]
        e['file']=f'icons_256/{item_id:02d}.png'
        e['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
        e['experiment']='matte_2d_no_specular'
        completed.append(e)
    assert len(completed)==5,'Need all five generated assets'
    (OUT/'catalog.json').write_text(json.dumps(completed,ensure_ascii=False,indent=2),encoding='utf-8')
    font=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',30)
    small_font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',23)
    board=Image.new('RGB',(1600,1600),'black');draw=ImageDraw.Draw(board)
    for x,label in [(200,'СЕЙЧАС'),(650,'ПРОБА 2D'),(1110,'64 px'),(1320,'32 px')]:
        draw.text((x,56),label,font=font,fill='white')
    for n,e in enumerate(completed):
        y=160+n*280
        draw.text((60,y+100),str(e['id']),font=font,fill='white')
        before=Image.open(OUT/'before'/f'{e["id"]:02d}.png').convert('RGBA')
        after=Image.open(OUT/e['file']).convert('RGBA')
        for x,im in [(170,before),(620,after)]:
            board.paste(im,(x,y),im)
            draw.rectangle((x,y,x+255,y+255),outline='#555',width=1)
        for x,size in [(1120,64),(1330,32)]:
            im=after.resize((size,size),Image.Resampling.NEAREST)
            board.paste(im,(x,y+(256-size)//2),im)
        draw.line((50,y+270,1540,y+270),fill='#222')
    board.save(OUT/'flat-comparison.png')
    grid=Image.new('RGB',(2560,2560),'black');d=ImageDraw.Draw(grid)
    number_font=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',25)
    for e in entries:
        path=OUT/'icons_256'/f'{e["id"]:02d}.png' if e['id'] in IDS else MAIN/e['file']
        im=Image.open(path).convert('RGBA');n=e['id']-1;x=n%10*256;y=128+n//10*256
        grid.paste(im,(x,y),im);d.rectangle((x+3,y+3,x+252,y+252),outline='#666',width=2)
        d.text((x+10,y+9),str(e['id']),font=number_font,fill='white',stroke_width=2,stroke_fill='black')
    grid.save(OUT/'context-grid-85.png')
    cards=''
    for e in completed:
        item_id=e['id']
        cards+=f'<article><h2>#{item_id} · {html.escape(e["new_name_en"])}</h2><div class="pair"><figure><img src="before/{item_id:02d}.png"><figcaption>Текущая иконка</figcaption></figure><figure><img src="{e["file"]}?v={e["sha256"][:10]}"><figcaption>Отдельная 2D-проба</figcaption></figure></div><div class="sizes"><img src="{e["file"]}" width="64" height="64"><img src="{e["file"]}" width="32" height="32"></div></article>'
    page='<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Отдельная 2D-проба: 5 предметов</title><style>body{background:#111;color:#ddd;font:16px system-ui;margin:24px}a{color:#8cf}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:20px}article{border:1px solid #555;background:#000;padding:12px}h2{font-size:18px}.pair{display:flex;gap:12px}figure{margin:0;text-align:center}.pair img{width:192px;height:192px}img{object-fit:contain;image-rendering:pixelated}.sizes{display:flex;gap:24px;align-items:center;padding:20px}</style><h1>Отдельная 2D-проба</h1><p>Пять предметов: 17, 20, 23, 27, 29. Меньше объёмного освещения, без глянцевых бликов. Основной набор сохраняет свои иконки.</p><p><a href="flat-comparison.png">Сравнение одним листом</a> · <a href="context-grid-85.png">Пять проб в общей сетке 85</a> · <a href="style-references-clean.png">Референсы стиля</a></p><div class="grid">'+cards+'</div>'
    (OUT/'preview.html').write_text(page,encoding='utf-8')
    report={'trial_ids':IDS,'count':5,'main_replacements':[],'main_clarity_fix_ids':[1,2],'other_main_83_byte_identical':True,'rgba_size':[256,256],'palette_body_max':16,'rarity_edge_width':3,'transparent_margins':True,'prompt_and_receipt_count':5,'method':'builtin-imagegen edits; coded normalization, one colored edge and layout'}
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    archive=ROOT/'output/items-flat-2d-attempt.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path in OUT.rglob('*'):
            if path.is_file() and 'raw' not in path.relative_to(OUT).parts:z.write(path,path.relative_to(OUT))
    print(json.dumps(report,ensure_ascii=True))


if __name__=='__main__':main()
