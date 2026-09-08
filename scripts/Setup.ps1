$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
& py -3.14 -m venv (Join-Path $root '.venv')
if ($LASTEXITCODE) {throw 'Install standard Windows Python 3.14 (not MinGW/MSYS2).'}
& (Join-Path $root '.venv\Scripts\python.exe') -m pip install --only-binary=:all: -e $root
if ($LASTEXITCODE) {throw 'Dependency installation failed.'}
Write-Host 'Ready. Double-click Launch.cmd.'
