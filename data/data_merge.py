import pandas as pd
import numpy as np
import re
import os

# Arbeitsverzeichnis auf das Skript-Verzeichnis setzen
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------
# 1. Laden und Bereinigen der Schulliste
# ---------------------------------------------------------
# Wir nutzen 'latin1' als Encoding, da deutsche Sonderzeichen enthalten sind
schulen = pd.read_csv('schulliste_sj_25_26_open_data.csv', sep=';', encoding='latin1')

# Funktion zur Bereinigung von Texten (z.B. kaputte Umlaute korrigieren)
def text_bereinigen(text):
    if not isinstance(text, str): return text
    # Typische Encoding-Fehler beheben (z.B. "M nster" -> "Münster")
    text = text.replace('M nster', 'Münster').replace('D sseldorf', 'Düsseldorf')
    text = text.replace('K ln', 'Köln').replace('K”ln', 'Köln')
    text = text.replace('H rth', 'Hürth').replace('st„dter', 'städter')
    text = text.replace('L dinghausen', 'Lüdinghausen').replace('M„rkischen', 'Märkischen')
    return text.strip()

# Anwenden der Bereinigung auf alle Textspalten
spalten_zum_bereinigen = ['Kurzbezeichnung', 'Bezirksregierung', 'Kreis', 'Gemeinde']
for spalte in spalten_zum_bereinigen:
    schulen[spalte] = schulen[spalte].apply(text_bereinigen)

# Schulformen kategorisieren (aus der Kurzbezeichnung ableiten, um später zu matchen)
def schulform_bestimmen(name):
    name = str(name).lower()
    if 'gym' in name: return 'Gymnasien'
    if 'ge ' in name or 'gesamtschule' in name: return 'Gesamtschulen'
    if 'rs ' in name or 'realschule' in name: return 'Realschulen'
    if 'gg ' in name or 'grundschule' in name: return 'Grundschulen'
    if 'sk ' in name or 'sekundarschule' in name: return 'Sekundarschulen'
    if 'gh ' in name or 'hauptschule' in name: return 'Hauptschulen'
    if 'fÃ¶rder' in name or 'foerder' in name or 'f rder' in name: return 'Förderschulen'
    return 'Sonstige'

schulen['Schulform_Gruppe'] = schulen['Kurzbezeichnung'].apply(schulform_bestimmen)

# ---------------------------------------------------------
# 2. Laden der Einkommensdaten
# ---------------------------------------------------------
# Überspringen der ersten 4 Zeilen (Metadaten)
einkommen = pd.read_excel('vgrdl_r2b3_bs2023.xlsx', sheet_name='2.4', skiprows=4)

# Filtern auf Kreisebene (NUTS 3 ist nicht leer) und Auswahl der relevanten Spalten (Name und Jahr 2022)
einkommen_clean = einkommen[einkommen['NUTS 3'].notna()][['Gebietseinheit', 2022]].copy()
einkommen_clean.columns = ['Gebietseinheit', 'Einkommen_2022']

# Funktion zur Normalisierung von Kreisnamen für den Merge (Verbinden der Tabellen)
def name_normalisieren(name):
    if not isinstance(name, str): return ""
    name = name.lower()
    # Entfernen von Zusätzen wie "Kreis", "Stadt", "Landkreis" für besseres Matching
    name = re.sub(r'(kreis|stadt|stâ€ždteregion|stã¤dteregion|regierungsbezirk|krfr\.|landkreis)', '', name)
    name = re.sub(r',', '', name) # Kommas weg
    # Umlaute normalisieren für den Vergleich
    name = name.replace('â€ž', 'ä').replace('ã¤', 'ä').replace('ã¼', 'ü').replace('ã¶', 'ö')
    name = name.replace('ü', 'u').replace('ä', 'a').replace('ö', 'o').replace('ß', 'ss')
    return re.sub(r'\W+', '', name).strip() # Nur Buchstaben behalten

# Erstellen der "Join Keys" (Schlüssel zum Verbinden)
einkommen_clean['Join_Key'] = einkommen_clean['Gebietseinheit'].apply(name_normalisieren)
schulen['Kreis_Key'] = schulen['Kreis'].apply(name_normalisieren)

