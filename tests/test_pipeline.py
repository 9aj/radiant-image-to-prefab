import math
import random
import re
import unittest
from PIL import Image
from prefabdrop.core import Settings, image_mask, rectangles, build, face_points, map_text


class PipelineTests(unittest.TestCase):
    def test_exact_coverage_random_masks(self):
        rng=random.Random(19)
        for _ in range(100):
            mask=[[rng.random()<0.6 for x in range(19)] for y in range(13)]
            coverage=[[0]*19 for _ in range(13)]
            for x,y,X,Y in rectangles(mask):
                for j in range(y,Y):
                    for i in range(x,X): coverage[j][i]+=1
            self.assertEqual(coverage,[[int(p) for p in row] for row in mask])

    def test_solid_image_is_one_brush(self):
        mask,boxes=build(Image.new('RGB',(8,4),'black'),Settings(resolution=8,cell=4,depth=16))
        self.assertEqual(boxes,[(-16,-8,0,16,8,16)])

    def test_hole_preserved(self):
        mask=[[True]*5 for _ in range(5)]; mask[2][2]=False
        rects=rectangles(mask)
        self.assertEqual(sum((X-x)*(Y-y) for x,y,X,Y in rects),24)
        self.assertFalse(any(x<=2<X and y<=2<Y for x,y,X,Y in rects))

    def test_transparency_and_modes(self):
        im=Image.new('RGBA',(4,4),(0,0,0,0)); im.putpixel((0,0),(255,255,255,255))
        self.assertEqual(sum(map(sum,image_mask(im,Settings(resolution=4,mode='alpha')))),1)
        self.assertEqual(sum(map(sum,image_mask(im,Settings(resolution=4,mode='light')))),1)
        self.assertEqual(sum(map(sum,image_mask(im,Settings(resolution=4,mode='dark')))),0)

    def test_wall_orientation(self):
        im=Image.new('RGB',(4,4),'white'); im.putpixel((0,0),(0,0,0))
        _,boxes=build(im,Settings(resolution=4,cell=2,depth=8,orientation='wall'))
        self.assertEqual(boxes,[(-4,0,2,-2,8,4)])

    def test_plane_winding_contains_all_corners(self):
        box=(-16,-8,0,24,12,32)
        corners=[(x,y,z) for x in (box[0],box[3]) for y in (box[1],box[4]) for z in (box[2],box[5])]
        for a,b,c in face_points(box):
            u=[a[i]-b[i] for i in range(3)]; v=[c[i]-b[i] for i in range(3)]
            n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            self.assertGreater(sum(t*t for t in n),0)
            for p in corners: self.assertLessEqual(sum(n[i]*(p[i]-b[i]) for i in range(3)),0)

    def test_export_structure(self):
        text=map_text([(0,0,0,4,4,4)])
        self.assertTrue(text.startswith('iwmap 4\n'))
        self.assertEqual(text.count('{'),text.count('}'))
        self.assertEqual(text.count('lightmap_gray'),6)
        points=re.findall(r'\( ([^()]+) \)',text)
        self.assertEqual(len(points),18)
        self.assertTrue(all(len(p.split())==3 for p in points))

    def test_guards(self):
        for s in (Settings(cell=math.nan),Settings(depth=0),Settings(resolution=513),Settings(material='bad\nname')):
            with self.assertRaises(ValueError): s.validate()
        with self.assertRaises(ValueError): build(Image.new('RGB',(4,4),'white'),Settings())
        with self.assertRaises(ValueError): map_text([(0,0,0,0,4,4)])
        im=Image.new('RGB',(4,4),'white'); im.putpixel((0,0),(0,0,0)); im.putpixel((3,3),(0,0,0))
        with self.assertRaises(ValueError): build(im,Settings(resolution=4,max_brushes=1))


if __name__=='__main__': unittest.main()
