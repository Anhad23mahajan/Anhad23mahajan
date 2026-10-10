# deliver.ps1 - copies the finished Lumen code into Eshaan's repo and commits it in logical steps under YOUR git identity.
# Run in Windows PowerShell:   powershell -ExecutionPolicy Bypass -File .\deliver.ps1
# Needs: Git for Windows (https://git-scm.com/download/win). The first push opens a browser sign-in to GitHub (Git Credential Manager).
# Commits are authored by whatever name/email your git is configured with. Use a normal PowerShell window (not the ISE).

$ErrorActionPreference = "Continue"   # git prints progress on stderr; failures are caught by the explicit exit-code checks below
$ProfileRepo = "https://github.com/Anhad23mahajan/Anhad23mahajan.git"
$ProfileBranch = "claude/confident-brown-ayxkb3"
$TeamRepo = "https://github.com/Eshaan1e24/Lumen.git"
$Work = Join-Path $HOME "lumen-delivery"

function Run($cmd) { Write-Host ">> $cmd" -ForegroundColor Cyan; Invoke-Expression $cmd; if ($LASTEXITCODE -ne 0) { throw "Command failed: $cmd" } }

# 0. who am I? (commits will carry this identity)
$name = (git config --global user.name); $email = (git config --global user.email)
if (-not $name)  { $name  = Read-Host "Your name for commits (e.g. Anhad Mahajan)"; git config --global user.name  "$name" }
if (-not $email) { $email = Read-Host "Your email for commits (the one on your GitHub account)"; git config --global user.email "$email" }
Write-Host "Commits will be authored by: $name <$email>" -ForegroundColor Green

# 1. fresh working folder
if (Test-Path $Work) { Remove-Item -Recurse -Force $Work -ErrorAction Stop }
New-Item -ItemType Directory -Path $Work -ErrorAction Stop | Out-Null
Set-Location $Work -ErrorAction Stop

# 2. get the finished code and the team repo
Run "git clone --depth 1 --branch $ProfileBranch $ProfileRepo code"
Run "git clone $TeamRepo team"
if (-not (Test-Path "code\lumen\app\main.py")) { throw "code\lumen\app\main.py not found - wrong branch?" }
Set-Location "$Work\team" -ErrorAction Stop
Run "git checkout main"
Run "git pull --ff-only"

# safety: this code was built on top of Eshaan's commit 66c6405. If he has pushed newer work, copying over it would overwrite his changes.
$base = "66c6405ad4a7c7284ef6af42e26ea3d5a7557567"
$head = (git rev-parse HEAD)
if ($head -ne $base) {
    Write-Host "Eshaan's main has moved since the code was built on it:" -ForegroundColor Yellow
    git log --oneline "$base..HEAD"
    Write-Host "Copying now would overwrite those changes in any file we both edited (static/index.html, app/*.py, README.md, requirements.txt)." -ForegroundColor Yellow
    $go = Read-Host "Type overwrite to continue anyway, or anything else to stop and tell your assistant"
    if ($go -ne "overwrite") { throw "Stopped: main has newer commits." }
}

# 3. copy the code over (everything under lumen/, no git metadata, no caches)
robocopy "$Work\code\lumen" "$Work\team" /E /XD .git __pycache__ .pytest_cache .venv /XF *.pyc /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }
$global:LASTEXITCODE = 0
git config core.autocrlf false

# 4. commit in logical steps (order keeps each step importable)
function Step($message, $paths) {
    $existing = @(); foreach ($p in $paths) { if (Test-Path $p) { $existing += $p } }
    if ($existing.Count -eq 0) { Write-Host "skip (nothing): $message"; return }
    git add -- $existing
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) { git commit -q -m "$message"; Write-Host "committed: $message" -ForegroundColor Green }
    $global:LASTEXITCODE = 0
}

Step "Pin dependencies, Python 3.13 Dockerfile, Render config, license" @("requirements.txt","requirements-dev.txt","Dockerfile",".dockerignore","render.yaml",".env.example",".gitignore",".gitattributes","LICENSE","pytest.ini")
Step "Replace regex SQL guard with a parser-based guard and hardened DuckDB sandbox" @("app/sqlguard.py","tests/__init__.py","tests/test_sqlguard.py")
Step "Add backtest-selected forecaster with ranges from past errors" @("app/forecasting.py","tests/test_forecasting.py")
Step "Add what-changed analysis and daily spike detection" @("app/drivers.py","tests/test_drivers.py")
Step "Make ingestion robust: header rows, Excel sheets, encodings, number and date formats; fix insight bugs" @("app/analytics.py","tests/fixtures","tests/test_fixtures.py")
Step "Add session store, rate limiter and upload size checks" @("app/limits.py","tests/test_limits.py")
Step "Rebuild question answering: second-query cross-check, number grounding, model fail-over, demo mode, samples" @("app/llm.py","app/samples.py","tests/test_llm.py")
Step "Wire API: limits, samples, demo fallback, security headers; test the API end to end" @("app/main.py","tests/test_api.py")
Step "UI: bundled Plotly and fonts, sample picker, answer checks, forecast panel, accessibility" @("static")
Step "Add evaluation harness and benchmarks" @("evals","tests/test_evals.py")
Step "Documentation: README, architecture diagram, screenshots" @("README.md","docs")
# anything left over (so nothing is silently dropped)
git add -A
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) { git commit -q -m "Add remaining project files"; Write-Host "committed: remaining files" -ForegroundColor Yellow }
$global:LASTEXITCODE = 0

Write-Host ""; git log --oneline -15
Write-Host ""
$ans = Read-Host "Push these commits to $TeamRepo (branch main)? Type yes to push"
if ($ans -eq "yes") { Run "git push origin main"; Write-Host "Done. Check https://github.com/Eshaan1e24/Lumen" -ForegroundColor Green }
else { Write-Host "Not pushed. The commits are in $Work\team - run 'git push origin main' there when ready." }
