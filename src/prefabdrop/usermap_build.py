from .paths import APP_ROOT
from .paths import APP_ROOT
"""Build usermap fastfiles and package loose IWI images using the stock linker."""
from datetime import datetime
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from .materials import conversion_lock


def map_name(value):
    if not re.fullmatch(r'mp_[a-z0-9_]{1,60}', value):
        raise ValueError('Map name must start with mp_ and contain lowercase letters, numbers and underscores.')
    return value


def bundle_images(folder, output):
    folder, output = Path(folder).resolve(), Path(output)
    if not folder.is_dir():
        raise ValueError('Choose an existing folder containing compiled .iwi images.')
    images = sorted(folder.rglob('*.iwi'))
    if not images:
        raise ValueError('No .iwi images found in the selected folder.')
    seen = set()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for image in images:
            if not image.resolve().is_relative_to(folder):
                raise ValueError(f'Image points outside the selected folder: {image.name}')
            with image.open('rb') as handle:
                if handle.read(3) != b'IWi':
                    raise ValueError(f'{image.name} is not an IWI image. Select actual images, not a renamed ZIP archive.')
            name = 'images/' + image.relative_to(folder).as_posix()
            if name.lower() in seen:
                raise ValueError(f'Duplicate image path: {name}')
            seen.add(name.lower())
            archive.write(image, name)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError('Image archive verification failed.')
    return len(images)


def compile_zone(root, name, language, stage, log_dir):
    output = root / 'zone' / language / (name + '.ff')
    output.parent.mkdir(parents=True, exist_ok=True)
    previous = output.with_name(output.name + '.' + uuid.uuid4().hex + '.previous')
    had_previous = output.exists()
    if had_previous:
        output.replace(previous)
    log = log_dir / (name + '.log')
    try:
        with log.open('wb') as handle:
            result = subprocess.run([str(root / 'bin/linker_pc.exe'), '-language', language,
                                     '-compress', name], cwd=root / 'bin', stdin=subprocess.DEVNULL,
                                    stdout=handle, stderr=subprocess.STDOUT, timeout=600,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        text = log.read_text(errors='replace')
        if result.returncode or re.search(r'(?im)^\s*(?:ERROR\b|FATAL\b)', text):
            raise ValueError(f'Fastfile build failed for {name}. See {log}')
        if not output.is_file() or output.stat().st_size < 12:
            raise ValueError(f'Linker produced no new fastfile for {name}. See {log}')
        if output.read_bytes()[:8] not in (b'IWffu100', b'IWffs100'):
            raise ValueError(f'Invalid fastfile header: {output}. See {log}')
        shutil.copy2(output, stage / output.name)
    except Exception:
        if output.exists():
            output.unlink()
        if had_previous:
            previous.replace(output)
        raise
    else:
        if had_previous:
            previous.replace(log_dir / (name + '.previous.ff'))


def deploy(stage, destination, backup):
    """Publish our named outputs and restore them if publishing fails."""
    destination.mkdir(parents=True, exist_ok=True)
    replaced = []
    backup.mkdir(parents=True, exist_ok=True)
    try:
        for source in sorted(stage.iterdir()):
            target = destination / source.name
            existed = target.exists()
            if existed:
                shutil.copy2(target, backup / target.name)
            temporary = target.with_name(target.name + '.' + uuid.uuid4().hex + '.tmp')
            try:
                shutil.copy2(source, temporary)
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
            replaced.append((target, existed))
    except Exception:
        for target, existed in reversed(replaced):
            if existed:
                shutil.copy2(backup / target.name, target)
            else:
                target.unlink(missing_ok=True)
        raise


def build_usermap(job, app_root=None):
    root = Path(job['game']).resolve()
    name = map_name(job.get('map_name', ''))
    language = job.get('language', 'english')
    if not re.fullmatch(r'[a-z]+', language):
        raise ValueError('Invalid language.')
    action = job.get('action', 'build')
    if action not in ('bundle', 'build'):
        raise ValueError('Unknown build action.')
    if not (root / 'bin/linker_pc.exe').is_file():
        raise ValueError('Choose the CoD4 folder containing bin/linker_pc.exe.')
    zones = [name]
    if action == 'build':
        if not (root / f'raw/maps/mp/{name}.d3dbsp').is_file():
            raise ValueError('Compile the map to BSP first. This action builds fastfiles from the existing BSP.')
        if not (root / f'zone_source/{name}.csv').is_file():
            raise ValueError(f'Missing zone_source/{name}.csv. Create the map zone source before building.')
        if (root / f'zone_source/{name}_load.csv').is_file():
            zones.append(name + '_load')
    app_root = Path(app_root or APP_ROOT)
    log_dir = app_root / '.prefabdrop/logs' / ('build-' + name + '-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6])
    log_dir.mkdir(parents=True)
    destination = root / 'usermaps' / name
    images = Path(job.get('images_folder') or root / 'raw/images')
    with conversion_lock(root, timeout=5), tempfile.TemporaryDirectory(prefix='prefabdrop-build-') as temporary:
        stage = Path(temporary)
        count = bundle_images(images, stage / (name + '_prefabdrop.iwd'))
        if action == 'build':
            for zone in zones:
                compile_zone(root, zone, language, stage, log_dir)
        deploy(stage, destination, log_dir / 'usermap-backup')
    message = (f'Built {len(zones)} fastfile(s) and bundled' if action == 'build' else 'Bundled') + f' {count} images for {name}. Restart the game before devmap.'
    return {'output': str(destination), 'images': count, 'log': str(log_dir), 'message': message}
