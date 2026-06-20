# Install mdir inside WSL from Windows PowerShell.
#
# Usage (in PowerShell):
#   cd C:\path\to\mdir
#   powershell -ExecutionPolicy Bypass -File scripts\setup-wsl-from-windows.ps1
#
# Or without a local clone (GitHub only):
#   wsl bash -lc "git clone https://github.com/jsjang-1126/mdir.git ~/apps/mdir && bash ~/apps/mdir/scripts/install-wsl.sh"

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/jsjang-1126/mdir.git"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$localRepo = Split-Path -Parent $scriptDir

Write-Host "Installing mdir in WSL ..." -ForegroundColor Cyan

if (Test-Path (Join-Path $localRepo "pyproject.toml")) {
    $drive = $localRepo.Substring(0, 1).ToLower()
    $rest = ($localRepo.Substring(2) -replace '\\', '/')
    $wslSource = "/mnt/$drive$rest"
    Write-Host "Copy local source from $wslSource"
    wsl bash -lc "set -e; mkdir -p ~/apps; rm -rf ~/apps/mdir; cp -a '$wslSource' ~/apps/mdir; bash ~/apps/mdir/scripts/install-wsl.sh ~/apps/mdir"
} else {
    Write-Host "Clone from GitHub into WSL ~/apps/mdir"
    wsl bash -lc "set -e; if [ -d ~/apps/mdir/.git ]; then cd ~/apps/mdir && git pull --ff-only; else git clone '$RepoUrl' ~/apps/mdir; fi; bash ~/apps/mdir/scripts/install-wsl.sh ~/apps/mdir"
}

Write-Host ""
Write-Host "Done. In WSL run:" -ForegroundColor Green
Write-Host "  source ~/.bashrc"
Write-Host "  mdir"
Write-Host "  mdir /mnt/c/Users"
