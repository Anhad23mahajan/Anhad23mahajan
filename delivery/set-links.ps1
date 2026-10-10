# set-links.ps1 - after deploying and uploading the video: puts the live URL and video URL into the README and pushes one small commit.
# Run:   powershell -ExecutionPolicy Bypass -File .\set-links.ps1
$ErrorActionPreference = "Continue"
$Work = Join-Path $HOME "lumen-delivery\team"
if (-not (Test-Path $Work)) { throw "Run deliver.ps1 first ($Work not found)." }
Set-Location $Work -ErrorAction Stop
git checkout main; git pull --ff-only
$live  = Read-Host "Live demo URL (https://...onrender.com)"
$video = Read-Host "YouTube video URL (https://youtu.be/...)"
if ($live -notmatch "^https://" -or $video -notmatch "^https://") { throw "Both links must start with https://" }
$text = [System.IO.File]::ReadAllText("$Work\README.md")
$text = $text.Replace("LIVE_URL_PLACEHOLDER", $live).Replace("VIDEO_URL_PLACEHOLDER", $video)
[System.IO.File]::WriteAllText("$Work\README.md", $text, (New-Object System.Text.UTF8Encoding($false)))
if (Select-String -Path README.md -Pattern "PLACEHOLDER" -Quiet) { throw "A placeholder is still in README.md" }
git add README.md
git commit -m "Add live demo and demo video links"
git push origin main
Write-Host "Done." -ForegroundColor Green
