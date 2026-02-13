# 🎓 NRW Bildungsanalyse - Interaktives Streamlit Dashboard

**Eine explorative Datenanalyse der Bildungssituation in Nordrhein-Westfalen mit 17 interaktiven Plotly-Visualisierungen**

---

## 🚀 **LIVE DASHBOARD**

### **➜ [https://nrw-bildungsanalyse.streamlit.app](https://nrw-bildungsanalyse.streamlit.app)**

✅ **Kein Setup nötig!** Einfach öffnen und erkunden.

---

## 🏃 **Lokales Setup (nur 2 Minuten)**

```powershell
# 1. Repository klonen
git clone <repository-url>
cd Techlabs-Data-Science-Projekt

# 2. Virtual Environment erstellen
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Dependencies installieren
pip install -r requirements.txt

# 4. Dashboard starten
streamlit run streamlit_app.py

# 5. Browser öffnet automatisch → http://localhost:8501
```

---

## 📊 **Dashboard Features**

### **3 interaktive Modi:**

| Modus | Beschreibung |
|-------|-------------|
| **🏠 Übersicht** | 📈 Statistiken, Kernerkenntnisse, Sozialindex-Verteilung |
| **📊 Dashboard** | 17 Visualisierungen in 4 Kategorien mit Filtern |
| **📖 Story** | Narrative Präsentation mit Erkenntnissen |

### **17 Interaktive Visualisierungen (Plotly):**

#### **Stadt-Ebene (VIZ 100-104)** - Korrelationen & Vergleiche
- **VIZ 100:** Korrelations-Heatmap (alle Indikatoren)
- **VIZ 101:** Einkommen vs. Sozialindex
- **VIZ 102:** Sozialindex vs. Betreuungsrelation
- **VIZ 103:** Top & Bottom 10 Städte/Kreise
- **VIZ 104:** Stadtgröße-Vergleich (nach Schulanzahl)

#### **Gymnasium-Ebene (VIZ 105-107)** - Gymnasien-Fokus
- **VIZ 105:** Top & Bottom Gymnasien-Kreise
- **VIZ 106:** Gymnasium Sozialindex vs. Betreuung
- **VIZ 107:** Gymnasien pro Kreis (Ranking)

#### **Erweiterte Gymnasium-Analysen (VIZ 200-203)** - Deep Dive
- **VIZ 200:** Gymnasium/Gesamtschule Heatmap nach Kreis
- **VIZ 201:** Top 20 Gymnasien mit besten Bedingungen
- **VIZ 202:** Gymnasium vs. Gesamtschule Vergleich
- **VIZ 203:** Gymnasium-Dichte vs. Sozialindex Scatterplot

#### **Ergänzungen (VIZ 01-05)** - Spezialanalysen
- **VIZ 01:** Schulformen Boxplot (Verteilungsanalyse)
- **VIZ 02:** Extrema-Vergleich (Spreizung)
- **VIZ 03:** Gymnasien-Konzentration
- **VIZ 04:** Spreizungs-Ranking
- **VIZ 05:** Schulformen Donut-Chart

**Alle Charts:** Zoom, Pan, Hover-Info, Download als PNG

---

## 📋 **Die Daten**

### **Datensatz: merged_schuldaten_extended.csv**

```
📊 4.142 Schulen NRW (Schuljahr 2025/26)
📍 53 Kreise & Städte
🧹 11 bereinigte Spalten
```

| Spalte | Wertbereich | Aggregation | Quelle |
|--------|------------|-------------|--------|
| **Schulnummer** | ID 1-9999 | Schule | IT.NRW |
| **Schulname** | Text | Schule | IT.NRW |
| **Schulform** | 7 Typen | Schule | IT.NRW |
| **Gemeinde** | Ortsname | Schule | IT.NRW |
| **Kreis** | 53 Kreise/Städte | Schule | IT.NRW |
| **Sozialindex_Stufe** | 1-9 (1=best, 9=worst) | **Schule** | IT.NRW (soziale Benachteiligung) |
| **Sozialindex** | 0.5-2.5 (numeric) | **Schule** | IT.NRW |
| **Einkommen_Pro_Einwohner_Euro** | 23.341€ - 29.108€ | **Kreis-Ebene** | VGR der Länder |
| **Einwohnerzahl** | Pro Kreis | **Kreis-Ebene** | VGR der Länder |
| **Bildungsausgaben_Euro** | Pro Kopf | **Kreis-Ebene** | VGR der Länder |
| **Schueler_Pro_Lehrkraft** | 10-15 Ratio | Schule/Schulform | IT.NRW |

