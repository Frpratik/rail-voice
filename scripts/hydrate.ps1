$paths = @(
    "c:\Users\prati\OneDrive\Desktop\RailVoice\railvoice-backend",
    "c:\Users\prati\OneDrive\Desktop\RailVoice\railvoice-web"
)

foreach ($p in $paths) {
    Get-ChildItem -Path $p -File -Recurse -Force | ForEach-Object {
        if ($_.FullName -notmatch "(\\node_modules\\|\\\.venv\\|\\\.next\\|\\\.git\\)") {
            try {
                $b = [System.IO.File]::ReadAllBytes($_.FullName)
                [System.IO.File]::Delete($_.FullName)
                [System.IO.File]::WriteAllBytes($_.FullName, $b)
            } catch {
                Write-Host "Skipped: " $_.FullName
            }
        }
    }
}
Write-Host "Hydration complete with accurate regex!"
