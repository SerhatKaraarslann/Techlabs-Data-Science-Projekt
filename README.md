# NRW Bildungsanalyse - Data Science Projekt

**Eine explorative Datenanalyse der Bildungssituation in Nordrhein-Westfalen**

---

## Übersicht

Dieses Projekt untersucht die Beziehungen zwischen **sozialen Faktoren** (Sozialindex, Einkommen) und **Bildungsindikatoren** (Schulformen, Betreuungsrelationen, Abitur-Ergebnisse) in Nordrhein-Westfalen.

**Kernfrage:** Welche Rolle spielen wirtschaftliche und soziale Bedingungen für die Bildungssituation?

### Was wird analysiert?

- **4142 Schulen** aus NRW (Schuljahr 2025-26)
- **53 Kreise und kreisfreie Städte**
- **Abiturdaten** von 2020-2024 (Zeitreihenanalyse)
- **Soziale Indikatoren:** Sozialindex, verfügbares Einkommen
- **Bildungsindikatoren:** Schulformen, Schüler/Lehrer-Verhältnisse, Abitur-Noten

---

##  Quick Start

### Windows (PowerShell)

```powershell
# 1. Virtual Environment erstellen (einmalig)
python -m venv .venv

# 2. Analyse-Skript ausführen
.\run_analysis.ps1

# 3. Ergebnisse anschauen
start .\data\viz_07_nrw_karte_advanced_folium.html
```

**Manuelle Alternative:**
```powershell
.\.venv\Scripts\Activate.ps1
cd data
pip install pandas numpy matplotlib seaborn folium geopy openpyxl
python data_merge_extended.py
python visualize_analysis.py
python analyze_abitur.py
python visualize_map_advanced.py
```

---

### macOS & Linux (Bash/Zsh)

```bash
# 1. Virtual Environment erstellen (einmalig)
python3 -m venv .venv

# 2. venv aktivieren
source .venv/bin/activate

# 3. Packages installieren
pip install pandas numpy matplotlib seaborn folium geopy openpyxl

# 4. Skripte ausführen
cd data
python data_merge_extended.py      # ① Datenvorbereitung
python visualize_analysis.py       # ② Visualisierungen
python analyze_abitur.py           # ③ Abitur-Analyse
python visualize_map_advanced.py   # ④ Interaktive Karte

# 5. Ergebnisse anschauen
# Öffne in Browser: data/viz_07_nrw_karte_advanced_folium.html
```

---

##  Projektstruktur

```
Techlabs-Data-Science-Projekt/
├── .venv/                              # Python Virtual Environment
├── .gitignore                          # Git-Exclusions
├── README.md                           # Diese Datei
├── requirements.txt                    # Python-Abhängigkeiten
├── run_analysis.ps1                    # Automatisierungs-Skript (Windows PowerShell)
│
├── code/                               # Python-Skripte
│   ├── data_merge_extended.py          # ① Datenvorbereitung & Merge
│   ├── visualize_analysis.py           # ② Visualisierungen
│   ├── analyze_abitur.py               # ③ Abitur-Analyse
│   └── visualize_map_advanced.py       # ④ Interaktive Karte
│
└── data/                               # Datenverzeichnis
    ├── input/                          # Rohdaten
    │   ├── schulliste_sj_25_26_open_data.csv
    │   ├── vgrdl_r2b3_bs2023.xlsx
    │   ├── vgrdl_r2b2_bs2024.xlsx
    │   ├── Schulen, Schülerinnen...csv
    │   ├── Aus_Abiturnoten_20XX.xlsx (2020-2024)
    │   ├── *.pdf
    │   └── *.md
    │
    └── output/                         # Ergebnisse (automatisch generiert)
        ├── merged_schuldaten_extended.csv
        ├── abitur_zeitreihe_nrw.csv
        ├── viz_01_korrelation_heatmap.png
        ├── viz_02_einkommen_sozialindex.png
        ├── viz_03_sozialindex_betreuung.png
        ├── viz_04_top_bottom_staedte.png
        ├── viz_05_stadtgroesse_vergleich.png
        ├── viz_06_gymnasien_sozialindex_betreuung.png
        ├── viz_07_gymnasien_schulanzahl.png
        ├── viz_abitur_01_zeitreihe.png
        ├── viz_abitur_02_pruefungsanzahl.png
        ├── viz_abitur_03_sozialindex_betreuung.png
        ├── viz_abitur_04_top_bottom_kreise.png
        └── viz_07_nrw_karte_advanced_folium.html
```