### **⚠️ Datenqualität - Wichtig zu verstehen:**

✅ **Einkommen & Einwohnerzahl:** 
- Aggregiert auf **KREIS-Ebene** (keine Duplikate)
- Alle Schulen im gleichen Kreis haben den gleichen Einkommen/Bevölkerungswert
- **Warum?** Einkommen wird nicht auf Schulebene, sondern auf Kreisebene gemessen

✅ **Sozialindex:** 
- **Individuell pro Schule** (Werte 1-9)
- Berücksichtigt soziale Benachteiligung im Schulumfeld

✅ **Datenquellen (öffentlich):**
- IT.NRW (Schulen, Schüler, Lehrer)
- VGR der Länder (Einkommen, Bevölkerung, Bildungsausgaben)
- Open Data NRW

---

## 💡 **Kernerkenntnisse**

### **1. Einkommenszusammenhang**
- 🔗 **Negative Korrelation** zwischen Einkommen und Sozialindex (r ≈ -0.65)
- 💰 Wohlhabendere Kreise haben bessere Sozialindizes (niedrigere Werte)
- 📊 Unterschiede: bis zu **5 Punkte** zwischen reichsten/ärmsten Kreisen
- **Erkenntnis:** Soziale Benachteiligung konzentriert sich in einkommensschwachen Regionen

### **2. Betreuungsqualität & Ungerechtigkeit**
- 👥 **Schlechtere Betreuungsverhältnisse** in ärmeren Gebieten
- 📈 Verhältnis 10-12 Schüler/Lehrer in wohlhabenden vs. 13-15 in armen Kreisen
- ⚠️ **Soziale Ungerechtigkeit** im Schulsystem nachweisbar
- **Erkenntnis:** Schüler mit höherem Förderbedarf bekommen weniger individuelle Unterstützung

### **3. Gymnasien-Segregation**
- 🏛️ Gymnasien konzentrieren sich in **wohlhabenderen Kreisen**
- 🎓 Gesamtschulen eher in sozial benachteiligten Gebieten
- 🚪 Zugang zu höherwertigen Schulformen **hängt von sozialer Lage ab**
- **Erkenntnis:** Schulform-Segregation spiegelt gesellschaftliche Ungleichheit wider

### **4. Regionale Disparitäten**
- 🗺️ Extreme Unterschiede zwischen Beste (Münster) und Schlechteste Kreise
- 📍 Top Gymnasien konzentrieren sich auf wenige Kreise
- 🏢 Bildungsinfrastruktur ungleich verteilt
- **Erkenntnis:** Chancengleichheit stark von Wohnort abhängig

---

## 📁 **Projektstruktur**

```
Techlabs-Data-Science-Projekt/
│
├── streamlit_app.py                    # 🎯 HAUPTDATEI - Streamlit Dashboard
├── requirements.txt                    # 📦 Python-Abhängigkeiten
├── README.md                           # 📄 Diese Datei
│
├── .streamlit/
│   └── config.toml                     # ⚙️ Streamlit-Konfiguration
│
├── code/                               # 🐍 Python-Datenverarbeitung
│   ├── data_merge_extended.py          # ① Datenmerge (3 Quellen → 1 CSV)
│   ├── visualize_plotly_all.py         # ② Stadt+Gymnasium VIZ (100-107)
│   ├── visualize_plotly_interactive.py # ③ Ergänzungen VIZ (01-05)
│   └── visualize_plotly_gymnasium_extended.py # ④ Gymnasium Deep-Dive (200-203)
│
└── data/
    ├── input/                          # 📥 Rohdaten (nicht versioniert)
    │   ├── Schulen, Schülerinnen... [Schulstatistik]
    │   ├── schulliste_sj_25_26_open_data.csv
    │   ├── vgrdl_r2b3_bs2023.xlsx [Einkommen 2023]
    │   └── vgrdl_r2b2_bs2024.xlsx [Einkommen 2024]
    │
    ├── output/                         # 📤 Generierte Dateien
    │   ├── merged_schuldaten_extended.csv    # Hauptdatensatz
    │   ├── viz_plotly_100.html ... 203.html  # 17 Plotly-Visualisierungen
    │   └── ABITUR_ERKENNTNISSE.md # Dokumentation
    │
    └── [ABITUR_ERKENNTNISSE.md]        # Hintergrund-Dokumentation
```

