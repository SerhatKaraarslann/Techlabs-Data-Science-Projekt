"""
Dieses Script führt alle Rohdaten zusammen und erstellt die zentrale Datei
'merged_schuldaten_extended.csv', die als Basis für alle Visualisierungen dient.

EINGABE-DATEIEN:
1. schulliste_sj_25_26_open_data.csv - Schuldaten NRW (Schulnummer, Name, Ort, Sozialindex)
2. Schulen, Schülerinnen und Schüler...csv - Statistik zu Lehrkräften & Schülern
3. vgrdl_r2b2_bs2024.xlsx / vgrdl_r2b3_bs2023.xlsx - Einkommensdaten nach Kreis

AUSGABE:
data/output/merged_schuldaten_extended.csv
- Enthält: Sozialindex, Einkommen pro Einwohner, Einwohnerzahl, Bildungsausgaben,
          Betreuungsrelation (Schüler/Lehrer), Abgangsquote für alle 4.142 Schulen

VERARBEITUNGSSCHRITTE:
1. Datenbereinigung: Encoding-Fehler korrigieren, Ortsnamen normalisieren
2. Datenanreicherung: Einkommensdaten, Einwohnerzahlen, Bildungsausgaben hinzufügen
3. Berechnung von Betreuungsrelationen und Abgangsquoten aus Statistikdaten
4. Intelligente Füllung fehlender Werte basierend auf Schulform-Durchs
5. Finale Aufbereitung und Export als CSV
ANALYSE-HINWEISE:
- Sozialindex: 1 (beste Bedingungen) bis 9 (schlechteste Bedingungen)
- Einkommensdaten: Verfügbares Einkommen pro Einwohner in Euro
- Einwohnerzahl: Anzahl der Einwohner in der Gemeinde/Kreis
- Bildungsausgaben: Durchschnittliche Ausgaben pro Kopf in Euro
- Betreuungsrelation: Anzahl Schüler pro Lehrkraft (niedriger = besser)
"""

import pandas as pd
import numpy as np
import re
import os
import sys

# Arbeitsverzeichnis zum data-Verzeichnis setzen
code_dir = os.path.dirname(os.path.abspath(__file__)) 
project_root = os.path.dirname(code_dir)
data_dir = os.path.join(project_root, "data")

# Sicherstellen, dass das data-Verzeichnis existiert
if not os.path.exists(data_dir):
    print(f"[ERROR] data-Verzeichnis nicht gefunden: {data_dir}")
    sys.exit(1)

# NO os.chdir() - use absolute paths instead
input_dir = os.path.join(data_dir, 'input')
output_dir = os.path.join(data_dir, 'output')
os.makedirs(output_dir, exist_ok=True)

print("=" * 80) 
print("ERWEITERTER DATENSATZ-MERGE - NRW BILDUNGSANALYSE")
print("=" * 80)
print(f"Input-Verzeichnis: {input_dir}")
print(f"Output-Verzeichnis: {output_dir}")
print()
def text_bereinigen(text):
    """
    Bereinigt Encoding-Fehler in deutschen Texte
    Korrigiert häufige Fehler wie "M nster" → "Münster", "D sseldorf" → "Düsseldorf", etc.
    Beispiel: "M nster" → "Münster", "D sseldorf" → "Düsseldorf", "K ln" → "Köln", "H rth" → "Hürth", "st„dter" → "städter", etc.
    return: Bereinigter Text oder Originaltext, wenn kein Fehler gefunden wurde
    """
    
    if not isinstance(text, str): return text
    text = text.replace('M nster', 'Münster').replace('D sseldorf', 'Düsseldorf')
    text = text.replace('K ln', 'Köln').replace('K"ln', 'Köln')
    text = text.replace('H rth', 'Hürth').replace('st„dter', 'städter')
    text = text.replace('L dinghausen', 'Lüdinghausen').replace('M„rkischen', 'Märkischen')
    return text.strip()

