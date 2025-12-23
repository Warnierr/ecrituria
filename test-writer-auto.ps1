# ========================================
# Test automatique du Writer Mode
# ========================================

Write-Host "`n🧪 TEST AUTOMATIQUE DU WRITER MODE" -ForegroundColor Cyan
Write-Host "=" * 60

$baseUrl = "http://localhost:8000/api/ai-write/anomalie2084"
$tests = @()

# ========================================
# TEST 1 : CREATE - Créer un nouveau fichier
# ========================================
Write-Host "`n📝 TEST 1: Créer un nouveau fichier" -ForegroundColor Yellow

$test1 = @{
    action        = "create"
    file_path     = "notes/test_writer_auto.md"
    instruction   = "Crée une note de 100 mots sur l'importance de la technologie open-source dans l'univers Anomalie 2084. Mentionne les Archives et le contrôle du savoir."
    preview_only  = $false
    context_files = @()
} | ConvertTo-Json -Depth 10

$test1 | Out-File "test1_create.json" -Encoding utf8

try {
    Write-Host "   Envoi de la requête..." -ForegroundColor Gray
    $result1 = Invoke-RestMethod -Method Post -Uri $baseUrl -InFile "test1_create.json" -ContentType "application/json"
    
    if ($result1.success) {
        Write-Host "   ✅ SUCCÈS - Fichier créé !" -ForegroundColor Green
        Write-Host "      Fichier: $($result1.file_path)" -ForegroundColor Cyan
        Write-Host "      Mode: $($result1.mode)" -ForegroundColor Cyan
        Write-Host "      Temps: $([math]::Round($result1.total_time, 2))s" -ForegroundColor Yellow
        Write-Host "      Taille: $($result1.content.Length) caractères" -ForegroundColor Cyan
        $tests += @{Test = "CREATE"; Status = "✅ PASS"; Time = $result1.total_time }
    }
    else {
        Write-Host "   ❌ ÉCHEC" -ForegroundColor Red
        $tests += @{Test = "CREATE"; Status = "❌ FAIL"; Time = 0 }
    }
}
catch {
    Write-Host "   ❌ ERREUR: $($_.Exception.Message)" -ForegroundColor Red
    $tests += @{Test = "CREATE"; Status = "❌ ERROR"; Time = 0 }
}

Start-Sleep -Seconds 2

# ========================================
# TEST 2 : APPEND - Ajouter du contenu
# ========================================
Write-Host "`n📝 TEST 2: Ajouter du contenu à un fichier existant" -ForegroundColor Yellow

$test2 = @{
    action        = "append"
    file_path     = "notes/test_writer_auto.md"
    instruction   = "Ajoute une section de 50 mots sur les dangers de la centralisation du savoir, en lien avec Lutéris."
    preview_only  = $false
    context_files = @()
} | ConvertTo-Json -Depth 10

$test2 | Out-File "test2_append.json" -Encoding utf8

try {
    Write-Host "   Envoi de la requête..." -ForegroundColor Gray
    $result2 = Invoke-RestMethod -Method Post -Uri $baseUrl -InFile "test2_append.json" -ContentType "application/json"
    
    if ($result2.success) {
        Write-Host "   ✅ SUCCÈS - Contenu ajouté !" -ForegroundColor Green
        Write-Host "      Fichier: $($result2.file_path)" -ForegroundColor Cyan
        Write-Host "      Mode: $($result2.mode)" -ForegroundColor Cyan
        Write-Host "      Temps: $([math]::Round($result2.total_time, 2))s" -ForegroundColor Yellow
        Write-Host "      Backup: $(if($result2.backup_created){'✅ Créé'}else{'❌ Non'})" -ForegroundColor Cyan
        $tests += @{Test = "APPEND"; Status = "✅ PASS"; Time = $result2.total_time }
    }
    else {
        Write-Host "   ❌ ÉCHEC" -ForegroundColor Red
        $tests += @{Test = "APPEND"; Status = "❌ FAIL"; Time = 0 }
    }
}
catch {
    Write-Host "   ❌ ERREUR: $($_.Exception.Message)" -ForegroundColor Red
    $tests += @{Test = "APPEND"; Status = "❌ ERROR"; Time = 0 }
}

Start-Sleep -Seconds 2

# ========================================
# TEST 3 : PREVIEW - Mode prévisualisation
# ========================================
Write-Host "`n📝 TEST 3: Prévisualisation sans sauvegarde" -ForegroundColor Yellow

$test3 = @{
    action        = "create"
    file_path     = "notes/test_preview_only.md"
    instruction   = "Génère 50 mots sur Alex Chen et son rôle dans la résistance."
    preview_only  = $true
    context_files = @()
} | ConvertTo-Json -Depth 10

$test3 | Out-File "test3_preview.json" -Encoding utf8

