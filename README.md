# NRW Bildungsanalyse - Interaktives Data Science Dashboard

Techlabs Data Science Projekt - Gruppe 4

**Autoren:** Andreas Ahrens, Franka Eberhardt, Chantal Reerink, Serhat Karaarslan

Explorative Datenanalyse der Bildungssituation in Nordrhein-Westfalen mit interaktiven Visualisierungen von 4.142 Schulen über 53 Kreise und 11 Sozialindikatoren.

---

## Live Dashboard

[https://nrw-bildungsanalyse.streamlit.app](https://nrw-bildungsanalyse.streamlit.app)

Sofort verfügbar - keine Installation notwendig.

---

## Quick Start

### Windows PowerShell
```powershell
git clone <repository-url>
cd Techlabs-Data-Science-Projekt
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Linux / macOS
```bash
git clone <repository-url>
cd Techlabs-Data-Science-Projekt
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Browser öffnet automatisch: http://localhost:8501

---

## Dashboard Übersicht

Das Dashboard bietet 3 Modi mit 18 interaktiven Visualisierungen:

- **Übersicht**: Statistiken, Kernerkenntnisse, Verteilungen
- **Dashboard**: 18 interaktive Charts in 4 Kategorien
- **Story**: Narrative Präsentation mit Erkenntnissen

### Visualisierungen

**Stadt/Kreis-Ebene (VIZ 100-104)**
- VIZ 100: Korrelations-Heatmap
- VIZ 101: Einkommen vs. Sozialindex
- VIZ 102: Sozialindex vs. Betreuungsrelation
- VIZ 103: Top & Bottom 10 Städte
- VIZ 104: Vergleich nach Schulanzahl

**Gymnasium-Ebene (VIZ 105-107)**
- VIZ 105: Top & Bottom Gymnasien-Kreise
- VIZ 106: Gymnasium Sozialindex vs. Betreuung
- VIZ 107: Gymnasien pro Kreis

**Gymnasium Deep-Dive (VIZ 200-203)**
- VIZ 200: Gymnasium/Gesamtschule Heatmap
- VIZ 201: Top 20 Gymnasien
- VIZ 202: Gymnasium vs. Gesamtschule
- VIZ 203: Gymnasium-Dichte vs. Sozialindex

**Spezialanalysen (VIZ 01-05)**
- VIZ 01: Schulformen Boxplot
- VIZ 02: Extrema-Vergleich
- VIZ 03: Gymnasien-Konzentration
- VIZ 04: Spreizungs-Ranking
- VIZ 05: Schulformen Donut

**Karten (VIZ 300-301)**
- VIZ 300: NRW Choropleth-Karte (Kreise/Städte)
- VIZ 301: Schulen-Karte (4.142 Schulen an echten Standorten mit GPS-Koordinaten)

---

## Daten

### Datensatz
```
4.142 Schulen NRW (Schuljahr 2025/26)
53 Kreise & kreisfreie Städte
11 bereinigte Spalten
```

### Wichtige Spalten

| Spalte | Niveau | Quelle |
|--------|--------|--------|
| Schulnummer, Schulname, Schulform | Schule | IT.NRW |
| Kreis, Gemeinde | Schule | IT.NRW |
| Sozialindex (1-9) | Schule | IT.NRW |
| Einkommen, Einwohnerzahl, Bildungsausgaben | Kreis | VGR 2022 |
| Schüler/Lehrkraft Ratio | Schule | IT.NRW |
| GPS-Koordinaten (lat/lon), Adresse | Schule | NRW INSPIRE OGC API |

### Datenqualität

- **Sozialindex**: Individuell pro Schule (1=besser, 9=schlechter)
- **Einkommen/Einwohnerzahl**: Auf Kreis-Ebene (alle Schulen im Kreis identisch)
- **Betreuungsrelation**: Unterschiede nach Schulform und einzelner Schule
- **GPS-Koordinaten**: Echte Schulstandorte von offizieller NRW INSPIRE OGC API (100% Coverage)

---

## Kernerkenntnisse

### 1. Starke Einkommensdependenz
- Negative Korrelation zwischen Einkommen und Sozialindex (r ≈ -0.65)
- Wohlhabendere Kreise haben bessere Sozialindizes
- Bis zu 5 Punkte Unterschied zwischen reichsten/ärmsten Kreisen

### 2. Ungerechtigkeit in der Betreuung
- Schüler in benachteiligten Gebieten: schlechtere Betreuungsverhältnisse
- Wohlhabende Kreise: 10-12 Schüler/Lehrer
- Arme Kreise: 13-15 Schüler/Lehrer

### 3. Gymnasien-Segregation
- Gymnasien konzentrieren sich in wohlhabenderen Kreisen
- Gesamtschulen eher in sozial benachteiligten Gebieten
- Zugang zu höherwertigen Schulformen hängt von sozialer Lage ab

### 4. Regionale Disparitäten
- Extreme Unterschiede zwischen Top und Bottom Kreisen
- Bildungsinfrastruktur ungleich verteilt
- Chancengleichheit stark vom Wohnort abhängig

---

## Projektstruktur

```
Techlabs-Data-Science-Projekt-1/
├── streamlit_app.py                 # Hauptdatei
├── requirements.txt                 # Dependencies
├── README.md                        # Diese Datei
├── .streamlit/
│   └── config.toml
├── code/
│   ├── data_merge_extended.py       # Datenmerge
│   ├── load_schools_from_ogc_api.py # OGC API Schuladressen
│   ├── check_coverage.py            # Coverage-Check
│   ├── visualize_plotly_all.py      # VIZ 100-107
│   ├── visualize_plotly_interactive.py # VIZ 01-05
│   └── visualize_plotly_gymnasium_extended.py # VIZ 200-203
└── data/
    ├── input/                       # Rohdaten
    │   ├── Schulen, Schülerinnen...
    │   ├── schulliste_sj_25_26_open_data.csv
    │   ├── vgrdl_r2b3_bs2023.xlsx
    │   ├── vgrdl_r2b2_bs2024.xlsx
    │   └── deutschland_kreise.geojson
    └── output/
        ├── merged_schuldaten_extended.csv
        ├── schulen_adressen_ogc_cache.csv # 5.423 Schulen mit GPS
        └── viz_plotly_*.html (18 Dateien)
```

---

## Daten aktualisieren

```bash
# 1. Neue Dateien in data/input/ kopieren

# 2. Daten mergen
python3 code/data_merge_extended.py

# 3. Schuladressen aktualisieren (optional, falls neue Schulen)
python3 code/load_schools_from_ogc_api.py

# 4. Visualisierungen regenerieren
python3 code/visualize_plotly_all.py
python3 code/visualize_plotly_interactive.py
python3 code/visualize_plotly_gymnasium_extended.py

# 5. Dashboard neu starten
streamlit run streamlit_app.py
```

---

## Systemanforderungen

| Anforderung | Minimum | Empfohlen |
|------------|---------|-----------|
| Python | 3.8+ | 3.10+ |
| RAM | 1 GB | 4 GB |
| Speicher | 200 MB | 1 GB |
| Betriebssystem | Windows/macOS/Linux | Alle |

### Dependencies
```
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.18.0
streamlit>=1.31.0
openpyxl>=3.1.0
```

---

## Datenquellen

| Datensatz | Quelle | Frequenz |
|----------|--------|----------|
| Schulverzeichnis 2025-26 | [IT.NRW](https://www.it.nrw/) | Jährlich |
| Einkommen & Bevölkerung | [VGR der Länder](https://www.statistikportal.de/vgrdl/) | Jährlich |
| Bildungsausgaben | VGR der Länder | Jährlich |
| Kreis-Grenzen | [deutschlandGeoJSON](https://github.com/isellsoap/deutschlandGeoJSON) | Public Domain |

Alle Daten sind öffentlich verfügbar und frei nutzbar.

---

## Deployment auf Streamlit Cloud

```bash
git add .
git commit -m "Update visualizations"
git push origin main
```

Öffne https://share.streamlit.io/:
1. GitHub Account verbinden
2. Repository: Techlabs-Data-Science-Projekt-1
3. Branch: main
4. Datei: streamlit_app.py
5. Deploy

Live unter: https://nrw-bildungsanalyse.streamlit.app

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| ModuleNotFoundError | `pip install -r requirements.txt` |
| Port 8501 bereits verwendet | `streamlit run streamlit_app.py --server.port 8502` |
| CSV-Dateien können nicht geladen werden | Encoding: `utf-8-sig`, Trennzeichen: `;` |
| Visualisierungen laden nicht | `python3 code/visualize_plotly_all.py` neu generieren |

---

## Version

| Aspekt | Details |
|--------|---------|
| Version | 2.1.0 |
| Letztes Update | 2026-02-27 |
| Status | Production Ready |
| Schulen | 4.142 (NRW) |
| Kreise | 53 |
| Visualisierungen | 18 + 2 Karten |

---

## Ressourcen

- [Streamlit Docs](https://docs.streamlit.io/)
- [Plotly Docs](https://plotly.com/python/)
- [Pandas Docs](https://pandas.pydata.org/docs/)
- [Open Data NRW](https://www.opendata.nrw/)
- [IT.NRW](https://www.it.nrw/)
