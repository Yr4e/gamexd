"""Collect original Megabonk tomes and build a portable reference gallery."""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlsplit, unquote
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
import csv, hashlib, html, json, io

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/tomes'
INDEX = 'https://megabonk.org/database/tomes/'
RU = [
    'Скорость передвижения', 'Скорость атаки', 'Множитель урона',
    'Уклонение', 'Получение золота', 'Максимальное здоровье', 'Отбрасывание',
    'Шанс критического удара', 'Скорость снарядов', 'Восстановление здоровья',
    'Щит', 'Получение серебра', 'Размер атак', 'Броня', 'Радиус подбора',
    'Кража жизни', 'Случайное улучшение характеристики', 'Сложность',
    'Длительность эффектов', 'Удача', 'Количество снарядов',
    'Ответный урон шипами', 'Получение опыта',
]


def fetch(url):
    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40) as response:
        return response.read()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    for directory in ('originals', 'data', 'sources'):
        (OUT / directory).mkdir(parents=True, exist_ok=True)
    raw = fetch(INDEX)
    (OUT / 'sources/index.html').write_bytes(raw)
    soup = BeautifulSoup(raw, 'html.parser')
    entries = []
    for row in soup.select('table tr'):
        cells = row.find_all('td')
        if len(cells) < 4:
            continue
        link = cells[0].find('a', href=True)
        image = cells[0].find('img')
        assert link and image
        n = len(entries) + 1
        name = link.get_text(' ', strip=True)
        page = urljoin(INDEX, link['href'])
        slug = page.rstrip('/').split('/')[-1]
        card_image = soup.find('img', alt=name)
        card = card_image.find_parent('a') if card_image else None
        stat = card.select_one('.tome-stat') if card else None
        description = card.select_one('.tome-description') if card else None
        note = ''
        if name == 'Precision Tome':
            note = 'На одной странице источника значения расходятся: таблица указывает +7% Crit Chance, карточка — +2%. Оба исходных текста сохранены; значение не считается подтверждённым.'
        entries.append({
            'id': n, 'asset_id': f'tome_{n:02d}', 'original_key': 'megabonk:tome:' + slug,
            'original_name': name, 'slug': slug, 'category': 'tomes',
            'source_url': page, 'index_url': INDEX, 'icon_url': urljoin(INDEX, image['src']),
            'original_file': f'originals/{n:02d}_{slug}.png', 'data_file': f'data/{n:02d}.json',
            'effect_source_en': cells[1].get_text(' ', strip=True), 'effect_label_ru': RU[n - 1],
            'unlock_source_en': cells[2].get_text(' ', strip=True),
            'build_fit_source_en': cells[3].get_text(' ', strip=True),
            'card_stat_source_en': stat.get_text(' ', strip=True) if stat else '',
            'description_source_en': description.get_text(' ', strip=True) if description else '',
            'value_context': 'Base Common upgrade for one Tome level, as stated by the source table; higher rarity can change the value.',
            'effect_status': 'conflicting' if note else 'source_description', 'effect_note': note,
            'rarity': None, 'rarity_note': 'Оригинальная иконка справочника; цвет обложки не назначен редкостью.',
            'new_name_en': None, 'new_name_ru': None, 'our_file': None,
            'stage': 'original-reference',
        })
    assert len(entries) == 23
    previous = OUT / 'catalog.json'
    if previous.exists():
        old = json.loads(previous.read_text(encoding='utf-8'))['tomes']
        assert [(e['id'], e['original_key']) for e in old] == [(e['id'], e['original_key']) for e in entries]

    def download(e):
        image_path = OUT / e['original_file']
        data = image_path.read_bytes() if image_path.exists() else fetch(e['icon_url'])
        with Image.open(io.BytesIO(data)) as im:
            assert im.format == 'PNG'
            e.update({'width': im.width, 'height': im.height, 'format': im.format})
            im.verify()
        image_path.write_bytes(data)
        e['sha256'] = hashlib.sha256(data).hexdigest()
        save(OUT / e['data_file'], e)
        return e

    with ThreadPoolExecutor(max_workers=6) as pool:
        entries = list(pool.map(download, entries))
    assert len({e['original_key'] for e in entries}) == 23
    catalog = {'schema_version': 1, 'stage': 'original-reference', 'source_url': INDEX,
               'accessed_utc': datetime.now(timezone.utc).isoformat(), 'count': 23, 'tomes': entries}
    save(OUT / 'catalog.json', catalog)
    save(OUT / 'lookup.json', {e['original_name'].casefold(): {'asset_id': e['asset_id'], 'original_key': e['original_key'], 'data_file': e['data_file']} for e in entries})
    with (OUT / 'catalog.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(entries[0]))
        writer.writeheader()
        writer.writerows(entries)

    board = Image.new('RGB', (1600, 1600), 'black')
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype('C:/Windows/Fonts/consolab.ttf', 28)
    for index, e in enumerate(entries):
        x = 80 + (index % 5) * 288
        y = 80 + (index // 5) * 288
        with Image.open(OUT / e['original_file']) as original:
            im = original.convert('RGBA')
            ratio = min(224 / im.width, 224 / im.height)
            im = im.resize((round(im.width * ratio), round(im.height * ratio)), Image.Resampling.NEAREST)
            board.paste(im, (x + (272 - im.width) // 2, y + (272 - im.height) // 2), im)
        draw.rectangle((x, y, x + 271, y + 271), outline='#666666', width=2)
        draw.text((x + 9, y + 7), str(e['id']), fill='white', font=font, stroke_width=2, stroke_fill='black')
    board.save(OUT / 'originals-grid.png')
    esc = html.escape
    cards = []
    for e in entries:
        note = f'<p class="note">{esc(e["effect_note"])}</p>' if e['effect_note'] else ''
        cards.append(f'''<article data-search="{esc((e['original_name']+' '+e['effect_label_ru']).casefold())}" data-id="{e['id']}">
<div class="icon"><span class="number">{e['id']}</span><img src="{e['original_file']}" alt="{esc(e['original_name'])}"></div>
<h2>{esc(e['original_name'])}</h2><p>{esc(e['effect_label_ru'])}</p><p class="value">{esc(e['effect_source_en'])}</p>
<p class="muted">{esc(e['unlock_source_en'])}</p>{note}<div class="links"><a href="{e['source_url']}">Megabonk</a><a href="{e['original_file']}" download>PNG</a><a href="{e['data_file']}">Данные</a></div></article>''')
    page = '''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Тома Megabonk — 23 оригинала</title><style>
*{box-sizing:border-box}body{margin:0;background:#080808;color:#eee;font:16px/1.5 system-ui}main{max-width:1500px;margin:auto;padding:28px}a{color:#ddd}h1{font-size:30px}h2{font-size:18px;margin-bottom:4px}.muted{color:#999;font-size:14px}.note{color:#ddd;border-left:2px solid #888;padding-left:10px;font-size:14px}nav,.links{display:flex;flex-wrap:wrap;gap:18px}.tools{display:flex;gap:16px;margin:24px 0;align-items:center;flex-wrap:wrap}input,select{font:inherit;background:#151515;color:#eee;border:1px solid #666;padding:9px}input{flex:1;min-width:200px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:18px}article{padding:16px;border:1px solid #444;background:#101010}.icon{position:relative;display:grid;place-items:center;width:100%;aspect-ratio:1;background:#000;border:1px solid #666}.icon img{width:var(--size,128px);height:var(--size,128px);max-width:90%;object-fit:contain;image-rendering:pixelated}.number{position:absolute;top:5px;left:8px;font-weight:700}.value{color:#eee}.links{font-size:14px;margin-top:18px}.hidden{display:none}@media(max-width:600px){main{padding:16px}}
</style><main><h1>Тома Megabonk · 23 оригинала</h1><p class="muted">Оригинальные иконки, названия и эффекты. Первый этап перед созданием наших версий.</p>
<nav><a href="originals-grid.png">Общая сетка</a><a href="catalog.json">Каталог JSON</a><a href="catalog.csv">Каталог CSV</a><a href="https://megabonk.org/database/tomes/">Источник</a></nav>
<p class="muted">Значения в таблице источника относятся к одному уровню тома обычной редкости. Редкость улучшения может менять величину бонуса. Цвета обложек сохранены как в оригиналах.</p>
<div class="tools"><input id="search" placeholder="Номер, название или характеристика" aria-label="Поиск"><label>Размер <select id="size"><option>32</option><option>64</option><option selected>128</option><option>192</option></select></label></div><p id="count"></p><div class="grid">''' + ''.join(cards) + '''</div></main>
<script src="preview.js"></script></html>'''
    (OUT / 'preview.html').write_text(page, encoding='utf-8')
    (OUT / 'preview.js').write_text('''const cards=[...document.querySelectorAll('article')];const search=document.querySelector('#search');function filter(){const q=search.value.trim().toLocaleLowerCase();let count=0;for(const card of cards){const ok=/^#?\\d+$/.test(q)?Number(card.dataset.id)===Number(q.replace('#','')):card.dataset.search.includes(q);card.classList.toggle('hidden',!ok);if(ok)count++;}document.querySelector('#count').textContent=`Показано ${count} из ${cards.length}`;}search.addEventListener('input',filter);document.querySelector('#size').addEventListener('change',e=>document.documentElement.style.setProperty('--size',e.target.value+'px'));filter();''', encoding='utf-8')
    (OUT / 'README.md').write_text('''# Тома Megabonk — оригиналы

23 оригинальные иконки и стабильные соответствия tome_01…tome_23. Этап: original-reference. Наши названия и изображения пока не назначены. preview.html — галерея, originals-grid.png — квадратная нумерованная сетка без названий, originals/ — скачанные PNG без изменения байтов. В JSON/CSV сохранены исходные эффекты, условия открытия, ссылки и хеши.

Значения из таблицы относятся к базовому улучшению Common на один уровень. У Precision Tome источник противоречит себе: +7% в таблице и +2% в карточке. Оба текста сохранены с пометкой conflicting. Точная копия страницы источника находится в sources/index.html. Числовые значения сохранены как сведения сайта, а не подтверждённые параметры реализации игры.

Цвет обложки не назначен редкостью автоматически. Новые варианты будут связаны с original_key, а оригинальные изображения останутся отдельными референсами. Сборка: python tools/build_tome_references.py.
''', encoding='utf-8')
    parsed = BeautifulSoup(page, 'html.parser')
    assert len(parsed.select('article')) == 23
    for selector, attr in [('a', 'href'), ('img', 'src'), ('script', 'src')]:
        for tag in parsed.select(selector):
            url = urlsplit(tag[attr])
            if not url.scheme:
                assert (OUT / unquote(url.path)).is_file(), tag[attr]
    for e in entries:
        assert hashlib.sha256((OUT / e['original_file']).read_bytes()).hexdigest() == e['sha256']
        assert json.loads((OUT / e['data_file']).read_text(encoding='utf-8')) == e
    report = {'count': 23, 'unique_ids': 23, 'unique_original_keys': 23, 'png_hashes_verified': True,
              'png_bytes_unchanged': True, 'local_links_verified': True, 'grid_size': [1600,1600],
              'source_conflicts': ['Precision Tome'], 'stage': 'original-reference', 'new_icons_created': 0}
    save(OUT / 'validation.json', report)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
