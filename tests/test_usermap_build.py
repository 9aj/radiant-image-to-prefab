from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from prefabdrop.usermap_build import bundle_images, compile_zone, deploy, map_name


class UsermapTests(unittest.TestCase):
    def test_archive_layout_and_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'images/sub').mkdir(parents=True)
            (root/'images/sub/test.iwi').write_bytes(b'IWi\x06texture')
            (root/'images/ignored.txt').write_text('ignore')
            self.assertEqual(bundle_images(root/'images', root/'map.iwd'), 1)
            with zipfile.ZipFile(root/'map.iwd') as archive:
                self.assertEqual(archive.namelist(), ['images/sub/test.iwi'])
                self.assertEqual(archive.read('images/sub/test.iwi'), b'IWi\x06texture')

    def test_reject_renamed_zip(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'bad.iwi').write_bytes(b'PKarchive')
            with self.assertRaisesRegex(ValueError, 'not an IWI'):
                bundle_images(root, root/'test.iwd')

    def test_map_path_cannot_escape(self):
        for name in ('../mp_test', 'mp_a/../../x', 'mp_a\\x', '-help', 'MP_TEST'):
            with self.assertRaises(ValueError):
                map_name(name)

    def test_failed_link_restores_previous_fastfile(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root/'zone/english/mp_test.ff'
            output.parent.mkdir(parents=True)
            output.write_bytes(b'previous build')
            with patch('prefabdrop.usermap_build.subprocess.run') as run:
                run.return_value.returncode = 1
                with self.assertRaisesRegex(ValueError, 'build failed'):
                    compile_zone(root, 'mp_test', 'english', root, root)
            self.assertEqual(output.read_bytes(), b'previous build')

    def test_zero_exit_without_new_output_is_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch('prefabdrop.usermap_build.subprocess.run') as run:
                run.return_value.returncode = 0
                with self.assertRaisesRegex(ValueError, 'no new fastfile'):
                    compile_zone(root, 'mp_test', 'english', root, root)

    def test_deployment_keeps_other_archives_and_backs_up(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stage, dest = root/'stage', root/'dest'
            stage.mkdir(); dest.mkdir()
            (stage/'mp_test_prefabdrop.iwd').write_bytes(b'new')
            (dest/'mp_test_prefabdrop.iwd').write_bytes(b'old')
            (dest/'handmade.iwd').write_bytes(b'untouched')
            deploy(stage, dest, root/'backup')
            self.assertEqual((dest/'mp_test_prefabdrop.iwd').read_bytes(), b'new')
            self.assertEqual((root/'backup/mp_test_prefabdrop.iwd').read_bytes(), b'old')
            self.assertEqual((dest/'handmade.iwd').read_bytes(), b'untouched')