---

## 🔄 **Workflow: Daten aktualisieren**

Falls Sie die Rohdaten aktualisieren und alle Visualisierungen neu generieren möchten:

```powershell
# 1. .venv aktivieren
.\.venv\Scripts\Activate.ps1

# 2. Neue Rohdaten in data/input/ kopieren

# 3. Daten mergen
python code/data_merge_extended.py
# Output: ERFOLG! 4142 Schulen im finalen Datensatz

# 4. Alle Visualisierungen regenerieren (parallel)
python code/visualize_plotly_all.py
python code/visualize_plotly_interactive.py
python code/visualize_plotly_gymnasium_extended.py
# Output: ERFOLG! Alle 17 Visualisierungen erstellt

# 5. Dashboard neu starten (Auto-Reload)
streamlit run streamlit_app.py
```

---

## 🌍 **Streamlit Cloud Deployment**

### **Automatisches Deployment:**

1. Push zu GitHub: `git push origin main`
2. Öffne https://share.streamlit.io/
3. GitHub Account verbinden
4. Repository & Branch auswählen
5. Hauptdatei: `streamlit_app.py`
6. Deploy! ✅

**Live unter:** https://nrw-bildungsanalyse.streamlit.app

---

## 💻 **Systemanforderungen**

| Anforderung | Minimum | Empfohlen |
|------------|---------|-----------|
| **Python** | 3.8+ | 3.10+ |
| **RAM** | 1 GB | 4 GB |
| **Speicher** | 200 MB | 500 MB |
| **Betriebssystem** | Windows / macOS / Linux | Alle |

### **Dependencies (in requirements.txt):**

```
pandas>=2.0.0              # Datenverarbeitung
numpy>=1.24.0              # Numerische Berechnungen
plotly>=5.18.0             # Interaktive Grafiken
streamlit>=1.31.0          # Web-Framework
matplotlib>=3.7.0          # Zusatz-Grafiken
seaborn>=0.13.0            # Erweiterte Visualisierungen
openpyxl>=3.1.0            # Excel-Import
```

---

## 📚 **Eingangsdaten (öffentliche Quellen)**

| Datensatz | Quelle | Frequenz | Format |
|----------|--------|----------|--------|
| **Schulverzeichnis 2025-26** | [IT.NRW](https://www.it.nrw/) | Jährlich | CSV |
| **Einkommen & Bevölkerung** | [VGR der Länder](https://www.statistikportal.de/vgrdl/) | Jährlich | XLSX |
| **Bildungsausgaben** | VGR der Länder | Jährlich | XLSX |
| **Schüler/Lehrer Verhältnis** | IT.NRW | Jährlich | CSV |

**Lizenzen:** Alle Daten sind öffentlich verfügbar und frei nutzbar.

---

## 👥 **Autoren & Credits**

**Projekt:** Techlabs Data Science Projekt - Gruppe 4
Andreas Ahrens, Franka Eberhardt, Chantal Reerink, Serhat Karaarslan

**Dashboard:** Streamlit + Plotly
**Daten:** Open Data NRW, IT.NRW, VGR der Länder

**Links:**
-  [Streamlit](https://streamlit.io/)
-  [Plotly](https://plotly.com/)
-  [Open Data NRW](https://www.opendata.nrw/)
-  [IT.NRW](https://www.it.nrw/)

---

**Version:** 1.0.0 | **Letztes Update:** 2025 | **Status:** ✅ Production Ready

