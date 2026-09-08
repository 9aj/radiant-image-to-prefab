"""JSON job bridge for the native UI. Converter logs never fill UI process pipes."""
import argparse
import json
from pathlib import Path
import sys
from PIL import Image
from core import Settings, build, map_text
from materials import import_material
from sf3d_pipeline import generate as generate_3d


def run(job):
    source = Path(job['source'])
    if job['kind'] == 'sf3d':
        return generate_3d(job, Path(__file__).parent)
    if job['kind'] == 'texture':
        return import_material(source, job['game'], job.get('name'))
    if job['kind'] != 'prefab':
        raise ValueError('Unknown job type.')
    destination = Path(job['folder'])
    if not destination.is_dir():
        raise ValueError('Prefab destination folder does not exist.')
    settings = Settings(**job.get('settings', {}))
    with Image.open(source) as image:
        mask, boxes = build(image, settings)
    imported = import_material(source, job['game']) if job.get('auto_texture') else None
    material = imported['material'] if imported else settings.material
    projection = None
    if imported:
        pixel_width, pixel_height = imported['size']
        projection = (len(mask[0]) * settings.cell, len(mask) * settings.cell,
                      pixel_width, pixel_height, settings.orientation)
    text = map_text(boxes, material, image_projection=projection)
    import re
    stem = re.sub(r'[^a-zA-Z0-9_-]', '_', source.stem).strip('_')[:80] or 'image'
    for i in range(100000):
        target = destination / (f'prefab_{stem}' + (f'_{i}' if i else '') + '.map')
        try:
            with target.open('x', encoding='utf-8') as handle:
                handle.write(text)
            return {'output':str(target), 'brushes':len(boxes), 'material':material, 'imported':imported}
        except FileExistsError:
            continue
    raise ValueError('Too many duplicate prefab names.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('request', type=Path)
    parser.add_argument('response', type=Path)
    args = parser.parse_args()
    try:
        result = {'ok':True, 'result':run(json.loads(args.request.read_text(encoding='utf-8-sig')))}
    except Exception as error:
        result = {'ok':False, 'error':str(error)}
    args.response.write_text(json.dumps(result), encoding='utf-8')
    sys.exit(0 if result['ok'] else 1)
