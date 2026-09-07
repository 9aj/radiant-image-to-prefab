import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw
base=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(base))
from core import Settings,build,map_text,preview
folder=base/'examples'; folder.mkdir(exist_ok=True)
im=Image.new('RGB',(512,448),'white'); d=ImageDraw.Draw(im)
for col in range(5):
    for row in range(4):
        cx=82+col*86; cy=65+row*100+(50 if col%2 else 0)
        if cy>400 or (col==4 and row==3): continue
        outer=[(cx+57*math.cos(math.pi*i/3),cy+57*math.sin(math.pi*i/3)) for i in range(6)]
        d.polygon(outer,fill='black')
for col in range(5):
    for row in range(4):
        cx=82+col*86; cy=65+row*100+(50 if col%2 else 0)
        if cy>400 or (col==4 and row==3): continue
        inner=[(cx+43*math.cos(math.pi*i/3),cy+43*math.sin(math.pi*i/3)) for i in range(6)]
        d.polygon(inner,fill='white')
im.save(folder/'honeycomb.png')
mask,boxes=build(im,Settings())
(folder/'honeycomb.map').write_text(map_text(boxes),encoding='utf-8')
preview(mask,boxes).save(folder/'honeycomb-preview.png')
print(f'Example generated: {len(boxes)} brushes')
