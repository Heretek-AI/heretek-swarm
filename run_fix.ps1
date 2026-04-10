# Run DeepSource Anti-Pattern Fixer
$ErrorActionPreference = "Continue"
Write-Host "Starting DeepSource Anti-Pattern Fixer..."
Write-Host "=========================================="

$scriptPath = "C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\fix_antipatterns_v2.py"
$logPath = "C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\fix_output.txt"

try {
    $result = & python $scriptPath 2>&1
    $result | Out-File -FilePath $logPath -Encoding UTF8
    Write-Host "Fixes completed. See $logPath for details."
} catch {
    Write-Host "Error running script: $_"
    $_.Exception.Message | Out-File -FilePath $logPath -Encoding UTF8
}
