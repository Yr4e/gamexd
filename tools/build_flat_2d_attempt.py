"""Build the separate matte 2D experiment without replacing the main set."""
from pathlib import Path
import json, html, hashlib, zipfile
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
MAIN=ROOT/'assets/items/revision-simple'
OUT=ROOT/'assets/items/flat-2d-attempt'
IDS=[5,6,9,12,15,17,20,23,27,29]
SMALLER={5,6,9,12,15}
LATEST=[5,6,9,12,15,23]


def sprite(path,color,logical=48):
    im=Image.open(path).convert('RGBA')
    assert im.getchannel('A').getextrema()[0]==0
    box=im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
    im=im.crop(box)
    scale=logical/max(im.size)
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
        original=entries[item_id-1]
        e={k:original[k] for k in ('id','original_name','new_name_en','new_name_ru','effect_summary_ru','page_url','outline_hex','outline_color_name')}
        image=sprite(raw,e['outline_hex'],45 if item_id in SMALLER else 48)
        target=OUT/'icons_256'/f'{item_id:02d}.png';image.save(target)
        assert image.size==(256,256) and image.mode=='RGBA'
        assert image.getchannel('A').getextrema()==(0,255)
        box=image.getchannel('A').getbbox()
        assert min(box)>0 and max(box)<256,item_id
        longest=max(box[2]-box[0],box[3]-box[1])
        assert 176<=longest<=186 if item_id in SMALLER else 188<=longest<=198,(item_id,longest)
        assert len(image.convert('RGB').getcolors(65536))<=18,item_id
        assert (OUT/'prompts'/f'{item_id:02d}.txt').is_file()
        assert (OUT/'raw'/f'{item_id:02d}.json').is_file()
        if item_id in LATEST:
            receipt=json.loads((OUT/'raw'/f'{item_id:02d}.json').read_text(encoding='utf-8'))
            assert receipt['pass']==2,item_id
            if item_id==23:
                assert receipt['intent']=='generate-from-original-reference'
                assert (OUT/'references/23-original.png').read_bytes()==(ROOT/'assets/items/originals/23_bobs-light.png').read_bytes()
        assert hashlib.sha256((OUT/'before'/f'{item_id:02d}.png').read_bytes()).hexdigest()==old_hashes[str(item_id)]
        e['file']=f'icons_256/{item_id:02d}.png'
        e['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
        e['experiment']='matte_2d_no_specular'
        e['body_extent']=180 if item_id in SMALLER else 192
        if item_id==23:e['reference_file']='references/23-original.png'
        completed.append(e)
    assert len(completed)==len(IDS),'Need all ten generated assets'
    latest_main=json.loads((OUT/'before-second-pass/baseline-main.json').read_text(encoding='utf-8'))
    for e in entries:
        assert hashlib.sha256((MAIN/e['file']).read_bytes()).hexdigest()==latest_main[str(e['id'])],e['id']
    old_trial=json.loads((OUT/'before-second-pass/baseline-trial.json').read_text(encoding='utf-8'))
    for e in completed:
        if e['id'] in (17,20,27,29):assert e['sha256']==old_trial[str(e['id'])],e['id']
    assert completed[IDS.index(23)]['sha256']!=old_trial['23']
    (OUT/'catalog.json').write_text(json.dumps(completed,ensure_ascii=False,indent=2),encoding='utf-8')
    font=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',28)
    label_font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',20)
    def comparison_board(ids,path,latest=False):
        rows=(len(ids)+1)//2
        size=1600
        board=Image.new('RGB',(size,size),'black');draw=ImageDraw.Draw(board)
        row_height=(size-120)//rows
        draw.text((40,32),'Матовая 2D-проба: текущие правки' if latest else 'Матовая 2D-проба: все 10 предметов',font=font,fill='white')
        for n,item_id in enumerate(ids):
            e=next(e for e in completed if e['id']==item_id)
            x=(n%2)*800;y=100+(n//2)*row_height
            im_size=256 if rows<=3 else 192
            old_x=x+40;new_x=x+340
            draw.text((x+16,y),f'#{item_id}',font=font,fill='white')
            before_path=OUT/'before-second-pass/icons_256/23.png' if latest and item_id==23 else OUT/'before'/f'{item_id:02d}.png'
            before=Image.open(before_path).convert('RGBA').resize((im_size,im_size),Image.Resampling.NEAREST)
            after=Image.open(OUT/e['file']).convert('RGBA').resize((im_size,im_size),Image.Resampling.NEAREST)
            for xx,im,label in ((old_x,before,'Было'),(new_x,after,'2D-проба')):
                draw.text((xx,y+34),label,font=label_font,fill='#aaa')
                board.paste(im,(xx,y+66),im)
                draw.rectangle((xx,y+66,xx+im_size-1,y+66+im_size-1),outline='#555')
            for xx,sz,dy in ((x+660,64,100),(x+676,32,210 if rows<=3 else 188)):
                tiny=Image.open(OUT/e['file']).convert('RGBA').resize((sz,sz),Image.Resampling.NEAREST)
                draw.text((xx,y+dy-24),f'{sz}px',font=label_font,fill='#aaa');board.paste(tiny,(xx,y+dy),tiny)
            draw.line((x+16,y+row_height-12,x+784,y+row_height-12),fill='#222')
        board.save(path)
    comparison_board(IDS,OUT/'flat-comparison.png')
    comparison_board(LATEST,OUT/'pass-02-comparison.png',latest=True)
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
    page='<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Отдельная 2D-проба: 10 предметов</title><style>body{background:#111;color:#ddd;font:16px system-ui;margin:24px}a{color:#8cf}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:20px}article{border:1px solid #555;background:#000;padding:12px}h2{font-size:18px}.pair{display:flex;gap:12px}figure{margin:0;text-align:center}.pair img{width:192px;height:192px}img{object-fit:contain;image-rendering:pixelated}.sizes{display:flex;gap:24px;align-items:center;padding:20px}</style><h1>Отдельная 2D-проба</h1><p>Десять предметов: 5, 6, 9, 12, 15, 17, 20, 23, 27, 29. Новые №5, 6, 9, 12, 15 чуть меньше; №23 заново по оригинальной лампочке Megabonk. Меньше объёмного освещения, без глянцевых бликов. Основной набор сохраняет свои иконки.</p><p><a href="pass-02-comparison.png">Последние шесть правок</a> · <a href="flat-comparison.png">Все десять проб</a> · <a href="context-grid-85.png">Десять проб в общей сетке 85</a> · <a href="style-references-clean.png">Референсы стиля</a></p><div class="grid">'+cards+'</div>'
    (OUT/'preview.html').write_text(page,encoding='utf-8')
    report={'trial_ids':IDS,'count':len(IDS),'main_replacements':[],'main_clarity_fix_ids':[1,2],'other_main_83_byte_identical':True,'rgba_size':[256,256],'palette_body_max':16,'rarity_edge_width':3,'transparent_margins':True,'prompt_and_receipt_count':len(IDS),'smaller_body_ids':sorted(SMALLER),'smaller_body_extent':180,'original_body_extent':192,'main_85_byte_identical_to_pass_02_start':True,'previous_4_trial_pngs_byte_identical':True,'latest_redrawn_id':23,'method':'builtin-imagegen edits; coded normalization, one colored edge and layout'}
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    archive=ROOT/'output/items-flat-2d-attempt.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path in OUT.rglob('*'):
            if path.is_file() and 'raw' not in path.relative_to(OUT).parts:z.write(path,path.relative_to(OUT))
    print(json.dumps(report,ensure_ascii=True))


if __name__=='__main__':main()
