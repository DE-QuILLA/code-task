# PowerShell 스크립트: UTF-8 BOM 제거 후 저장
$utf8NoBOM = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllLines(".secrets.baseline", (Get-Content ".secrets.baseline"), $utf8NoBOM)
Write-Output "Converted .secrets.baseline to UTF-8 without BOM"
