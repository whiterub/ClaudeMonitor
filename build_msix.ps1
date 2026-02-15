# ClaudeMonitor MSIX Build Pipeline
# Usage: .\build_msix.ps1 [-SkipBuild] [-Sign]
#   -SkipBuild : Skip Nuitka build, use existing dist\main.dist output
#   -Sign      : Sign the MSIX with a self-signed certificate (for local testing)
#
# Requirements:
#   - Python 3.12 with nuitka<=2.5.9, customtkinter, pystray, Pillow
#   - Windows 10 SDK (makeappx.exe, makepri.exe, signtool.exe)
#   - Nuitka uses MinGW64 (auto-downloaded) for C compilation

param(
    [switch]$SkipBuild,
    [switch]$Sign
)

$ErrorActionPreference = "Stop"

# --- Configuration ---
$Version = "1.0.3.0"
$AppName = "ClaudeMonitor"
$ProjectRoot = $PSScriptRoot
$DistDir = Join-Path $ProjectRoot "dist\main.dist"
$MsixDir = Join-Path $ProjectRoot "msix"
$AssetsDir = Join-Path $MsixDir "Assets"
$PackageDir = Join-Path $ProjectRoot "msix_package"
$OutputMsix = Join-Path $ProjectRoot "${AppName}_${Version}_x64.msix"

# Find Windows SDK tools
$SdkBinPaths = @(
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64",
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22000.0\x64",
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64"
)

$SdkBin = $null
foreach ($path in $SdkBinPaths) {
    if (Test-Path (Join-Path $path "makeappx.exe")) {
        $SdkBin = $path
        break
    }
}

if (-not $SdkBin) {
    Write-Error "Windows SDK not found. Install Windows 10 SDK."
    exit 1
}

$MakeAppx = Join-Path $SdkBin "makeappx.exe"
$MakePri = Join-Path $SdkBin "makepri.exe"
$SignTool = Join-Path $SdkBin "signtool.exe"

Write-Host "=== ClaudeMonitor MSIX Build Pipeline ===" -ForegroundColor Cyan
Write-Host "Version: $Version"
Write-Host "SDK: $SdkBin"
Write-Host ""

# --- Step 1: Generate icon assets ---
Write-Host "[1/6] Generating icon assets..." -ForegroundColor Yellow
python (Join-Path $ProjectRoot "generate_icons.py")
if ($LASTEXITCODE -ne 0) {
    Write-Error "Icon generation failed."
    exit 1
}
Write-Host ""

# --- Step 2: Nuitka standalone build ---
if (-not $SkipBuild) {
    Write-Host "[2/6] Running Nuitka standalone build..." -ForegroundColor Yellow
    Push-Location $ProjectRoot
    & cmd /c "build_standalone.bat"
    Pop-Location
    if (-not (Test-Path (Join-Path $DistDir "ClaudeMonitor.exe"))) {
        Write-Error "Nuitka build failed. ClaudeMonitor.exe not found in $DistDir"
        exit 1
    }
} else {
    Write-Host "[2/6] Skipping Nuitka build (using existing output)..." -ForegroundColor DarkYellow
    if (-not (Test-Path (Join-Path $DistDir "ClaudeMonitor.exe"))) {
        Write-Error "No existing build found at $DistDir. Run without -SkipBuild."
        exit 1
    }
}
Write-Host ""

# --- Step 3: Assemble package layout ---
Write-Host "[3/6] Assembling package layout..." -ForegroundColor Yellow

# Clean previous package directory
if (Test-Path $PackageDir) {
    Remove-Item -Recurse -Force $PackageDir
}
New-Item -ItemType Directory -Path $PackageDir -Force | Out-Null

# Copy Nuitka output (entire standalone directory)
Write-Host "  Copying Nuitka output..."
Copy-Item -Path "$DistDir\*" -Destination $PackageDir -Recurse -Force

# Copy MSIX icon assets
$PkgAssetsDir = Join-Path $PackageDir "Assets"
New-Item -ItemType Directory -Path $PkgAssetsDir -Force | Out-Null
Copy-Item -Path "$AssetsDir\*.png" -Destination $PkgAssetsDir -Force
Write-Host "  Copied icon assets to Assets\"

