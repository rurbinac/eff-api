# Start Cloud SQL Proxy for local DBeaver connection
# This script creates a local tunnel to the Cloud SQL database

Write-Host "=== Starting Cloud SQL Proxy ===" -ForegroundColor Green
Write-Host ""
Write-Host "This will create a local connection at: localhost:3306" -ForegroundColor Cyan
Write-Host "Connection String: sublime-scion-499902-m5:us-central1:eff-db" -ForegroundColor Cyan
Write-Host ""
Write-Host "In DBeaver, use:" -ForegroundColor Yellow
Write-Host "  Host: localhost"
Write-Host "  Port: 3306"
Write-Host "  Database: eff_db"
Write-Host "  Username: appuser"
Write-Host "  Password: (from Secret Manager)"
Write-Host ""

# Get the proxy path
$proxyPath = "C:\Users\rurbi\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\cloud-sql-proxy.exe"

if (-not (Test-Path $proxyPath)) {
    Write-Host "ERROR: cloud-sql-proxy not found at $proxyPath" -ForegroundColor Red
    exit 1
}

Write-Host "Starting proxy..." -ForegroundColor Green
Write-Host ""

# Start the proxy (cloud-sql-proxy v2 syntax)
& $proxyPath sublime-scion-499902-m5:us-central1:eff-db `
    --port 3306 `
    --address 127.0.0.1

# If we get here, proxy was closed
Write-Host ""
Write-Host "Proxy stopped. Press Enter to exit." -ForegroundColor Yellow
Read-Host