def name_normalisieren(name):
    """
    Normalisiert Orts-/Kreisnamen für besseres Matching
    
     - Entfernt häufige Zusätze wie "Kreis", "Stadt", "Regierungsbezirk
     - Korrigiert häufige Encoding-Fehler
     - Entfernt Sonderzeichen und Leerzeichen
     - Konvertiert zu Kleinbuchstaben
     return: Normalisierter Name, z.B. "Kreis M nster" → "munster", "D sseldorf" → "dusseldorf", "K ln" → "koln", etc.
    """
    if not isinstance(name, str): return ""
    name = name.lower()
    # Entferne komplexe Zusätze zuerst
    name = name.replace('kreisfreie stadt', '').replace('kreisfreie', '').replace('freie', '')
    name = name.replace('staedteregion', '').replace('städteregion', '')
    # Entferne generische Zusätze
    name = re.sub(r'(kreis|stadt|regierungsbezirk|krfr\.|landkreis)', '', name)
    name = re.sub(r',', '', name)
    name = name.replace('â€ž', 'ä').replace('ã¤', 'ä').replace('ã¼', 'ü').replace('ã¶', 'ö')
    name = name.replace('ü', 'ue').replace('ä', 'ae').replace('ö', 'oe').replace('ß', 'ss')
    return re.sub(r'\W+', '', name).strip()

def schulform_bestimmen(name):
    """
    Kategorisiert Schulen nach ihrer Schulform
    - Sucht nach Schlüsselwörtern im Schulnamen, um die Schulform zu bestimmen
     - Gymnasien, Gesamtschulen, Realschulen, Grundschulen, Sekundarschulen, Hauptschulen, Förderschulen, Sonstige
     return: Schulform-Kategorie als String, z.B. "Gymnasien", "Gesamtschulen", "Realschulen", etc.
    """
    name = str(name).lower()
    if 'gym' in name: return 'Gymnasien'
    if 'ge ' in name or 'gesamtschule' in name: return 'Gesamtschulen'
    if 'rs ' in name or 'realschule' in name: return 'Realschulen'
    if 'gg ' in name or 'grundschule' in name: return 'Grundschulen'
    if 'sk ' in name or 'sekundarschule' in name: return 'Sekundarschulen'
    if 'gh ' in name or 'hauptschule' in name: return 'Hauptschulen'
    if 'fÃ¶rder' in name or 'foerder' in name or 'f rder' in name: return 'Förderschulen'
    return 'Sonstige'

def zahl_bereinigen(x):
    """
    Konvertiert deutsche Zahlenformate in floats
     - Entfernt Tausendertrennzeichen (Punkte) und ersetzt Dezimaltrennzeichen (Komma) durch Punkt
     - Behandelt fehlende Werte (NaN oder '-') als 0
     return: Bereinigte Zahl als float, z.B. "1.234,56" → 1234.56, "-" oder NaN → 0.0
    """
    if pd.isna(x) or x == '-': return 0
    return float(str(x).replace('.', '').replace(',', '.'))


#  Laden und Bereinigen der Schulliste

print("\n Lade Schulliste...")
# Schulliste laden - Encoding-Fehler ignorieren und reparieren
schulen = pd.read_csv(os.path.join(input_dir, 'schulliste_sj_25_26_open_data.csv'), sep=';', encoding='latin1', encoding_errors='ignore')

# Fehlerhafte Zeichen ersetzen (aus fehlerhaftem Encoding)
# \x81 -> ü/ö (depends on context), \x94 -> ö
char_fix_map = {
    '\x81': 'ue',  # Falsch kodiertes ü
    '\x94': 'oe',  # Falsch kodiertes ö
    '\x84': 'ae',  # Falsch kodiertes ä
    '\x9a': 'Ue',  # Falsch kodiertes Ü
    '\x99': 'Oe',  # Falsch kodiertes Ö
    '\x8e': 'Ae',  # Falsch kodiertes Ä
    '\xe1': 'ss',  # Falsch kodiertes ß
}

