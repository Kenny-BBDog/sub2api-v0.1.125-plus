$ErrorActionPreference = "Stop"

function New-HexSecret([int]$Bytes) {
  $bytes = New-Object byte[] $Bytes
  [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
  -join ($bytes | ForEach-Object { $_.ToString("x2") })
}

if (Test-Path ".env") {
  throw ".env already exists. Remove it first if you want to regenerate secrets."
}

$template = Get-Content ".env.example" -Raw
$template = $template.Replace("change-me-postgres-password", (New-HexSecret 24))
$template = $template.Replace("change-me-redis-password", (New-HexSecret 24))
$template = $template.Replace("change-me-admin-password", (New-HexSecret 16))
$template = $template.Replace("change-me-64-hex-jwt-secret", (New-HexSecret 32))
$template = $template.Replace("change-me-64-hex-totp-key", (New-HexSecret 32))
Set-Content -Path ".env" -Value $template -NoNewline

Write-Host "Generated .env. Review ADMIN_EMAIL and SERVER_PORT before starting."

