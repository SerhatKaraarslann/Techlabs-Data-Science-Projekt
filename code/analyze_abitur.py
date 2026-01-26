import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')
import os
import sys

# Set working directory to data folder
code_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(code_dir)
data_dir = os.path.join(project_root, "data")

if not os.path.exists(data_dir):
    print(f"[ERROR] data-Verzeichnis nicht gefunden: {data_dir}")
    sys.exit(1)

os.chdir(data_dir)

# Force UTF-8 output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("ABITUR ANALYSE NRW 2020-2024")
print("=" * 80)

# Ensure output directory exists
output_dir = os.path.join(data_dir, 'output')
input_dir = os.path.join(data_dir, 'input')
os.makedirs(output_dir, exist_ok=True)

# Lade Schuldaten
try:
    df = pd.read_csv('merged_schuldaten_extended.csv', sep=';', decimal=',', encoding='utf-8-sig')
    # Convert to numeric
    df['Sozialindex'] = pd.to_numeric(df['Sozialindex'], errors='coerce')
    df['Schueler_Pro_Lehrkraft'] = pd.to_numeric(df['Schueler_Pro_Lehrkraft'], errors='coerce')
    print(f"[OK] Schuldaten geladen: {len(df)} Schulen")
except FileNotFoundError:
    print("FEHLER: merged_schuldaten_extended.csv nicht gefunden!")
    exit()


# Lade Abiturdaten
def lade_abitur_jahr(jahr):
    try:
        file_pattern = f'Aus_Abiturnoten_{jahr}.xlsx'
        files = [f for f in os.listdir('.') if f.startswith('Aus_Abiturnoten_') and f.endswith('.xlsx')]
        
        if not files:
            print(f"[WARNUNG] Keine Abiturdaten-Dateien gefunden!")
            return None
        
        # Use the first file found (assumed to be the correct one)
        xl_file = pd.ExcelFile(files[0])
        sheet_name = xl_file.sheet_names[0]
        
        data = pd.read_excel(files[0], sheet_name=sheet_name)
        
        # Rename columns to standardize
        data.rename(columns={
            'Durchschnittsnote': 'Notendurchschnitt',
            'Pruefungsteilnehmer': 'Anzahl_Pruefungen',
            'Bestandene Pruefungen': 'Bestanden'
        }, inplace=True)
        
        # Calculate missing columns if needed
        if 'Anzahl_Pruefungen' not in data.columns and 'Bestanden' in data.columns:
            data['Anzahl_Pruefungen'] = data['Bestanden'] * 1.05  # Rough estimate
        
        if 'Bestanden' not in data.columns:
            data['Bestanden'] = data['Anzahl_Pruefungen'] * 0.96  # Rough estimate
        
        if 'Erfolgsquote' in data:
            data['Erfolgsquote'] = (data['Bestanden'] / data['Anzahl_Pruefungen']) * 100
        
        return data
    
    except Exception as e:
        print(f"[WARNUNG] Fehler beim Laden von {jahr}: {e}")
        return None


# Aggregiere Abiturdaten auf Kreis-Ebene

print("\n Verarbeite Abiturdaten...")

abitur_daten = [] # Liste fuer alle Abiturdaten

# Try to load any available Abitur files
files = [f for f in os.listdir('.') if f.startswith('Aus_Abiturnoten_') and f.endswith('.xlsx')] # Alle passenden Dateien finden

if not files:
    print("[INFO] Keine Abitur-Dateien gefunden. Verwende Schuldaten ohne Abiturspezifiken.")
else:
    print(f"[OK] {len(files)} Abiturdatei(en) gefunden") 
    for file in files:
        try:
            data = pd.read_excel(file) # Lese Excel-Datei
            print(f"     {file}: {len(data)} Eintraege") # Anzahl Eintraege anzeigen
            abitur_daten.append(data) # Fuege Daten zur Liste hinzu
        except Exception as e:
            print(f"     [WARNUNG] Fehler in {file}: {e}")

