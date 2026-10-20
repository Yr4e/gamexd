"""Apply the user's per-ID revisions, preserve requested older artwork."""
from pathlib import Path
import csv, hashlib, json, shutil, html
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from scipy import ndimage as ndi

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'assets/items/individual-redesign'
OUT=ROOT/'assets/items/revision-simple'

def clear_empty_rgb(image):
    a=np.array(image.convert('RGBA'))
    a[a[:,:,3]==0,:3]=0
    return Image.fromarray(a)

def old_cutout(path):
    image=Image.open(path).convert('RGB')
    a=np.asarray(image).astype(float)
    peak=a.max(2)
    support=peak>15
    labels,count=ndi.label(support)
    sizes=np.bincount(labels.ravel())
    valid=sizes>=3;valid[0]=False
    support=valid[labels]
    solid=ndi.binary_fill_holes(support)
    # Retain the opaque physical image, remove only the black sheet matte.
    opacity=np.where(solid,1.,np.clip(peak/255,0,1))
    opacity[~support & ~solid]=0
    rgb=np.clip(a/np.maximum(opacity[:,:,None],1/255),0,255)
    result=np.dstack((rgb,opacity*255)).round().astype('uint8')
    result[result[:,:,3]==0,:3]=0
    return Image.fromarray(result)

