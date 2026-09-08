import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('repository_guard', Path(__file__).resolve().parents[1] / 'scripts/check_repository.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

class RepositoryGuardTests(unittest.TestCase):
    def test_credentials_in_ordinary_source_are_rejected(self):
        for value in (b'hf' + b'_' + b'x' * 30, b'ghp' + b'_' + b'x' * 36):
            self.assertIn('possible credential', guard.issues('src/config.py', value))

    def test_weights_and_local_files_are_rejected_even_when_force_added(self):
        for name in ('exec.ps1', '.env', 'weights/model.safetensors', '.cache/huggingface/token', '.venv/file.py'):
            self.assertTrue(guard.issues(name, b'ordinary content'))

    def test_documentation_and_notices_are_allowed(self):
        self.assertEqual(guard.issues('NOTICE', b'Powered by Stability AI'), [])
