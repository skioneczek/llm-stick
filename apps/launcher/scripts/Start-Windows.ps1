# Portable launcher entry point for Windows development builds.
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$StickRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
$env:LLM_STICK_ROOT = $StickRoot

$Python = if ($env:PYTHON) { $env:PYTHON } else { "python" }

& $Python -m apps.launcher
