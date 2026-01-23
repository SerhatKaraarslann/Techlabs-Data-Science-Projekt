# Schuldaten-Merge Projekt

## Übersicht

Dieses Projekt führt verschiedene Datensätze über Schulen in Nordrhein-Westfalen zusammen, um eine umfassende Analyse der Zusammenhänge zwischen Sozialindex, Einkommen und Betreuungsrelationen zu ermöglichen.

## Verwendete Datensätze

1. **schulliste_sj_25_26_open_data.csv**: Aktuelle Schulliste mit Schulnummern, Namen, Standorten und Sozialindexstufen
2. **vgrdl_r2b3_bs2023.xlsx**: Einkommensdaten auf Kreisebene (VGR der Länder, Tabelle 2.4)
3. **Schulen, Schülerinnen und Schüler, Schulabgängerinnen und Schulabgänger und Lehrkräfte an allgemeinbildende Schulen.csv**: Schulstatistiken mit Schüler- und Lehrerzahlen

## Was macht data_merge.py?

Das Skript führt folgende Schritte aus:

### 1. Laden und Bereinigen der Schulliste
- Lädt die Schulliste mit deutscher Zeichenkodierung (latin1)
- Bereinigt typische Encoding-Fehler bei Umlauten (z.B. "M nster" → "Münster")
- Kategorisiert Schulen nach Schulform (Gymnasium, Gesamtschule, Realschule, etc.)

### 2. Verknüpfen mit Einkommensdaten
- Lädt Einkommensdaten aus der Excel-Datei (Verfügbares Einkommen pro Einwohner, Jahr 2022)
- Normalisiert Kreis- und Gemeindenamen für besseres Matching
- Ordnet jeder Schule das durchschnittliche Einkommen ihres Kreises zu
- Fallback: Nutzt Gemeinde-Matching für kreisfreie Städte

### 3. Berechnung der Betreuungsrelation
- Lädt Schulstatistiken mit Schüler- und Lehrerzahlen
- Berechnet für jede Gemeinde und Schulform das Verhältnis Schüler pro Lehrkraft
- Ordnet jeder Schule die entsprechende Betreuungsrelation zu

### 4. Finales Aufräumen und Speichern
- Konvertiert Sozialindexstufen in numerische Werte
- Speichert den finalen Datensatz als **merged_schuldaten_final.csv**

## Output-Datei: merged_schuldaten_final.csv

Die finale Datei enthält folgende Spalten:
- **Schulnummer**: Eindeutige Identifikationsnummer der Schule
- **Schulname**: Name/Bezeichnung der Schule
- **Schulform**: Kategorisierte Schulform (Gymnasium, Gesamtschule, etc.)
- **Gemeinde**: Standortgemeinde
- **Kreis**: Standortkreis
- **Sozialindex_Stufe**: Sozialindex-Kategorie (1-9)
- **Sozialindex**: Sozialindex als Zahl für Analysen
- **Einkommen_Pro_Einwohner_Euro**: Verfügbares Einkommen pro Einwohner im Kreis (in Euro, 2022)
- **Schueler_Pro_Lehrkraft**: Durchschnittliche Anzahl Schüler pro Lehrkraft (Betreuungsrelation)

### Besonderheiten:
- **Keine NaN-Werte**: Fehlende Werte werden intelligent gefüllt (Durchschnitt der Schulform)
- **Gut lesbar**: Deutsche Spaltennamen, gerundete Zahlen
- **UTF-8 Encoding**: Korrekte Darstellung von Umlauten
- **Deutsches CSV-Format**: Semikolon als Trennzeichen, Komma als Dezimalzeichen

## Verwendung

### Skript ausführen:
```bash
python data_merge.py
```

### Ergebnis-Datei einlesen:
Siehe `read_merged_data.py` für ein Beispiel zum Einlesen und Analysieren der finalen Datei.

## Anforderungen

- Python 3.8+
- pandas
- numpy
- openpyxl (für Excel-Dateien)

Installation:
```bash
pip install pandas numpy openpyxl
```

## Hinweise

- Das Skript wechselt automatisch in sein eigenes Verzeichnis, daher kann es von überall ausgeführt werden
- Encoding-Probleme werden automatisch bereinigt
- Fehlende Matches (z.B. wenn Kreis nicht gefunden wird) werden als NaN gespeichert