# Fehlerhafte Zeichen + normale Umlauts ersetzen
for col in schulen.select_dtypes(include=['object']).columns:
    # Erst fehlerhafte Encoding-Zeichen
    for bad_char, replacement in char_fix_map.items():
        schulen[col] = schulen[col].astype(str).str.replace(bad_char, replacement, regex=False)
    # Dann normale Umlauts (falls noch vorhanden)
    schulen[col] = schulen[col].str.replace('ü', 'ue', regex=False)
    schulen[col] = schulen[col].str.replace('Ü', 'Ue', regex=False)
    schulen[col] = schulen[col].str.replace('ö', 'oe', regex=False)
    schulen[col] = schulen[col].str.replace('Ö', 'Oe', regex=False)
    schulen[col] = schulen[col].str.replace('ä', 'ae', regex=False)
    schulen[col] = schulen[col].str.replace('Ä', 'Ae', regex=False)
    schulen[col] = schulen[col].str.replace('ß', 'ss', regex=False)

# Relevante Spalten auswählen und umbenennen
spalten_zum_bereinigen = ['Kurzbezeichnung', 'Bezirksregierung', 'Kreis', 'Gemeinde']
for spalte in spalten_zum_bereinigen:
    schulen[spalte] = schulen[spalte].apply(text_bereinigen)

schulen['Schulform_Gruppe'] = schulen['Kurzbezeichnung'].apply(schulform_bestimmen) # Schulform kategorisieren
schulen['Kreis_Key'] = schulen['Kreis'].apply(name_normalisieren) # Normalisierte Kreisschlüssel
schulen['Gemeinde_Key'] = schulen['Gemeinde'].apply(name_normalisieren) # Normalisierte Gemeindeschlüssel

print(f"{len(schulen)} Schulen geladen")


#  Einkommensdaten (verfügbares Einkommen pro Einwohner - NUR AUF KREIS-EBENE)

print("\n Lade Einkommensdaten...")
# lade Einkommensdaten aus VGRDL - NUR KREIS-EBENE
einkommen = pd.read_excel(os.path.join(input_dir, 'vgrdl_r2b3_bs2023.xlsx'), sheet_name='2.4', skiprows=4)
# Filter auf KREIS-Ebene (nicht Gemeinden), nutze nur aktuelles Jahr (2022)
einkommen_clean = einkommen[einkommen['NUTS 3'].notna()][['Gebietseinheit', 2022]].copy()
# Nur Unter-Kreisebene filtern (Gemeinde/Verbandsgemeinde) - kreisfreie Städte behalten
einkommen_clean = einkommen_clean[~einkommen_clean['Gebietseinheit'].str.contains('Gemeinde|Verbandsgem', case=False, na=False)]
einkommen_clean.columns = ['Gebietseinheit', 'Einkommen_2022']
einkommen_clean['Join_Key'] = einkommen_clean['Gebietseinheit'].apply(name_normalisieren)
# Duplikate entfernen (nur neuester Datensatz pro Kreis)
einkommen_clean = einkommen_clean.drop_duplicates(subset=['Join_Key'], keep='first')
einkommen_map = einkommen_clean.set_index('Join_Key')['Einkommen_2022'].to_dict()

schulen['Einkommen_Pro_Einwohner'] = schulen['Kreis_Key'].map(einkommen_map)

print(f"Einkommensdaten verknüpft ({schulen['Einkommen_Pro_Einwohner'].notna().sum()} Schulen)")


# Einwohnerzahlen (Stadtgröße - NUR AUF KREIS-EBENE)

