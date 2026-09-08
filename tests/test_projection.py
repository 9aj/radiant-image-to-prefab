import unittest
from core import map_text


class ProjectionTests(unittest.TestCase):
    def test_same_transform_on_separate_brush_caps(self):
        boxes=[(-40,-50,0,-20,40,8),(20,-50,0,40,40,8)]
        text=map_text(boxes,'test', (128,256,512,1024,'floor'))
        faces=[line for line in text.splitlines() if line.startswith('( ')]
        for i in (0,1,6,7):
            self.assertIn('test 128 256 64 -128 0 0 ',faces[i])
        # With the serialized CoD convention, all full-canvas corners map to
        # 0 or 1, regardless of the positions/bounds of individual brushes.
        tokens=faces[1].split('test ')[1].split()
        sx,sy,tx,ty=map(float,tokens[:4])
        for x,y,u,v in [(-64,128,0,0),(64,128,1,0),(-64,-128,0,1),(64,-128,1,1)]:
            self.assertAlmostEqual((x+tx)/sx,u)
            self.assertAlmostEqual((-y-ty)/sy,v)

    def test_wall_uses_y_facing_caps(self):
        text=map_text([(-8,0,-16,8,4,16)],'test',(16,32,64,128,'wall'))
        faces=[line for line in text.splitlines() if line.startswith('( ')]
        for i in (2,4): self.assertIn('test 16 32 8 -16 0 0 ',faces[i])
        self.assertIn('test 128 128 0 0 0 0 ',faces[0])

    def test_default_unchanged(self):
        self.assertEqual(map_text([(0,0,0,8,8,8)]).count('caulk 128 128 0 0 0 0'),6)

    def test_compiled_pixel_size_does_not_change_projection(self):
        boxes=[(-90,-192,0,90,192,32)]
        self.assertEqual(map_text(boxes,'test',(180,384,512,1024,'floor')),
                         map_text(boxes,'test',(180,384,256,512,'floor')))
