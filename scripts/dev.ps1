# AI Habitat — Development Launcher
# Starts backend (FastAPI) and frontend (Vite) in parallel.

Write-Host ""
Write-Host "=== AI Habitat — Starting Development Servers ===" -ForegroundColor Cyan
Write-Host ""

$backendJob = Start-Job -ScriptBlock {
    Set-Location "$using:PSScriptRoot\..\apps\api"
    & uvicorn app.main:app --reload --port 8000 2>&1
}

$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:PSScriptRoot\..\apps\web"
    & npm run dev 2>&1
}

Write-Host "Backend  → http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend → http://localhost:5173" -ForegroundColor Green
Write-Host "API Docs → http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop all servers." -ForegroundColor Yellow
Write-Host ""

try {
    while ($true) {
        Receive-Job -Job $backendJob -ErrorAction SilentlyContinue
        Receive-Job -Job $frontendJob -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
}
finally {
    Stop-Job -Job $backendJob, $frontendJob
    Remove-Job -Job $backendJob, $frontendJob
    Write-Host "Servers stopped." -ForegroundColor Red
}