print("\n Lade Einwohnerzahlen...")
einwohner = pd.read_excel(os.path.join(input_dir, 'vgrdl_r2b3_bs2023.xlsx'), sheet_name='3', skiprows=4)
# Filter auf KREIS-Ebene (nicht Gemeinden), nutze nur aktuelles Jahr (2022)
einwohner_clean = einwohner[einwohner['NUTS 3'].notna()][['Gebietseinheit', 2022]].copy()
# Nur Unter-Kreisebene filtern (Gemeinde/Verbandsgemeinde) - kreisfreie Städte behalten
einwohner_clean = einwohner_clean[~einwohner_clean['Gebietseinheit'].str.contains('Gemeinde|Verbandsgem', case=False, na=False)]
einwohner_clean.columns = ['Gebietseinheit', 'Einwohner_2022']
einwohner_clean['Join_Key'] = einwohner_clean['Gebietseinheit'].apply(name_normalisieren)
# Duplikate entfernen (nur neuester Datensatz pro Kreis)
einwohner_clean = einwohner_clean.drop_duplicates(subset=['Join_Key'], keep='first')
einwohner_map = einwohner_clean.set_index('Join_Key')['Einwohner_2022'].to_dict()

schulen['Einwohnerzahl'] = schulen['Kreis_Key'].map(einwohner_map)
schulen['Einwohnerzahl'] = pd.to_numeric(schulen['Einwohnerzahl'], errors='coerce') * 1000

print(f"Einwohnerzahlen verknüpft ({schulen['Einwohnerzahl'].notna().sum()} Schulen)")


#  Bildungsausgaben (Arbeitnehmerentgelt Bildungssektor)

print("\n Lade Bildungsausgaben ...")
try:
    bildung_ausgaben = pd.read_excel(os.path.join(input_dir, 'vgrdl_r2b2_bs2024.xlsx'), sheet_name='2.2', skiprows=4)
    # Filtern auf "Erziehung und Unterricht" (WZ08-Code P)
    bildung_clean = bildung_ausgaben[bildung_ausgaben['NUTS 3'].notna()][['Gebietseinheit', 2022]].copy() # Nur relevante Spalten, keine NaNs
    bildung_clean.columns = ['Gebietseinheit', 'Bildungsausgaben_2022'] # Spalten umbenennen
    bildung_clean['Join_Key'] = bildung_clean['Gebietseinheit'].apply(name_normalisieren) # Normalisierte Join-Keys
    bildung_map = bildung_clean.set_index('Join_Key')['Bildungsausgaben_2022'].to_dict() # Mapping erstellen
    
    schulen['Bildungsausgaben_Pro_Kopf'] = schulen['Kreis_Key'].map(bildung_map) # Bildungsausgaben mappen
    maske_fehlt = schulen['Bildungsausgaben_Pro_Kopf'].isna() # Maske für fehlende Werte
    schulen.loc[maske_fehlt, 'Bildungsausgaben_Pro_Kopf'] = schulen.loc[maske_fehlt, 'Gemeinde_Key'].map(bildung_map) # Fehlende Werte mit Gemeinde-Daten füllen
    
    print(f"Bildungsausgaben verknüpft ({schulen['Bildungsausgaben_Pro_Kopf'].notna().sum()} Matches)")
except Exception as e:
    print(f"Bildungsausgaben konnten nicht geladen werden: {e}")
    schulen['Bildungsausgaben_Pro_Kopf'] = np.nan


#  Schüler-Lehrkräfte-Verhältnis (Betreuungsrelation)

print("\n Berechne Betreuungsrelationen...") 
stats = pd.read_csv(os.path.join(input_dir, 'Schulen, Schülerinnen und Schüler, Schulabgängerinnen und Schulabgänger und Lehrkräfte an allgemeinbildende Schulen.csv'), 
                    sep=';', encoding='latin1', skiprows=5) # Lade Statistikdaten

stats.columns = ['Region', 'Jahr', 'Kategorie', 'Subkategorie', 'Einheit', 'Gesamt', 'Grundschulen', 
                 'Hauptschulen', 'Volksschulen', 'Foerderschulen_GH', 'Foerderschulen_RG', 'Realschulen', 
                 'PRIMUS', 'Sekundarschulen', 'Gesamtschulen', 'Gemeinschaftsschulen', 'Waldorf', 
                 'Gymnasien', 'Weiterbildungskollegs'] # Spalten umbenennen
 
