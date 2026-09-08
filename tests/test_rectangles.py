import random
import unittest
from prefabdrop.core import rectangles, _run_rectangles


class RectangleTests(unittest.TestCase):
    def test_taper_merges_vertical_spine(self):
        mask=[[1,1,0],[1,1,1],[1,1,0],[1,1,1],[1,1,0]]
        self.assertLess(len(rectangles(mask)),len(_run_rectangles(mask)))

    def test_exact_nonoverlapping_coverage_and_never_worse(self):
        rng=random.Random(17)
        for _ in range(50):
            mask=[[rng.random()<0.7 for x in range(30)] for y in range(24)]
            found=rectangles(mask)
            self.assertLessEqual(len(found),len(_run_rectangles(mask)))
            coverage=[[0]*30 for _ in range(24)]
            for x,y,X,Y in found:
                for j in range(y,Y):
                    for i in range(x,X): coverage[j][i]+=1
            self.assertEqual(coverage,mask)