# Copy AppxManifest.xml
Copy-Item -Path (Join-Path $MsixDir "AppxManifest.xml") -Destination $PackageDir -Force
Write-Host "  Copied AppxManifest.xml"
Write-Host ""

# --- Step 4: Generate resources.pri ---
Write-Host "[4/6] Generating resources.pri..." -ForegroundColor Yellow

$PriConfigPath = Join-Path $PackageDir "priconfig.xml"

# Create pri config
& $MakePri createconfig /cf $PriConfigPath /dq "ko-KR_en-US" /o
if ($LASTEXITCODE -ne 0) {
    Write-Warning "makepri createconfig failed. Trying without resources.pri..."
} else {
    & $MakePri new /pr $PackageDir /cf $PriConfigPath /of (Join-Path $PackageDir "resources.pri") /o
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "makepri new failed. Continuing without resources.pri..."
    } else {
        Write-Host "  Generated resources.pri"
    }
}

# Clean up pri config file from package
if (Test-Path $PriConfigPath) {
    Remove-Item $PriConfigPath -Force
}
Write-Host ""

# --- Step 5: Pack MSIX ---
Write-Host "[5/6] Packing MSIX..." -ForegroundColor Yellow

if (Test-Path $OutputMsix) {
    Remove-Item $OutputMsix -Force
}

& $MakeAppx pack /d $PackageDir /p $OutputMsix /o
if ($LASTEXITCODE -ne 0) {
    Write-Error "makeappx pack failed."
    exit 1
}

$msixSize = (Get-Item $OutputMsix).Length / 1MB
Write-Host "  Created: $OutputMsix ($([math]::Round($msixSize, 1)) MB)" -ForegroundColor Green
Write-Host ""

# --- Step 6: Sign (optional) ---
if ($Sign) {
    Write-Host "[6/6] Signing MSIX with self-signed certificate..." -ForegroundColor Yellow

    $CertSubject = "CN=ClaudeMonitor-Dev"
    $PfxPath = Join-Path $ProjectRoot "ClaudeMonitor-Dev.pfx"
    $PfxPassword = "ClaudeMonitorDev2024"

    # Check if cert already exists
    $existingCert = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Subject -eq $CertSubject } | Select-Object -First 1

    if (-not $existingCert) {
        Write-Host "  Creating self-signed certificate..."
        $cert = New-SelfSignedCertificate `
            -Type Custom `
            -Subject $CertSubject `
            -KeyUsage DigitalSignature `
            -FriendlyName "ClaudeMonitor Development" `
            -CertStoreLocation "Cert:\CurrentUser\My" `
            -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")

        $securePassword = ConvertTo-SecureString -String $PfxPassword -Force -AsPlainText
        Export-PfxCertificate -Cert $cert -FilePath $PfxPath -Password $securePassword | Out-Null
        Write-Host "  Certificate created and exported to $PfxPath"
    } else {
        Write-Host "  Using existing certificate: $CertSubject"
        if (-not (Test-Path $PfxPath)) {
            $securePassword = ConvertTo-SecureString -String $PfxPassword -Force -AsPlainText
            Export-PfxCertificate -Cert $existingCert -FilePath $PfxPath -Password $securePassword | Out-Null
        }
    }

    # Sign the MSIX
    & $SignTool sign /fd SHA256 /a /f $PfxPath /p $PfxPassword $OutputMsix
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Signing failed."
        exit 1
    }
    Write-Host "  MSIX signed successfully" -ForegroundColor Green

    Write-Host ""
    Write-Host "  NOTE: To install, first trust the certificate:" -ForegroundColor Yellow
    Write-Host "    1. Double-click $PfxPath"
    Write-Host "    2. Install to 'Local Machine' > 'Trusted Root Certification Authorities'"
    Write-Host "    3. Then double-click $OutputMsix to install"
} else {
    Write-Host "[6/6] Skipping signing (use -Sign flag for local testing)" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "=== Build Complete ===" -ForegroundColor Green
Write-Host "MSIX: $OutputMsix"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. For local testing: .\build_msix.ps1 -Sign -SkipBuild"
Write-Host "  2. For Store submission: Upload $OutputMsix to Partner Center"
Write-Host "     (Update AppxManifest.xml Publisher values from Partner Center first)"