stats_aktuell = stats[stats['Jahr'] == '2022/23'].copy() # Nur aktuelles Schuljahr
relevante_schulformen = ['Grundschulen', 'Hauptschulen', 'Realschulen', 'Sekundarschulen', 'Gesamtschulen', 'Gymnasien'] # Relevante Schulformen

for spalte in relevante_schulformen: # Zahlen bereinigen
    stats_aktuell[spalte] = stats_aktuell[spalte].apply(zahl_bereinigen)

stats_aktuell['Gemeinde_Key'] = stats_aktuell['Region'].apply(name_normalisieren) # Normalisierte Gemeindeschlüssel

ratio_map = {} # Mapping für Schüler-Lehrkräfte-Verhältnis
for gem in stats_aktuell['Gemeinde_Key'].unique(): # Durchlauf pro Gemeinde
    daten_gem = stats_aktuell[stats_aktuell['Gemeinde_Key'] == gem] # Daten der Gemeinde filtern
    try:
        schueler_row = daten_gem[daten_gem['Kategorie'].str.contains('Schüler', na=False)] # Schüler-Zeile
        lehrer_row = daten_gem[daten_gem['Kategorie'].str.contains('Lehrkräfte', na=False)] # Lehrkräfte-Zeile
        
        if not schueler_row.empty and not lehrer_row.empty: # Sicherstellen, dass beide Zeilen existieren
            for form in relevante_schulformen: # Durchlauf pro Schulform
                s = schueler_row[form].values[0] # Schülerzahl
                l = lehrer_row[form].values[0] # Lehrkräftezahl
                if l > 0: # Division durch Null vermeiden
                    ratio_map[(gem, form)] = s / l # Verhältnis berechnen und speichern
    except:
        continue

def get_ratio(row):
    """"
    Holt das Schüler-Lehrkräfte-Verhältnis aus dem Mapping
    - key: (Gemeinde_Key, Schulform_Gruppe)
    - value: Schüler-Lehrkräfte-Verhältnis oder NaN, wenn nicht verfügbar
    return: Verhältnis als float oder NaN
    """
    key = (row['Gemeinde_Key'], row['Schulform_Gruppe']) # Schlüssel erstellen
    return ratio_map.get(key, np.nan) # Verhältnis zurückgeben oder NaN

schulen['Schueler_Pro_Lehrkraft'] = schulen.apply(get_ratio, axis=1) # Verhältnis in den DataFrame einfügen

print(f"Betreuungsrelationen berechnet ({schulen['Schueler_Pro_Lehrkraft'].notna().sum()} Schulen)")


#  Schulabgangsquoten - ENTFERNT

print("\n Abgangsquote: NICHT BERÜCKSICHTIGT (keine zuverlässigen Daten auf Schulebene)")


# Finales Aufräumen und Aggregation
print("\n Erstelle finalen Datensatz...")

# Sozialindex numerisch konvertieren
schulen['Sozialindex_Numerisch'] = pd.to_numeric(schulen['Sozialindexstufe'], errors='coerce') # Fehlerhafte Werte zu NaN konvertieren 

# Finale Spaltenauswahl - OHNE Abgangsquote!
finaler_datensatz = schulen[[
    'Schulnummer', 'Kurzbezeichnung', 'Schulform_Gruppe', 
    'Gemeinde', 'Kreis', 'Sozialindexstufe', 'Sozialindex_Numerisch',
    'Einkommen_Pro_Einwohner', 'Einwohnerzahl', 'Bildungsausgaben_Pro_Kopf',
    'Schueler_Pro_Lehrkraft'
]].copy()

# Nur Schulen mit Sozialindex behalten 
finaler_datensatz = finaler_datensatz[finaler_datensatz['Sozialindex_Numerisch'].notna()]

