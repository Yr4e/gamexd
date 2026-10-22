"""Package two alternative 23-tome sets with source-to-variant mappings."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup
import argparse, csv, hashlib, html, json, shutil, zipfile
from build_asset_review import CSS, JS, draw_fit, wrap

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/tomes/cards-refined'
FONT='C:/Windows/Fonts/consola.ttf'
BOLD='C:/Windows/Fonts/consolab.ttf'
TITLES={'cards':'Карты','seals':'Печати'}
EFFECTS=[
    '+15% к скорости передвижения','+7,5% к скорости атаки','+0,08× к множителю урона',
    '+10% к уклонению','+12% к получению золота','+25 к максимальному здоровью',
    '+20% к отбрасыванию','+7% к шансу крита по таблице; +2% по карточке источника',
    '+15% к скорости снарядов','+40 здоровья в минуту','+25 к щиту',
    '+12% к получению серебра','+10% к размеру атак','+12% к броне',
    '+75% к радиусу подбора','+10% к краже жизни','Одна случайная характеристика за уровень',
    '+3,5% к сложности','+15% к длительности эффектов','+7% к удаче',
    '+1 снаряд','+15 к урону шипами','+7% к получению опыта',
]


def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def esc(s):return html.escape(str(s),quote=True)


def shell(title,content,root=''):
    return f'''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><link rel="stylesheet" href="{root}review.css"><main><nav><a href="{root}index.html">Два набора томов</a><a href="{root}cards/preview.html">Карты · 23</a><a href="{root}seals/preview.html">Печати · 23</a><a href="{root}comparison.html">Оригинал → карта → печать</a><a href="{root}manifest.json">Каталог</a></nav>{content}<footer>23 тома: актуальные карты и сохранённые печати. Карты — выбранный набор. Печати сохранены как альтернативный вариант. Оригиналы и описания — Megabonk.org.</footer></main><script src="{root}review.js"></script></html>'''


def controls():
    return '<div class="tools"><input id="search" aria-label="Поиск по номеру, названию или эффекту" placeholder="Номер, оригинальное или наше название…"><label>Размер <select id="size"><option>32</option><option>64</option><option selected>128</option><option>192</option></select></label><button data-mode="compare" aria-pressed="true">С оригиналом</button><button data-mode="ours" aria-pressed="false">Наши варианты</button></div><p id="shown"></p>'


def figure(path,label,name,ru='',root='',original=False):
    return f'<figure class="{"original" if original else ""}"><div class="label">{esc(label)}</div><div class="art"><img loading="lazy" src="{root}{path}" alt="{esc(name)}"></div><figcaption><div class="name">{esc(name)}</div><div class="ru">{esc(ru)}</div></figcaption></figure>'


def card(records,root='',detail=False):
    e=records[0]
    terms=[e['asset_id'],e['original_name'],e['original_effect_ru']]
    for r in records:terms += [r['new_name_en'],r['new_name_ru']]
    search=esc(' '.join(terms).casefold())
    art=figure(e['original_file'],'Megabonk',e['original_name'],root=root,original=True)
    art+=''.join(figure(r['our_file'],TITLES[r['group']],r['new_name_en'],r['new_name_ru'],root) for r in records)
    columns=' style="grid-template-columns:repeat(3,minmax(0,1fr))"' if len(records)==2 else ''
    out=f'<article class="card" data-id="{e["asset_id"]}" data-search="{search}"><div class="card-top"><span class="id">#{e["id"]:02d} · {e["asset_id"]}</span><span class="muted">Связь с оригиналом</span></div><div class="compare"{columns}>{art}</div><p class="effect"><span>Эффект оригинального тома · базовое улучшение Common</span>{esc(e["original_effect_ru"])}</p>'
    if e['effect_note']:out+=f'<p class="notice">{esc(e["effect_note"])}</p>'
    out+=f'<div class="links"><a href="{esc(e["source_url"])}">Источник Megabonk</a>'
    for r in records:
        out+=f'<a href="{root}{r["entry_file"]}">{TITLES[r["group"]]} · карточка</a><a href="{root}{r["data_file"]}">JSON</a><a href="{root}{r["our_file"]}" download>PNG</a>'
    out+='</div>'
    if detail:
        for r in records:out+=f'<div class="smallrow"><span>64 px</span><img src="{root}{r["our_file"]}" width="64" height="64"><span>32 px</span><img src="{root}{r["our_file"]}" width="32" height="32"></div>'
    return out+'</article>'


def normalize(source,target):
    with Image.open(source) as raw:
        raw=raw.convert('RGBA')
        assert raw.getchannel('A').getextrema()[0]==0,source
        bbox=raw.getchannel('A').point(lambda a:255 if a>96 else 0).getbbox()
        assert bbox,source
        crop=raw.crop(bbox)
        ratio=48/max(crop.size)
        logical=crop.resize((max(1,round(crop.width*ratio)),max(1,round(crop.height*ratio))),Image.Resampling.NEAREST)
        color=logical.convert('RGB').quantize(colors=24,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGBA')
        # Treat nearly opaque generated pixels as opaque at export resolution.
        # Keep the genuine transparent edge; do not add another outline.
        color.putalpha(logical.getchannel('A').point(lambda a:255 if a>=240 else a))
        sprite=color.resize((color.width*4,color.height*4),Image.Resampling.NEAREST)
        canvas=Image.new('RGBA',(256,256))
        canvas.alpha_composite(sprite,((256-sprite.width)//2,(256-sprite.height)//2))
        canvas.save(target)


def make_grids(records):
    for group in TITLES:
        board=Image.new('RGB',(1600,1600),'black');d=ImageDraw.Draw(board)
        d.text((60,35),TITLES[group]+' · 23 тома',font=ImageFont.truetype(BOLD,34),fill='white')
        for e in [r for r in records if r['group']==group]:
            i=e['id']-1;x=160+(i%5)*256;y=160+(i//5)*256
            draw_fit(board,OUT/e['our_file'],(x,y,256,256))
            d.rectangle((x+2,y+2,x+253,y+253),outline='#666',width=2)
            d.text((x+9,y+7),str(e['id']),font=ImageFont.truetype(BOLD,27),fill='white',stroke_width=2,stroke_fill='black')
        board.save(OUT/group/'grid.png')


def make_sheets(records):
    pages={}
    for group,title in TITLES.items():
        entries=sorted([r for r in records if r['group']==group],key=lambda r:r['id'])
        pages[group]=[]
        for page,start in enumerate(range(0,len(entries),8),1):
            board=Image.new('RGB',(1600,1600),'black');d=ImageDraw.Draw(board)
            d.text((30,25),f'{title}: Megabonk → наши · {page}',font=ImageFont.truetype(BOLD,30),fill='white')
            nf=ImageFont.truetype(BOLD,22);tf=ImageFont.truetype(FONT,22);sf=ImageFont.truetype(FONT,18)
            for i,e in enumerate(entries[start:start+8]):
                x=16+(i%2)*800;y=100+(i//2)*370
                d.rectangle((x,y,x+766,y+350),outline='#444')
                d.text((x+12,y+8),f'#{e["id"]:02d}',font=nf,fill='white')
                d.text((x+84,y+10),'Megabonk',font=sf,fill='#aaa');d.text((x+410,y+10),title,font=sf,fill='#aaa')
                draw_fit(board,OUT/e['original_file'],(x+28,y+64,96,96));draw_fit(board,OUT/e['our_file'],(x+400,y+48,128,128))
                for xx,text in [(x+150,e['original_name']),(x+540,e['new_name_en']+'\n'+e['new_name_ru'])]:
                    yy=y+50
                    for para in text.split('\n'):
                        for line in wrap(d,para,nf,205):d.text((xx,yy),line,font=nf,fill='white');yy+=27
                d.text((x+14,y+194),'Эффект оригинала · Common / уровень:',font=sf,fill='#aaa')
                lines=wrap(d,e['original_effect_ru'],tf,730);assert len(lines)<=4
                for j,line in enumerate(lines):d.text((x+14,y+221+j*27),line,font=tf,fill='#ddd')
                if e['effect_status']=='conflicting':d.text((x+14,y+326),'Значения источника расходятся · примечание в карточке',font=sf,fill='#aaa')
            name=f'comparison-{page:02d}.png';board.save(OUT/group/'sheets'/name);pages[group].append(name)
    return pages


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--partial',action='store_true');args=parser.parse_args()
    plan=read(OUT/'plan.json')['variants'];source=read(OUT/'source-catalog.json')
    originals={e['id']:e for e in source['tomes']}
    (OUT/'originals').mkdir(exist_ok=True);(OUT/'entities').mkdir(exist_ok=True)
    for e in originals.values():
        src=ROOT/'assets/tomes'/e['original_file'];assert digest(src)==e['sha256']
        shutil.copyfile(src,OUT/e['original_file'])
    records=[]
    for p in plan:
        raw=OUT/p['raw_file']
        if not raw.exists():
            if args.partial:continue
            raise FileNotFoundError(raw)
        receipt=read(OUT/p['receipt_file']);assert receipt['variant_id']==p['variant_id']
        normalize(raw,OUT/p['our_file'])
        src=originals[p['id']]
        record={k:v for k,v in p.items() if k not in ('prompt','references')}
        record.update({'category':'tomes','original_file':src['original_file'],'original_sha256':src['sha256'],
            'source_url':src['source_url'],'source_image_url':src['icon_url'],
            'original_effect_ru':EFFECTS[p['id']-1],'original_effect_source_en':src['effect_source_en'],
            'unlock_source_en':src['unlock_source_en'],'value_context':src['value_context'],
            'effect_status':src['effect_status'],'effect_note':src['effect_note'],
            'our_sha256':digest(OUT/p['our_file']),'generation_mode':'built-in-imagegen',
            'lifecycle':'current' if p['group']=='cards' else 'candidate','is_default':p['group']=='cards','body_logical_pixels':48,'pixel_scale':4,'palette_max':24,
            'outline_policy':'Generated rim preserved; no second outline added.','rarity':None})
        save(OUT/p['data_file'],record);records.append(record)
    if not args.partial:assert len(records)==46
    make_grids(records);pages=make_sheets(records)
    css=CSS+'\n.cross-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(730px,100%),1fr));gap:18px;margin-top:24px}.ours-only .cross-grid .compare{grid-template-columns:repeat(2,minmax(0,1fr))!important}@media(max-width:600px){.cross-grid .card{padding:10px}.cross-grid .name{font-size:13px}.cross-grid .ru{font-size:12px}}'
    (OUT/'review.css').write_text(css,encoding='utf-8');(OUT/'review.js').write_text(JS,encoding='utf-8')
    for group,title in TITLES.items():
        entries=sorted([r for r in records if r['group']==group],key=lambda r:r['id'])
        links='<div class="sheets"><a href="grid.png">Сетка всех иконок</a>'+''.join(f'<a href="sheets/{p}">Лист сравнения {i+1}</a>' for i,p in enumerate(pages[group]))+'</div>'
        content=f'<h1>{title} · {len(entries)} тома</h1><p class="notice">Карты выбраны для дальнейшей работы; печати сохранены отдельно. Те же ID и эффекты оригиналов Megabonk; собственные названия EN/RU и картинки. Карты — выбранный набор. Печати сохранены как альтернативный вариант.</p>'+controls()+links+'<div class="grid">'+''.join(card([e],root='../') for e in entries)+'</div>'
        (OUT/group/'preview.html').write_text(shell(title,content,'../'),encoding='utf-8')
        for e in entries:
            content=f'<div class="detail"><h1>#{e["id"]:02d} · {esc(e["new_name_en"])}</h1>'+card([e],root='../../',detail=True)+f'<p><a href="../preview.html">Весь набор</a> · <a href="../../comparison.html">Сравнение двух наборов</a></p></div>'
            (OUT/e['entry_file']).write_text(shell(e['new_name_en'],content,'../../'),encoding='utf-8')
    entities=[];cross=[]
    for n,src in originals.items():
        variants=[r for r in records if r['id']==n]
        entity={'id':n,'asset_id':src['asset_id'],'original_key':src['original_key'],'original_name':src['original_name'],
                'source_url':src['source_url'],'original_file':src['original_file'],'original_effect_ru':EFFECTS[n-1],
                'selected_set':'tomes-cards-v2','variants':[{'set_id':r['set_id'],'variant_id':r['variant_id'],'new_name_en':r['new_name_en'],'new_name_ru':r['new_name_ru'],'our_file':r['our_file'],'data_file':r['data_file'],'entry_file':r['entry_file']} for r in variants]}
        save(OUT/'entities'/f'{n:02d}.json',entity);entities.append(entity)
        if variants:cross.append(card(variants))
    content='<h1>Оригинал → карта → печать</h1><p class="notice">Каждая строка — один том Megabonk и два его оформления. Иконка и название меняются, исходная связь с томом остаётся общей.</p>'+controls()+'<div class="cross-grid">'+''.join(cross)+'</div>'
    (OUT/'comparison.html').write_text(shell('Сравнение двух наборов томов',content),encoding='utf-8')
    content='<h1>Тома Megabonk · карты</h1><p class="notice">23 оригинальных тома, 46 новых иконок. Два самостоятельных варианта: карты, печати. Каждый связан с оригинальным названием и эффектом; основной набор пока не выбран.</p><div class="hub">'+''.join(f'<a href="{g}/preview.html"><h2>{t} · 23</h2><p>Оригиналы Megabonk → наши названия EN/RU и иконки</p><img src="{g}/grid.png" alt="{t}"></a>' for g,t in TITLES.items())+'</div><p><a href="comparison.html">Оригинал, карта и печать рядом</a> · <a href="manifest.json">Полный каталог</a> · <a href="lookup.json">Связи по оригинальным названиям</a> · <a href="catalog.csv">CSV</a></p>'
    (OUT/'index.html').write_text(shell('Тома — карты и печати',content),encoding='utf-8')
    save(OUT/'manifest.json',{'schema_version':1,'stage':'two-alternative-sets','entities_count':23,'variants_count':len(records),'selected_set':'tomes-cards-v2','sets':{g:{'set_id':'tomes-'+g+('-v2' if g=='cards' else '-v1'),'label':t,'is_default':g=='cards','preview_file':g+'/preview.html','grid_file':g+'/grid.png'} for g,t in TITLES.items()},'tomes':entities,'variants':records})
    save(OUT/'lookup.json',{'entity_category':'tomes','selected_set':'tomes-cards-v2','by_original_name':{e['original_name'].casefold():e for e in entities}})
    if records:
        with (OUT/'catalog.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    for page in OUT.rglob('*.html'):
        soup=BeautifulSoup(page.read_text(encoding='utf-8'),'html.parser')
        for tag,key in [('a','href'),('img','src'),('script','src'),('link','href')]:
            for node in soup.find_all(tag):
                parsed=urlsplit(node.get(key,''))
                if parsed.scheme or not parsed.path:continue
                target=(page.parent/unquote(parsed.path)).resolve()
                assert target.is_relative_to(OUT.resolve()) and target.is_file(),(page,node.get(key))
    for e in records:
        with Image.open(OUT/e['our_file']) as im:
            assert im.mode=='RGBA' and im.size==(256,256)
            assert im.getchannel('A').getextrema()==(0,255),e['our_file']
            colors={c[:3] for _,c in im.getcolors(256*256) if c[3]>0};assert len(colors)<=24
            box=im.getchannel('A').getbbox();assert max(box[2]-box[0],box[3]-box[1])<=192
        assert digest(OUT/e['original_file'])==e['original_sha256']
        assert read(OUT/e['data_file'])==e
    if not args.partial:
        assert len({r['variant_id'] for r in records})==46
        assert len({r['original_key'] for r in records})==23
        assert all(len(e['variants'])==2 and e['selected_set']=='tomes-cards-v2' for e in entities)
        assert len(list(OUT.rglob('*.html')))==50
    report={'originals':23,'cards':sum(r['group']=='cards' for r in records),'seals':sum(r['group']=='seals' for r in records),'variants':len(records),'unique_variant_ids':len({r['variant_id'] for r in records}),'selected_set':'tomes-cards-v2','source_hashes_verified':True,'source_ids_preserved':True,'transparent_square_pngs_verified':True,'body_size_max':192,'palette_max':24,'html_local_links_verified':True,'precision_source_conflict_preserved':True,'complete':not args.partial}
    save(OUT/'validation.json',report)
    (OUT/'README.md').write_text('''# Тома Megabonk — карты и печати

Два альтернативных набора для одних и тех же 23 томов: карты/колоды и печати. 23 актуальные карты и 23 сохранённые печати; прозрачные PNG 256×256. Восемь карт исправлены в этой версии: 5, 12, 13, 14, 15, 18, 20 и 23. Карты — выбранный набор. Печати сохранены как альтернативный вариант. index.html — общий просмотр; comparison.html — оригинал, карта и печать рядом; cards/preview.html и seals/preview.html — отдельные галереи с именами EN/RU, исходными эффектами и малыми размерами.

asset_id и original_key обозначают один оригинальный том, set_id и variant_id — конкретное оформление. Имена файлов сохраняют номера исходного каталога 01…23. В lookup.json поиск по оригинальному названию возвращает обе версии; selected_set=tomes-cards-v2 фиксирует выбор карт. Например, Agility Tome связан с Fleet Card / Карта прыти и Fleet Seal / Печать прыти.

originals/ содержит оригинальные PNG без изменения байтов. cards/ и seals/ содержат отдельные icons_256, data, entries, sheets, raw и prompts. Все генерации выполнены встроенным imagegen по одной иконке; сведения об исходниках — raw/NN.json. Рамки, подписи, номера и листы собраны кодом. Размер тела нормализован до 48 логических пикселей с масштабом ×4; палитра ограничена 24 цветами; вторая обводка не добавлялась.

Сохранены эффекты оригиналов из Megabonk.org, не подтверждение реализации механик. Значения относятся к базовому Common-улучшению на один уровень. У Precision Tome таблица сайта указывает +7% Crit Chance, карточка — +2%; оба значения и пометка расхождения сохранены. Цвета оригинальных обложек служили палитрой, а не назначением редкости.

Сборка: python tools/build_tome_cards_refined.py. Проверяются 23 исходных ID, 46 вариантов, хеши оригиналов, прозрачность, размеры, палитры, соответствия и локальные ссылки. HTML проверен статически; управление браузером для file:// недоступно.
''',encoding='utf-8')
    if not args.partial:
        archive=ROOT/'output/tomes-cards-refined.zip';archive.parent.mkdir(exist_ok=True)
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for file in OUT.rglob('*'):
                if file.is_file():z.write(file,file.relative_to(OUT))
    print(json.dumps(report))


if __name__=='__main__':main()
