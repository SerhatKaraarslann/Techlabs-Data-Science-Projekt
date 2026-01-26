import pandas as pd
import numpy as np
import re
import os
import sys

# Arbeitsverzeichnis zum data-Verzeichnis setzen
code_dir = os.path.dirname(os.path.abspath(__file__)) 
project_root = os.path.dirname(code_dir)
data_dir = os.path.join(project_root, "data")

if not os.path.exists(data_dir):
    print(f"[ERROR] data-Verzeichnis nicht gefunden: {data_dir}")
    sys.exit(1)

os.chdir(data_dir)

print("=" * 80)
print("ERWEITERTER DATENSATZ-MERGE - NRW BILDUNGSANALYSE")
print("=" * 80)

# Ensure output directory exists
output_dir = os.path.join(data_dir, 'output')
input_dir = os.path.join(data_dir, 'input')
os.makedirs(output_dir, exist_ok=True)

# ---------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------
def text_bereinigen(text):
    """Bereinigt Encoding-Fehler in deutschen Texten"""
    if not isinstance(text, str): return text
    text = text.replace('M nster', 'Münster').replace('D sseldorf', 'Düsseldorf')
    text = text.replace('K ln', 'Köln').replace('K"ln', 'Köln')
    text = text.replace('H rth', 'Hürth').replace('st„dter', 'städter')
    text = text.replace('L dinghausen', 'Lüdinghausen').replace('M„rkischen', 'Märkischen')
    return text.strip()

def name_normalisieren(name):
    """Normalisiert Orts-/Kreisnamen für besseres Matching"""
    if not isinstance(name, str): return ""
    name = name.lower()
    name = re.sub(r'(kreis|stadt|stâ€ždteregion|stã¤dteregion|regierungsbezirk|krfr\.|landkreis)', '', name)
    name = re.sub(r',', '', name)
    name = name.replace('â€ž', 'ä').replace('ã¤', 'ä').replace('ã¼', 'ü').replace('ã¶', 'ö')
    name = name.replace('ü', 'u').replace('ä', 'a').replace('ö', 'o').replace('ß', 'ss')
    return re.sub(r'\W+', '', name).strip()

def schulform_bestimmen(name):
    """Kategorisiert Schulen nach ihrer Schulform"""
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
    """Konvertiert deutsche Zahlenformate in floats"""
    if pd.isna(x) or x == '-': return 0
    return float(str(x).replace('.', '').replace(',', '.'))


#  Laden und Bereinigen der Schulliste

print("\n Lade Schulliste...")
# Schulliste laden
schulen = pd.read_csv(os.path.join(input_dir, 'schulliste_sj_25_26_open_data.csv'), sep=';', encoding='latin1')

# Relevante Spalten auswählen und umbenennen
spalten_zum_bereinigen = ['Kurzbezeichnung', 'Bezirksregierung', 'Kreis', 'Gemeinde']
for spalte in spalten_zum_bereinigen:
    schulen[spalte] = schulen[spalte].apply(text_bereinigen)

schulen['Schulform_Gruppe'] = schulen['Kurzbezeichnung'].apply(schulform_bestimmen) # Schulform kategorisieren
schulen['Kreis_Key'] = schulen['Kreis'].apply(name_normalisieren) # Normalisierte Kreisschlüssel
schulen['Gemeinde_Key'] = schulen['Gemeinde'].apply(name_normalisieren) # Normalisierte Gemeindeschlüssel

print(f"   ✓ {len(schulen)} Schulen geladen")


#  Einkommensdaten (verfügbares Einkommen pro Einwohner)

print("\n Lade Einkommensdaten...")
# lade Einkommensdaten aus VGRDL
einkommen = pd.read_excel(os.path.join(input_dir, 'vgrdl_r2b3_bs2023.xlsx'), sheet_name='2.4', skiprows=4)
einkommen_clean = einkommen[einkommen['NUTS 3'].notna()][['Gebietseinheit', 2022]].copy() # Nur relevante Spalten, keine NaNs
einkommen_clean.columns = ['Gebietseinheit', 'Einkommen_2022'] # Spalten umbenennen
einkommen_clean['Join_Key'] = einkommen_clean['Gebietseinheit'].apply(name_normalisieren) # Normalisierte Join-Keys
einkommen_map = einkommen_clean.set_index('Join_Key')['Einkommen_2022'].to_dict() # Mapping erstellen

