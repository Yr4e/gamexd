"""Normalize individual generated sprites, then add the recorded rarity edge."""
from pathlib import Path
import csv, hashlib, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/items/individual-redesign'

def finish(path,color):
    raw=Image.open(path).convert('RGBA')
    assert raw.getchannel('A').getextrema()[0]==0, f'No transparency: {path}'
    visible=raw.getchannel('A').point(lambda a:255 if a>6 else 0)
    bounds=visible.getbbox()
    assert bounds, f'Empty: {path}'
    x0,y0,x1,y1=bounds
    raw=raw.crop((max(0,x0-16),max(0,y0-16),min(raw.width,x1+16),min(raw.height,y1+16)))
    scale=174/max(raw.size)
    raw=raw.resize((max(1,round(raw.width*scale)),max(1,round(raw.height*scale))),Image.Resampling.NEAREST)
    art=Image.new('RGBA',(256,256))
    art.paste(raw,((256-raw.width)//2,(256-raw.height)//2))
    alpha=np.asarray(art.getchannel('A'))
    solid=alpha>=128
    distance=ndi.distance_transform_edt(~solid)
    stroke=(distance>0)&(distance<=3)
    rgb=tuple(int(color[i:i+2],16) for i in (1,3,5))
    glow_alpha=(ndi.gaussian_filter(stroke.astype(float),sigma=2.5)*120).clip(0,255).astype(np.uint8)
    glow=Image.new('RGBA',(256,256),rgb+(0,))
    glow.putalpha(Image.fromarray(glow_alpha))
    edge=Image.new('RGBA',(256,256),rgb+(0,))
    edge.putalpha(Image.fromarray((stroke*255).astype(np.uint8)))
    result=Image.alpha_composite(Image.alpha_composite(glow,edge),art)
    rgba=np.array(result)
    rgba[rgba[...,3]==0,:3]=0
    result=Image.fromarray(rgba)
    a=np.asarray(result.getchannel('A'))
    assert not a[:12].any() and not a[-12:].any() and not a[:,:12].any() and not a[:,-12:].any()
    return result

def main():
    plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
    canvas=Image.new('RGB',(2560,2560),'black')
    draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',25)
    completed=[]
    for e in plan:
        raw=OUT/e['raw_file']
        e['status']='pending'
        if raw.exists():
            icon=finish(raw,e['outline_hex'])
            icon.save(OUT/e['icon_file'])
            e['status']='complete'
            e['icon_sha256']=hashlib.sha256((OUT/e['icon_file']).read_bytes()).hexdigest()
            completed.append(e['id'])
            i=e['id']-1
            x,y=(i%10)*256,128+(i//10)*256
            canvas.paste(icon,(x,y),icon)
            draw.rectangle((x+3,y+3,x+252,y+252),outline='#666666',width=2)
            draw.text((x+10,y+9),str(e['id']),font=font,fill='white',stroke_width=2,stroke_fill='black')
    canvas.save(OUT/'items-new-grid.png')
    (OUT/'catalog.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    fields=['id','original_name','new_name_en','new_name_ru','effect_summary_ru','effect_source_en','page_url','outline_color_name','outline_hex','rarity','concept_en','crop_file','raw_file','icon_file','status']
    with (OUT/'catalog.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        writer.writeheader();writer.writerows(plan)
    cards=''.join(f'<article><div class="num">{e["id"]}</div><img src="{e["icon_file"]}?v={e.get("icon_sha256", "pending")[:8]}" alt="{e["new_name_en"]}"><p>{e["new_name_en"]}<br>{e["new_name_ru"]}</p></article>' for e in plan if e['status']=='complete')
    (OUT/'preview.html').write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>85 новых предметов</title><style>body{background:#111;color:#ddd;font:14px system-ui;margin:24px}.grid{display:grid;grid-template-columns:repeat(auto-fill,180px);gap:12px}article{position:relative;border:1px solid #666;background:#000}img{display:block;width:180px;height:180px;image-rendering:pixelated}p{text-align:center;margin:0 4px 12px}.num{position:absolute;left:8px;top:5px}a{color:#8cf}</style><p>'+str(len(completed))+' / 85 индивидуальных иконок · <a href="items-new-grid.png">Общий лист</a></p><div class="grid">'+cards+'</div>',encoding='utf-8')
    print(f'Completed: {len(completed)}/85; IDs: {completed}')
    print('Missing:',[e['id'] for e in plan if e['status']!='complete'])

if __name__=='__main__':main()
