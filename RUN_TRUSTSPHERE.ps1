$ScriptPath = Join-Path $PSScriptRoot "scripts\start_trustsphere_stack.ps1"
powershell -ExecutionPolicy Bypass -File $ScriptPath
