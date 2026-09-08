"""Run inside the dedicated Stable Fast 3D environment."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--texture-resolution', type=int, default=1024)
    parser.add_argument('--target-vertices', type=int, default=1500)
    parser.add_argument('--foreground-ratio', type=float, default=.85)
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo.resolve()))

    import torch
    from PIL import Image
    import rembg
    from sf3d.system import SF3D
    from sf3d.utils import remove_background, resize_foreground
    from trimesh.exchange.obj import export_obj

    if not torch.cuda.is_available():
        raise RuntimeError('Stable Fast 3D requires the CUDA environment for this integration.')
    args.output.mkdir(parents=True, exist_ok=True)
    image = remove_background(Image.open(args.image).convert('RGBA'), rembg.new_session())
    image = resize_foreground(image, args.foreground_ratio)
    model = SF3D.from_pretrained('stabilityai/stable-fast-3d', config_name='config.yaml', weight_name='model.safetensors')
    model.to('cuda').eval()
    with torch.no_grad(), torch.autocast(device_type='cuda', dtype=torch.bfloat16):
        mesh, _ = model.run_image(image, bake_resolution=args.texture_resolution,
                                  remesh='triangle', vertex_count=args.target_vertices)

    glb_path = args.output / 'mesh.glb'
    obj_path = args.output / 'mesh.obj'
    mesh.export(glb_path, include_normals=True)
    obj_text, assets = export_obj(mesh, include_normals=True, include_texture=True,
                                  return_texture=True, write_texture=True, mtl_name='mesh.mtl')
    obj_path.write_text(obj_text, encoding='utf-8')
    for name, data in assets.items():
        safe = Path(name).name
        (args.output / safe).write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))
    material_files = sorted(p for p in args.output.iterdir() if p.suffix.lower() == '.mtl')
    texture = None
    if material_files:
        for line in material_files[0].read_text(encoding='utf-8', errors='replace').splitlines():
            if line.lower().startswith('map_kd '):
                texture = args.output / Path(line.split(maxsplit=1)[1]).name
                break
    images = sorted(p for p in args.output.iterdir() if p.suffix.lower() in ('.png', '.jpg', '.jpeg'))
    if texture is None and images:
        texture = images[0]
    if texture is None or not texture.is_file():
        raise RuntimeError('Stable Fast 3D exported no albedo texture.')
    (args.output / 'manifest.json').write_text(json.dumps({
        'obj': str(obj_path), 'glb': str(glb_path), 'texture': str(texture),
        'vertices': len(mesh.vertices), 'triangles': len(mesh.faces)
    }), encoding='utf-8')


if __name__ == '__main__':
    main()