# NaN-Werte intelligent füllen 
print("\n   Fülle fehlende Werte...")
for spalte in ['Einkommen_Pro_Einwohner', 'Einwohnerzahl', 'Bildungsausgaben_Pro_Kopf', 
               'Schueler_Pro_Lehrkraft']:
    for schulform in finaler_datensatz['Schulform_Gruppe'].unique(): # Durchlauf pro Schulform
        maske = (finaler_datensatz['Schulform_Gruppe'] == schulform) & (finaler_datensatz[spalte].notna()) # Maske für vorhandene Werte
        if maske.sum() > 0: # Sicherstellen, dass es Werte zum Berechnen gibt
            durchschnitt = finaler_datensatz.loc[maske, spalte].mean() # Durchschnitt berechnen
            fehlend = (finaler_datensatz['Schulform_Gruppe'] == schulform) & (finaler_datensatz[spalte].isna()) # Maske für fehlende Werte
            finaler_datensatz.loc[fehlend, spalte] = durchschnitt # Fehlende Werte füllen
    
    # Fallback: Gesamtdurchschnitt
    finaler_datensatz[spalte] = finaler_datensatz[spalte].fillna(finaler_datensatz[spalte].mean())

# Zahlen runden
finaler_datensatz['Einkommen_Pro_Einwohner'] = finaler_datensatz['Einkommen_Pro_Einwohner'].round(0).astype(int)
finaler_datensatz['Einwohnerzahl'] = finaler_datensatz['Einwohnerzahl'].round(0).astype(int)
finaler_datensatz['Bildungsausgaben_Pro_Kopf'] = finaler_datensatz['Bildungsausgaben_Pro_Kopf'].round(0).astype(int)
finaler_datensatz['Schueler_Pro_Lehrkraft'] = finaler_datensatz['Schueler_Pro_Lehrkraft'].round(2)

# Umlauts in finalen Daten ersetzen (nochmal, für Output-CSV)
for col in finaler_datensatz.select_dtypes(include=['object']).columns:
    finaler_datensatz[col] = finaler_datensatz[col].astype(str).str.replace('ü', 'ue', regex=False)
    finaler_datensatz[col] = finaler_datensatz[col].str.replace('Ü', 'Ue', regex=False)
    finaler_datensatz[col] = finaler_datensatz[col].str.replace('ö', 'oe', regex=False)
    finaler_datensatz[col] = finaler_datensatz[col].str.replace('Ö', 'Oe', regex=False)
    finaler_datensatz[col] = finaler_datensatz[col].str.replace('ä', 'ae', regex=False)
    finaler_datensatz[col] = finaler_datensatz[col].str.replace('Ä', 'Ae', regex=False)
    finaler_datensatz[col] = finaler_datensatz[col].str.replace('ß', 'ss', regex=False)

# Deutsche Spaltennamen
finaler_datensatz.columns = [
    'Schulnummer', 'Schulname', 'Schulform', 
    'Gemeinde', 'Kreis', 'Sozialindex_Stufe', 'Sozialindex',
    'Einkommen_Pro_Einwohner_Euro', 'Einwohnerzahl', 'Bildungsausgaben_Euro',
    'Schueler_Pro_Lehrkraft'
]

# Speichern
finaler_datensatz.to_csv(os.path.join(output_dir, 'merged_schuldaten_extended.csv'), index=False, sep=';', decimal=',', encoding='utf-8-sig')

print(f"\n{'='*80}")
print(f"ERFOLG! {len(finaler_datensatz)} Schulen im finalen Datensatz")
print(f"{'='*80}")
print(f"\nDatei erstellt: merged_schuldaten_extended.csv")
print(f"\nEnthaltene Variablen:")
print(f"   • Sozialindex (1-9)")
print(f"   • Einkommen pro Einwohner (€) - KREIS-EBENE, dedupliziert")
print(f"   • Einwohnerzahl (Stadtgröße) - KREIS-EBENE, dedupliziert")
print(f"   • Bildungsausgaben (€)")
print(f"   • Schüler-Lehrkraft-Verhältnis")
print(f"\n➜ Bereit für Visualisierungen und Analysen!")
