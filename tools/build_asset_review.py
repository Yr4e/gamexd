"""Freeze the selected 30 weapons and 85 items into a portable, ID-linked review."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from datetime import datetime,timezone
import json,csv,shutil,hashlib,html,zipfile,math
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/review'
W=ROOT/'assets/weapon-icons'
I=ROOT/'assets/items/revision-simple'
F=ROOT/'assets/items/flat-2d-attempt'
FLAT_IDS={1,2,5,6,7,8,9,12,13,15,16,17,20,23,27,29,38}
EFFECTS={
1:'Широкий взмах мечом поражает нескольких врагов.',
2:'Выпускает огненные шары, взрывающиеся при попадании.',
3:'Бьёт ближайших врагов молнией; улучшения добавляют цепные переходы.',
4:'Оставляет за персонажем огненный след, наносящий урон.',
5:'Камни вращаются вокруг персонажа и поражают врагов.',
6:'Метает кость, которая отскакивает от целей.',
7:'Стреляет пробивающими стрелами, проходящими сквозь врагов.',
8:'Выпускает несколько пуль с рикошетами.',
9:'Блокирует атаки и отвечает ударными волнами.',
10:'Бросает банан, который возвращается к персонажу.',
11:'Постоянно наносит урон врагам рядом с персонажем.',
12:'Бросает вращающиеся топоры, некоторое время поражающие врагов.',
13:'Связывает персонажа с врагом и наносит урон целям между ними.',
14:'Дальний точный выстрел пробивает врагов.',
15:'Выпускает самонаводящиеся ракеты.',
16:'Ручной выстрел дробью; улучшения усиливают отбрасывание и критический урон.',
17:'Ставит мины, взрывающиеся при приближении врагов.',
18:'Метает самонаводящиеся кинжалы с отскоками.',
19:'Замораживает ближайших врагов и наносит им урон.',
20:'Создаёт торнадо, которые отбрасывают врагов.',
21:'Пробивающий клинок имеет шанс казнить врага.',
22:'Убийства могут навсегда повышать максимальное здоровье.',
23:'Стягивает врагов в гравитационную область, наносящую урон.',
24:'Создаёт сохраняющиеся на земле ядовитые области.',
25:'Быстро рубит ближайшего врага с автоматическим наведением.',
26:'Автоматически направляет вращающееся пламя на врагов.',
27:'Урон зависит от броска 1–6; шестёрки навсегда увеличивают шанс крита.',
28:'Удар перед персонажем поражает несколько врагов и выпускает дальний разрез.',
29:'Удары спереди и сзади усиливаются при низком здоровье.',
30:'Круговой взмах; убийства элитных врагов заряжают усиленную атаку.',
}
RARITY={'Legendary':'Легендарный','Epic':'Эпический','Rare':'Редкий','Common':'Обычный'}
SOURCE_NOTES={
4:{'status':'conflicting','note':'Megabonk.org описывает уменьшение перезарядки и восстановление энергии. В таблице другой Wiki указаны энергетические сферы; источники расходятся. Здесь сохранено описание выбранного сайта.','links':['https://megabonk.org/database/items/energy-core','https://megabonk.wiki/wiki/Items']},
8:{'status':'unconfirmed','note':'На Megabonk.org эффект помечен как спорный: сообщения об увеличении золота противоречат сообщениям об отсутствии эффекта. Не назначен выдуманный бонус.','links':['https://megabonk.org/database/items/golden-ring','https://megabonk.wiki/wiki/Golden_Ring']},
31:{'status':'conflicting','note':'Megabonk.org указывает срабатывание при убийстве и отмечает сообщения о срабатывании при попадании. Другая Wiki описывает попадание; это расхождение сохранено в данных.','links':['https://megabonk.org/database/items/slutty-cannon','https://megabonk.wiki/wiki/Items']},
}

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def prepare():
    for cat in ('weapons','items'):
        for sub in ('ours','originals','data','entries','sheets'):(OUT/cat/sub).mkdir(parents=True,exist_ok=True)
    weapons=read(W/'catalog.json');wr={e['id']:e for e in read(W/'weapon-research.json')['weapons']}
    items=read(I/'catalog.json');ir={e['id']:e for e in read(ROOT/'assets/items/individual-redesign/research.json')}
    flat={e['id']:e for e in read(F/'catalog.json')}
    assert set(flat)==FLAT_IDS
    result=[]
    for cat,entries in (('weapons',weapons),('items',items)):
        for e in entries:
            n=e['id'];key=f'{"weapon" if cat=="weapons" else "item"}_{n:02d}'
            if cat=='weapons':
                src=wr[n];assert src['name']==e['megabonk']
                original=W/src['file'];ours=W/e['file']
                name=e['megabonk'];en=e['english'];ru=e['russian'];effect=EFFECTS[n]
                source_en=src['effect_source_en'];version='weapon-approved';rarity=None;color=None
            else:
                src=ir[n];assert src['original_name']==e['original_name']
                original=ROOT/'assets/items'/src['file']
                selected=flat[n] if n in flat else e
                ours=(F if n in flat else I)/selected['file']
                name=e['original_name'];en=e['new_name_en'];ru=e['new_name_ru'];effect=e['effect_summary_ru']
                assert selected['original_name']==name and selected['new_name_en']==en
                source_en=src['effect_source_en'];version='matte-2d' if n in flat else 'item-approved-base'
                rarity=src['rarity'];color=e['outline_hex']
            assert digest(original)==src['sha256']
            for source,sub in ((original,'originals'),(ours,'ours')):shutil.copyfile(source,OUT/cat/sub/f'{n:02d}.png')
            record={'asset_id':key,'id':n,'category':cat,'original_key':src.get('original_key','megabonk:item:'+src.get('slug',src['page_url'].rstrip('/').split('/')[-1])),
                'original_name':name,'new_name_en':en,'new_name_ru':ru,'original_effect_ru':effect,'original_effect_source_en':source_en,
                'source_url':src['page_url'],'source_image_url':src['icon_url'],'rarity':rarity,'rarity_ru':RARITY.get(rarity),'outline_hex':color,
                'original_file':f'{cat}/originals/{n:02d}.png','our_file':f'{cat}/ours/{n:02d}.png','entry_file':f'{cat}/entries/{n:02d}.html',
                'data_file':f'{cat}/data/{n:02d}.json','original_sha256':digest(original),'our_sha256':digest(ours),
                'selected_version':version,'selected_source':ours.relative_to(ROOT).as_posix()}
            note=SOURCE_NOTES.get(n) if cat=='items' else None
            record.update({'effect_status':note['status'] if note else 'source_description','effect_note':note['note'] if note else '', 'effect_note_sources':note['links'] if note else [],'free_association':bool(e.get('associative')) if cat=='items' else False})
            record.update({'entity_category':cat,'set_id':cat+'-current','variant_id':key+'@current','is_default':True,'version_label':'Основной — актуальный','lifecycle':'current'})
            save(OUT/cat/'data'/f'{n:02d}.json',record);result.append(record)
    assert len(result)==115 and len({e['asset_id'] for e in result})==115 and len({e['original_key'] for e in result})==115
    return result

def prepare_glossy(current):
    """Archive complete historical sprites without replacing a current asset."""
    source=ROOT/'assets/items/individual-redesign'
    target=OUT/'items-glossy-early'
    for sub in ('ours','data','entries','sheets'):(target/sub).mkdir(parents=True,exist_ok=True)
    base={e['id']:e for e in current if e['category']=='items'}
    result=[]
    for old in read(source/'catalog.json'):
        n=old['id'];active=base[n];assert old['original_name']==active['original_name']
        image=source/old['icon_file'];assert digest(image)==old['icon_sha256']
        shutil.copyfile(image,target/'ours'/f'{n:02d}.png')
        e=dict(active)
        e.update({'category':'items-glossy-early','set_id':'items-glossy-early','variant_id':active['asset_id']+'@glossy-early',
            'is_default':False,'version_label':'Глянец — ранняя версия','lifecycle':'archived','free_association':False,
            'new_name_en':old['new_name_en'],'new_name_ru':old['new_name_ru'],
            'current_name_en':active['new_name_en'],'current_name_ru':active['new_name_ru'],
            'current_data_file':active['data_file'],'current_entry_file':active['entry_file'],
            'our_file':f'items-glossy-early/ours/{n:02d}.png','our_sha256':digest(image),
            'data_file':f'items-glossy-early/data/{n:02d}.json','entry_file':f'items-glossy-early/entries/{n:02d}.html',
            'selected_version':'glossy-early','selected_source':image.relative_to(ROOT).as_posix(),
            'version_note':'Ранний альтернативный рисунок. Не смешивать с основным набором; выбирать весь set_id явно. Названия этой версии исторические.'})
        save(OUT/e['data_file'],e);result.append(e)
    assert len(result)==85
    archive=OUT/'history';archive.mkdir(exist_ok=True)
    shutil.copyfile(I/'items-natural-edge-grid.png',archive/'revision-simple-0049.png')
    return result

CSS='''*{box-sizing:border-box}body{margin:0;background:#080808;color:#e6e6e6;font:16px/1.5 system-ui,sans-serif}main{max-width:1600px;margin:auto;padding:28px}a{color:#ddd;text-underline-offset:4px}a:hover{color:white}h1{font-size:32px;margin:12px 0}h2{font-size:22px}p{margin:8px 0}nav{display:flex;gap:20px;flex-wrap:wrap;border-bottom:1px solid #444;padding-bottom:15px}.muted{color:#aaa}.tools{position:sticky;top:0;z-index:2;background:#101010;display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:14px 0;border-bottom:1px solid #444}input,select,button{font:inherit;background:#191919;color:#eee;border:1px solid #666;border-radius:4px;padding:9px 12px}input{min-width:250px;flex:1}button{cursor:pointer}button[aria-pressed=true]{background:#ddd;color:#111}input:focus,select:focus,button:focus,a:focus{outline:2px solid #bbb;outline-offset:2px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(440px,100%),1fr));gap:18px;margin-top:20px}.card{border:1px solid #555;background:#101010;padding:18px;min-width:0}.card-top{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:12px}.id{font-weight:700}.compare{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}figure{margin:0;min-width:0;text-align:center}.art{display:grid;place-items:center;width:min(var(--size,128px),100%);aspect-ratio:1;margin:10px auto;background:#000;border:1px solid #555}.art img{width:100%;height:100%;object-fit:contain;image-rendering:pixelated}.original .art img{width:75%;height:75%}.label{color:#aaa;font-size:13px}.name{font-weight:650;overflow-wrap:anywhere;margin-top:6px}.ru{font-size:14px;color:#bbb}.effect{margin:16px 0 12px;padding-top:12px;border-top:1px solid #333}.effect span{display:block;color:#999;font-size:12px;margin-bottom:4px}.links{display:flex;gap:16px;flex-wrap:wrap;font-size:14px}.ours-only .original{display:none}.ours-only .compare{grid-template-columns:1fr}.hidden{display:none!important}.sheets{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}footer{margin:28px 0;color:#999;font-size:14px}.detail{max-width:950px}.detail .art{width:min(256px,100%)}.hub{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-top:24px}.hub a{display:block;border:1px solid #555;padding:24px;background:#101010;text-decoration:none}.hub img{max-width:100%;height:auto}.notice{border-left:2px solid #777;padding-left:12px;color:#bbb}.smallrow{display:flex;align-items:center;justify-content:center;gap:18px;margin-top:16px}.smallrow img{image-rendering:pixelated;object-fit:contain;background:#000}@media(max-width:600px){main{padding:16px}.tools{position:static}.compare{gap:10px}h1{font-size:26px}}'''

JS='''const cards=[...document.querySelectorAll('.card[data-search]')];const q=document.querySelector('#search');const rarity=document.querySelector('#rarity');function filter(){const term=q.value.trim().toLocaleLowerCase();const r=rarity?rarity.value:'';let count=0;for(const card of cards){const match=/^#?[0-9]{1,2}$/.test(term)?card.dataset.id.endsWith('_'+String(Number(term.replace('#',''))).padStart(2,'0')):card.dataset.search.includes(term);const show=match&&(!r||card.dataset.rarity===r);card.classList.toggle('hidden',!show);if(show)count++}document.querySelector('#shown').textContent=`Показано ${count} из ${cards.length}`}q?.addEventListener('input',filter);rarity?.addEventListener('change',filter);document.querySelector('#size')?.addEventListener('change',e=>document.documentElement.style.setProperty('--size',e.target.value+'px'));document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{document.body.classList.toggle('ours-only',b.dataset.mode==='ours');document.querySelectorAll('[data-mode]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)))}));if(q)filter();'''

def esc(s):return html.escape(str(s),quote=True)
def shell(title,content,root='../'):
    return f'<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><link rel="stylesheet" href="{root}review.css"><main><nav><a href="{root}index.html">Все материалы</a><a href="{root}weapons/preview.html">Пушки · актуальные</a><a href="{root}items/preview.html">Айтемы · актуальные</a><a href="{root}items-glossy-early/preview.html">Глянец — ранняя версия</a><a href="{root}manifest.json">Данные</a></nav>{content}<footer>Источник оригиналов и описаний: Megabonk.org. Названия и ID в предпросмотре нанесены кодом. Игровые PNG прозрачные, без подписей и рамок.</footer></main><script src="{root}review.js"></script></html>'

def card(e,root='../',detail=False):
    badge=f'<span style="color:{e["outline_hex"]}">{esc(e["rarity_ru"])}</span>' if e['rarity'] else ''
    search=esc(' '.join([str(e['id']),f'{e["id"]:02d}',e['asset_id'],e['original_name'],e['new_name_en'],e['new_name_ru'],e['original_effect_ru']]).lower())
    out=f'<article class="card" data-id="{e["asset_id"]}" data-search="{search}" data-rarity="{e["rarity"] or ""}"><div class="card-top"><a class="id" href="{root}{e["entry_file"]}">#{e["id"]:02d} · {e["asset_id"]}</a>{badge}</div><div class="compare"><figure class="original"><div class="label">Megabonk</div><div class="art"><img loading="lazy" src="{root}{e["original_file"]}" alt="Megabonk: {esc(e["original_name"])}"></div><figcaption class="name">{esc(e["original_name"])}</figcaption></figure><figure><div class="label">Наша иконка</div><div class="art"><img loading="lazy" src="{root}{e["our_file"]}" alt="{esc(e["new_name_en"])} / {esc(e["new_name_ru"])}"></div><figcaption><div class="name">{esc(e["new_name_en"])}</div><div class="ru">{esc(e["new_name_ru"])}</div></figcaption></figure></div><p class="effect"><span>Эффект оригинала в Megabonk</span>{esc(e["original_effect_ru"])}</p><div class="links"><a target="_blank" rel="noopener" href="{esc(e["source_url"])}">Источник</a><a href="{root}{e["our_file"]}" download>Наш PNG · {e["id"]:02d}</a><a href="{root}{e["data_file"]}">Связь по ID · JSON</a></div>'
    version=f'<p class="notice"><strong>{esc(e["version_label"])}</strong> · {esc(e["set_id"])}</p>'
    if not e['is_default']:
        version+=f'<p class="notice">Архивный вариант. Название выше — раннее. Актуальное: <a href="{root}{e["current_entry_file"]}">{esc(e["current_name_en"])} / {esc(e["current_name_ru"])}</a>. Связь с {esc(e["original_name"])} та же.</p>'
    out+=version
    if e['effect_note']:
        out+='<details><summary>Примечание к данным источника</summary><p>'+esc(e['effect_note'])+'</p><p>'+''.join(f'<a href="{esc(url)}" target="_blank" rel="noopener">Источник {n+1}</a> ' for n,url in enumerate(e['effect_note_sources']))+'</p></details>'
    if detail:out+=f'<div class="smallrow"><span>64 px</span><img src="{root}{e["our_file"]}" width="64" height="64"><span>32 px</span><img src="{root}{e["our_file"]}" width="32" height="32"></div>'
    return out+'</article>'

def write_pages(records,sheets):
    (OUT/'review.css').write_text(CSS,encoding='utf-8');(OUT/'review.js').write_text(JS,encoding='utf-8')
    for cat,title in (('weapons','Пушки — актуальные'),('items','Айтемы — актуальные'),('items-glossy-early','Глянец — ранняя версия')):
        entries=[e for e in records if e['category']==cat]
        rarity='<label>Редкость <select id="rarity"><option value="">Все</option>'+''.join(f'<option value="{k}">{v}</option>' for k,v in RARITY.items())+'</select></label>' if cat!='weapons' else ''
        controls=f'<div class="tools"><input id="search" aria-label="Поиск по ID, названию или эффекту" placeholder="ID, название или эффект…"><label>Размер <select id="size"><option>32</option><option>64</option><option selected>128</option><option>192</option></select></label>{rarity}<button data-mode="compare" aria-pressed="true">Оригинал → наши</button><button data-mode="ours" aria-pressed="false">Только наши</button></div>'
        originals='../items/originals-grid.png' if cat=='items-glossy-early' else 'originals-grid.png'
        links='<div class="sheets">'+f'<a href="ours-grid.png">Сетка наших иконок</a><a href="{originals}">Сетка оригиналов</a>'+''.join(f'<a href="sheets/{p}">Сравнение {i+1}</a>' for i,p in enumerate(sheets[cat]))+'</div>'
        notice='Архив: 85 ранних глянцевых айтемов из первой индивидуальной переработки. Сохранены ранние названия и ссылки на актуальные варианты. Набор отделён от основных иконок.' if cat=='items-glossy-early' else 'Основной актуальный набор. Ранние глянцевые айтемы хранятся отдельно и не подставляются автоматически.'
        content=f'<h1>{title} · {len(entries)}</h1><p class="notice">{notice}</p><p class="muted">Постоянный ID и original_key связывают оригинал, нашу картинку, названия и эффект.</p>'+controls+'<p id="shown"></p>'+links+'<div class="grid">'+''.join(card(e) for e in entries)+'</div>'
        (OUT/cat/'preview.html').write_text(shell(title,content),encoding='utf-8')
        for n,e in enumerate(entries):
            prev=f'<a href="{entries[n-1]["id"]:02d}.html">← Предыдущий</a>' if n else ''
            nxt=f'<a href="{entries[n+1]["id"]:02d}.html">Следующий →</a>' if n+1<len(entries) else ''
            content=f'<div class="detail"><h1>#{e["id"]:02d} · {esc(e["new_name_en"])}</h1>'+card(e,root='../../',detail=True)+f'<p class="links">{prev}<a href="../preview.html">Все {title.lower()}</a>{nxt}</p></div>'
            (OUT/e['entry_file']).write_text(shell(e['new_name_en'],content,root='../../'),encoding='utf-8')
    content='<h1>Оригиналы Megabonk → наши иконки</h1><p class="notice">115 игровых сущностей: 30 пушек и 85 айтемов. Основной набор — актуальный. Глянец — отдельная ранняя версия тех же 85 айтемов, а не дополнительные предметы.</p><div class="hub">'+''.join(f'<a href="{cat}/preview.html"><h2>{title} · {count}</h2><p>{desc}</p><img src="{cat}/ours-grid.png" alt="{title}"></a>' for cat,title,count,desc in [('weapons','Пушки — актуальные',30,'30 актуальных иконок оружия'),('items','Айтемы — актуальные',85,'85 актуальных иконок предметов'),('items-glossy-early','Глянец — ранняя версия',85,'Отдельный архив ранних глянцевых айтемов')])+'</div><h2>Связь с Megabonk</h2><p>Для всех 85 айтемов и 30 оружий сохранено соответствие: оригинальное название Megabonk → наше название EN/RU → наша иконка. Каждая запись содержит ID, описание исходного эффекта и ссылку на источник. Например, Anvil → Triune Gear / Тройная шестерня. Актуальные и ранние глянцевые варианты связаны с одним оригиналом и хранятся отдельно.</p><p><a href="lookup.json">Поиск по оригинальному названию</a> · <a href="manifest.json">Каталог актуальных + архив</a> · <a href="manifest.csv">Актуальный CSV</a> · <a href="items-glossy-early/manifest.csv">Ранний глянец CSV</a> · <a href="README.md">Структура файлов</a></p><h2>Сохранённый исторический лист из сообщения 00:49</h2><p>Смешанный набор revision-simple того этапа. Это отдельный снимок истории, он не определяет активные файлы.</p><p><a href="history/revision-simple-0049.png">Открыть сохранённый лист из сообщения</a></p>'
    (OUT/'index.html').write_text(shell('Предпросмотр 115 иконок',content,root=''),encoding='utf-8')

FONT='C:/Windows/Fonts/consola.ttf'
BOLD='C:/Windows/Fonts/consolab.ttf'
def draw_fit(board,path,box):
    im=Image.open(path).convert('RGBA');im.thumbnail((box[2],box[3]),Image.Resampling.NEAREST)
    if im.width<box[2] and im.height<box[3]:
        ratio=min(box[2]/im.width,box[3]/im.height);im=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.NEAREST)
    board.paste(im,(box[0]+(box[2]-im.width)//2,box[1]+(box[3]-im.height)//2),im)

def wrap(draw,text,font,width):
    lines=[];line=''
    for word in text.split():
        trial=(line+' '+word).strip()
        if draw.textlength(trial,font=font)>width and line:lines.append(line);line=word
        else:line=trial
    return lines+[line]

def write_images(records):
    pages={}
    for cat in ('weapons','items','items-glossy-early'):
        entries=[e for e in records if e['category']==cat];cols=6 if cat=='weapons' else 10
        size=1600 if cat=='weapons' else 2560;cell=256;rows=math.ceil(len(entries)/cols)
        for field,name in (('our_file','ours-grid.png'),('original_file','originals-grid.png')):
            if cat=='items-glossy-early' and field=='original_file':continue
            board=Image.new('RGB',(size,size),'black');d=ImageDraw.Draw(board)
            dx=(size-cols*cell)//2;dy=(size-rows*cell)//2
            label='Глянец — ранняя версия · АРХИВ' if cat=='items-glossy-early' else 'Основной — актуальный'
            d.text((20,20),label,font=ImageFont.truetype(BOLD,28),fill='#ddd')
            for n,e in enumerate(entries):
                x=dx+(n%cols)*cell;y=dy+(n//cols)*cell
                draw_fit(board,OUT/e[field],(x+32,y+32,192,192) if field=='original_file' else (x,y,cell,cell))
                d.rectangle((x+3,y+3,x+252,y+252),outline='#666',width=2)
                d.text((x+10,y+9),str(e['id']),font=ImageFont.truetype(BOLD,25),fill='white',stroke_width=2,stroke_fill='black')
            board.save(OUT/cat/name)
        pages[cat]=[]
        for page,start in enumerate(range(0,len(entries),8),1):
            board=Image.new('RGB',(1600,1600),'black');d=ImageDraw.Draw(board)
            title='Глянец — ранняя версия' if cat=='items-glossy-early' else ('Пушки — актуальные' if cat=='weapons' else 'Айтемы — актуальные')
            d.text((30,25),f'{title}: Megabonk → наши · {page}',font=ImageFont.truetype(BOLD,30),fill='white')
            namefont=ImageFont.truetype(BOLD,22);textfont=ImageFont.truetype(FONT,22);smallfont=ImageFont.truetype(FONT,18)
            for n,e in enumerate(entries[start:start+8]):
                x=(n%2)*800+16;y=100+(n//2)*370
                d.rectangle((x,y,x+766,y+350),outline='#444',width=1)
                d.text((x+12,y+8),f'#{e["id"]:02d}',font=namefont,fill='white')
                d.text((x+84,y+10),'Megabonk',font=smallfont,fill='#aaa');d.text((x+410,y+10),'Наша иконка',font=smallfont,fill='#aaa')
                draw_fit(board,OUT/e['original_file'],(x+28,y+64,96,96));draw_fit(board,OUT/e['our_file'],(x+400,y+48,128,128))
                for xx,label in ((x+150,e['original_name']),(x+540,e['new_name_en']+'\n'+e['new_name_ru'])):
                    yy=y+50
                    for para in label.split('\n'):
                        for line in wrap(d,para,namefont,205):d.text((xx,yy),line,font=namefont,fill='white');yy+=27
                d.text((x+14,y+194),'Эффект оригинала:',font=smallfont,fill='#aaa')
                lines=wrap(d,e['original_effect_ru'],textfont,730)
                assert len(lines)<=4,(cat,e['id'],lines)
                for j,line in enumerate(lines):d.text((x+14,y+221+j*27),line,font=textfont,fill='#ddd')
                if e['effect_status'] in ('unconfirmed','conflicting'):
                    d.text((x+14,y+326),'Данные источника спорные — примечание есть в карточке',font=smallfont,fill='#aaa')
            filename=f'comparison-{page:02d}.png';board.save(OUT/cat/'sheets'/filename);pages[cat].append(filename)
    return pages

def validate(records):
    for cat,count in (('weapons',30),('items',85),('items-glossy-early',85)):
        selected=[e for e in records if e['category']==cat]
        assert [e['id'] for e in selected]==list(range(1,count+1))
        assert len(list((OUT/cat/'ours').glob('*.png')))==count
        if cat!='items-glossy-early':assert len(list((OUT/cat/'originals').glob('*.png')))==count
        assert len(list((OUT/cat/'data').glob('*.json')))==count
        for e in selected:
            assert e['original_effect_ru'] and e['new_name_ru'] and e['source_url'].startswith('https://megabonk.org/')
            assert digest(OUT/e['our_file'])==e['our_sha256']
            assert digest(OUT/e['original_file'])==e['original_sha256']
            with Image.open(OUT/e['our_file']) as im:
                assert im.size==(256,256) and im.mode=='RGBA',(cat,e['id'])
                assert im.getchannel('A').getextrema()==(0,255),(cat,e['id'])
            assert read(OUT/e['data_file'])==e
            assert (OUT/e['entry_file']).is_file()
            assert e['is_default']==(cat!='items-glossy-early')
    current={e['asset_id']:e for e in records if e['is_default']}
    glossy=[e for e in records if not e['is_default']]
    assert len(current)==115 and len(glossy)==85 and len({e['variant_id'] for e in records})==200
    for e in glossy:
        active=current[e['asset_id']]
        assert e['original_key']==active['original_key'] and e['original_file']==active['original_file']
        assert e['current_data_file']==active['data_file'] and e['our_file']!=active['our_file']
        assert e['current_name_en']==active['new_name_en'] and e['original_effect_ru']==active['original_effect_ru']
    lookup=read(OUT/'lookup.json')
    for e in current.values():
        entry=lookup['by_original_name']['weapons' if e['category']=='weapons' else 'items'][e['original_name'].casefold()]
        assert entry['default_data_file']==e['data_file'] and entry['default_png']==e['our_file']
    pages=list(OUT.rglob('*.html'));assert len(pages)==204
    for path in pages:
        soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
        assert soup.html.get('lang')=='ru',path
        for tag,key in (('a','href'),('img','src'),('script','src'),('link','href')):
            for node in soup.find_all(tag):
                value=node.get(key)
                if not value or value.startswith('#'):continue
                parsed=urlsplit(value)
                if parsed.scheme:continue
                target=(path.parent/unquote(parsed.path)).resolve()
                assert target.is_relative_to(OUT.resolve()) and target.is_file(),(path,value)
    with (OUT/'manifest.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f));assert len(rows)==115 and len({r['asset_id'] for r in rows})==115
    with (OUT/'items-glossy-early/manifest.csv').open(encoding='utf-8-sig',newline='') as f:
        assert len(list(csv.DictReader(f)))==85
    report={'weapons':30,'items':85,'total_entities':115,'archived_glossy_variants':85,'unique_variant_ids':200,'unique_original_links':115,'flat_items':sorted(FLAT_IDS),'individual_pngs_ours':200,'individual_pngs_originals':115,'individual_records':200,'individual_pages':200,'html_pages_checked':204,'local_links_verified':True,'effect_and_names_present':True,'hashes_verified':True,'source_notes_items':[4,8,31],'version_separation_verified':True,'default_resolution_verified':True,'release_approval':'user_granted'}
    save(OUT/'validation.json',report);return report

AI_GUIDE='''# Связи Megabonk → наши ассеты: инструкция для ИИ и балансировки

## Выбор предмета

Сначала прочитать manifest.json и lookup.json. Категория сущности entity_category (items или weapons) обязательна: предметы и оружие имеют независимую нумерацию. Поле category обозначает папку коллекции; у архива это items-glossy-early, но entity_category остаётся items. Искать по оригинальному названию Megabonk без учёта регистра и крайних пробелов. original_key и asset_id обозначают игровую сущность, variant_id и set_id — конкретную версию картинки. Наши числовые ID не являются enum из кода Megabonk.

Пример: lookup.json → by_original_name → items → anvil. Это item_01, megabonk:item:anvil, Triune Gear / Тройная шестерня. Основной PNG: items/ours/01.png. Эффект и ссылки: items/data/01.json. Слова Anvil, Triune Gear и Тройная шестерня относятся к одной игровой сущности. Имя файла, рисунок и название не определяют новую механику.

Оружие: weapons → sword возвращает weapon_01, Iron Fang / Железный клык, weapons/ours/01.png. Аналогично сопоставлены все 30 оружий и 85 айтемов.

## Версии — обязательно сохранять разделение

По умолчанию использовать weapons-current и items-current. Это основной актуальный набор, включая последние 17 матовых правок. Не считать все основные картинки полностью матовыми: набор содержит и ранее сохранённые рисунки.

items-glossy-early — «Глянец — ранняя версия»: отдельный архив 85 иконок первой индивидуальной переработки. is_default=false, lifecycle=archived. Не выбирать архив автоматически, по сходству картинки, по порядку обхода папок или по одному числовому ID. Не смешивать его PNG с актуальными по отдельности без прямого запроса пользователя.

Для раннего глянца нужен явный выбор всего set_id items-glossy-early; затем разрешать каждый предмет по asset_id/original_key внутри этого набора. В раннем архиве сохранены исторические new_name_en/new_name_ru. Поля current_name_en/current_name_ru и current_data_file ведут на актуальное имя и запись той же сущности. Разные исторические имена не создают дополнительные предметы и не заменяют актуальные названия.

Для оружия отдельный ранний глянцевый набор здесь не заявлен: доступны 30 актуальных иконок weapons-current. Оригиналы Megabonk в originals/ служат только референсами.

Всего 115 игровых сущностей и 200 наших PNG-вариантов: 115 актуальных + 85 ранних глянцевых. Уникальный вариант — variant_id, например item_01@current и item_01@glossy-early. У них одна связь с Anvil, но разные файлы и роли.

## Балансировка

original_effect_ru и original_effect_source_en описывают эффект оригинала из указанного источника. Это справочник соответствий, а не полная база числового баланса и не подтверждение реализации механик в нашей игре. При изменении характеристик ориентироваться на original_key, source_url и игровую реализацию друга; не выводить механику из изображения. Проверять effect_status/effect_note: у айтемов 4, 8 и 31 источники расходятся или эффект не подтверждён.

Все пути в JSON заданы относительно assets/review/. Сохранять эту папку целиком. Для просмотра открыть index.html после клонирования/распаковки; сервер не нужен.
'''

def main():
    records=prepare();glossy=prepare_glossy(records);all_records=records+glossy
    pages=write_images(all_records);write_pages(all_records,pages)
    save(OUT/'manifest.json',{'schema_version':2,'status':'approved_for_commit_and_private_push','default_sets':{'weapons':'weapons-current','items':'items-current'},'version_policy':'Resolve original_name within category to the default set. Use an archived set only when explicitly selected; never mix sets automatically.','weapons':[e for e in records if e['category']=='weapons'],'items':[e for e in records if e['category']=='items'],'archived_sets':{'items-glossy-early':{'label':'Глянец — ранняя версия','is_default':False,'manifest_file':'items-glossy-early/manifest.json'}},'comparison_sheets':pages})
    save(OUT/'items-glossy-early/manifest.json',{'schema_version':2,'set_id':'items-glossy-early','label':'Глянец — ранняя версия','lifecycle':'archived','is_default':False,'items':glossy})
    by_name={'items':{},'weapons':{}}
    archived={e['asset_id']:e for e in glossy}
    for e in records:
        variants=[{'set_id':e['set_id'],'is_default':True,'data_file':e['data_file'],'png':e['our_file']}]
        if e['asset_id'] in archived:
            g=archived[e['asset_id']];variants.append({'set_id':g['set_id'],'is_default':False,'data_file':g['data_file'],'png':g['our_file']})
        by_name[e['category']][e['original_name'].casefold()]={'asset_id':e['asset_id'],'original_key':e['original_key'],'original_name':e['original_name'],'current_name_en':e['new_name_en'],'current_name_ru':e['new_name_ru'],'default_set':e['set_id'],'default_data_file':e['data_file'],'default_png':e['our_file'],'variants':variants}
    save(OUT/'lookup.json',{'schema_version':1,'name_matching':'Choose category, strip whitespace and casefold original Megabonk name.','by_original_name':by_name})
    fields=list(records[0])
    with (OUT/'manifest.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v for k,v in e.items()} for e in records)
    fields=list(glossy[0])
    with (OUT/'items-glossy-early/manifest.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v for k,v in e.items()} for e in glossy)
    (OUT/'AI_USAGE.md').write_text(AI_GUIDE,encoding='utf-8')
    report=validate(all_records)
    (OUT/'README.md').write_text('''# Иконки игры: актуальный набор и ранний глянец

Открыть index.html после клонирования или распаковки всего проекта. Путь D:/gamexd не требуется: все ссылки относительные. Работает локально без сервера, зависимостей и интернет-загрузки данных. Есть поиск по ID, оригинальному/нашему имени и эффекту, фильтр редкости айтемов, размеры 32/64/128/192 и режим «только наши».

## Три отдельные галереи

- weapons/preview.html — 30 актуальных пушек, set_id weapons-current.
- items/preview.html — 85 актуальных айтемов, set_id items-current. Основной набор по умолчанию.
- items-glossy-early/preview.html — «Глянец — ранняя версия»: архив 85 айтемов первой индивидуальной переработки. set_id items-glossy-early, is_default=false, lifecycle=archived. Его нельзя автоматически смешивать с основным набором. Ранние названия сохранены; рядом указаны актуальные имена и ссылка на текущую запись.

Всего 115 игровых сущностей и 200 вариантов наших PNG. Это не 200 разных предметов. Отдельного раннего глянцевого оружейного набора здесь нет.

## Связь с Megabonk

Для каждого айтема и оружия сохранено соответствие оригинального названия Megabonk нашему названию, иконке и описанию исходного эффекта. lookup.json содержит поиск по оригинальным названиям, manifest.json — основной каталог и связь с архивом. Например, Anvil соответствует Triune Gear / Тройная шестерня, а Sword — Iron Fang / Железный клык. Подробные технические заметки о выборе версий находятся в AI_USAGE.md.

Категории weapons и items имеют собственную нумерацию 01…30 и 01…85. Это постоянные ID нашего каталога, не внутренние числовые enum игры Megabonk. asset_id и original_key связывают игровую сущность с оригиналом. set_id и variant_id определяют конкретную версию, например item_01@current и item_01@glossy-early. Изображение и имя не определяют механику.

В каждой категории originals/NN.png — скачанный оригинал без изменения байтов; ours/NN.png — выбранная наша прозрачная иконка без номера, названия и рамки. data/NN.json связывает обе картинки, исходное название, новые названия EN/RU, эффект оригинала, URL источника, цвет редкости, выбранную версию и SHA-256. entries/NN.html — отдельная подписанная карточка каждого ID. sheets/ содержит квадратные листы сравнения со всеми названиями и эффектами. ours-grid.png и originals-grid.png — полные сетки с номерами, нанесёнными кодом.

В итоговый просмотр выбраны 17 последних матовых айтемов, остальные айтемы взяты из актуального revision-simple/. Пушки взяты из действующего weapon-icons/catalog.json, включая согласованные лук, ауру и кубик. Выбор каждого PNG записан в selected_source и selected_version; выбранные байты скопированы в эту папку, поэтому просмотр не зависит от будущих правок рабочих папок.

Исходные названия, картинки и механики — из независимой базы Megabonk.org: https://megabonk.org/database/weapons/ и https://megabonk.org/database/items/. Эффекты описывают оригинал Megabonk; эта папка не утверждает, что механики уже реализованы в коде нашей игры. Ссылки на конкретные страницы и оригинальные изображения есть в каждой записи. Авторство оригинальных иконок Megabonk не присваивается.

validation.json проверяет 115 сущностей, 200 вариантов, уникальные связи, разделение версий, разрешение оригинального имени в основной набор, наличие названий и эффектов, прозрачные PNG RGBA 256×256 и хеши. HTML и все локальные ссылки проверяются статически. Проверка кнопок в живом браузере не выполнялась из-за ограничения инструмента на file://.

history/revision-simple-0049.png — точный сохранённый лист из сообщения пользователя 00:49. Это исторический смешанный набор того этапа, не источник выбора активных PNG.

Пересборка: python tools/collect_weapon_reference_data.py (только если нужно обновить скачанные оружейные референсы), затем python tools/build_asset_review.py. Готовый переносимый архив — output/asset-review.zip.
''',encoding='utf-8')
    archive=ROOT/'output/asset-review.zip';archive.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(OUT.rglob('*')):
            if path.is_file():z.write(path,path.relative_to(OUT))
    print(json.dumps(report,ensure_ascii=True));print(f'Archive {archive.stat().st_size/1048576:.2f} MiB')

if __name__=='__main__':main()
