from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen
import csv, hashlib, json, time, sys
import numpy as np
from bs4 import BeautifulSoup
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'assets/items'
OUT=BASE/'individual-redesign'
OUTLINE_ROWS=[
 ['yellow']*10,['yellow']*10,
 ['yellow','yellow']+['pink']*8,
 ['pink']*3+['blue']*7,
 ['blue','mint','blue','blue','mint','blue','pink','blue','pink','blue'],
 ['blue','mint','pink','pink','blue','mint','blue','mint','mint','mint'],
 ['pink','blue','pink','mint','mint','blue','mint','blue','mint','pink'],
 ['blue','mint','blue','blue','mint','blue','mint','mint','mint','mint'],
 ['mint','pink','mint','mint','mint']]
COLORS={'yellow':'#FFD928','pink':'#FF239F','blue':'#1689FF','mint':'#55EDBB'}

def fetch(e):
    path=OUT/'sources'/f'{e["id"]:02d}_{e["slug"]}.html'
    if not path.exists():
        for attempt in range(3):
            try:
                with urlopen(Request(e['page_url'],headers={'User-Agent':'Mozilla/5.0'}),timeout=35) as r:
                    path.write_bytes(r.read())
                break
            except Exception:
                if attempt==2: raise
                time.sleep(attempt+1)
    soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
    effect=soup.select_one('.item-effect')
    meta=soup.select_one('meta[name="description"]')
    e['effect_source_en']=effect.get_text(' ',strip=True) if effect else meta.get('content','') if meta else ''
    e['effect_extraction']='item-effect' if effect else 'meta-description'
    # Retain the short overview as source context, not as commands.
    overview=[]
    for h in soup.find_all(['h2','h3']):
        if any(s in h.get_text(' ',strip=True).lower() for s in ['overview','how it works','how '+e['original_name'].lower()+' works']):
            p=h.find_next('p')
            if p: overview.append(p.get_text(' ',strip=True))
    e['overview_source_en']=' '.join(overview)[:1800]
    return e

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    for p in ['sources','crops','raw','icons_256','prompts']:(OUT/p).mkdir(parents=True,exist_ok=True)
    entries=json.loads((BASE/'catalog.json').read_text(encoding='utf-8'))['items']
    source=Image.open(BASE/'style-passes/passes-01-04-combined.png').convert('RGB')
    outline=[c for row in OUTLINE_ROWS for c in row]
    for e,color in zip(entries,outline):
        e['outline_color_name']=color
        e['outline_hex']=COLORS[color]
        col,row=(e['id']-1)%10,(e['id']-1)//10
        # Use the unnumbered source, inside the gray frame.
        crop=source.crop((col*256+14,128+row*256+14,(col+1)*256-14,128+(row+1)*256-14))
        crop.save(OUT/'crops'/f'{e["id"]:02d}_{e["slug"]}.png')
        e['crop_file']=f'crops/{e["id"]:02d}_{e["slug"]}.png'
        e['status']='researched'
    errors=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures={pool.submit(fetch,e):e for e in entries}
        for f in as_completed(futures):
            try:f.result()
            except Exception as ex:errors.append(f'{futures[f]["id"]}: {ex}')
    (OUT/'research.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Researched:',len(entries),'Errors:',errors)
    for e in entries: print(f'{e["id"]:02d} | {e["original_name"]} | {e["outline_color_name"]} | {e["effect_source_en"]}')
    if errors:raise RuntimeError(errors)

if __name__=='__main__':main()
