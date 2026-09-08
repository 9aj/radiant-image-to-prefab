import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
import materials
import worker


class MaterialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ('bin','deffiles','source_data','raw/materials','raw/images','raw/material_properties'):
            (self.root/folder).mkdir(parents=True)
        (self.root/'bin/converter.exe').touch()
        (self.root/'deffiles/material.gdf').touch()
        self.source=self.root/'test image.png'
        Image.new('RGBA',(70,140),(90,110,70,255)).save(self.source)

    def test_normalization_and_safe_name(self):
        data,size=materials.prepare_image(self.source)
        self.assertEqual(size,(64,128))
        name=materials.asset_name(self.source,data,'../../BAD " name')
        self.assertRegex(name,r'^pd_[a-z0-9_]+$')
        self.assertEqual(name,materials.asset_name(self.source,data,'../../BAD " name'))
        self.assertIn('"materialType" "world phong"',materials.gdt_text(name))
        self.assertIn('"locale_Generic" "1"', materials.gdt_text(name))
        self.assertNotIn('locale_Industrial', materials.gdt_text(name))

    def test_never_overwrite_different_source(self):
        path=self.root/'owned'
        materials.write_owned(path,b'first')
        with self.assertRaises(ValueError): materials.write_owned(path,b'second')
        self.assertEqual(path.read_bytes(),b'first')

    def test_zero_exit_without_outputs_is_failure(self):
        with patch('materials.subprocess.run',return_value=subprocess.CompletedProcess([],0,b'',b'')):
            with self.assertRaisesRegex(ValueError,'did not create'):
                materials.import_material(self.source,self.root)

    def test_error_text_even_with_outputs_is_failure(self):
        def convert(*args,**kwargs):
            name=args[0][-1]
            (self.root/'raw/materials'/name).write_bytes(b'material')
            (self.root/'raw/images'/(name+'.iwi')).write_bytes(b'IWi\x06fake')
            return subprocess.CompletedProcess([],0,b'aborting....',b'')
        with patch('materials.subprocess.run',side_effect=convert):
            with self.assertRaisesRegex(ValueError,'reported an error'):
                materials.import_material(self.source,self.root)

    def test_success_cached_and_missing_output_rebuilt(self):
        def convert(*args,**kwargs):
            self.assertEqual(kwargs['cwd'],self.root/'bin')
            self.assertNotIn('-gamedir',args[0])
            name=args[0][-1]
            (self.root/'raw/materials'/name).write_bytes(b'material')
            (self.root/'raw/material_properties'/name).write_bytes(b'metadata')
            (self.root/'raw/images'/(name+'.iwi')).write_bytes(b'IWi\x06fake')
            return subprocess.CompletedProcess([],0,b'Converted',b'')
        with patch('materials.subprocess.run',side_effect=convert) as run:
            first=materials.import_material(self.source,self.root)
            second=materials.import_material(self.source,self.root)
            self.assertFalse(first['cached']); self.assertTrue(second['cached']); self.assertEqual(run.call_count,1)
            Path(first['image_file']).unlink()
            self.assertFalse(materials.import_material(self.source,self.root)['cached'])
            self.assertEqual(run.call_count,2)
            (self.root/'raw/material_properties'/first['material']).unlink()
            self.assertFalse(materials.import_material(self.source,self.root)['cached'])
            self.assertEqual(run.call_count,3)

    def test_prefab_failure_does_not_save_map(self):
        with patch('worker.import_material',side_effect=ValueError('conversion failed')):
            with self.assertRaises(ValueError): worker.run({'kind':'prefab','source':str(self.source),'folder':str(self.root),'game':str(self.root),'auto_texture':True})
        self.assertEqual(list(self.root.glob('*.map')),[])

    def test_assignment_and_no_overwrite(self):
        job={'kind':'prefab','source':str(self.source),'folder':str(self.root),'game':str(self.root),'auto_texture':True}
        with patch('worker.import_material',return_value={'material':'pd_test_123', 'size':(64,128)}):
            first=worker.run(job); second=worker.run(job)
        self.assertNotEqual(first['output'],second['output'])
        text=Path(first['output']).read_text()
        self.assertEqual(text.count('pd_test_123'),first['brushes']*6)


if __name__=='__main__': unittest.main()
