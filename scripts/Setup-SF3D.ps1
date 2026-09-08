param([string]$PythonVersion='3.11')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$repo=Join-Path $root 'tools\stable-fast-3d'
$venv=Join-Path $root '.venv-sf3d'
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'

if (-not (Test-Path -LiteralPath $vswhere)) { throw 'Install Visual Studio 2022 Build Tools with the Desktop development with C++ workload.' }
$vsPath=& $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vsPath) { throw 'Add the Desktop development with C++ workload to Visual Studio 2022.' }
$devCommand=Join-Path $vsPath 'Common7\Tools\VsDevCmd.bat'
& cmd.exe /s /c "`"$devCommand`" -arch=x64 -host_arch=x64 >nul && set" | ForEach-Object {
 $name,$value=$_.Split('=',2)
 if ($name -and $value) { Set-Item -LiteralPath "env:$name" -Value $value }
}
$env:DISTUTILS_USE_SDK='1'
$env:MSSdk='1'

$nvcc=(Get-Command nvcc.exe -ErrorAction SilentlyContinue)
if (-not $nvcc) { throw 'Install an NVIDIA CUDA Toolkit supported by the installed PyTorch releases.' }
$cudaText=(& $nvcc.Source --version) -join "`n"
if ($cudaText -notmatch 'release\s+(\d+\.\d+)') { throw 'Could not determine the installed CUDA Toolkit version.' }
$cudaVersion=$Matches[1]
$cudaWheel=@{'13.0'='cu130';'12.8'='cu128';'12.6'='cu126';'12.4'='cu124'}[$cudaVersion]
if (-not $cudaWheel) { throw "CUDA Toolkit $cudaVersion is not supported by this setup. Install CUDA 13.0, 12.8, 12.6, or 12.4." }

& py "-$PythonVersion" -c 'import sys; print(sys.version)'
if ($LASTEXITCODE) { throw "Install standard Windows Python $PythonVersion, then run this setup again." }
if (-not (Test-Path -LiteralPath (Join-Path $repo '.git'))) {
 git clone https://github.com/Stability-AI/stable-fast-3d.git $repo
 if ($LASTEXITCODE) { throw 'Could not clone Stable Fast 3D.' }
}
if (-not (Test-Path -LiteralPath (Join-Path $venv 'Scripts\python.exe'))) {
 & py "-$PythonVersion" -m venv $venv
 if ($LASTEXITCODE) { throw 'Could not create the Stable Fast 3D environment.' }
}
$python=Join-Path $venv 'Scripts\python.exe'
$setuptools=if ($cudaWheel -eq 'cu130') {'setuptools>=77.0.3'} else {'setuptools==69.5.1'}
& $python -m pip install --upgrade pip wheel $setuptools
if ($LASTEXITCODE) { throw 'Could not prepare pip.' }
& $python -m pip install --upgrade torch torchvision --index-url "https://download.pytorch.org/whl/$cudaWheel"
if ($LASTEXITCODE) { throw 'Could not install CUDA-enabled PyTorch.' }
Push-Location $repo
try {
 # The bundled CUDA extensions import torch during setup, so they must build
 # against the PyTorch already installed in this environment.
 & $python -m pip install --no-build-isolation -r requirements.txt
 if ($LASTEXITCODE) { throw 'Could not install Stable Fast 3D dependencies.' }
} finally { Pop-Location }

Write-Host ''
Write-Host 'Stable Fast 3D is installed.' -ForegroundColor Green
Write-Host 'Before first use, request access to stabilityai/stable-fast-3d on Hugging Face and run:'
Write-Host "  $(Join-Path $venv 'Scripts\huggingface-cli.exe') login"
