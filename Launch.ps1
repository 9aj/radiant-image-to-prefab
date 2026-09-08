$ErrorActionPreference = 'Stop'
try {
    & (Join-Path $PSScriptRoot 'ui\PrefabDrop.ps1')
} catch {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($_.Exception.Message, 'Prefab Drop could not start')
}
