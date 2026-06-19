# Deploy mdir from Windows to iwin server.
# Run in PowerShell on your Windows PC (where iwin_key exists).
#
# Usage:
#   cd \\wsl$\... or clone path, OR adjust $LgNoteHost below
#   .\scripts\deploy-from-windows.ps1

$ErrorActionPreference = "Stop"

$IwinHost = "115.68.232.200"
$IwinUser = "root"
$KeyFile  = "$env:USERPROFILE\.ssh\iwin_key"
$LgNoteHost = "jsunrise1126@lg-note"   # change if your lg-note address differs
$RemoteDir = "apps/mdir"

if (-not (Test-Path $KeyFile)) {
    Write-Error "Key not found: $KeyFile"
}

Write-Host "1) Fetch mdir from lg-note ..."
$temp = Join-Path $env:TEMP "mdir-deploy"
if (Test-Path $temp) { Remove-Item -Recurse -Force $temp }
New-Item -ItemType Directory -Path $temp | Out-Null

ssh $LgNoteHost "tar czf - -C ~/apps mdir --exclude=mdir/.venv --exclude=mdir/__pycache__ --exclude=mdir/.git" |
    tar xzf - -C $temp

Write-Host "2) Upload to iwin ($IwinHost) ..."
ssh -i $KeyFile -o StrictHostKeyChecking=accept-new "${IwinUser}@${IwinHost}" "mkdir -p ~/$RemoteDir"
scp -i $KeyFile -r "$temp\mdir\*" "${IwinUser}@${IwinHost}:~/$RemoteDir/"

Write-Host "3) Install on iwin ..."
ssh -i $KeyFile "${IwinUser}@${IwinHost}" "bash ~/$RemoteDir/scripts/remote-setup.sh ~/$RemoteDir"

Write-Host ""
Write-Host "Done. Connect with:"
Write-Host "  ssh -i $KeyFile ${IwinUser}@${IwinHost}"
Write-Host "  mdir"