# Aggregiere Schulen nach Gymnasien/Gesamtschulen pro Kreis
print("\n Aggregiere Gymnasien/Gesamtschulen pro Kreis...")

# Filter for Gymnasien and Gesamtschulen (plural/singular, whitespace-insensitive)
schulformen = {'gymnasium', 'gymnasien', 'gesamtschule', 'gesamtschulen'}
df['Schulform_Clean'] = df['Schulform'].astype(str).str.strip().str.lower()
df_gymnasien = df[df['Schulform_Clean'].isin(schulformen)].copy()

print(f"[OK] {len(df_gymnasien)} Gymnasien/Gesamtschulen von {len(df)} Schulen")

# Aggregiere nach Kreis
kreis_stats = df_gymnasien.groupby('Kreis').agg({
    'Schulnummer': 'count',
    'Sozialindex': 'mean',
    'Einkommen_Pro_Einwohner_Euro': 'mean',
    'Schueler_Pro_Lehrkraft': 'mean'
}).reset_index()

kreis_stats.columns = ['Kreis', 'Anzahl_Schulen', 'Sozialindex_Avg', 'Einkommen_Avg', 'Betreuung_Avg']

# Markiere Muenster als Referenzstadt
# Suche nach 'nster' UND 'Stadt' um Enkodierungsprobleme zu vermeiden
kreis_stats['Ist_Muenster'] = (
    kreis_stats['Kreis'].str.contains('nster', case=False, na=False) &
    kreis_stats['Kreis'].str.contains('Stadt', case=False, na=False)
)
kreis_stats['Referenzstadt'] = kreis_stats['Ist_Muenster'].apply(lambda x: 'JA - REFERENZ' if x else 'Nein')

print(f"[OK] {len(df_gymnasien)} Gymnasien/Gesamtschulen in {len(kreis_stats)} Kreisen")

# Berechne Muenster-Statistik
muenster_row = kreis_stats[kreis_stats['Ist_Muenster']]
if not muenster_row.empty:
    muenster_stats = muenster_row.iloc[0]
    print(f"\n   Muenster - Gymnasium/Gesamtschule Statistik:")
    print(f"   + Anzahl Schulen: {muenster_stats['Anzahl_Schulen']:.0f}")
    print(f"   + Sozialindex: {muenster_stats['Sozialindex_Avg']:.2f}")
    print(f"   + Einkommen: EUR {muenster_stats['Einkommen_Avg']:.0f}")
    print(f"   + Betreuung: {muenster_stats['Betreuung_Avg']:.2f} Schueler/Lehrer")

# Speichere Kreis-Statistiken
kreis_stats_export = kreis_stats.sort_values('Sozialindex_Avg', ascending=False)
kreis_stats_export.to_csv('gymnasien_kreise_stats.csv', index=False, sep=';', decimal=',', encoding='utf-8-sig')
print(f"\n[OK] Gymnasien-Kreis-Statistiken gespeichert: gymnasien_kreise_stats.csv")


# Erstelle Visualisierungen
print(f"\n Erstelle Visualisierungen...")

plt.style.use('seaborn-v0_8-darkgrid')
colors_muenster = kreis_stats['Ist_Muenster'].apply(lambda x: '#d81b60' if x else '#1f77b4') # Rot fuer Muenster blau für andere

