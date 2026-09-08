"""Image masks -> merged, non-overlapping cuboids -> CoD4 iwmap 4."""
from dataclasses import dataclass
import math
import re
from PIL import Image, ImageOps, ImageDraw


@dataclass
class Settings:
    resolution: int = 96
    threshold: int = 128
    mode: str = 'dark'
    cell: float = 4
    depth: float = 32
    orientation: str = 'floor'
    material: str = 'caulk'
    max_brushes: int = 4096

    def validate(self):
        if not 4 <= self.resolution <= 512:
            raise ValueError('Resolution must be between 4 and 512.')
        if not 0 <= self.threshold <= 255:
            raise ValueError('Threshold must be between 0 and 255.')
        if self.mode not in ('dark', 'light', 'alpha'):
            raise ValueError('Choose dark, light, or alpha mask.')
        if self.orientation not in ('floor', 'wall'):
            raise ValueError('Choose floor or wall orientation.')
        if not all(math.isfinite(v) and 0.125 <= v <= 8192 for v in (self.cell, self.depth)):
            raise ValueError('Cell size and depth must be finite, between 0.125 and 8192 units.')
        if not re.fullmatch(r'[A-Za-z0-9_./-]+', self.material):
            raise ValueError('Material must be a single Radiant material name, without spaces.')
        if not 1 <= self.max_brushes <= 65536:
            raise ValueError('Brush limit must be between 1 and 65536.')


def image_mask(image, settings):
    settings.validate()
    image = ImageOps.exif_transpose(image).convert('RGBA')
    w, h = image.size
    ratio = settings.resolution / max(w, h)
    size = (max(1, round(w * ratio)), max(1, round(h * ratio)))
    image = image.resize(size, Image.Resampling.LANCZOS)
    alpha = image.getchannel('A')
    gray = image.convert('L')
    mask = []
    for y in range(size[1]):
        row = []
        for x in range(size[0]):
            a, v = alpha.getpixel((x, y)), gray.getpixel((x, y))
            on = a > settings.threshold if settings.mode == 'alpha' else (
                a >= 128 and (v < settings.threshold if settings.mode == 'dark' else v >= settings.threshold))
            row.append(bool(on))
        mask.append(row)
    return mask


def rectangles(mask):
    """Merge identical horizontal runs on adjacent rows; exact mask coverage."""
    active, result = {}, []
    for y, row in enumerate(mask):
        runs, x = [], 0
        while x < len(row):
            if not row[x]:
                x += 1
                continue
            start = x
            while x < len(row) and row[x]:
                x += 1
            runs.append((start, x))
        current = {}
        for run in runs:
            current[run] = active.pop(run, (run[0], y, run[1], y))[0:3] + (y + 1,)
        result.extend(active.values())
        active = current
    result.extend(active.values())
    return result


def build(image, settings):
    mask = image_mask(image, settings)
    rects = rectangles(mask)
    if not rects:
        raise ValueError('The mask is empty. Change mask mode or threshold.')
    if len(rects) > settings.max_brushes:
        raise ValueError(f'{len(rects):,} brushes exceeds the {settings.max_brushes:,} limit. Lower resolution or simplify the image.')
    w, h = len(mask[0]), len(mask)
    boxes = []
    for x0, y0, x1, y1 in rects:
        left, right = (x0 - w / 2) * settings.cell, (x1 - w / 2) * settings.cell
        bottom, top = (h / 2 - y1) * settings.cell, (h / 2 - y0) * settings.cell
        if settings.orientation == 'floor':
            boxes.append((left, bottom, 0, right, top, settings.depth))
        else:
            boxes.append((left, 0, bottom, right, settings.depth, top))
    if any(abs(v) > 32768 for b in boxes for v in b):
        raise ValueError('Geometry exceeds +/-32768 units. Reduce cell size or depth.')
    return mask, boxes


def face_points(box):
    x0, y0, z0, x1, y1, z1 = box
    # Radiant plane convention: (p0-p1) cross (p2-p1) points outwards.
    return [
        ((x1,y1,z0),(x0,y1,z0),(x0,y0,z0)),
        ((x0,y0,z1),(x0,y1,z1),(x1,y1,z1)),
        ((x0,y0,z1),(x1,y0,z1),(x1,y0,z0)),
        ((x1,y0,z1),(x1,y1,z1),(x1,y1,z0)),
        ((x1,y1,z1),(x0,y1,z1),(x0,y1,z0)),
        ((x0,y1,z1),(x0,y0,z1),(x0,y0,z0)),
    ]


