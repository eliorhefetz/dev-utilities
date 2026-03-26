param(
    [ValidateSet("css", "js", "all")]
    [string]$Type = "all",

    [string]$Root = "."
)

$ErrorActionPreference = "Stop"

function Get-CssPath {
    param([string]$BasePath)
    return Join-Path $BasePath "css"
}

function Get-JsPath {
    param([string]$BasePath)
    return Join-Path $BasePath "js"
}

function Get-CssFiles {
    param([string]$CssPath)

    return Get-ChildItem -Path $CssPath -Filter *.css -File |
        Where-Object { $_.Name -notlike "*.min.css" }
}

function Get-JsFiles {
    param([string]$JsPath)

    return Get-ChildItem -Path $JsPath -Filter *.js -File |
        Where-Object { $_.Name -notlike "*.min.js" }
}

function Test-CssReady {
    param([string]$BasePath)

    $errors = @()
    $cssPath = Get-CssPath -BasePath $BasePath

    if (-not (Test-Path $cssPath)) {
        $errors += "CSS folder not found: $cssPath"
        return @{
            IsValid = $false
            Files = @()
            Errors = $errors
        }
    }

    $cssFiles = Get-CssFiles -CssPath $cssPath

    if (-not $cssFiles -or $cssFiles.Count -eq 0) {
        $errors += "No CSS files found in: $cssPath"
    }

    return @{
        IsValid = ($errors.Count -eq 0)
        Files = $cssFiles
        Errors = $errors
    }
}

function Test-JsReady {
    param([string]$BasePath)

    $errors = @()
    $jsPath = Get-JsPath -BasePath $BasePath

    if (-not (Test-Path $jsPath)) {
        $errors += "JS folder not found: $jsPath"
        return @{
            IsValid = $false
            Files = @()
            Errors = $errors
        }
    }

    $jsFiles = Get-JsFiles -JsPath $jsPath

    if (-not $jsFiles -or $jsFiles.Count -eq 0) {
        $errors += "No JS files found in: $jsPath"
    }

    return @{
        IsValid = ($errors.Count -eq 0)
        Files = $jsFiles
        Errors = $errors
    }
}

function Invoke-CssMinify {
    param([array]$Files)

    foreach ($file in $Files) {
        $outputFile = Join-Path $file.DirectoryName ($file.BaseName + ".min.css")
        Write-Host "Minifying CSS: $($file.Name) -> $(Split-Path $outputFile -Leaf)"
        cleancss -o $outputFile $file.FullName

        if (-not (Test-Path $outputFile)) {
            throw "CSS minify failed for: $($file.FullName)"
        }
    }
}

function Invoke-JsMinify {
    param([array]$Files)

    foreach ($file in $Files) {
        $outputFile = Join-Path $file.DirectoryName ($file.BaseName + ".min.js")
        Write-Host "Minifying JS: $($file.Name) -> $(Split-Path $outputFile -Leaf)"
        terser $file.FullName -o $outputFile --compress --mangle

        if (-not (Test-Path $outputFile)) {
            throw "JS minify failed for: $($file.FullName)"
        }
    }
}

try {
    switch ($Type) {
        "css" {
            $cssCheck = Test-CssReady -BasePath $Root

            if (-not $cssCheck.IsValid) {
                foreach ($message in $cssCheck.Errors) {
                    Write-Host "Error: $message" -ForegroundColor Red
                }
                exit 1
            }

            Invoke-CssMinify -Files $cssCheck.Files
        }

        "js" {
            $jsCheck = Test-JsReady -BasePath $Root

            if (-not $jsCheck.IsValid) {
                foreach ($message in $jsCheck.Errors) {
                    Write-Host "Error: $message" -ForegroundColor Red
                }
                exit 1
            }

            Invoke-JsMinify -Files $jsCheck.Files
        }

        "all" {
            $cssCheck = Test-CssReady -BasePath $Root
            $jsCheck = Test-JsReady -BasePath $Root

            $allErrors = @()
            $allErrors += $cssCheck.Errors
            $allErrors += $jsCheck.Errors

            if ($allErrors.Count -gt 0) {
                foreach ($message in $allErrors) {
                    Write-Host "Error: $message" -ForegroundColor Red
                }
                exit 1
            }

            Invoke-CssMinify -Files $cssCheck.Files
            Invoke-JsMinify -Files $jsCheck.Files
        }
    }

    Write-Host ""
    Write-Host "Minification completed successfully."
}
catch {
    Write-Host ""
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}