def normalize(image,extent,logical=None):
    image=image.convert('RGBA')
    mask=image.getchannel('A').point(lambda a:255 if a>8 else 0)
    box=mask.getbbox()
    if not box:raise ValueError('Empty sprite')
    image=image.crop(box)
    if logical:
        scale=logical/max(image.size)
        sampling=Image.Resampling.NEAREST if logical>32 else Image.Resampling.BOX
        image=image.resize((max(1,round(image.width*scale)),max(1,round(image.height*scale))),sampling)
        alpha=image.getchannel('A')
        rgb=ImageEnhance.Color(image.convert('RGB')).enhance(.82)
        rgb=rgb.quantize(colors=32 if logical>32 else 16,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGB')
        image=rgb.convert('RGBA');image.putalpha(alpha)
    scale=extent/max(image.size)
    image=image.resize((max(1,round(image.width*scale)),max(1,round(image.height*scale))),Image.Resampling.NEAREST)
    canvas=Image.new('RGBA',(256,256))
    canvas.paste(image,((256-image.width)//2,(256-image.height)//2))
    return clear_empty_rgb(canvas)

def outline(image,color):
    solid=np.asarray(image.getchannel('A'))>=128
    distance=ndi.distance_transform_edt(~solid)
    band=(distance>0)&(distance<=3)
    rgb=tuple(int(color[k:k+2],16) for k in (1,3,5))
    layer=Image.new('RGBA',(256,256),rgb+(0,))
    layer.putalpha(Image.fromarray((band*255).astype('uint8')))
    glow=Image.new('RGBA',(256,256),rgb+(0,))
    glow.putalpha(Image.fromarray((ndi.gaussian_filter(band.astype(float),1.2)*50).astype('uint8')))
    return clear_empty_rgb(Image.alpha_composite(Image.alpha_composite(glow,layer),image))

def pixelate_existing(image,color,logical=40):
    # Area sampling retains thin strokes; nearest enlargement keeps crisp blocks.
    small=image.convert('RGBA').resize((logical,logical),Image.Resampling.BOX)
    alpha=small.getchannel('A').point(lambda a:255 if a>=128 else 0)
    rgb=small.convert('RGB').quantize(colors=24,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGB')
    small=rgb.convert('RGBA');small.putalpha(alpha)
    return outline(clear_empty_rgb(small.resize((256,256),Image.Resampling.NEAREST)),color)

def main():
    plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
    (OUT/'icons_256').mkdir(exist_ok=True)
    grid=Image.new('RGB',(2560,2560),'black')
    draw=ImageDraw.Draw(grid);font=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',25)
    done=[]
    for e in plan:
        target=OUT/e['file']
        e['status']='pending'
        extent=198 if e['id'] in [9,11,34] else e['target_extent']
        if e['mode'] in ['generate','edit']:
            raw=OUT/'raw'/f'{e["id"]:02d}.png'
            if not raw.exists():continue
            image=Image.open(raw).convert('RGBA')
            assert image.getchannel('A').getextrema()[0]==0
            image=outline(normalize(image,extent,e['logical_size']),e['outline_hex'])
            image.save(target)
        elif e['mode']=='restore':
            image=normalize(old_cutout(OLD/e['crop_file']),192)
            image.save(target)
        elif e['mode']=='scale':
            image=normalize(Image.open(OLD/e['icon_file']),extent)
            image.save(target)
        else:
            shutil.copyfile(OLD/e['icon_file'],target)
            image=Image.open(target).convert('RGBA')
        if e.get('pixelate_existing'):
            image=pixelate_existing(image,e['outline_hex'],e['pixel_canvas_size'])
            image.save(target)
        e['status']='complete'
        e['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
        done.append(e['id'])
        n=e['id']-1;x,y=n%10*256,128+n//10*256
        grid.paste(image,(x,y),image)
        draw.rectangle((x+3,y+3,x+252,y+252),outline='#666',width=2)
        draw.text((x+10,y+9),str(e['id']),font=font,fill='white',stroke_width=2,stroke_fill='black')
    grid.save(OUT/'items-simple-grid.png')
    (OUT/'catalog.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    fields=['id','original_name','new_name_en','new_name_ru','effect_summary_ru','page_url','outline_hex','outline_color_name','mode','pixelate_existing','associative','status','file']
    with (OUT/'catalog.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(plan)
    cards=''.join(f'<article><b>{e["id"]}</b><img src="{e["file"]}?v={e["sha256"][:10]}"><p>{html.escape(e["new_name_en"])}<br>{html.escape(e["new_name_ru"])}</p></article>' for e in plan if e['status']=='complete')
    style='<style>body{margin:24px;background:#111;color:#ddd;font:14px system-ui}a{color:#8cf}.grid{display:grid;grid-template-columns:repeat(auto-fill,200px);gap:12px}article{position:relative;background:#000;border:1px solid #555}b{position:absolute;left:8px;top:6px}img{display:block;width:200px;height:200px;object-fit:contain;image-rendering:pixelated}p{text-align:center;margin:8px}.pair{display:flex}figure{margin:0;text-align:center}figcaption{color:#999;font-size:12px}</style>'
    nav='<p><a href="items-simple-grid.png">Общий лист</a> · <a href="comparison.html">Сравнение</a> · <a href="catalog.csv">Таблица</a></p>'
    (OUT/'preview.html').write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Предметы — правки и упрощение</title>'+style+nav+f'<p>{len(done)} / 85</p><div class="grid">'+cards+'</div>',encoding='utf-8')
    pairs=''.join(f'<article><p>#{e["id"]} · {html.escape(e["new_name_ru"])}</p><div class="pair"><figure><img src="../individual-redesign/{e["crop_file"]}"><figcaption>Картинка 1</figcaption></figure><figure><img src="../individual-redesign/{e["icon_file"]}"><figcaption>Предыдущая версия</figcaption></figure><figure><img src="{e["file"]}?v={e["sha256"][:10]}"><figcaption>Правка</figcaption></figure></div><p>{html.escape(e["effect_summary_ru"])}</p></article>' for e in plan if e['status']=='complete')
    (OUT/'comparison.html').write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Предметы — сравнение правок</title>'+style+'<style>.grid{grid-template-columns:repeat(auto-fill,420px)}.pair img{width:140px;height:140px}</style>'+nav+'<div class="grid">'+pairs+'</div>',encoding='utf-8')
    print(f'Completed {len(done)}/85. Missing: {[e["id"] for e in plan if e["status"]!="complete"]}')

if __name__=='__main__':main()
