"""Application-side orchestration for the optional Stable Fast 3D worker."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import uuid

from .materials import import_material
from .mesh import load_obj, map_text


def _unique(directory: Path, stem: str, suffix: str) -> Path:
    for i in range(100000):
        target = directory / (stem + (f'_{i}' if i else '') + suffix)
        if not target.exists() and not (directory / (target.stem + '_source')).exists():
            return target
    raise ValueError('Too many duplicate output names.')


def generate(job: dict, app_root: str | Path) -> dict:
    root = Path(app_root)
    source = Path(job['source'])
    destination = Path(job['folder'])
    game = Path(job['game'])
    sf3d_repo = root / 'tools' / 'stable-fast-3d'
    sf3d_python = root / '.venv-sf3d' / 'Scripts' / 'python.exe'
    if not source.is_file():
        raise ValueError('The source image does not exist.')
    if not destination.is_dir():
        raise ValueError('3D prefab destination folder does not exist.')
    if not (game / 'bin' / 'converter.exe').is_file():
        raise ValueError('Choose the CoD4 folder containing bin\\converter.exe.')
    if not sf3d_python.is_file() or not (sf3d_repo / 'sf3d' / 'system.py').is_file():
        raise ValueError('Stable Fast 3D is not installed. Follow the Stable Fast 3D setup section in README.md.')
    target_vertices = int(job.get('target_vertices', 1500))
    texture_resolution = int(job.get('texture_resolution', 1024))
    longest_edge = float(job.get('longest_edge', 256))
    if not 100 <= target_vertices <= 10000:
        raise ValueError('Target vertices must be between 100 and 10000.')
    if texture_resolution not in (512, 1024, 2048):
        raise ValueError('Texture resolution must be 512, 1024, or 2048.')

    work = root / '.prefabdrop' / 'sf3d' / uuid.uuid4().hex
    work.mkdir(parents=True)
    log_dir = root / '.prefabdrop' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f'sf3d-{work.name}.log'
    command = [str(sf3d_python), str(root / 'src' / 'prefabdrop' / 'sf3d_bridge.py'), '--repo', str(sf3d_repo),
               '--image', str(source), '--output', str(work), '--texture-resolution', str(texture_resolution),
               '--target-vertices', str(target_vertices)]
    try:
        with log_path.open('w', encoding='utf-8') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, text=True, timeout=900)
        if result.returncode:
            raise RuntimeError(f'Stable Fast 3D failed. See {log_path}')
        manifest = json.loads((work / 'manifest.json').read_text(encoding='utf-8'))
        imported = import_material(Path(manifest['texture']), game, source.stem)
        obj = load_obj(manifest['obj'])
        text = map_text(obj, imported['material'], imported['size'], longest_edge=longest_edge)
        stem = re.sub(r'[^a-zA-Z0-9_-]', '_', source.stem).strip('_')[:70] or 'asset'
        map_path = _unique(destination, f'prefab_3d_{stem}', '.map')
        base = map_path.with_suffix('')
        source_dir = destination / (base.name + '_source')
        source_dir.mkdir()
        obj_path, glb_path = source_dir / 'mesh.obj', source_dir / 'mesh.glb'
        for asset in work.iterdir():
            if asset.name != 'manifest.json':
                shutil.copy2(asset, source_dir / asset.name)
        map_path.write_text(text, encoding='utf-8')
        return {'output': str(map_path), 'obj': str(obj_path), 'glb': str(glb_path),
                'patches': len(obj.triangles), 'material': imported['material'], 'imported': imported}
    finally:
        shutil.rmtree(work, ignore_errors=True)
