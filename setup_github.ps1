# Run this script from INSIDE the taguchi_lib folder.
# Open Git Bash or PowerShell, cd into the folder, then run:
#   powershell -ExecutionPolicy Bypass -File setup_github.ps1
#
# Requires: git   (https://git-scm.com)
#           gh    (https://cli.github.com)  — needed for step 2 only

$repoName = "tagupy"
$repoDesc = "Taguchi experimental design and analysis library for vibration-based SHM research"
$ghUser   = "grcarmenaty"   # <-- change if your GitHub username differs

# ── 0. Remove any broken .git folder left from a previous attempt ─────────────
if (Test-Path ".git") {
    Write-Host "Removing existing .git folder..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force ".git"
}

# ── 1. Init & first commit ────────────────────────────────────────────────────
Write-Host "`n=== Initialising git repo ===" -ForegroundColor Cyan
git init
git branch -m main
git config user.name  "Guillermo Reyes-Carmenaty"
git config user.email "grcarmenaty@gmail.com"
git add .
git commit -m "Initial commit: tagupy v0.1.0"

# ── 2. Create GitHub repo and push ────────────────────────────────────────────
Write-Host "`n=== Creating GitHub repo ===" -ForegroundColor Cyan

if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh repo create "$ghUser/$repoName" `
        --public `
        --description $repoDesc `
        --source . `
        --remote origin `
        --push
    Write-Host "`nDone!  https://github.com/$ghUser/$repoName" -ForegroundColor Green
} else {
    Write-Host "gh CLI not found. Create the repo manually on github.com, then run:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  git remote add origin https://github.com/$ghUser/$repoName.git"
    Write-Host "  git push -u origin main"
    Write-Host ""
    Write-Host "Or install gh from https://cli.github.com and re-run this script."
}
