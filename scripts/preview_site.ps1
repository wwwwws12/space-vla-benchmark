param([ValidateRange(1024,65535)][int]$Port = 8766, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$python = Get-Command python.exe -ErrorAction SilentlyContinue
if (-not $python) { throw 'Python 3 is required to serve the local preview.' }
Write-Host "Local acceptance preview: http://127.0.0.1:$Port/index.zh-CN.html"
Write-Host 'Keep this window open. Ctrl+C stops the local preview. No external hosting or upload.'
$previewArgs = @('-B', (Join-Path $PSScriptRoot 'preview_site.py'), '--port', $Port)
if ($NoBrowser) { $previewArgs += '--no-browser' }
& $python.Source @previewArgs
if ($LASTEXITCODE -ne 0) { throw 'Local preview server stopped with an error.' }
