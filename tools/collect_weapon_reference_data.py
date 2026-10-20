"""Fetch the Megabonk weapon reference matched to the project's stable 1..30 IDs."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from bs4 import BeautifulSoup
from PIL import Image
import json,hashlib,re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/weapon-icons'
INDEX='https://megabonk.org/database/weapons/'

def fetch(url):
    return urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read()

def normalized(name):
    return re.sub('[^a-z0-9]','',name.lower())

def main():
    existing=json.loads((OUT/'catalog.json').read_text(encoding='utf-8'))
    soup=BeautifulSoup(fetch(INDEX),'html.parser')
    by_name={}
    for row in soup.select('table tr'):
        cells=row.find_all('td')
        if len(cells)<3:continue
        link=cells[0].find('a',href=True)
        if not link:continue
        name=re.sub(r'^[^A-Za-z]+','',link.get_text(' ',strip=True))
        im=cells[0].find('img')
        by_name[normalized(name)]={'name':name,'page_url':urljoin(INDEX,link['href']),'effect_source_en':cells[1].get_text(' ',strip=True),'unlock_source_en':cells[2].get_text(' ',strip=True),'icon_url':urljoin(INDEX,im['src']) if im else None}
    (OUT/'megabonk-originals').mkdir(exist_ok=True)
    def collect(e):
        source=by_name[normalized(e['megabonk'])]
        if not source['icon_url']:
            page=BeautifulSoup(fetch(source['page_url']),'html.parser')
            icon=next(i for i in page.find_all('img') if normalized(e['megabonk']) in normalized(i.get('alt','')))
            source['icon_url']=urljoin(source['page_url'],icon['src'])
        slug=source['page_url'].rstrip('/').split('/')[-1]
        file=OUT/'megabonk-originals'/f'{e["id"]:02d}_{slug}.png'
        if not file.exists():file.write_bytes(fetch(source['icon_url']))
        with Image.open(file) as im:
            im.verify()
        return {**source,'id':e['id'],'slug':slug,'original_key':'megabonk:weapon:'+slug,'file':file.relative_to(OUT).as_posix(),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'index_url':INDEX}
    with ThreadPoolExecutor(max_workers=6) as pool:result=sorted(pool.map(collect,existing),key=lambda e:e['id'])
    assert len(result)==30 and len({e['original_key'] for e in result})==30
    data={'source_url':INDEX,'accessed_utc':datetime.now(timezone.utc).isoformat(),'weapons':result}
    (OUT/'weapon-research.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Downloaded and matched {len(result)} original weapon icons.')

if __name__=='__main__':main()
