param(
    [string]$StickRoot = (Resolve-Path "$PSScriptRoot/../stick_root"),
    [string]$Python = "python",
    [string]$VendorDir = (Resolve-Path "$PSScriptRoot/../vendor"),
    [ValidateSet("pyinstaller", "nuitka")]
    [string]$Backend = "pyinstaller"
)

$ErrorActionPreference = "Stop"

function Assert-Path {
    param(
        [string]$Path,
        [string]$Message
    )
    if (-not (Test-Path $Path)) {
        throw $Message
    }
}

Assert-Path -Path $StickRoot -Message "Stick root '$StickRoot' is missing. Create the layout before packaging."
Assert-Path -Path $VendorDir -Message "Vendor cache '$VendorDir' is missing. Populate offline dependencies first."

$BuildRoot = Join-Path $PSScriptRoot ".build/windows"
$VenvPath = Join-Path $BuildRoot ".venv"
$DistDir = Join-Path $BuildRoot "dist"
$SpecDir = Join-Path $BuildRoot "spec"

New-Item -ItemType Directory -Force -Path $BuildRoot | Out-Null
New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
New-Item -ItemType Directory -Force -Path $SpecDir | Out-Null

if (-not (Test-Path $VenvPath)) {
    & $Python -m venv $VenvPath
}

$VenvPython = Join-Path $VenvPath "Scripts/python.exe"

$PipArgs = @("install", "--no-index", "--find-links", (Join-Path $VendorDir "wheels"))
if ($Backend -eq "pyinstaller") {
    & $VenvPython -m pip @PipArgs "pyinstaller"
} else {
    & $VenvPython -m pip @PipArgs "nuitka", "zstandard"
}

$RepoRoot = Resolve-Path "$PSScriptRoot/.."
$EntryPoint = Join-Path $RepoRoot "apps/launcher/__main__.py"

if ($Backend -eq "pyinstaller") {
    $Args = @(
        "--clean",
        "--noconfirm",
        "--name", "Start-Windows",
        "--onedir",
        "--distpath", $DistDir,
        "--workpath", (Join-Path $BuildRoot "build"),
        "--specpath", $SpecDir,
        "--hidden-import", "apps.launcher",
        "--collect-submodules", "apps.launcher",
        $EntryPoint
    )
    & $VenvPython -m PyInstaller @Args
} else {
    $Args = @(
        "--standalone",
        "--onefile",
        "--output-dir", $DistDir,
        "--include-package=apps.launcher",
        $EntryPoint
    )
    & $VenvPython -m nuitka @Args
}

$ExePath = if ($Backend -eq "pyinstaller") {
    Join-Path $DistDir "Start-Windows/Start-Windows.exe"
} else {
    Join-Path $DistDir "Start-Windows.exe"
}

Assert-Path -Path $ExePath -Message "Build failed: missing Start-Windows executable."

Copy-Item $ExePath (Join-Path $StickRoot "Start-Windows.exe") -Force

$AppSource = Join-Path $RepoRoot "App"
if (-not (Test-Path $AppSource)) {
    throw "Missing App/ directory at $AppSource"
}
Copy-Item $AppSource (Join-Path $StickRoot "App") -Recurse -Force

foreach ($folder in @("Docs", "Samples")) {
    $src = Join-Path $RepoRoot $folder
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $StickRoot $folder) -Recurse -Force
    }
}

"Packaging complete. Output written to $StickRoot"