try {
    Write-Host "   Envoi de la requête..." -ForegroundColor Gray
    $result3 = Invoke-RestMethod -Method Post -Uri $baseUrl -InFile "test3_preview.json" -ContentType "application/json"
    
    if ($result3.success -and $result3.preview) {
        Write-Host "   ✅ SUCCÈS - Preview généré (non sauvegardé) !" -ForegroundColor Green
        Write-Host "      Preview: $($result3.preview)" -ForegroundColor Cyan
        Write-Host "      Temps: $([math]::Round($result3.generation_time, 2))s" -ForegroundColor Yellow
        Write-Host "      Taille: $($result3.content.Length) caractères" -ForegroundColor Cyan
        $tests += @{Test = "PREVIEW"; Status = "✅ PASS"; Time = $result3.generation_time }
    }
    else {
        Write-Host "   ❌ ÉCHEC" -ForegroundColor Red
        $tests += @{Test = "PREVIEW"; Status = "❌ FAIL"; Time = 0 }
    }
}
catch {
    Write-Host "   ❌ ERREUR: $($_.Exception.Message)" -ForegroundColor Red
    $tests += @{Test = "PREVIEW"; Status = "❌ ERROR"; Time = 0 }
}

# ========================================
# TEST 4 : Vérifier les fichiers créés
# ========================================
Write-Host "`n📁 TEST 4: Vérification des fichiers créés" -ForegroundColor Yellow

$createdFile = "data\anomalie2084\notes\test_writer_auto.md"
if (Test-Path $createdFile) {
    $content = Get-Content $createdFile -Raw
    Write-Host "   ✅ Fichier test_writer_auto.md trouvé !" -ForegroundColor Green
    Write-Host "      Taille: $($content.Length) caractères" -ForegroundColor Cyan
    Write-Host "      Lignes: $((Get-Content $createdFile).Count)" -ForegroundColor Cyan
    $tests += @{Test = "FILE_CHECK"; Status = "✅ PASS"; Time = 0 }
}
else {
    Write-Host "   ❌ Fichier non trouvé !" -ForegroundColor Red
    $tests += @{Test = "FILE_CHECK"; Status = "❌ FAIL"; Time = 0 }
}

# ========================================
# TEST 5 : Vérifier les backups
# ========================================
Write-Host "`n💾 TEST 5: Vérification des backups" -ForegroundColor Yellow

$backupDir = "data\.backups\anomalie2084"
if (Test-Path $backupDir) {
    $backups = Get-ChildItem $backupDir -Filter "test_writer_auto_*.md"
    if ($backups.Count -gt 0) {
        Write-Host "   ✅ $($backups.Count) backup(s) trouvé(s) !" -ForegroundColor Green
        foreach ($backup in $backups) {
            Write-Host "      - $($backup.Name)" -ForegroundColor Cyan
        }
        $tests += @{Test = "BACKUP_CHECK"; Status = "✅ PASS"; Time = 0 }
    }
    else {
        Write-Host "   ⚠️  Aucun backup trouvé (normal si 1er test)" -ForegroundColor Yellow
        $tests += @{Test = "BACKUP_CHECK"; Status = "⚠️  SKIP"; Time = 0 }
    }
}
else {
    Write-Host "   ⚠️  Dossier backup n'existe pas encore" -ForegroundColor Yellow
    $tests += @{Test = "BACKUP_CHECK"; Status = "⚠️  SKIP"; Time = 0 }
}

# ========================================
# RÉSUMÉ DES TESTS
# ========================================
Write-Host "`n" -NoNewline
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "📊 RÉSUMÉ DES TESTS" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

$tests | ForEach-Object {
    $timeStr = if ($_.Time -gt 0) { "$([math]::Round($_.Time, 2))s" } else { "-" }
    Write-Host "   $($_.Test.PadRight(15)) : $($_.Status.PadRight(10)) [$timeStr]" -ForegroundColor White
}

$passCount = ($tests | Where-Object { $_.Status -eq "✅ PASS" }).Count
$totalCount = $tests.Count

Write-Host "`n✨ Tests réussis: $passCount/$totalCount" -ForegroundColor $(if ($passCount -eq $totalCount) { "Green" } else { "Yellow" })

# Calcul temps total
$totalTime = ($tests | Where-Object { $_.Time -gt 0 } | Measure-Object -Property Time -Sum).Sum
Write-Host "⏱️  Temps total: $([math]::Round($totalTime, 2))s" -ForegroundColor Cyan

# ========================================
# AFFICHAGE DU CONTENU CRÉÉ
# ========================================
if (Test-Path $createdFile) {
    Write-Host "`n" -NoNewline
    Write-Host "=" * 60 -ForegroundColor Magenta
    Write-Host "📄 CONTENU DU FICHIER CRÉÉ" -ForegroundColor Magenta
    Write-Host "=" * 60 -ForegroundColor Magenta
    Write-Host ""
    Get-Content $createdFile
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Magenta
}

# Nettoyage
Remove-Item "test*.json" -ErrorAction SilentlyContinue

Write-Host "`n✅ Test automatique terminé !`n" -ForegroundColor Green
