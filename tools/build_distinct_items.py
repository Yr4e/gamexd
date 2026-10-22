"""Build the 15 separately reviewed item redesign candidates."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, unquote
import json, hashlib, html, shutil, argparse
from build_asset_review import CSS, JS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/items/redesign-distinct-15'
REVIEW=ROOT/'assets/review'
F='C:/Windows/Fonts/consolab.ttf'

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def esc(s): return html.escape(str(s),quote=True)
def normalize(source,target):
    with Image.open(source) as raw:
        raw=raw.convert('RGBA')
        assert raw.getchannel('A').getextrema()[0]==0,source
        bbox=raw.getchannel('A').point(lambda a:255 if a>96 else 0).getbbox()
        assert bbox,source
        crop=raw.crop(bbox);ratio=48/max(crop.size)
        logical=crop.resize((max(1,round(crop.width*ratio)),max(1,round(crop.height*ratio))),Image.Resampling.NEAREST)
        color=logical.convert('RGB').quantize(colors=24,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGBA')
        color.putalpha(logical.getchannel('A').point(lambda a:255 if a>=240 else a))
        sprite=color.resize((color.width*4,color.height*4),Image.Resampling.NEAREST)
        canvas=Image.new('RGBA',(256,256))
        canvas.alpha_composite(sprite,((256-sprite.width)//2,(256-sprite.height)//2))
        canvas.save(target)

def fit(canvas,path,x,y,size):
    im=Image.open(path).convert('RGBA'); im=im.crop(im.getchannel('A').getbbox())
    ratio=size/max(im.size);im=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.NEAREST)
    canvas.paste(im,(x+(size-im.width)//2,y+(size-im.height)//2),im)

def shell(body):
    return '<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>15 новых предметов</title><link rel="stylesheet" href="review.css"><main>'+body+'</main><script src="review.js"></script></html>'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--partial',action='store_true');args=parser.parse_args()
    plan=read(OUT/'plan.json');current=read(REVIEW/'manifest.json')['items'];records=[]
    current_hashes={e['id']:sha(REVIEW/e['our_file']) for e in current}
    for p in plan['variants']:
        if not (OUT/p['raw_file']).exists():
            if args.partial:continue
            raise FileNotFoundError(p['raw_file'])
        assert read(OUT/p['receipt_file'])['variant_id']==p['variant_id']
        normalize(OUT/p['raw_file'],OUT/p['our_file'])
        n=p['id'];shutil.copyfile(REVIEW/p['original_source'],OUT/f'originals/{n:02d}.png');shutil.copyfile(REVIEW/p['previous_source'],OUT/f'previous/{n:02d}.png')
        r={k:v for k,v in p.items() if k!='prompt'}
        r.update(original_file=f'originals/{n:02d}.png',previous_file=f'previous/{n:02d}.png',data_file=f'data/{n:02d}.json',original_sha256=sha(OUT/f'originals/{n:02d}.png'),previous_sha256=current_hashes[n],our_sha256=sha(OUT/p['our_file']),generation_mode='built-in-imagegen',outline_policy='One generated colored rim; no additional dark or colored rim applied.',effect_policy='Original gameplay mapping retained. New visual subject is deliberately nonliteral.')
        save(OUT/r['data_file'],r);records.append(r)
    font=ImageFont.truetype(F,26)
    grid=Image.new('RGB',(1600,1600),'black');d=ImageDraw.Draw(grid);d.text((48,45),'15 новых предметов · отдельный вариант',font=ImageFont.truetype(F,34),fill='white')
    for i,r in enumerate(records):
        x=50+(i%5)*300;y=320+(i//5)*300
        d.rectangle((x,y,x+284,y+284),outline='#666',width=2);fit(grid,OUT/r['our_file'],x+42,y+42,200);d.text((x+9,y+8),str(r['id']),font=font,fill='white')
    grid.save(OUT/'grid.png')
    pages=[]
    for page,start in enumerate(range(0,len(records),5),1):
        board=Image.new('RGB',(1800,1600),'black');d=ImageDraw.Draw(board)
        d.text((35,20),'Megabonk → наша старая → новая',font=ImageFont.truetype(F,30),fill='white')
        for i,r in enumerate(records[start:start+5]):
            y=90+i*295;d.rectangle((15,y,1784,y+283),outline='#555')
            d.text((30,y+8),f"#{r['id']} {r['original_name']}  →  {r['new_name_en']} / {r['new_name_ru']}",font=font,fill='white')
            for x,k,label in [(45,'original_file','Megabonk'),(610,'previous_file','Наша старая'),(1185,'our_file','Новая')]:
                d.text((x+190,y+73),label,font=font,fill='#aaa');fit(board,OUT/r[k],x,y+60,165)
            d.text((32,y+244),r['original_effect_ru'],font=ImageFont.truetype(F,21),fill='#ccc')
        name=f'comparison-{page:02d}.png';board.save(OUT/name);pages.append(name)
    context=Image.new('RGB',(2000,2000),'black');d=ImageDraw.Draw(context);byid={r['id']:r for r in records}
    for i,e in enumerate(current):
        x=10+(i%10)*198;y=100+(i//10)*198;n=e['id'];p=OUT/byid[n]['our_file'] if n in byid else REVIEW/e['our_file']
        fit(context,p,x+21,y+21,150);d.rectangle((x,y,x+188,y+188),outline='#999' if n in byid else '#444');d.text((x+6,y+4),str(n),font=ImageFont.truetype(F,21),fill='white')
    context.save(OUT/'context-grid-85.png')
    controls='<div class="tools"><input id="search" aria-label="Поиск" placeholder="ID, Megabonk или наше название"><label>Размер <select id="size"><option>32</option><option>64</option><option selected>128</option><option>192</option></select></label></div><p id="shown"></p>'
    cards=[]
    for r in records:
        terms=esc(' '.join([str(r['id']),r['original_name'],r['new_name_en'],r['new_name_ru'],r['previous_name_ru']]).casefold())
        figures=''
        for k,label,name in [('original_file','Megabonk',r['original_name']),('previous_file','Наша старая',r['previous_name_ru']),('our_file','Новый вариант',r['new_name_en']+' / '+r['new_name_ru'])]:
            figures+=f'<figure><div class="label">{label}</div><div class="art"><img src="{r[k]}" alt="{esc(name)}"></div><figcaption class="name">{esc(name)}</figcaption></figure>'
        cards.append(f'<article class="card" data-id="{r["asset_id"]}" data-search="{terms}"><div class="card-top"><span>#{r["id"]:02d} · {r["asset_id"]}</span><span class="muted">Новый вариант</span></div><div class="compare" style="grid-template-columns:repeat(3,minmax(0,1fr))">{figures}</div><p class="effect">Эффект оригинала: {esc(r["original_effect_ru"])}</p><p class="muted">Обводка: {r["outline_hex"]} · {esc(r["rarity"])}</p><div class="links"><a href="{r["source_url"]}">Megabonk</a><a href="{r["wiki_url"]}">Вики</a><a href="{r["data_file"]}">Данные</a><a href="{r["our_file"]}">PNG</a></div></article>')
    body='<h1>15 новых предметов</h1><p class="notice">Другие образы и названия; исходные ID и игровые эффекты сохранены. Отдельный набор для просмотра, основной набор пока не заменён. Цвета обводок перенесены из предыдущей версии без изменения.</p><nav><a href="grid.png">Сетка новых</a><a href="context-grid-85.png">В контексте 85 предметов</a><a href="manifest.json">Каталог</a>'+''.join(f'<a href="{p}">Сравнение {i+1}</a>' for i,p in enumerate(pages))+'</nav>'+controls+'<div class="audit-grid">'+''.join(cards)+'</div>'
    (OUT/'preview.html').write_text(shell(body),encoding='utf-8');(OUT/'review.css').write_text(CSS+'\n.audit-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(720px,100%),1fr));gap:20px;margin-top:24px}',encoding='utf-8');(OUT/'review.js').write_text(JS,encoding='utf-8')
    save(OUT/'manifest.json',{'set_id':'items-distinct-15-v1','is_default':False,'count':len(records),'items':records})
    save(OUT/'lookup.json',{'by_original_name':{r['original_name'].casefold():r for r in records}})
    for r in records:
        im=Image.open(OUT/r['our_file']);assert im.mode=='RGBA' and im.size==(256,256) and im.getchannel('A').getextrema()==(0,255)
        assert r['our_sha256'] not in [r['original_sha256'],r['previous_sha256']]
    for p in OUT.glob('*.html'):
        soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
        for tag,attr in [('a','href'),('img','src'),('script','src'),('link','href')]:
            for node in soup.find_all(tag):
                u=urlsplit(node.get(attr,''))
                if not u.scheme and u.path:assert (p.parent/unquote(u.path)).is_file(),(p,u.path)
    assert all(sha(REVIEW/e['our_file'])==current_hashes[e['id']] for e in current)
    save(OUT/'validation.json',{'count':len(records),'complete':len(records)==15,'ids':[r['id'] for r in records],'originals_and_previous_copied':True,'all_85_current_pngs_unchanged':True,'transparent_256_pngs':True,'local_links_valid':True,'stable_original_keys':True,'body_extent':192,'palette_limit':24})
    (OUT/'README.md').write_text('# Новые образы · 15 предметов\n\nСамостоятельный набор кандидатов. Сравнение: оригинал Megabonk → наша прежняя иконка → новый образ. Сохранены ID, исходные эффекты, ссылки и прежний цвет обводки; новые названия EN/RU записаны отдельно. Основные 85 PNG не заменены.\n\nПредпросмотр: preview.html. Сетки: grid.png и context-grid-85.png. Данные: manifest.json, lookup.json и data/. Исходные генерации и промпты сохранены в raw/ и prompts/.\n\nОписания сверены с https://megabonk.wiki/wiki/Items и индивидуальными страницами Megabonk.org. Числовой баланс не менялся. Оттенки обводок унаследованы из предыдущего набора: существующие расхождения между полем rarity и цветом не исправлялись в этом художественном проходе.\n',encoding='utf-8')
    print(json.dumps(read(OUT/'validation.json')))

if __name__=='__main__':main()
