param(
  [Parameter(Mandatory=$true)]
  [string]$OutputPath,
  [string]$WatermarkMain,
  [string]$WatermarkSub
)

$ErrorActionPreference = "Stop"

$skillRoot = Split-Path -Parent $PSScriptRoot
$template = Join-Path $skillRoot 'assets\slides-template-v3.html'

if (!(Test-Path $template)) {
  throw "Template not found: $template"
}

$outDir = Split-Path -Parent $OutputPath
if ($outDir -and !(Test-Path $outDir)) {
  New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

Copy-Item -Path $template -Destination $OutputPath -Force

if ($WatermarkMain -or $WatermarkSub) {
  $html = Get-Content -Path $OutputPath -Raw -Encoding UTF8

  if ($WatermarkMain) {
    $html = [regex]::Replace(
      $html,
      '<span class="brand-main">[\s\S]*?<\/span>',
      ('<span class="brand-main">' + [System.Security.SecurityElement]::Escape($WatermarkMain) + '</span>'),
      1
    )
  }

  if ($WatermarkSub) {
    $html = [regex]::Replace(
      $html,
      '<span class="brand-sub">[\s\S]*?<\/span>',
      ('<span class="brand-sub">' + [System.Security.SecurityElement]::Escape($WatermarkSub) + '</span>'),
      1
    )
  }

  Set-Content -Path $OutputPath -Value $html -Encoding UTF8
}

Write-Host "Slides scaffold created:" $OutputPath
