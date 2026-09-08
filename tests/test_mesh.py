import tempfile
import unittest
from pathlib import Path

from prefabdrop.mesh import fitted_vertices, load_obj, map_text


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
        self.assertIn('t 0 256 ', text)
        self.assertIn('t 512 0 ', text)
        self.assertTrue(text.startswith('iwmap 4\n"000_Global"'))

    def test_missing_uv_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'UV mapping'):
            self.load('v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n')

    def test_lightmap_has_area_for_each_face_orientation_even_with_constant_texture_uv(self):
        for vertices in ('v 0 0 0\nv 1 0 0\nv 0 1 0',
                         'v 0 0 0\nv 0 1 0\nv 0 0 1',
                         'v 0 0 0\nv 1 0 0\nv 0 0 1'):
            text = map_text(self.load(vertices + '\nvt 0 0\nf 1/1 2/1 3/1\n'), 'pd_test', (512, 512))
            records = [line.split() for line in text.splitlines() if line.strip().startswith('v ')]
            coords = [tuple(map(float, row[-2:])) for row in records]
            a, b, c = coords[0], coords[2], coords[3]
            self.assertGreater(abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])), 0)
            self.assertEqual(coords[0], coords[1])


if __name__ == '__main__':
    unittest.main()
