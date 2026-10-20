from pathlib import Path
import json
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
base = root/'assets/items'
out = base/'style-passes'
(out/'inputs').mkdir(parents=True,exist_ok=True)
entries = json.loads((base/'catalog.json').read_text(encoding='utf-8'))['items']
groups = [(0,20),(20,40),(40,60),(60,85)]
manifest = []
for number,(start,end) in enumerate(groups,1):
    group = entries[start:end]
    columns,rows,cell = 5,(len(group)+4)//5,224
    canvas = Image.new('RGB',(columns*cell,rows*cell),'black')
    draw = ImageDraw.Draw(canvas)
    for i,e in enumerate(group):
        x,y = (i%columns)*cell,(i//columns)*cell
        draw.rectangle((x+6,y+6,x+cell-7,y+cell-7),outline='#737373',width=2)
        im = Image.open(base/e['file']).convert('RGBA')
        scale = 160/max(im.size)
        im = im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
        canvas.paste(im,(x+(cell-im.width)//2,y+(cell-im.height)//2),im)
    filename = f'originals-pass-{number:02d}.png'
    canvas.save(out/'inputs'/filename)
    manifest.append({'pass':number,'start_id':start+1,'end_id':end,'count':len(group),'columns':5,'rows':rows,'input':f'inputs/{filename}','items':group})
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Prepared four source sheets: 20 + 20 + 20 + 25 = 85')
