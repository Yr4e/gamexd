"""Rearrange the four selected sheets without regenerating their artwork."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
folder = root/'assets/items/style-passes'
cell = 256
canvas = Image.new('RGB',(2560,2560),'black')
index = 0
for number,rows in [(1,4),(2,4),(3,4),(4,5)]:
    source = Image.open(folder/f'pass-{number:02d}.png').convert('RGB')
    for row in range(rows):
        for column in range(5):
            box = (round(column*source.width/5),round(row*source.height/rows),round((column+1)*source.width/5),round((row+1)*source.height/rows))
            tile = source.crop(box).resize((cell,cell),Image.Resampling.NEAREST)
            canvas.paste(tile,((index%10)*cell,128+(index//10)*cell))
            index += 1
assert index == 85
output = folder/'passes-01-04-combined.png'
canvas.save(output)
print(f'Combined {index} cells into {output} (2560x2560).')