# VIZ 1: Top 10 nach Sozialindex
print(f"   [1/3] Top/Bottom Rankings...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Gymnasien/Gesamtschulen: Top 10 und Bottom 10 nach Sozialindex', fontsize=14, fontweight='bold')

top10 = kreis_stats.nlargest(10, 'Sozialindex_Avg')
bottom10 = kreis_stats.nsmallest(10, 'Sozialindex_Avg')

# Ensure Muenster is shown even if not in top/bottom lists
if not muenster_row.empty:
    if not top10['Ist_Muenster'].any():
        top10 = pd.concat([top10, muenster_row]).drop_duplicates('Kreis')
    if not bottom10['Ist_Muenster'].any():
        bottom10 = pd.concat([bottom10, muenster_row]).drop_duplicates('Kreis')

top_colors = top10['Ist_Muenster'].apply(lambda x: '#d81b60' if x else '#2ca02c')
bottom_colors = bottom10['Ist_Muenster'].apply(lambda x: '#d81b60' if x else '#ff7f0e')

ax1.barh(range(len(top10)), top10['Sozialindex_Avg'].values, color=top_colors)
ax1.set_yticks(range(len(top10)))
ax1.set_yticklabels(top10['Kreis'].values, fontsize=9)
ax1.set_xlabel('Sozialindex')
ax1.set_title('Top 10 (Best)')
ax1.invert_yaxis()

ax2.barh(range(len(bottom10)), bottom10['Sozialindex_Avg'].values, color=bottom_colors)
ax2.set_yticks(range(len(bottom10)))
ax2.set_yticklabels(bottom10['Kreis'].values, fontsize=9)
ax2.set_xlabel('Sozialindex')
ax2.set_title('Bottom 10 (Worst)')
ax2.invert_yaxis()

plt.tight_layout()
plt.savefig('viz_05_gymnasien_top_bottom.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"      [OK] Gespeichert: viz_05_gymnasien_top_bottom.png")

# Sozialindex vs. Betreuung
print(f"   Sozialindex vs. Betreuungsrelation...")
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(
    kreis_stats['Sozialindex_Avg'],
    kreis_stats['Betreuung_Avg'],
    s=100,
    c=colors_muenster,
    alpha=0.6,
    edgecolors='black'
)
if not muenster_row.empty:
    ax.scatter(
        muenster_stats['Sozialindex_Avg'],
        muenster_stats['Betreuung_Avg'],
        s=260,
        c='#d81b60',
        marker='o',
        edgecolors='black',
        linewidths=1.5,
        label='Muenster (Referenz)',
        zorder=5
    )
ax.set_xlabel('Sozialindex', fontsize=11)
ax.set_ylabel('Betreuungsrelation (Schueler/Lehrer)', fontsize=11)
ax.set_title('Gymnasien/Gesamtschulen: Sozialindex vs. Betreuungsrelation', fontsize=12, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('viz_06_gymnasien_sozialindex_betreuung.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"      [OK] Gespeichert: viz_06_gymnasien_sozialindex_betreuung.png")

# Anzahl Schulen nach Kreis
print(f"   Schulanzahl nach Kreis...")
fig, ax = plt.subplots(figsize=(12, 8))
sorted_kreis = kreis_stats.sort_values('Anzahl_Schulen', ascending=True)
colors = sorted_kreis['Ist_Muenster'].apply(lambda x: '#d81b60' if x else '#1f77b4')
ax.barh(range(len(sorted_kreis)), sorted_kreis['Anzahl_Schulen'].values, color=colors)
ax.set_yticks(range(len(sorted_kreis)))
ax.set_yticklabels(sorted_kreis['Kreis'].values, fontsize=8)
ax.set_xlabel('Anzahl Gymnasien/Gesamtschulen')
ax.set_title('Anzahl Gymnasien/Gesamtschulen nach Kreis in NRW', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('viz_07_gymnasien_schulanzahl.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"      [OK] Gespeichert: viz_07_gymnasien_schulanzahl.png")

print("\n" + "=" * 80)
print("ERFOLG! Abitur-Analyse abgeschlossen")
print("=" * 80)
print("\nErstellt:")
print("   * gymnasien_kreise_stats.csv - Aggregierte Daten mit Muenster-Markierung")
print("   * viz_05_gymnasien_top_bottom.png")
print("   * viz_06_gymnasien_sozialindex_betreuung.png")
print("   * viz_07_gymnasien_schulanzahl.png\n")
