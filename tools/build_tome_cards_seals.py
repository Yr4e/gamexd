"""Compose two five-candidate sheets, without selecting a tome replacement."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
import hashlib, json
import build_tome_concepts as layout

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/tomes/cards-seals-01'
GROUPS={'cards':'Карты и колоды','seals':'Печати'}


def main():
    specs=json.loads((OUT/'specs.json').read_text(encoding='utf-8'))
    result=[]
    for group,title in GROUPS.items():
        chosen=[s for s in specs if s['group']==group]
        assert len(chosen)==5
        folder=OUT/group
        layout.OUT=folder
        layout.OPTIONS=[(s['id'],s['name'],s['variation']) for s in chosen]
        layout.main()
        with Image.open(folder/'comparison.png') as image:
            board=image.convert('RGB')
            d=ImageDraw.Draw(board)
            d.rectangle((0,0,1599,180),fill='black')
            font=ImageFont.truetype(layout.BOLD,40)
            small=ImageFont.truetype(layout.FONT,24)
            layout.center(d,title+' · 5 вариантов',45,font,'white')
            layout.center(d,'Разные формы и конструкции · крупно, 64 px и 32 px',105,small,'#aaa')
            board.save(folder/'comparison.png')
        page=(folder/'preview.html').read_text(encoding='utf-8')
        page=page.replace('5 основ для новых томов',title+' · 5 вариантов').replace('5 основ для томов',title+' · 5 вариантов')
        (folder/'preview.html').write_text(page,encoding='utf-8')
        catalog=json.loads((folder/'catalog.json').read_text(encoding='utf-8'))
        catalog['group']=group
        for r,s in zip(catalog['candidates'],chosen):
            r['code']=s['code'];r['group']=group
            r['receipt_file']=f'raw/{s["id"]:02d}.json'
            assert (folder/r['receipt_file']).is_file()
        (folder/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
        result+=catalog['candidates']
    sections=[]
    for group,title in GROUPS.items():
        sections.append(f'<section><h2>{title}</h2><p><a href="{group}/preview.html">Отдельный предпросмотр</a> · <a href="{group}/comparison.png">Полный лист</a></p><div class="grid">')
        for s in [s for s in specs if s['group']==group]:
            image=f'{group}/icons_256/{s["id"]:02d}.png'
            sections.append(f'<article><h3>{s["code"]}. {s["name"]}</h3><img src="{image}" width="256" height="256" alt="{s["name"]}"><p>{s["variation"]}</p><div class="small"><span>64 px</span><img src="{image}" width="64" height="64"><span>32 px</span><img src="{image}" width="32" height="32"></div></article>')
        sections.append('</div></section>')
    (OUT/'preview.html').write_text('''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Карты и печати — 10 вариантов для томов</title><style>body{margin:0;background:#080808;color:#eee;font:16px/1.5 system-ui}main{max-width:1600px;padding:24px;margin:auto}a{color:#ddd}h1{font-size:30px}h2{font-size:26px}h3{font-size:18px}p{color:#aaa}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}article{background:#101010;border:1px solid #555;padding:15px;text-align:center}article>img{max-width:100%;height:auto}img{object-fit:contain;image-rendering:pixelated}.small{height:80px;display:flex;align-items:center;justify-content:center;gap:12px}section{margin:40px 0}</style><main><h1>Карты, колоды и печати</h1><p>10 эскизов для выбора основы новых томов. Карты: К1–К5. Печати: П1–П5. Эти номера обозначают варианты формы, а не ID оригинальных томов.</p>'''+''.join(sections)+'</main></html>',encoding='utf-8')
    manifest={'stage':'family-selection','generation_mode':'built-in-imagegen','count':10,'groups':GROUPS,'selected_candidate':None,'candidates':result}
    (OUT/'catalog.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    for page in OUT.rglob('*.html'):
        soup=BeautifulSoup(page.read_text(encoding='utf-8'),'html.parser')
        for tag,key in [('a','href'),('img','src')]:
            for node in soup.select(tag):assert (page.parent/node[key]).resolve().is_file(),(page,node[key])
    for s in specs:
        p=OUT/s['group']/'icons_256'/f'{s["id"]:02d}.png'
        with Image.open(p) as im:
            assert im.size==(256,256) and im.mode=='RGBA'
            assert im.getchannel('A').getextrema()==(0,255)
    report={'count':10,'cards':5,'seals':5,'unique_codes':len({s['code'] for s in specs}),'pngs_transparent':True,'square_256':True,'preview_links_verified':True,'generation_mode':'built-in-imagegen','selected_candidate':None}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
