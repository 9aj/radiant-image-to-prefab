"""Textured OBJ triangles -> CoD4 iwmap 4 mesh patches."""
from dataclasses import dataclass
import math
from pathlib import Path
import re


@dataclass(frozen=True)
class Corner:
    vertex: int
    texcoord: int | None


@dataclass(frozen=True)
class ObjMesh:
    vertices: tuple[tuple[float, float, float], ...]
    texcoords: tuple[tuple[float, float], ...]
    triangles: tuple[tuple[Corner, Corner, Corner], ...]


def _index(value: str, count: int) -> int:
    raw = int(value)
    result = raw - 1 if raw > 0 else count + raw
    if result < 0 or result >= count:
        raise ValueError(f'OBJ index {raw} is out of range.')
    return result


def load_obj(path: str | Path) -> ObjMesh:
    vertices, texcoords, triangles = [], [], []
    for number, original in enumerate(Path(path).read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        line = original.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        try:
            if parts[0] == 'v' and len(parts) >= 4:
                vertices.append(tuple(float(v) for v in parts[1:4]))
            elif parts[0] == 'vt' and len(parts) >= 3:
                texcoords.append((float(parts[1]), float(parts[2])))
            elif parts[0] == 'f' and len(parts) >= 4:
                corners = []
                for token in parts[1:]:
                    fields = token.split('/')
                    vertex = _index(fields[0], len(vertices))
                    texcoord = _index(fields[1], len(texcoords)) if len(fields) > 1 and fields[1] else None
                    corners.append(Corner(vertex, texcoord))
                for i in range(1, len(corners) - 1):
                    triangles.append((corners[0], corners[i], corners[i + 1]))
        except (ValueError, IndexError) as error:
            raise ValueError(f'Invalid OBJ data on line {number}: {error}') from error
    if not vertices or not triangles:
        raise ValueError('The OBJ contains no triangle geometry.')
    if not texcoords or any(c.texcoord is None for tri in triangles for c in tri):
        raise ValueError('The OBJ has no complete UV mapping. Stable Fast 3D must export its texture coordinates.')
    return ObjMesh(tuple(vertices), tuple(texcoords), tuple(triangles))


def fitted_vertices(mesh: ObjMesh, longest_edge: float) -> tuple[tuple[float, float, float], ...]:
    if not math.isfinite(longest_edge) or not 1 <= longest_edge <= 32768:
        raise ValueError('Longest edge must be between 1 and 32768 units.')
    mins = [min(p[axis] for p in mesh.vertices) for axis in range(3)]
    maxs = [max(p[axis] for p in mesh.vertices) for axis in range(3)]
    extent = max(maxs[axis] - mins[axis] for axis in range(3))
    if not math.isfinite(extent) or extent <= 1e-9:
        raise ValueError('The OBJ has zero-size geometry.')
    scale = longest_edge / extent
    center_x = (mins[0] + maxs[0]) / 2
    center_y = (mins[1] + maxs[1]) / 2
    ground = mins[2]
    return tuple(((x-center_x)*scale, (y-center_y)*scale, (z-ground)*scale) for x, y, z in mesh.vertices)


def _number(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError('Mesh contains a non-finite number.')
    text = f'{value:.6f}'.rstrip('0').rstrip('.')
    return text if text and text != '-0' else '0'


def map_text(mesh: ObjMesh, material: str, texture_size: tuple[int, int], longest_edge: float = 256,
             max_patches: int = 20000) -> str:
    if not re.fullmatch(r'[A-Za-z0-9_./-]+', material):
        raise ValueError('Material must be a single Radiant material name, without spaces.')
    if len(mesh.triangles) > max_patches:
        raise ValueError(f'{len(mesh.triangles):,} triangles exceeds the {max_patches:,} patch limit. Lower the target vertex count.')
    width, height = texture_size
    if width <= 0 or height <= 0:
        raise ValueError('Texture dimensions must be positive.')
    vertices = fitted_vertices(mesh, longest_edge)
    lines = ['iwmap 4', '"000_Global" flags  active', '"The Map" flags ', '// entity 0', '{', '"classname" "worldspawn"']
    written = 0
    for triangle in mesh.triangles:
        points = [vertices[corner.vertex] for corner in triangle]
        ax, ay, az = (points[1][i] - points[0][i] for i in range(3))
        bx, by, bz = (points[2][i] - points[0][i] for i in range(3))
        area2 = math.sqrt((ay*bz-az*by)**2 + (az*bx-ax*bz)**2 + (ax*by-ay*bx)**2)
        if area2 <= 1e-6:
            continue
        records = []
        for corner, point in zip(triangle, points):
            u, v = mesh.texcoords[corner.texcoord]
            records.append('v ' + ' '.join(_number(n) for n in point) +
                           ' t ' + _number(u * width) + ' ' + _number((1-v) * height) + ' 0 0')
        lines.extend([
            f'// brush {written}', ' {', '  mesh', '  {', f'   {material}', '   lightmap_gray',
            '   smoothing smoothing_hard', '   2 2 16 8', '   (', f'    {records[0]}', f'    {records[0]}',
            '   )', '   (', f'    {records[1]}', f'    {records[2]}', '   )', '  }', ' }'
        ])
        written += 1
    if not written:
        raise ValueError('The OBJ contains only degenerate triangles.')
    return '\n'.join(lines + ['}', ''])
