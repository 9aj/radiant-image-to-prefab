import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sf3d_pipeline


OBJ = '''v 0 0 0
v 1 0 0
v 0 1 1
vt 0 0
vt 1 0
vt 0 1
f 1/1 2/2 3/3
'''


class SF3DPipelineTests(unittest.TestCase):
    def test_worker_keeps_sources_and_writes_map_last(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            destination = root / 'out'; destination.mkdir()
            game = root / 'game'; (game / 'bin').mkdir(parents=True); (game / 'bin' / 'converter.exe').touch()
            repo = root / 'tools' / 'stable-fast-3d' / 'sf3d'; repo.mkdir(parents=True); (repo / 'system.py').touch()
            python = root / '.venv-sf3d' / 'Scripts' / 'python.exe'; python.parent.mkdir(parents=True); python.touch()
            source = root / 'thing.png'; source.touch()

            def fake_run(command, **kwargs):
                work = Path(command[command.index('--output') + 1])
                (work / 'mesh.obj').write_text(OBJ, encoding='utf-8')
                (work / 'mesh.glb').write_bytes(b'glb')
                (work / 'albedo.png').write_bytes(b'png')
                (work / 'mesh.mtl').write_text('map_Kd albedo.png', encoding='utf-8')
                (work / 'manifest.json').write_text(json.dumps({
                    'obj': str(work / 'mesh.obj'), 'glb': str(work / 'mesh.glb'),
                    'texture': str(work / 'albedo.png'), 'vertices': 3, 'triangles': 1
                }), encoding='utf-8')
                return type('Result', (), {'returncode': 0})()

            with patch.object(sf3d_pipeline.subprocess, 'run', side_effect=fake_run), patch.object(
                    sf3d_pipeline, 'import_material', return_value={'material': 'pd_thing', 'size': (512, 512)}):
                result = sf3d_pipeline.generate({'source': str(source), 'folder': str(destination),
                    'game': str(game), 'target_vertices': 500, 'texture_resolution': 512,
                    'longest_edge': 128}, root)

            output = Path(result['output'])
            self.assertTrue(output.is_file())
            self.assertIn('pd_thing', output.read_text(encoding='utf-8'))
            self.assertTrue(Path(result['obj']).is_file())
            self.assertTrue(Path(result['glb']).is_file())
            self.assertTrue(Path(result['obj']).with_name('albedo.png').is_file())


if __name__ == '__main__':
    unittest.main()