---

##  Kernerkenntnisse

### Einkommenszusammenhang
- **Negative Korrelation** zwischen Einkommen und Sozialindex
- Wohlhabendere Kreise haben bessere Sozialindizes
- Unterschiede bis zu 5 Punkte zwischen reichsten/ärmsten Kreisen

###  Betreuungsqualität
- Schlechtere Betreuungsverhältnisse in ärmeren Gebieten
- Unterschiede: 10-12 Schüler/Lehrer in reicheren vs. 13-15 in ärmeren Kreisen
- **Soziale Ungerechtigkeit** im Schulsystem nachweisbar

### Schulform-Segregation
- Gymnasien konzentrieren sich in wohlhabenderen Kreisen
- Gesamtschulen eher in sozial benachteiligten Gebieten
- Zugang zu höherwertigen Schulformen hängt von sozialer Lage ab

### Abitur-Trends (2020-2024)
-  Notendurchschnitt: stabil 2.36-2.43
-  Erfolgsquote: ~95-97%
-  Prüflingszahlen sinken (demografischer Wandel)
-  Regionale Unterschiede: bis zu 0,8 Noten-Punkte

---

##  Visualisierungen

### Statische Grafiken (PNG)

| Datei | Beschreibung |
|-------|-------------|
| **viz_01_korrelation_heatmap.png** | Korrelationsmatrix aller Indikatoren |
| **viz_02_einkommen_sozialindex.png** | Einkommen vs. Sozialindex Scatterplot |
| **viz_03_sozialindex_betreuung.png** | Sozialindex vs. Betreuungsrelation |
| **viz_04_top_bottom_staedte.png** | Top 10 & Bottom 10 Kreise |
| **viz_05_stadtgroesse_vergleich.png** | Stadtgröße vs. Sozialindex |
| **viz_06_gymnasien_sozialindex_betreuung.png** | Gymnasien-Spezial-Analyse |
| **viz_07_gymnasien_schulanzahl.png** | Gymnasien-Dichte pro Kreis |

### Abitur-Visualisierungen (2020-2024)

| Datei | Beschreibung |
|-------|-------------|
| **viz_abitur_01_zeitreihe.png** | Notenschnitt & Erfolgsquote |
| **viz_abitur_02_pruefungsanzahl.png** | Prüflinge pro Kreis (Trend) |
| **viz_abitur_03_sozialindex_betreuung.png** | Abitur vs. Sozialindex |
| **viz_abitur_04_top_bottom_kreise.png** | Top/Bottom 10 Gymnasien-Kreise |

### Interaktive Karte

**viz_07_nrw_karte_advanced_folium.html**
-  Echte Straßenkarte (CartoDB)
-  4142 Schulmarker (nach Schulform farbcodiert)
-  Schulform-Filter (7 Layer zum Ein-/Ausblenden)
-  Kreis-Agglomerate nach Sozialindex gefärbt
-  Münster hervorgehoben
-  Detaillierte Popups mit Schuldaten

---

##  Systemanforderungen

- **Python:** 3.8+
- **RAM:** ≥ 2 GB
- **Speicher:** ≥ 500 MB für alle Outputs
- **Betriebssysteme:** Windows, macOS, Linux

### Abhängigkeiten

```
pandas>=1.3.0          # Datenverarbeitung
numpy>=1.21.0          # Numerische Berechnungen
matplotlib>=3.4.0      # Grafiken
seaborn>=0.11.0        # Erweiterte Visualisierungen
folium>=0.12.0         # Interaktive Karten
geopy>=2.1.0           # Geocodierung (optional)
openpyxl>=3.6.0        # Excel-Import
```

---

##  Input-Daten

Alle Datensätze sind **öffentliche Datenquellen**:

| Datensatz | Quelle | Format |
|----------|--------|--------|
| Schulliste 2025-26 | IT.NRW | CSV |
| Einkommen & Bevölkerung | VGR der Länder | XLSX |
| Bildungsausgaben | VGR der Länder | XLSX |
| Schüler/Lehrer | IT.NRW | CSV |
| Abitur-Noten 2020-2024 | Open.NRW | XLSX |

---

##  Lizenz & Datenquellen

**Datenquellen:**
- Open Data NRW (https://www.opendata.nrw/)
- Ministerium für Schule und Bildung NRW
- Statistisches Landesamt NRW


---

