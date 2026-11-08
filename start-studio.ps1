$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$comfyProject = if ($env:UGC_COMFY_HOME) { $env:UGC_COMFY_HOME } else { (Join-Path $PSScriptRoot '..\ComfyUI') }
$comfyPython = Join-Path $comfyProject 'venv\Scripts\python.exe'
$comfyMain = Join-Path $comfyProject 'ComfyUI\main.py'
$studio = Join-Path $projectRoot '.venv\Scripts\ugc-studio.exe'

$envFile = Join-Path $projectRoot '.env'
if (Test-Path -LiteralPath $envFile) {
    foreach ($line in Get-Content -LiteralPath $envFile) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
        }
    }
}

try {
    Invoke-RestMethod 'http://127.0.0.1:8188/system_stats' -TimeoutSec 2 | Out-Null
} catch {
    if (-not (Test-Path -LiteralPath $comfyPython) -or -not (Test-Path -LiteralPath $comfyMain)) {
        throw "No se encontró ComfyUI en $comfyProject. Define UGC_COMFY_HOME con su carpeta."
    }
    Start-Process -FilePath $comfyPython -ArgumentList @($comfyMain, '--listen', '127.0.0.1', '--port', '8188') -WorkingDirectory (Join-Path $comfyProject 'ComfyUI') -WindowStyle Hidden
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        Start-Sleep -Seconds 1
        try {
            Invoke-RestMethod 'http://127.0.0.1:8188/system_stats' -TimeoutSec 2 | Out-Null
            break
        } catch {
            if ($attempt -eq 59) { throw 'ComfyUI no respondió después de 60 segundos.' }
        }
    }
}

& $studio
