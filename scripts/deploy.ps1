# deploy.ps1 — rebuild and redeploy production containers
# Usage:
#   .\scripts\deploy.ps1              — rebuild everything
#   .\scripts\deploy.ps1 -Service frontend   — rebuild only frontend
#   .\scripts\deploy.ps1 -Service backend    — rebuild only backend
#
# IMPORTANT: must be run from the repo root (E:\taro_cards)
# The --env-file flag makes Docker Compose read .env.prod for build-arg
# substitution (NEXT_PUBLIC_* vars baked into the Next.js bundle).

param(
    [string]$Service = "all"
)

$EnvFile  = ".env.prod"
$Compose  = "docker-compose.prod.yml"
$DC       = "docker compose --env-file $EnvFile -f $Compose"

if (-not (Test-Path $EnvFile)) {
    Write-Error "Missing $EnvFile — cannot deploy without secrets."
    exit 1
}

function Rebuild-And-Restart($svc) {
    Write-Host "`n==> Building $svc ..." -ForegroundColor Cyan
    Invoke-Expression "$DC build $svc"
    if ($LASTEXITCODE -ne 0) { Write-Error "Build failed for $svc"; exit 1 }

    Write-Host "==> Restarting $svc ..." -ForegroundColor Cyan
    Invoke-Expression "$DC up -d --no-deps $svc"
    if ($LASTEXITCODE -ne 0) { Write-Error "Start failed for $svc"; exit 1 }
}

switch ($Service) {
    "frontend" { Rebuild-And-Restart "frontend" }
    "backend"  {
        Rebuild-And-Restart "backend"
        # worker shares the same image
        Invoke-Expression "$DC up -d --no-deps worker"
    }
    "all" {
        Rebuild-And-Restart "backend"
        Invoke-Expression "$DC up -d --no-deps worker"
        Rebuild-And-Restart "frontend"
    }
    default {
        Write-Error "Unknown service '$Service'. Use: frontend | backend | all"
        exit 1
    }
}

Write-Host "`n==> Done. Container status:" -ForegroundColor Green
Invoke-Expression "$DC ps"