# Erstellen einer Mapping-Tabelle (Wörterbuch) für das Einkommen
einkommen_map = einkommen_clean.set_index('Join_Key')['Einkommen_2022'].to_dict()

# Einkommen an die Schulen mergen (basierend auf dem Kreis)
schulen['Einkommen_Kreis'] = schulen['Kreis_Key'].map(einkommen_map)

# Fallback: Wenn Kreis-Match fehlschlägt, versuche Gemeinde-Match (manche kreisfreie Städte heißen wie Gemeinden)
schulen['Gemeinde_Key'] = schulen['Gemeinde'].apply(name_normalisieren)
maske_fehlt = schulen['Einkommen_Kreis'].isna()
schulen.loc[maske_fehlt, 'Einkommen_Kreis'] = schulen.loc[maske_fehlt, 'Gemeinde_Key'].map(einkommen_map)

# ---------------------------------------------------------
# 3. Laden der Schulstatistiken (Schüler/Lehrkräfte)
# ---------------------------------------------------------
stats = pd.read_csv('Schulen, Schülerinnen und Schüler, Schulabgängerinnen und Schulabgänger und Lehrkräfte an allgemeinbildende Schulen.csv', sep=';', encoding='latin1', skiprows=5)

# Spalten manuell benennen, da die Datei keine sauberen Header hat
stats.columns = ['Region', 'Jahr', 'Kategorie', 'Subkategorie', 'Einheit', 'Gesamt', 'Grundschulen', 'Hauptschulen', 'Volksschulen', 'Foerderschulen_GH', 'Foerderschulen_RG', 'Realschulen', 'PRIMUS', 'Sekundarschulen', 'Gesamtschulen', 'Gemeinschaftsschulen', 'Waldorf', 'Gymnasien', 'Weiterbildungskollegs']

# Filtern auf das aktuellste Jahr (2022/23)
stats_aktuell = stats[stats['Jahr'] == '2022/23'].copy()

# Hilfsfunktion zum Bereinigen von Zahlen (Tausenderpunkte entfernen, Komma zu Punkt)
def zahl_bereinigen(x):
    if pd.isna(x) or x == '-': return 0
    return float(str(x).replace('.', '').replace(',', '.'))

# Zahlen für relevante Schulformen bereinigen
relevante_schulformen = ['Grundschulen', 'Hauptschulen', 'Realschulen', 'Sekundarschulen', 'Gesamtschulen', 'Gymnasien']
for spalte in relevante_schulformen:
    stats_aktuell[spalte] = stats_aktuell[spalte].apply(zahl_bereinigen)

# Normalisieren der Gemeindenamen in der Statistik für den Merge
stats_aktuell['Gemeinde_Key'] = stats_aktuell['Region'].apply(name_normalisieren)

# Erstellen einer Lookup-Table für Betreuungsrelationen (Schüler pro Lehrkraft)
# Struktur: (Gemeinde, Schulform) -> Verhältnis
ratio_map = {}
gemeinden = stats_aktuell['Gemeinde_Key'].unique()

for gem in gemeinden:
    daten_gem = stats_aktuell[stats_aktuell['Gemeinde_Key'] == gem]
    try:
        # Zeilen für Schüler und Lehrkräfte finden
        schueler_row = daten_gem[daten_gem['Kategorie'].str.contains('Schüler', na=False)]
        lehrer_row = daten_gem[daten_gem['Kategorie'].str.contains('Lehrkräfte', na=False)]
        
        if not schueler_row.empty and not lehrer_row.empty:
            for form in relevante_schulformen:
                s = schueler_row[form].values[0] # Schülerzahl
                l = lehrer_row[form].values[0]   # Lehrerzahl
                if l > 0:
                    ratio_map[(gem, form)] = s / l
    except:
        continue

# Funktion, um die Ratio für jede Schule abzurufen
def get_ratio(row):
    # Schlüssel ist Kombination aus Gemeinde und Schulform
    key = (row['Gemeinde_Key'], row['Schulform_Gruppe'])
    return ratio_map.get(key, np.nan)

schulen['Betreuungsrelation'] = schulen.apply(get_ratio, axis=1)