def map_text(boxes, material='caulk', image_projection=None):
    Settings(material=material).validate()
    if image_projection is not None:
        width, height, pixel_width, pixel_height, orientation = image_projection
        if orientation not in ('floor', 'wall') or not all(math.isfinite(v) and v > 0 for v in (width, height, pixel_width, pixel_height)):
            raise ValueError('Invalid image projection.')
    if not boxes:
        raise ValueError('Cannot export an empty prefab.')
    lines = ['iwmap 4', '// entity 0', '{', '"classname" "worldspawn"']
    for i, box in enumerate(boxes):
        if len(box) != 6 or not all(math.isfinite(v) for v in box) or any(box[j] >= box[j+3] for j in range(3)):
            raise ValueError('Invalid or zero-volume brush.')
        lines.extend([f'// brush {i}', '{'])
        for face_index, points in enumerate(face_points(box)):
            plane = ' '.join('( ' + ' '.join(f'{v:.6f}'.rstrip('0').rstrip('.') if v else '0' for v in p) + ' )' for p in points)
            mapping = '128 128 0 0 0 0'
            if image_projection is not None and face_index in ((0, 1) if orientation == 'floor' else (2, 4)):
                # CoD stores both repeat sizes and shifts in WORLD units.
                # Verified against IW3xRadiant's Brush_FitTexture helper at
                # 0x47c590: offsets are computed from projected world bounds.
                # A shared transform spans the full image canvas, including blank
                # margins, rather than fitting a fresh copy to each small brush.
                # U=x/width+0.5; V=-y/height+0.5 (or -z for a wall).
                mapping = f'{width:g} {height:g} {width / 2:g} {-height / 2:g} 0 0'
            lines.append(f'{plane} {material} {mapping} lightmap_gray 16384 16384 0 0 0 0')
        lines.append('}')
    return '\n'.join(lines + ['}', ''])


def preview(mask, boxes, size=(1000, 620)):
    """Orthographic mask + isometric brush preview; no GPU dependencies."""
    out = Image.new('RGB', size, '#141b20')
    draw = ImageDraw.Draw(out)
    draw.text((22, 18), 'MASK / TOP VIEW', fill='#c6dbcf')
    draw.text((size[0]//2+22, 18), 'EXTRUDED BRUSHES', fill='#c6dbcf')
    w, h = len(mask[0]), len(mask)
    thumb = Image.new('RGB', (w,h), '#202c32')
    thumb.putdata([(165,191,157) if p else (32,44,50) for row in mask for p in row])
    thumb.thumbnail((size[0]//2-44,size[1]-90), Image.Resampling.NEAREST)
    scale = min((size[0]//2-44)/w, (size[1]-90)/h)
    thumb = thumb.resize((max(1,int(w*scale)),max(1,int(h*scale))),Image.Resampling.NEAREST)
    out.paste(thumb, ((size[0]//2-thumb.width)//2,(size[1]-thumb.height)//2))
    def project(p):
        x,y,z=p
        return (x-y)*0.866, (x+y)*0.5-z
    faces=[]
    for b in boxes:
        x,y,z,X,Y,Z=b
        for poly,color in [([(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)],'#a4bd99'), ([(X,y,z),(X,Y,z),(X,Y,Z),(X,y,Z)],'#546e61'), ([(x,Y,z),(X,Y,z),(X,Y,Z),(x,Y,Z)],'#7d8e70')]:
            faces.append((sum(p[0]+p[1]+p[2]*0.001 for p in poly)/4, [project(p) for p in poly],color))
    points=[p for _,poly,_ in faces for p in poly]
    xmin,ymin=min(p[0] for p in points),min(p[1] for p in points)
    xmax,ymax=max(p[0] for p in points),max(p[1] for p in points)
    scale=min((size[0]/2-50)/max(1,xmax-xmin),(size[1]-110)/max(1,ymax-ymin))
    cx,cy=size[0]*0.75,size[1]*0.5
    for _,poly,color in sorted(faces,key=lambda f:f[0]):
        draw.polygon([(cx+(x-(xmin+xmax)/2)*scale,cy+(y-(ymin+ymax)/2)*scale) for x,y in poly],fill=color,outline='#2e433d')
    draw.text((22,size[1]-28),f'{w} x {h} cells | {len(boxes):,} brushes | {len(boxes)*6:,} faces',fill='#c6dbcf')
    return out