schulen['Einkommen_Pro_Einwohner'] = schulen['Kreis_Key'].map(einkommen_map) # Einkommensdaten mappen
maske_fehlt = schulen['Einkommen_Pro_Einwohner'].isna() # Maske für fehlende Werte, da manche Gemeinden nicht im Kreis gelistet sind
schulen.loc[maske_fehlt, 'Einkommen_Pro_Einwohner'] = schulen.loc[maske_fehlt, 'Gemeinde_Key'].map(einkommen_map) # Fehlende Werte mit Gemeinde-Daten füllen

print(f"   ✓ Einkommensdaten verknüpft ({schulen['Einkommen_Pro_Einwohner'].notna().sum()} Matches)")


# Einwohnerzahlen (Stadtgröße)

print("\n Lade Einwohnerzahlen...")
einwohner = pd.read_excel(os.path.join(input_dir, 'vgrdl_r2b3_bs2023.xlsx'), sheet_name='3', skiprows=4)
einwohner_clean = einwohner[einwohner['NUTS 3'].notna()][['Gebietseinheit', 2022]].copy() # Nur relevante Spalten, keine NaNs
einwohner_clean.columns = ['Gebietseinheit', 'Einwohner_2022'] # Spalten umbenennen
einwohner_clean['Join_Key'] = einwohner_clean['Gebietseinheit'].apply(name_normalisieren) # Normalisierte Join-Keys
einwohner_map = einwohner_clean.set_index('Join_Key')['Einwohner_2022'].to_dict() # Mapping erstellen

schulen['Einwohnerzahl'] = schulen['Kreis_Key'].map(einwohner_map)
maske_fehlt = schulen['Einwohnerzahl'].isna()
schulen.loc[maske_fehlt, 'Einwohnerzahl'] = schulen.loc[maske_fehlt, 'Gemeinde_Key'].map(einwohner_map)

print(f" Einwohnerzahlen verknüpft ({schulen['Einwohnerzahl'].notna().sum()} Matches)")


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
    """"Holt das Schüler-Lehrkräfte-Verhältnis aus dem Mapping"""
    key = (row['Gemeinde_Key'], row['Schulform_Gruppe']) # Schlüssel erstellen
    return ratio_map.get(key, np.nan) # Verhältnis zurückgeben oder NaN

schulen['Schueler_Pro_Lehrkraft'] = schulen.apply(get_ratio, axis=1) # Verhältnis in den DataFrame einfügen

print(f"Betreuungsrelationen berechnet ({schulen['Schueler_Pro_Lehrkraft'].notna().sum()} Schulen)")


#  Schulabgangsquoten (Abgänger ohne Hauptschulabschluss)

print("\nExtrahiere Schulabgangsquoten...")
try:
    # Filtern auf Zeilen mit "Abgänger" und "ohne Hauptschulabschluss"
    abgaenger = stats_aktuell[ 
        (stats_aktuell['Kategorie'].str.contains('Abgänger', na=False)) &  # Nur Abgänger
        (stats_aktuell['Subkategorie'].str.contains('ohne Hauptschulabschluss', na=False)) # Nur ohne Hauptschulabschluss
    ].copy() # Kopie erstellen
    
    # Gesamtzahl der Schüler für Quotenberechnung
    schueler_gesamt = stats_aktuell[ # Nur Gesamtzahl der Schüler
        stats_aktuell['Kategorie'].str.contains('Schüler/-innen insgesamt', na=False) # Filtern auf Gesamtzahl
    ].copy() # Kopie erstellen
    
    # Mapping für Abgangsquote (Anteil ohne Hauptschulabschluss)
    abgangsquote_map = {} # Initialisierung des Mappings
    
    for gem in abgaenger['Gemeinde_Key'].unique(): # Durchlauf pro Gemeinde
        try: # Fehlerbehandlung
            abg = abgaenger[abgaenger['Gemeinde_Key'] == gem] # Abgänger-Daten der Gemeinde filtern
            sch = schueler_gesamt[schueler_gesamt['Gemeinde_Key'] == gem] # Schüler-Gesamt-Daten der Gemeinde filtern
            
            if not abg.empty and not sch.empty: # Sicherstellen, dass beide Datensätze existieren
                for form in relevante_schulformen: # Durchlauf pro Schulform
                    abg_zahl = abg[form].values[0] if len(abg[form].values) > 0 else 0 # Abgängerzahl
                    sch_zahl = sch[form].values[0] if len(sch[form].values) > 0 else 0 # Schülergesamtzahl
                    
                    if sch_zahl > 0:
                        # Quote = Abgänger ohne Hauptschulabschluss / Gesamtschülerzahl * 100
                        quote = (abg_zahl / sch_zahl) * 100
                        abgangsquote_map[(gem, form)] = quote
        except:
            continue
    
    def get_abgangsquote(row):
        """"Holt die Abgangsquote aus dem Mapping"""
        key = (row['Gemeinde_Key'], row['Schulform_Gruppe']) # Schlüssel erstellen
        return abgangsquote_map.get(key, np.nan) # Quote zurückgeben oder NaN
    
    schulen['Abgangsquote_Ohne_Abschluss'] = schulen.apply(get_abgangsquote, axis=1) # Quote in den DataFrame einfügen
    
    print(f"Abgangsquoten berechnet ({schulen['Abgangsquote_Ohne_Abschluss'].notna().sum()} Schulen)") # Ausgabe der Anzahl berechneter Quoten