# ---------------------------------------------------------
# 4. Finales Aufräumen und Speichern
# ---------------------------------------------------------
# Sozialindex numerisch machen (für Korrelationen)
schulen['Sozialindex_Numerisch'] = pd.to_numeric(schulen['Sozialindexstufe'], errors='coerce')

# Endgültige Auswahl der Spalten für die Datei
finaler_datensatz = schulen[[
    'Schulnummer', 'Kurzbezeichnung', 'Schulform_Gruppe', 
    'Gemeinde', 'Kreis', 'Sozialindexstufe', 'Sozialindex_Numerisch',
    'Einkommen_Kreis', 'Betreuungsrelation'
]].copy()

# Statistik vor dem Bereinigen
print(f"Anzahl Schulen gesamt: {len(finaler_datensatz)}")
print(f"Schulen ohne Einkommensdaten: {finaler_datensatz['Einkommen_Kreis'].isna().sum()}")
print(f"Schulen ohne Betreuungsrelation: {finaler_datensatz['Betreuungsrelation'].isna().sum()}")

# NaN-Werte behandeln:
# 1. Zeilen ohne Sozialindex entfernen (sind ungültige Daten)
finaler_datensatz = finaler_datensatz[finaler_datensatz['Sozialindex_Numerisch'].notna()]

# 2. Für fehlende Einkommensdaten: Durchschnitt der Schulform verwenden
for schulform in finaler_datensatz['Schulform_Gruppe'].unique():
    maske = (finaler_datensatz['Schulform_Gruppe'] == schulform) & (finaler_datensatz['Einkommen_Kreis'].notna())
    if maske.sum() > 0:
        durchschnitt = finaler_datensatz.loc[maske, 'Einkommen_Kreis'].mean()
        fehlend = (finaler_datensatz['Schulform_Gruppe'] == schulform) & (finaler_datensatz['Einkommen_Kreis'].isna())
        finaler_datensatz.loc[fehlend, 'Einkommen_Kreis'] = durchschnitt

# 3. Für fehlende Betreuungsrelation: Durchschnitt der Schulform verwenden
for schulform in finaler_datensatz['Schulform_Gruppe'].unique():
    maske = (finaler_datensatz['Schulform_Gruppe'] == schulform) & (finaler_datensatz['Betreuungsrelation'].notna())
    if maske.sum() > 0:
        durchschnitt = finaler_datensatz.loc[maske, 'Betreuungsrelation'].mean()
        fehlend = (finaler_datensatz['Schulform_Gruppe'] == schulform) & (finaler_datensatz['Betreuungsrelation'].isna())
        finaler_datensatz.loc[fehlend, 'Betreuungsrelation'] = durchschnitt

# Falls immer noch NaN vorhanden sind (z.B. ganze Schulform fehlt), mit Gesamtdurchschnitt füllen
finaler_datensatz['Einkommen_Kreis'].fillna(finaler_datensatz['Einkommen_Kreis'].mean(), inplace=True)
finaler_datensatz['Betreuungsrelation'].fillna(finaler_datensatz['Betreuungsrelation'].mean(), inplace=True)

# Zahlen runden für bessere Lesbarkeit
finaler_datensatz['Einkommen_Kreis'] = finaler_datensatz['Einkommen_Kreis'].round(0).astype(int)
finaler_datensatz['Betreuungsrelation'] = finaler_datensatz['Betreuungsrelation'].round(2)

# Spaltennamen ins Deutsche übersetzen für bessere Verständlichkeit
finaler_datensatz.columns = [
    'Schulnummer', 'Schulname', 'Schulform', 
    'Gemeinde', 'Kreis', 'Sozialindex_Stufe', 'Sozialindex',
    'Einkommen_Pro_Einwohner_Euro', 'Schueler_Pro_Lehrkraft'
]

print(f"\nNach Bereinigung: {len(finaler_datensatz)} Schulen")
print("Keine fehlenden Werte mehr!")

# Speichern als CSV (Semikolon getrennt, deutsches Format)
finaler_datensatz.to_csv('merged_schuldaten_final.csv', index=False, sep=';', decimal=',', encoding='utf-8-sig')

print("\nFertig! Datei 'merged_schuldaten_final.csv' wurde erstellt.")
print("Die Datei enthält keine NaN-Werte und ist gut lesbar.")