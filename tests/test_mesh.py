import tempfile
import unittest
from pathlib import Path

from mesh import fitted_vertices, load_obj, map_text


OBJ = '''
v -1 -1 2
v 1 -1 2
v 1 1 4
v -1 1 4
vt 0 0
vt 1 0
vt 1 1
vt 0 1
f 1/1 2/2 3/3 4/4
'''


class MeshTests(unittest.TestCase):
    def load(self, text=OBJ):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'mesh.obj'
            path.write_text(text, encoding='utf-8')
            return load_obj(path)

    def test_quad_is_triangulated_and_fitted(self):
        mesh = self.load()
        self.assertEqual(2, len(mesh.triangles))
        points = fitted_vertices(mesh, 256)
        self.assertEqual((-128, -128, 0), points[0])
        self.assertEqual((128, 128, 256), points[2])

    def test_patch_export_preserves_uvs(self):
        text = map_text(self.load(), 'pd_test', (512, 256), 256)
        self.assertEqual(2, text.count('\n  mesh\n'))
        self.assertIn('t 0 256 0 0', text)
        self.assertIn('t 512 0 0 0', text)
        self.assertTrue(text.startswith('iwmap 4\n"000_Global"'))

    def test_missing_uv_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'UV mapping'):
            self.load('v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n')


if __name__ == '__main__':
    unittest.main()