except Exception as e:
    print(f"Abgangsquoten konnten nicht berechnet werden: {e}")
    schulen['Abgangsquote_Ohne_Abschluss'] = np.nan


# Finales Aufräumen und Aggregation
print("\n Erstelle finalen Datensatz...")

# Sozialindex numerisch konvertieren
schulen['Sozialindex_Numerisch'] = pd.to_numeric(schulen['Sozialindexstufe'], errors='coerce') # Fehlerhafte Werte zu NaN konvertieren 

# Finale Spaltenauswahl 
finaler_datensatz = schulen[[
    'Schulnummer', 'Kurzbezeichnung', 'Schulform_Gruppe', 
    'Gemeinde', 'Kreis', 'Sozialindexstufe', 'Sozialindex_Numerisch',
    'Einkommen_Pro_Einwohner', 'Einwohnerzahl', 'Bildungsausgaben_Pro_Kopf',
    'Schueler_Pro_Lehrkraft', 'Abgangsquote_Ohne_Abschluss'
]].copy()

# Nur Schulen mit Sozialindex behalten 
finaler_datensatz = finaler_datensatz[finaler_datensatz['Sozialindex_Numerisch'].notna()]

# NaN-Werte intelligent füllen 
print("\n   Fülle fehlende Werte...")
for spalte in ['Einkommen_Pro_Einwohner', 'Einwohnerzahl', 'Bildungsausgaben_Pro_Kopf', 
               'Schueler_Pro_Lehrkraft', 'Abgangsquote_Ohne_Abschluss']:
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
finaler_datensatz['Abgangsquote_Ohne_Abschluss'] = finaler_datensatz['Abgangsquote_Ohne_Abschluss'].round(2)

# Deutsche Spaltennamen
finaler_datensatz.columns = [
    'Schulnummer', 'Schulname', 'Schulform', 
    'Gemeinde', 'Kreis', 'Sozialindex_Stufe', 'Sozialindex',
    'Einkommen_Pro_Einwohner_Euro', 'Einwohnerzahl', 'Bildungsausgaben_Euro',
    'Schueler_Pro_Lehrkraft', 'Abgangsquote_Prozent'
]

# Speichern
finaler_datensatz.to_csv(os.path.join(output_dir, 'merged_schuldaten_extended.csv'), index=False, sep=';', decimal=',', encoding='utf-8-sig')

print(f"\n{'='*80}")
print(f"ERFOLG! {len(finaler_datensatz)} Schulen im finalen Datensatz")
print(f"{'='*80}")
print(f"\nDatei erstellt: merged_schuldaten_extended.csv")
print(f"\nEnthaltene Variablen:")
print(f"   • Sozialindex (1-9)")
print(f"   • Einkommen pro Einwohner (€)")
print(f"   • Einwohnerzahl (Stadtgröße)")
print(f"   • Bildungsausgaben (€)")
print(f"   • Schüler-Lehrkraft-Verhältnis")
print(f"   • Abgangsquote ohne Abschluss (%)")
print(f"\n➜ Bereit für Visualisierungen und Analysen!")
