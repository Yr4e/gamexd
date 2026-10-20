"""Download original site item images and arrange them without redrawing."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import csv
import hashlib
import html
import json
import math
import time

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'assets/items'
URL = 'https://megabonk.org/database/items/'

class ItemsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.items = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and 'item-card' in a.get('class','').split():
            self.current = {'slug':a['href'].strip('/').split('/')[-1], 'rarity':a.get('data-rarity',''), 'page_url':urljoin(URL,a['href'])}
        if tag == 'img' and self.current is not None:
            self.current.update(original_name=a['alt'], icon_url=urljoin(URL,a['src']))

    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            if 'icon_url' in self.current:
                self.items.append(self.current)
            self.current = None

def get(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (item reference collection)'}),timeout=30) as response:
                return response.read()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt+1)

def download(entry):
    path = OUT/entry['file']
    if not path.exists():
        path.write_bytes(get(entry['icon_url']))
    with Image.open(path) as image:
        image.load()
        entry.update(width=image.width,height=image.height,format=image.format)
    entry['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    return entry

def main():
    (OUT/'originals').mkdir(parents=True,exist_ok=True)
    snapshot = OUT/'source-page.html'
    if not snapshot.exists():
        cached = ROOT/'output/megabonk-items-page.html'
        snapshot.write_bytes(cached.read_bytes() if cached.exists() else get(URL))
    parser = ItemsParser()
    parser.feed(snapshot.read_text(encoding='utf-8-sig'))
    entries = parser.items
    assert len(entries) == 85, f'Expected source list of 85, got {len(entries)}'
    assert len({e['slug'] for e in entries}) == len(entries)
    for index,e in enumerate(entries,1):
        e['id'] = index
        e['file'] = f'originals/{index:02d}_{e["slug"]}.png'
    failures = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(download,e):e for e in entries}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as error:
                failures.append(f'{futures[future]["original_name"]}: {error}')
    if failures:
        raise RuntimeError('\n'.join(failures))
    (OUT/'catalog.json').write_text(json.dumps({'source_url':URL,'collected_utc':datetime.now(timezone.utc).isoformat(),'count':len(entries),'items':entries},ensure_ascii=False,indent=2),encoding='utf-8')
    with (OUT/'catalog.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer = csv.DictWriter(handle,fieldnames=['id','original_name','slug','rarity','file','icon_url','page_url','width','height','format','sha256'])
        writer.writeheader()
        writer.writerows(entries)
    canvas = Image.new('RGB',(1440,1440),'black')
    draw = ImageDraw.Draw(canvas)
    columns, cell, gap = 10,128,12
    rows = math.ceil(len(entries)/columns)
    origin_x = (1440-(columns*cell+(columns-1)*gap))//2
    origin_y = (1440-(rows*cell+(rows-1)*gap))//2
    for offset, entry in enumerate(entries):
        x = origin_x+(offset%columns)*(cell+gap)
        y = origin_y+(offset//columns)*(cell+gap)
        draw.rectangle((x,y,x+cell-1,y+cell-1),outline=(115,115,115),width=2)
        image = Image.open(OUT/entry['file']).convert('RGBA')
        scale = max(1,int(96/max(image.size))) if max(image.size)<=96 else 96/max(image.size)
        image = image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.NEAREST)
        canvas.paste(image,(x+(cell-image.width)//2,y+(cell-image.height)//2),image)
    canvas.save(OUT/'items-grid.png')
    cards = ''.join(f'<div><img src="{e["file"]}" alt="{html.escape(e["original_name"],quote=True)}" loading="lazy"></div>' for e in entries)
    (OUT/'preview.html').write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Megabonk — оригинальные предметы</title><style>html,body{background:#000;margin:0}.grid{display:grid;grid-template-columns:repeat(10,128px);gap:12px;padding:24px;width:max-content}.grid>div{box-sizing:border-box;width:128px;height:128px;border:2px solid #737373;display:flex;align-items:center;justify-content:center}img{width:96px;height:96px;object-fit:contain;image-rendering:pixelated}@media(max-width:900px){.grid{grid-template-columns:repeat(6,96px);gap:8px;padding:16px}.grid>div{width:96px;height:96px}img{width:72px;height:72px}}</style><div class="grid">'+cards+'</div></html>',encoding='utf-8')
    print(f'Validated {len(entries)} original images; grid: 1440x1440, 10 columns, no text.')
    print('Rarities: '+', '.join(f'{r}={sum(e["rarity"]==r for e in entries)}' for r in ['Legendary','Epic','Rare','Common']))
    print('Original sizes: '+', '.join(sorted({f'{e["width"]}x{e["height"]}' for e in entries})))

if __name__ == '__main__':
    main()
