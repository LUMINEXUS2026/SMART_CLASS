$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$env:PYTHONPATH = Join-Path $projectRoot ".deps"

Write-Host ""
Write-Host "EduCam / Smart Class RRO server" -ForegroundColor Cyan
Write-Host "Project: $projectRoot"
Write-Host ""
Write-Host "Open on this PC:"
Write-Host "  http://127.0.0.1:5000/auth/login" -ForegroundColor Green
Write-Host ""
Write-Host "Open on another PC in the same network:"
$ips = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
  Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" -and $_.IPAddress -notlike "172.19.*" } |
  Select-Object -ExpandProperty IPAddress
if (-not $ips) {
  $ips = (ipconfig | Select-String "IPv4" | ForEach-Object { ($_ -split ":")[-1].Trim() })
}
foreach ($ip in $ips) {
  Write-Host "  http://$ip`:5000/auth/login" -ForegroundColor Green
  Write-Host "  http://$ip`:5000/admin/cameras/classroom-5/demo" -ForegroundColor Green
}
Write-Host ""
Write-Host "Accounts:"
Write-Host "  admin@example.com / password"
Write-Host "  teacher1@example.com / password"
Write-Host "  parent1@example.com / password"
Write-Host ""
Write-Host "If another PC cannot open the link, allow inbound TCP port 5000 in Windows Firewall." -ForegroundColor Yellow
Write-Host ""

Start-Process -WindowStyle Hidden -WorkingDirectory $projectRoot -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "camera_service\demo_state_simulator.py"

.\.venv\Scripts\python.exe run_public.py
