"""Build the separate matte 2D experiment without replacing the main set."""
from pathlib import Path
import json, html, hashlib, zipfile
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
MAIN=ROOT/'assets/items/revision-simple'
OUT=ROOT/'assets/items/flat-2d-attempt'
IDS=[1,2,5,6,7,8,9,12,13,15,16,17,20,23,27,29,38]
SMALLER={1,2,5,6,7,8,9,12,13,15,16}
LATEST=[1,2,7,8,12,13,16,38]


def sprite(path,color,logical=48,palette=16):
    im=Image.open(path).convert('RGBA')
    assert im.getchannel('A').getextrema()[0]==0
    box=im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
    im=im.crop(box)
    scale=logical/max(im.size)
    small=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.BOX)
    alpha=small.getchannel('A').point(lambda a:255 if a>=128 else 0)
    rgb=small.convert('RGB').quantize(colors=palette,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGBA')
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
        image=sprite(raw,e['outline_hex'],45 if item_id in SMALLER else 48,24 if item_id==38 else 16)
        target=OUT/'icons_256'/f'{item_id:02d}.png';image.save(target)
        assert image.size==(256,256) and image.mode=='RGBA'
        assert image.getchannel('A').getextrema()==(0,255)
        box=image.getchannel('A').getbbox()
        assert min(box)>0 and max(box)<256,item_id
        longest=max(box[2]-box[0],box[3]-box[1])
        assert 176<=longest<=186 if item_id in SMALLER else 188<=longest<=198,(item_id,longest)
        assert len(image.convert('RGB').getcolors(65536))<=(26 if item_id==38 else 18),item_id
        assert (OUT/'prompts'/f'{item_id:02d}.txt').is_file()
        assert (OUT/'raw'/f'{item_id:02d}.json').is_file()
        if item_id in LATEST:
            receipt=json.loads((OUT/'raw'/f'{item_id:02d}.json').read_text(encoding='utf-8'))
            assert receipt['pass']==3,item_id

        expected_before=json.loads((OUT/'before-review-pass/baseline-main.json').read_text(encoding='utf-8')) if item_id in (1,2,7,8,13,16,38) else old_hashes
        assert hashlib.sha256((OUT/'before'/f'{item_id:02d}.png').read_bytes()).hexdigest()==expected_before[str(item_id)]
        e['file']=f'icons_256/{item_id:02d}.png'
        e['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
        e['experiment']='matte_2d_no_specular'
        e['body_extent']=180 if item_id in SMALLER else 192
        e['body_palette_max']=24 if item_id==38 else 16
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
    latest_trial=json.loads((OUT/'before-review-pass/baseline-trial.json').read_text(encoding='utf-8'))
    for e in completed:
        if str(e['id']) in latest_trial and e['id']!=12:assert e['sha256']==latest_trial[str(e['id'])],e['id']
    patch=np.asarray(Image.open(OUT/'icons_256/12.png').convert('RGBA'))
    assert not np.any((patch[:,:,2].astype(float)>patch[:,:,0]*1.10)&(patch[:,:,1].astype(float)>patch[:,:,0]*1.05)&(patch[:,:,3]>0)),'cyan remains in item 12'
    (OUT/'catalog.json').write_text(json.dumps(completed,ensure_ascii=False,indent=2),encoding='utf-8')
    font=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',28)
    label_font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',20)
    def comparison_board(ids,path,latest=False):
        cols=3 if len(ids)>10 else 2
        rows=(len(ids)+cols-1)//cols
        size=1600
        board=Image.new('RGB',(size,size),'black');draw=ImageDraw.Draw(board)
        row_height=(size-120)//rows
        draw.text((40,32),'Матовая 2D-проба: текущие правки' if latest else f'Матовая 2D-проба: все {len(IDS)} предметов',font=font,fill='white')
        for n,item_id in enumerate(ids):
            e=next(e for e in completed if e['id']==item_id)
            x=(n%cols)*(size//cols);y=100+(n//cols)*row_height
            im_size=256 if rows<=4 else 160
            old_x=x+(40 if cols==2 else 28);new_x=x+(340 if cols==2 else 244)
            draw.text((x+16,y),f'#{item_id}',font=font,fill='white')
            before_path=OUT/'before-review-pass/icons_256/12.png' if latest and item_id==12 else OUT/'before'/f'{item_id:02d}.png'
            before=Image.open(before_path).convert('RGBA').resize((im_size,im_size),Image.Resampling.NEAREST)
            after=Image.open(OUT/e['file']).convert('RGBA').resize((im_size,im_size),Image.Resampling.NEAREST)
            for xx,im,label in ((old_x,before,'Было'),(new_x,after,'2D-проба')):
                draw.text((xx,y+34),label,font=label_font,fill='#aaa')
                board.paste(im,(xx,y+66),im)
                draw.rectangle((xx,y+66,xx+im_size-1,y+66+im_size-1),outline='#555')
            for xx,sz,dy in ((x+(660 if cols==2 else 448),64,100),(x+(676 if cols==2 else 464),32,210 if rows<=3 else 188)):
                tiny=Image.open(OUT/e['file']).convert('RGBA').resize((sz,sz),Image.Resampling.NEAREST)
                draw.text((xx,y+dy-24),f'{sz}px',font=label_font,fill='#aaa');board.paste(tiny,(xx,y+dy),tiny)
            draw.line((x+16,y+row_height-12,x+(size//cols)-16,y+row_height-12),fill='#222')
        board.save(path)
    comparison_board(IDS,OUT/'flat-comparison.png')
    comparison_board(LATEST,OUT/'pass-03-comparison.png',latest=True)
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
    page='<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Отдельная 2D-проба: 17 предметов</title><style>body{background:#111;color:#ddd;font:16px system-ui;margin:24px}a{color:#8cf}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:20px}article{border:1px solid #555;background:#000;padding:12px}h2{font-size:18px}.pair{display:flex;gap:12px}figure{margin:0;text-align:center}.pair img{width:192px;height:192px}img{object-fit:contain;image-rendering:pixelated}.sizes{display:flex;gap:24px;align-items:center;padding:20px}</style><h1>Отдельная 2D-проба</h1><p>Семнадцать предметов: 1, 2, 5, 6, 7, 8, 9, 12, 13, 15, 16, 17, 20, 23, 27, 29, 38. Последние правки: №1, 2, 7, 8, 13, 16; №38 слегка, у №12 убрано голубое пятно. Меньше объёмного освещения, без глянцевых бликов. Основной набор сохраняет свои иконки.</p><p><a href="pass-03-comparison.png">Последние восемь правок</a> · <a href="flat-comparison.png">Все семнадцать проб</a> · <a href="context-grid-85.png">Семнадцать проб в общей сетке 85</a> · <a href="style-references-clean.png">Референсы стиля</a></p><div class="grid">'+cards+'</div>'
    (OUT/'preview.html').write_text(page,encoding='utf-8')
    report={'trial_ids':IDS,'count':len(IDS),'main_replacements':[],'main_clarity_fix_ids':[1,2],'other_main_83_byte_identical':True,'rgba_size':[256,256],'palette_body_max':24,'standard_palette_body_max':16,'mild_palette_body_max':24,'rarity_edge_width':3,'transparent_margins':True,'prompt_and_receipt_count':len(IDS),'smaller_body_ids':sorted(SMALLER),'smaller_body_extent':180,'original_body_extent':192,'main_85_byte_identical_to_pass_02_start':True,'previous_9_trial_pngs_byte_identical':True,'latest_modified_ids':LATEST,'cyan_patch_removed_id':12,'mild_flattening_id':38,'method':'builtin-imagegen edits; coded normalization, one colored edge and layout'}
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    archive=ROOT/'output/items-flat-2d-attempt.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path in OUT.rglob('*'):
            if path.is_file() and 'raw' not in path.relative_to(OUT).parts:z.write(path,path.relative_to(OUT))
    print(json.dumps(report,ensure_ascii=True))


if __name__=='__main__':main()
