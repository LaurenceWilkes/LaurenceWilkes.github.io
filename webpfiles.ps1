# Local directory containing files to convert
$localDirectory = "C:\Users\Laurie\OneDrive\Documents\Projects\Website\images\kmeansascii"

# Directory to save the converted files
$destinationDirectory = "C:\Users\Laurie\OneDrive\Documents\Projects\Website\images\kmeansascii"

# Quality level for conversion
$quality = Read-Host "Enter quality level (0-100):"

# Get all files in the local directory
$files = Get-ChildItem -Path $localDirectory | Where-Object { -not $_.PSIsContainer }

# Path to cwebp executable
$cwebpPath = "C:\Users\Laurie\OneDrive\Apps\libwebp-1.6.0-windows-x64\bin\cwebp.exe"

# Iterate over files
foreach ($file in $files) {
    # Construct the output file path in the destination directory with the same file name
    $outputFileName = $file.Name -replace '\.jpg$', '.webp'
    $outputFile = Join-Path -Path $destinationDirectory -ChildPath $outputFileName

    # Run cwebp with the appropriate arguments
    & $cwebpPath -q $quality $file.FullName -o $outputFile
}
