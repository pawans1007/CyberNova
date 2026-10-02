
$ProjectPath = "C:\Users\luffy\CyberNova"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ZipPath = Join-Path $DesktopPath "CyberNova_Source.zip"
$TempPath = Join-Path $env:TEMP "CyberNova_Source"

# Remove any previous temporary copy
if (Test-Path $TempPath) {
    Remove-Item $TempPath -Recurse -Force
}

New-Item -ItemType Directory -Path $TempPath -Force | Out-Null

# Folders and files to exclude
$ExcludedDirectories = @(
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".vscode",
    "models",
    "ollama_models"
)

$ExcludedFiles = @(
    ".env",
    ".env.local",
    ".env.production",
    "*.pyc",
    "*.pyo",
    "*.log",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx"
)

# Copy required project files
Get-ChildItem -LiteralPath $ProjectPath -Recurse -File -Force |
    ForEach-Object {
        $File = $_
        $RelativePath = $File.FullName.Substring($ProjectPath.Length).TrimStart("\")
        $Parts = $RelativePath -split '[\\/]'

        $Skip = $false

        foreach ($Part in $Parts) {
            if ($ExcludedDirectories -contains $Part) {
                $Skip = $true
                break
            }
        }

        foreach ($Pattern in $ExcludedFiles) {
            if ($File.Name -like $Pattern) {
                $Skip = $true
                break
            }
        }

        # Exclude common backup and temporary files
        if ($File.Name -match '\.(bak|tmp|swp)$' -or
            $File.Name -match '^~\$') {
            $Skip = $true
        }

        if (-not $Skip) {
            $Destination = Join-Path $TempPath $RelativePath
            $DestinationDirectory = Split-Path $Destination -Parent

            New-Item -ItemType Directory -Path $DestinationDirectory -Force |
                Out-Null

            Copy-Item -LiteralPath $File.FullName -Destination $Destination -Force
        }
    }

# Create ZIP
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

Compress-Archive -Path (Join-Path $TempPath "*") -DestinationPath $ZipPath -CompressionLevel Optimal

# Clean temporary copy
Remove-Item $TempPath -Recurse -Force

Write-Host ""
Write-Host "ZIP created successfully:"
Write-Host $ZipPath -ForegroundColor Green