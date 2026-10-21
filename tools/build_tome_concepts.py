"""Lay out five independently generated tome-family candidates for selection."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, hashlib, html

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/tomes/concepts-01'
FONT='C:/Windows/Fonts/consola.ttf'
BOLD='C:/Windows/Fonts/consolab.ttf'
OPTIONS=[
    (1,'Футляр','Тонкий / толстый; открытый / закрытый'),
    (2,'Свиток','Узкий / широкий; свёрнутый / развёрнутый'),
    (3,'Медальон','Плоский / объёмный; открытый / закрытый'),
    (4,'Мешочек','Плоский / полный; завязанный / раскрытый'),
    (5,'Картридж','Тонкий / толстый; цельный / со вставкой'),
]


def center(draw,text,y,font,color,x=0,width=1600):
    draw.text((x+(width-draw.textlength(text,font=font))/2,y),text,font=font,fill=color)


def main():
    (OUT/'icons_256').mkdir(parents=True,exist_ok=True)
    records=[]
    for n,name,variation in OPTIONS:
        source=OUT/'raw'/f'{n:02d}.png'
        with Image.open(source) as im:
            im=im.convert('RGBA')
            assert im.getchannel('A').getextrema()[0]==0,source
            bbox=im.getchannel('A').point(lambda x:255 if x>96 else 0).getbbox()
            assert bbox,source
            crop=im.crop(bbox)
            ratio=min(196/crop.width,196/crop.height)
            sprite=crop.resize((round(crop.width*ratio),round(crop.height*ratio)),Image.Resampling.NEAREST)
            canvas=Image.new('RGBA',(256,256))
            canvas.alpha_composite(sprite,((256-sprite.width)//2,(256-sprite.height)//2))
            canvas.save(OUT/'icons_256'/f'{n:02d}.png')
        records.append({'candidate_id':n,'name_ru':name,'variation_potential_ru':variation,
                        'file':f'icons_256/{n:02d}.png','raw_file':f'raw/{n:02d}.png',
                        'prompt_file':f'prompts/{n:02d}.txt','generation_mode':'built-in-imagegen',
                        'status':'candidate-not-selected','is_game_asset':False,
                        'sha256':hashlib.sha256((OUT/'icons_256'/f'{n:02d}.png').read_bytes()).hexdigest()})
    board=Image.new('RGB',(1600,1600),'black');d=ImageDraw.Draw(board)
    title=ImageFont.truetype(BOLD,40);label=ImageFont.truetype(BOLD,34);small=ImageFont.truetype(FONT,24)
    center(d,'5 основ для новых томов',45,title,'white')
    center(d,'Выбор формы · одна категория станет основой набора',105,small,'#aaa')
    positions=[(50,210),(560,210),(1070,210),(305,860),(815,860)]
    for record,(x,y) in zip(records,positions):
        d.rectangle((x,y,x+480,y+570),outline='#555',width=2)
        center(d,f'{record["candidate_id"]}. {record["name_ru"]}',y+18,label,'white',x,480)
        im=Image.open(OUT/record['file']).convert('RGBA')
        enlarged=im.resize((384,384),Image.Resampling.NEAREST)
        board.paste(enlarged,(x+48,y+65),enlarged)
        center(d,'64 px                  32 px',y+445,small,'#aaa',x,480)
        for size,cx in ((64,x+141),(32,x+344)):
            icon=im.resize((size,size),Image.Resampling.NEAREST)
            board.paste(icon,(cx-size//2,y+485+(64-size)//2),icon)
    board.save(OUT/'comparison.png')
    cards=[]
    for r in records:
        cards.append(f'<article><h2>{r["candidate_id"]}. {html.escape(r["name_ru"])}</h2><img class="large" src="{r["file"]}" alt="{html.escape(r["name_ru"])}"><p>{html.escape(r["variation_potential_ru"])}</p><div class="small"><span>64 px</span><img src="{r["file"]}" width="64" height="64"><span>32 px</span><img src="{r["file"]}" width="32" height="32"></div></article>')
    (OUT/'preview.html').write_text('''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>5 основ для томов</title><style>body{margin:0;background:#080808;color:#eee;font:16px/1.5 system-ui}main{max-width:1550px;margin:auto;padding:24px}h1{font-size:30px}h2{font-size:22px}a{color:#ddd}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}article{background:#101010;border:1px solid #555;padding:20px;text-align:center}.large{width:100%;max-width:320px;aspect-ratio:1;object-fit:contain;image-rendering:pixelated}.small{display:flex;align-items:center;justify-content:center;gap:15px;height:80px}.small img{image-rendering:pixelated}p{color:#aaa}</style><main><h1>5 основ для новых томов</h1><p>Пять самостоятельных категорий. Эскизы для выбора основы; соответствия конкретным томам пока не назначены.</p><p><a href="comparison.png">Общий лист</a> · <a href="../preview.html">Оригиналы Megabonk</a></p><div class="grid">'''+''.join(cards)+'</div></main></html>',encoding='utf-8')
    (OUT/'catalog.json').write_text(json.dumps({'stage':'family-selection','count':5,'selected_candidate':None,'candidates':records},ensure_ascii=False,indent=2),encoding='utf-8')
    assert all((OUT/r['prompt_file']).is_file() for r in records)
    print('Five transparent candidates and square comparison saved; no existing item or weapon replaced.')


if __name__=='__main__':main()
