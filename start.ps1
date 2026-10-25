# Starts the whole app on Windows with one command: .\start.bat
# Opens the backend and the frontend in two new windows, waits for the server, then opens the app.
# To stop: close the two windows (or press Ctrl+C in each).

$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

# 1. Backend environment must exist (first-time setup is in README Section 3)
if (-not (Test-Path $python)) {
    Write-Host "The backend is not installed yet. Follow README Section 3, Step 1, then run start.bat again." -ForegroundColor Red
    exit 1
}

# 2. Create backend/.env with a random secret key if it is missing (it is never committed)
$envFile = Join-Path $backend ".env"
if (-not (Test-Path $envFile)) {
    & $python -c "import secrets; open(r'$envFile','w').write('SECRET_KEY='+secrets.token_hex(32)+'\n')"
    Write-Host "Created backend/.env with a new random secret key."
}

# 3. Install the web app packages the first time
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "Installing the web app packages (first time only)..."
    Push-Location $frontend; npm install; Pop-Location
}

# 4. Start both servers in their own windows
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle='Backend (FastAPI)'; Set-Location '$backend'; & '$python' -m uvicorn app.main:app"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle='Frontend (Vite)'; Set-Location '$frontend'; npm run dev"

# 5. Wait until the model is loaded (up to 4 minutes on a slow laptop), then open the app
Write-Host "Starting... loading the model can take up to a minute or two on a laptop."
$clock = [Diagnostics.Stopwatch]::StartNew()
$ready = $false
while ($clock.Elapsed.TotalSeconds -lt 240) {
    Start-Sleep -Seconds 3
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
        if ($health.model_loaded) { $ready = $true; break }
    } catch { }
}
$seconds = [int]$clock.Elapsed.TotalSeconds
if ($ready) {
    Write-Host "Ready after $seconds s. Opening http://localhost:5173 (API docs: http://localhost:8000/docs)" -ForegroundColor Green
} else {
    Write-Host "The backend is not ready after $seconds s. Opening the app anyway; if it cannot connect, look at the 'Backend (FastAPI)' window." -ForegroundColor Yellow
}
Start-Process "http://localhost:5173"
