# NRW Bildungsanalyse - Setup und Ausführung
# Dieses Skript aktiviert das Virtual Environment und führt die Analyse durch

# Farben für Output
$colors = @{
    "Success" = "Green"
    "Error" = "Red"
    "Info" = "Cyan"
    "Warning" = "Yellow"
}

function Write-Info { param([string]$msg); Write-Host "ℹ️  $msg" -ForegroundColor $colors["Info"] }
function Write-Success { param([string]$msg); Write-Host "✅ $msg" -ForegroundColor $colors["Success"] }
function Write-Error-Msg { param([string]$msg); Write-Host "❌ $msg" -ForegroundColor $colors["Error"] }
function Write-Warn { param([string]$msg); Write-Host "⚠️  $msg" -ForegroundColor $colors["Warning"] }

# Projekt-Root ermitteln
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$CodeDir = Join-Path $ProjectRoot "code"
$DataDir = Join-Path $ProjectRoot "data"
$VenvPath = Join-Path $ProjectRoot ".venv"
$VenvActivate = Join-Path $VenvPath "Scripts" "Activate.ps1"

Write-Info "========================================"
Write-Info "NRW Bildungsanalyse - Projekt Setup"
Write-Info "========================================"
Write-Info "Projekt-Root: $ProjectRoot"
Write-Info "Code-Verzeichnis: $CodeDir"
Write-Info "Daten-Verzeichnis: $DataDir"

# 1. venv prüfen
if (-not (Test-Path $VenvPath)) {
    Write-Error-Msg "Virtual Environment nicht gefunden unter: $VenvPath"
    Write-Info "Bitte folgendes Kommando ausführen:"
    Write-Host "    python -m venv $VenvPath" -ForegroundColor Yellow
    exit 1
}

Write-Success "Virtual Environment gefunden"

# 2. venv aktivieren
Write-Info "Aktiviere Virtual Environment..."
& $VenvActivate
Write-Success "Virtual Environment aktiviert"

# 3. Dependencies prüfen/installieren
Write-Info "Prüfe erforderliche Packages..."
$requiredPackages = @("pandas", "numpy", "matplotlib", "seaborn", "folium", "geopy")

foreach ($pkg in $requiredPackages) {
    python -c "import $pkg" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Package '$pkg' nicht installiert, installiere..."
        pip install $pkg -q
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Package '$pkg' installiert"
        } else {
            Write-Error-Msg "Fehler beim Installieren von '$pkg'"
            exit 1
        }
    }
}

Write-Success "Alle Packages installiert"

# 4. Datenvorbereitung
Write-Info "========================================"
Write-Info "Phase 1: Datenvorbereitung"
Write-Info "========================================"

Write-Info "Führe data_merge_extended.py aus..."
python (Join-Path $CodeDir "data_merge_extended.py") -DataDir $DataDir

if ($LASTEXITCODE -ne 0) {
    Write-Error-Msg "Fehler bei der Datenvorbereitung"
    exit 1
}

Write-Success "Datenvorbereitung abgeschlossen"

# 5. Visualisierungen erstellen
Write-Info "========================================"
Write-Info "Phase 2: Visualisierungen und Analyse"
Write-Info "========================================"

Write-Info "Führe visualize_analysis.py aus..."
python (Join-Path $CodeDir "visualize_analysis.py") -DataDir $DataDir

if ($LASTEXITCODE -ne 0) {
    Write-Error-Msg "Fehler bei der Visualisierung"
    exit 1
}

Write-Success "Visualisierungen erstellt"

# 6. Abitur-Analyse
Write-Info "========================================"
Write-Info "Phase 3: Abitur-Noten-Analyse"
Write-Info "========================================"

Write-Info "Führe analyze_abitur.py aus..."
python (Join-Path $CodeDir "analyze_abitur.py") -DataDir $DataDir

if ($LASTEXITCODE -ne 0) {
    Write-Warn "Abitur-Analyse fehlgeschlagen (Optional)"
} else {
    Write-Success "Abitur-Analyse abgeschlossen"
}

# 7. Interaktive Karte erstellen (optional - mit Timeout)
Write-Info "========================================"
Write-Info "Phase 4: Interaktive NRW-Karte"
Write-Info "========================================"

Write-Info "Führe visualize_map_advanced.py aus (kann 5-10 Minuten dauern)..."
Write-Info "Die Geocoding-Ergebnisse werden gecacht - beim nächsten Mal schneller!"

$mapScript = Join-Path $CodeDir "visualize_map_advanced.py"

try {
    python $mapScript -DataDir $DataDir
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Interaktive Karte erstellt"
    } else {
        Write-Warn "Fehler bei Kartenerstellung (Optional)"
    }
} catch {
    Write-Warn "Kartenerstellung abgebrochen (Optional)"
}

# 8. Zusammenfassung
Write-Info "========================================"
Write-Info "Analyse abgeschlossen! ✨"
Write-Info "========================================"
Write-Info ""
Write-Host "Generierte Dateien sind in:" -ForegroundColor Cyan
Write-Host "  📂 data/output/" -ForegroundColor Cyan
Write-Host ""
Write-Host "  📊 Visualisierungen (PNG):"
Write-Host "     - viz_01_korrelation_heatmap.png"
Write-Host "     - viz_02_einkommen_sozialindex.png"
Write-Host "     - viz_03_sozialindex_betreuung.png"
Write-Host "     - viz_04_top_bottom_staedte.png"
Write-Host "     - viz_05_stadtgroesse_vergleich.png"
Write-Host "     - viz_06_gymnasien_sozialindex_betreuung.png"
Write-Host "     - viz_07_gymnasien_schulanzahl.png"
Write-Host "  📈 Abitur-Visualisierungen (PNG):"
Write-Host "     - viz_abitur_01_zeitreihe.png"
Write-Host "     - viz_abitur_02_pruefungsanzahl.png"
Write-Host "     - viz_abitur_03_sozialindex_betreuung.png"
Write-Host "     - viz_abitur_04_top_bottom_kreise.png"
Write-Host "  🗺️  Interaktive Karte:"
Write-Host "     - viz_07_nrw_karte_advanced_folium.html (im Browser öffnen!)"
Write-Host "  📋 Datensätze:"
Write-Host "     - merged_schuldaten_extended.csv"
Write-Host "     - abitur_zeitreihe_nrw.csv"
Write-Info ""
Write-Host "Öffne die HTML-Karte mit: start .\data\output\viz_07_nrw_karte_advanced_folium.html" -ForegroundColor Yellow
