from .paths import APP_ROOT
from .paths import APP_ROOT
"""CoD4 material import through the installed Mod Tools converter."""
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import time
from PIL import Image, ImageOps

VERSION = 2


def game_root(path):
    root = Path(path).resolve()
    for relative in ('bin/converter.exe', 'deffiles/material.gdf', 'source_data'):
        if not (root / relative).exists():
            raise ValueError(f'Not a CoD4 Mod Tools installation: missing {relative}')
    return root


def prepare_image(source):
    """Opaque, bounded power-of-two TGA accepted by the legacy converter."""
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original).convert('RGBA')
    background = Image.new('RGBA', image.size, (32, 32, 32, 255))
    background.alpha_composite(image)
    image = background.convert('RGB')
    # Independent dimensions retain the full image; no crop, maximum 1024 per axis.
    dimensions = tuple(max(32, min(1024, 2 ** round(__import__('math').log2(v)))) for v in image.size)
    image = image.resize(dimensions, Image.Resampling.LANCZOS)
    stream = io.BytesIO()
    image.save(stream, format='TGA')
    return stream.getvalue(), dimensions


def asset_name(source, data, label=None):
    label = label.strip() if label else Path(source).stem
    label = re.sub(r'[^a-z0-9_]+', '_', label.lower()).strip('_')[:32] or 'image'
    digest = hashlib.sha256(str(VERSION).encode() + data).hexdigest()[:12]
    return f'pd_{label}_{digest}'


def gdt_text(name):
    if not re.fullmatch(r'pd_[a-z0-9_]+', name):
        raise ValueError('Invalid material name')
    return ('{\n"' + name + '" ( "material.gdf" )\n{\n'
            '"materialType" "world phong"\n"surfaceType" "metal"\n'
            '"usage" "floor"\n"colorMap" "texture_assets/' + name + '.tga"\n'
            '"locale_Generic" "1"\n}\n}\n')


@contextmanager
def conversion_lock(root, timeout=100):
    """OS-owned lock releases on crash and serializes our converter invocations."""
    import msvcrt
    path = root / 'source_data' / '.prefabdrop.lock'
    with path.open('a+b') as handle:
        if handle.tell() == 0:
            handle.write(b'0'); handle.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError('Another material conversion is still running. Try again shortly.')
                time.sleep(0.1)
        try:
            yield
        finally:
            handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def write_owned(path, content):
    """Never replace files with different content, even in our namespace."""
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f'Existing asset differs; refusing to replace {path}')
    else:
        with path.open('xb') as handle:
            handle.write(content)


def verify_outputs(root, name):
    material = root / 'raw/materials' / name
    image = root / 'raw/images' / (name + '.iwi')
    if not material.is_file() or material.stat().st_size == 0:
        raise ValueError('Converter did not create a material file.')
    if not image.is_file() or image.read_bytes()[:3] != b'IWi':
        raise ValueError('Converter did not create a valid IWI image.')
    properties = root / 'raw/material_properties' / name
    if not properties.is_file() or properties.stat().st_size == 0:
        raise ValueError('Converter did not create material_properties metadata for Radiant.')
    return material, image


def import_material(source, installation, label=None):
    root = game_root(installation)
    data, size = prepare_image(source)
    name = asset_name(source, data, label)
    gdt = root / 'source_data' / (name + '.gdt')
    texture = root / 'texture_assets' / (name + '.tga')
    log_dir = APP_ROOT / '.prefabdrop' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / (name + '.log')
    manifest = log_dir / (name + '.json')
    with conversion_lock(root):
        texture.parent.mkdir(exist_ok=True)
        write_owned(texture, data)
        write_owned(gdt, gdt_text(name).encode('ascii'))
        cached = False
        if manifest.exists():
            try:
                previous = json.loads(manifest.read_text())
                material, iwi = verify_outputs(root, name)
                cached = previous.get('root') == str(root) and previous.get('hashes') == [hashlib.sha256(p.read_bytes()).hexdigest() for p in (material, iwi)]
            except (ValueError, OSError):
                pass
        if not cached:
            command = [str(root / 'bin/converter.exe'), '-nopause', '-single', 'material', name]
            # In this tool build absolute -gamedir creates invalid doubled paths.
            try:
                result = subprocess.run(command, cwd=root / 'bin', capture_output=True,
                                        timeout=90, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            except subprocess.TimeoutExpired as error:
                log.write_bytes((error.stdout or b'') + (error.stderr or b'') + b'\nConversion timed out.')
                raise ValueError(f'Material conversion timed out. Log: {log}') from error
            output = (result.stdout + result.stderr).decode('utf-8', errors='replace')
            log.write_text(output, encoding='utf-8')
            try:
                if result.returncode or re.search(r'(?im)\b(?:aborting|fatal error|cannot open|failed to)\b', output):
                    raise ValueError('Converter reported an error.')
                material, iwi = verify_outputs(root, name)
            except ValueError as error:
                raise ValueError(f'{error} See {log}') from error
            manifest.write_text(json.dumps({'root':str(root), 'hashes':[hashlib.sha256(p.read_bytes()).hexdigest() for p in (material, iwi)]}))
    return {'material': name, 'material_file': str(material), 'image_file': str(iwi),
            'gdt': str(gdt), 'source_texture': str(texture), 'size': size, 'cached': cached, 'log': str(log)}
