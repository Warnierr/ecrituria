# ========================================
# Script d'ajout rapide de contenu
# ========================================
# Usage: .\add-content.ps1 "fichier.md" "Votre contenu ici"

param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath,
    
    [Parameter(Mandatory = $true)]
    [string]$Content,
    
    [string]$Action = "append",  # append, rewrite, create
    [string]$Project = "anomalie2084"
)

Write-Host "`n📝 Ajout de contenu via Writer Mode..." -ForegroundColor Cyan
Write-Host "Fichier: $FilePath" -ForegroundColor Yellow
Write-Host "Action: $Action`n" -ForegroundColor Yellow

# Créer la requête JSON
$request = @{
    action        = $Action
    file_path     = $FilePath
    instruction   = "Ajoute exactement ce contenu sans le modifier : `n`n$Content"
    preview_only  = $false
    context_files = @()
} | ConvertTo-Json -Depth 10

# Sauvegarder dans un fichier temporaire
$tempFile = "temp_request.json"
$request | Out-File -FilePath $tempFile -Encoding utf8

try {
    # Appeler l'API
    $response = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/ai-write/$Project" -InFile $tempFile -ContentType "application/json"
    
    if ($response.success) {
        Write-Host "✅ SUCCÈS !`n" -ForegroundColor Green
        Write-Host "Fichier: $($response.file_path)" -ForegroundColor Cyan
        Write-Host "Mode: $($response.mode)" -ForegroundColor Yellow
        
        if ($response.backup_created) {
            Write-Host "💾 Backup créé" -ForegroundColor Magenta
        }
        
        Write-Host "`nContenu ajouté:" -ForegroundColor Green
        Write-Host $Content
    }
    else {
        Write-Host "❌ Échec" -ForegroundColor Red
    }
    
}
catch {
    Write-Host "`n❌ ERREUR:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}
finally {
    # Nettoyer
    if (Test-Path $tempFile) {
        Remove-Item $tempFile
    }
}

Write-Host "`n✨ Terminé !`n"
