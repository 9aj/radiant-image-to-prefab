"""Conservative index/history audit. Reports paths/object IDs, never secret values."""
from pathlib import PurePosixPath
import re
import subprocess
import sys

PATTERNS = [re.compile(p) for p in (
    rb'\bhf' + rb'_[A-Za-z0-9]{20,}\b',
    rb'\bgh[pousr]' + rb'_[A-Za-z0-9]{20,}\b',
    rb'\bgithub_pat' + rb'_[A-Za-z0-9_]{20,}\b',
    rb'\bsk' + rb'-(?:proj-)?[A-Za-z0-9_-]{20,}\b',
    rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    rb'\bAKIA[A-Z0-9]{16}\b',
)]
FORBIDDEN = {'.safetensors','.ckpt','.pt','.pth','.onnx','.bin','.ff','.iwd','.iwi','.d3dbsp','.pem','.key'}


def git(*args):
    return subprocess.check_output(['git', *args])


def issues(path, data):
    p = PurePosixPath(path)
    result = []
    if (p.suffix.lower() in FORBIDDEN or p.name in ('exec.ps1','token','stored_tokens','preferences.json')
        or (p.name.startswith('.env') and p.name != '.env.example')
        or any(part in ('.prefabdrop','.cache','models','weights','checkpoints') or part.startswith('.venv') for part in p.parts)
        or path.startswith('tools/stable-fast-3d/')):
        result.append('local/generated/credential file')
    if len(data) > 5 * 1024 * 1024:
        result.append('file exceeds 5 MiB; review before publishing')
    if any(pattern.search(data) for pattern in PATTERNS):
        result.append('possible credential')
    return result


def main():
    failed = False
    if '--history' in sys.argv:
        objects = git('rev-list','--objects','--all').decode().splitlines()
        for row in objects:
            oid, _, path = row.partition(' ')
            if git('cat-file','-t',oid).strip() != b'blob':
                continue
            findings = issues(path, git('cat-file','blob',oid))
            if findings:
                failed = True
                print(path, oid[:12], ':', ', '.join(findings))
    else:
        for path in git('ls-files','-z').decode().split('\0'):
            if not path:
                continue
            findings = issues(path, git('show', ':'+path))
            if findings:
                failed = True
                print(path, ':', ', '.join(findings))
    if not failed:
        print('PASS: no recognized credentials, weights, or forbidden generated files in '+('history' if '--history' in sys.argv else 'the Git index')+'.')
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
