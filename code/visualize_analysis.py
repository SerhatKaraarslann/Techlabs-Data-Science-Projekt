import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')
import json
import urllib.request
import unicodedata
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

# Force UTF-8 output, especially on Windows consoles
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def normalize_name(name):
    """Normalize German city/county names for safer matching."""
    if name is None:
        return ''
    txt = unicodedata.normalize('NFKD', str(name)) # Normalize Unicode
    txt = ''.join(ch for ch in txt if not unicodedata.combining(ch)) # Remove diacritics
    txt = txt.replace('kreisfreie stadt', '').replace('stadt', '').replace('-kreis', '').replace('kreis', '') # Remove common suffixes
    txt = ''.join(ch for ch in txt if ch.isalnum() or ch.isspace() or ch == '-') # Keep alphanumeric, spaces, hyphens
    return ' '.join(txt.lower().split()) # Lowercase and normalize spaces

print("=" * 80)     
print("NRW BILDUNGSANALYSE - VISUALISIERUNGEN")
print("=" * 80)

# Ensure output directory exists
output_dir = os.path.join(data_dir, 'output')
os.makedirs(output_dir, exist_ok=True)

try:
    print(f"\n Lade Daten...")
    df = pd.read_csv(os.path.join(output_dir, 'merged_schuldaten_extended.csv'), sep=';', decimal=',', encoding='utf-8-sig')
    
    # Convert string columns to numeric
    df['Sozialindex'] = pd.to_numeric(df['Sozialindex'], errors='coerce') # Fehlerhafte Werte zu NaN konvertieren
    df['Schueler_Pro_Lehrkraft'] = pd.to_numeric(df['Schueler_Pro_Lehrkraft'], errors='coerce') # Fehlerhafte Werte zu NaN konvertieren
    
    print(f"   [OK] {len(df)} Schulen geladen") 
    
except FileNotFoundError:
    print("   [FEHLER] merged_schuldaten_extended.csv nicht gefunden!")
    exit()


# Datenübersicht
print(f"\n Datenübersicht")
print(f"\n   Spalten: {list(df.columns)}")
print(f"\n   Statistische Zusammenfassung:")
print(df.describe().to_string())


# Aggregation auf Stadt-Ebene
print(f"\n Aggregiere auf Stadt-Ebene...")

# Gruppierung nach Kreis/Stadt
stadt_agg = df.groupby('Kreis').agg({
    'Schulnummer': 'count', # Anzahl der Schulen
    'Sozialindex': 'mean', # Durchschnitt Sozialindex
    'Einkommen_Pro_Einwohner_Euro': 'mean', # Durchschnitt Einkommen
    'Einwohnerzahl': 'first', # Einwohnerzahl (einmalig pro Stadt)
    'Bildungsausgaben_Euro': 'mean', # Durchschnitt Bildungsausgaben
    'Schueler_Pro_Lehrkraft': 'mean' # Durchschnitt Betreuungsrelation
}).reset_index()

stadt_agg.columns = ['Stadt', 'Anzahl_Schulen', 'Sozialindex_Avg', 'Einkommen_Avg', 
                     'Einwohnerzahl', 'Bildungsausgaben_Avg', 'Betreuungsrelation_Avg']

# Stadtgrößen-Kategorien
def stadtgroesse_kategorie(einwohner):
    if einwohner < 50000:
        return 'Klein (<50k)'
    elif einwohner < 150000:
        return 'Mittel (50-150k)'
    elif einwohner < 500000:
        return 'Gross (150-500k)'
    else:
        return 'Metropole (>500k)'

stadt_agg['Stadtgroesse'] = stadt_agg['Einwohnerzahl'].apply(stadtgroesse_kategorie) # Kategorisierung der Stadtgröße

# Markiere Muenster als Referenzstadt
# Suche nach 'nster' UND 'Stadt' um Enkodierungsprobleme zu vermeiden
stadt_agg['Ist_Muenster'] = ( # Filtern nach Münster
    stadt_agg['Stadt'].str.contains('nster', case=False, na=False) & # Sicherstellen, dass 'Stadt' im Namen ist
    stadt_agg['Stadt'].str.contains('Stadt', case=False, na=False) # Sicherstellen, dass 'Stadt' im Namen ist
)
stadt_agg['Referenzstadt'] = stadt_agg['Ist_Muenster'].apply(lambda x: 'JA - REFERENZ' if x else 'Nein') # Markierung für Export
stadt_agg['Stadt_norm'] = stadt_agg['Stadt'].apply(normalize_name) # Normalisierte Stadtnamen für spätere Verwendung

print(f"   [OK] {len(stadt_agg)} Staedte/Kreise aggregiert") # Ausgabe der Anzahl der aggregierten Städte

# Berechne Muenster als Referenzstadt
muenster_row = stadt_agg[stadt_agg['Ist_Muenster']]
if not muenster_row.empty:
    muenster_stats = muenster_row.iloc[0]
    print(f"\n   Muenster als Referenzstadt:")
    print(f"   + Sozialindex: {muenster_stats['Sozialindex_Avg']:.2f}") # Durchschnitt Sozialindex
    print(f"   + Einkommen: EUR {muenster_stats['Einkommen_Avg']:.0f}") # Durchschnitt Einkommen
    print(f"   + Einwohnerzahl: {muenster_stats['Einwohnerzahl']:.0f}") # Einwohnerzahl
    print(f"   + Betreuung: {muenster_stats['Betreuungsrelation_Avg']:.2f} Schueler/Lehrkraft") # Durchschnitt Betreuungsrelation

print(f"\n   Verteilung Stadtgroessen:")
print(stadt_agg['Stadtgroesse'].value_counts())

# Speichern der Stadt-Aggregation mit Muenster-Markierung
stadt_agg_export = stadt_agg[['Stadt', 'Referenzstadt', 'Anzahl_Schulen', 'Sozialindex_Avg', 
                               'Einkommen_Avg', 'Einwohnerzahl', 'Bildungsausgaben_Avg', 
                               'Betreuungsrelation_Avg', 'Stadtgroesse']].copy()
stadt_agg_export = stadt_agg_export.sort_values('Sozialindex_Avg', ascending=False)
stadt_agg_export.to_csv(os.path.join(output_dir, 'stadt_aggregiert.csv'), index=False, sep=';', decimal=',', encoding='utf-8-sig')
print(f"   [OK] Stadt-Aggregation gespeichert: stadt_aggregiert.csv")


# VISUALISIERUNGEN
print(f"\n Erstelle Visualisierungen...")

plt.style.use('seaborn-v0_8-darkgrid') # Setze Stil, benutze seaborn darkgrid
colors_muenster = stadt_agg['Ist_Muenster'].apply(lambda x: '#d62728' if x else '#1f77b4') # Rot für Muenster, Blau für andere Städte

#  Korrelations-Heatmap
print(f"  Korrelations-Heatmap...")
fig, ax = plt.subplots(figsize=(10, 8))
corr_data = stadt_agg[['Sozialindex_Avg', 'Einkommen_Avg', 'Einwohnerzahl', 
                        'Bildungsausgaben_Avg', 'Betreuungsrelation_Avg']].corr() # Korrelationen berechnen
sns.heatmap(corr_data, annot=True, cmap='coolwarm', center=0, ax=ax, cbar_kws={'label': 'Korrelation'}) # Heatmap erstellen
ax.set_title('Korrelationen zwischen NRW Bildungsindikatoren', fontsize=14, fontweight='bold') # Titel setzen
plt.tight_layout() # Layout anpassen
plt.savefig(os.path.join(output_dir, 'viz_01_korrelation_heatmap.png'), dpi=300, bbox_inches='tight') # Speichern der Abbildung
plt.close() # Schließe die Abbildung
print(f"      [OK] Gespeichert: viz_01_korrelation_heatmap.png")

#  Einkommen vs. Sozialindex
print(f"   Sozialindex vs. Einkommen...")
fig, ax = plt.subplots(figsize=(10, 6)) # Figur und Achse erstellen
ax.scatter(stadt_agg['Einkommen_Avg'], stadt_agg['Sozialindex_Avg'],  # Scatterplot
          s=100, c=colors_muenster, alpha=0.6, edgecolors='black') # Punkte zeichnen
# Highlight Muenster with a distinct color
if not muenster_row.empty: # Sicherstellen, dass Muenster existiert
    ax.scatter(muenster_stats['Einkommen_Avg'], muenster_stats['Sozialindex_Avg'], # Muenster hervorheben
              s=280, c='#ff1493', marker='o', edgecolors='darkred', linewidths=2, # Marker-Eigenschaften
              label='Muenster (Referenz)', zorder=5) # Label und zorder setzen
ax.set_xlabel('Durchschnitt Einkommen pro Einwohner (EUR)', fontsize=11) # X-Achsenbeschriftung
ax.set_ylabel('Durchschnitt Sozialindex', fontsize=11) # Y-Achsenbeschriftung
ax.set_title('Einkommen vs. Sozialindex in NRW Staedten', fontsize=12, fontweight='bold') # Titel setzen
ax.legend() # Legende anzeigen
ax.grid(True, alpha=0.3) # Gitterlinien
plt.tight_layout() # Layout anpassen
plt.savefig('viz_02_einkommen_sozialindex.png', dpi=300, bbox_inches='tight') # Speichern der Abbildung
plt.close() # Schließe die Abbildung
print(f"      [OK] Gespeichert: viz_02_einkommen_sozialindex.png")

# Sozialindex vs. Betreuungsrelation
print(f"    Sozialindex vs. Betreuungsrelation...")
fig, ax = plt.subplots(figsize=(10, 6)) # Figur und Achse erstellen
ax.scatter(stadt_agg['Sozialindex_Avg'], stadt_agg['Betreuungsrelation_Avg'],  # Scatterplot
          s=100, c=colors_muenster, alpha=0.6, edgecolors='black') # Punkte zeichnen
# Highlight Muenster mit klarer Farbe 
if not muenster_row.empty: # Sicherstellen, dass Muenster existiert
    ax.scatter(muenster_stats['Sozialindex_Avg'], muenster_stats['Betreuungsrelation_Avg'], # Muenster hervorheben
              s=280, c='#ff1493', marker='o', edgecolors='darkred', linewidths=2, # Marker-Eigenschaften
              label='Muenster (Referenz)', zorder=5) # Label und zorder setzen
    # Add label for Münster
    ax.annotate('Muenster', 
                xy=(muenster_stats['Sozialindex_Avg'], muenster_stats['Betreuungsrelation_Avg']), # Koordinaten
                xytext=(10, 10), textcoords='offset points', # Textposition
                fontsize=10, fontweight='bold', color='red', #  Textstil
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7), # Box-Eigenschaften
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='red', lw=2)) # Pfeil-Eigenschaften
ax.set_xlabel('Sozialindex', fontsize=11) # X-Achsenbeschriftung
ax.set_ylabel('Betreuungsrelation (Schueler/Lehrer)', fontsize=11) # Y-Achsenbeschriftung
ax.set_title('Sozialindex vs. Betreuungsrelation in NRW Staedten', fontsize=12, fontweight='bold') # Titel setzen
ax.legend() # Legende anzeigen
ax.grid(True, alpha=0.3)    # Gitterlinien
plt.tight_layout() # Layout anpassen
plt.savefig('viz_03_sozialindex_betreuung.png', dpi=300, bbox_inches='tight') # Speichern der Abbildung
plt.close() # Schließe die Abbildung
print(f"      [OK] Gespeichert: viz_03_sozialindex_betreuung.png")

# Top 10 nach Sozialindex (mit Münster-Label)
print(f"   Top/Bottom Stadte...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 8)) # Zwei Subplots nebeneinander
fig.suptitle('Top 10 und Bottom 10 Staedte nach Sozialindex', fontsize=14, fontweight='bold') # Gesamt-Titel

top10 = stadt_agg.nlargest(10, 'Sozialindex_Avg').reset_index(drop=True) # Top 10 Staedte
bottom10 = stadt_agg.nsmallest(10, 'Sozialindex_Avg').reset_index(drop=True) # Bottom 10 Staedte

# Stelle sicher, dass Muenster in den Balkendiagrammen erscheint
if not muenster_row.empty:
    mu_entry = muenster_row[['Stadt', 'Sozialindex_Avg', 'Ist_Muenster']].copy()
    if mu_entry['Stadt'].iloc[0] not in top10['Stadt'].values:
        top10 = pd.concat([top10, mu_entry], ignore_index=True)
    if mu_entry['Stadt'].iloc[0] not in bottom10['Stadt'].values:
        bottom10 = pd.concat([bottom10, mu_entry], ignore_index=True)

# Top 10 - mit besonderen Labels fuer Muenster
top_colors = ['#d62728' if is_m else '#2ca02c' for is_m in top10['Ist_Muenster']]
top_labels = [f"{stadt} [REFERENZ]" if is_m else stadt for stadt, is_m in zip(top10['Stadt'], top10['Ist_Muenster'])]

ax1.barh(range(len(top10)), top10['Sozialindex_Avg'].values, color=top_colors)
ax1.set_yticks(range(len(top10)))
ax1.set_yticklabels(top_labels, fontsize=9)
# Make Muenster labels bold manually
for i, (label, is_m) in enumerate(zip(ax1.get_yticklabels(), top10['Ist_Muenster'])):
    if is_m:
        label.set_fontweight('bold')
        label.set_color('red')
ax1.set_xlabel('Sozialindex', fontsize=10)
ax1.set_title('Top 10 (Best)', fontsize=11, fontweight='bold')
ax1.invert_yaxis()

# Bottom 10 - mit besonderen Labels fuer Muenster
bottom_colors = ['#d62728' if is_m else '#ff7f0e' for is_m in bottom10['Ist_Muenster']]
bottom_labels = [f"{stadt} [REFERENZ]" if is_m else stadt for stadt, is_m in zip(bottom10['Stadt'], bottom10['Ist_Muenster'])]

ax2.barh(range(len(bottom10)), bottom10['Sozialindex_Avg'].values, color=bottom_colors)
ax2.set_yticks(range(len(bottom10)))
ax2.set_yticklabels(bottom_labels, fontsize=9)
# Make Muenster labels bold manually
for i, (label, is_m) in enumerate(zip(ax2.get_yticklabels(), bottom10['Ist_Muenster'])):
    if is_m:
        label.set_fontweight('bold')
        label.set_color('red')
ax2.set_xlabel('Sozialindex', fontsize=10)
ax2.set_title('Bottom 10 (Worst)', fontsize=11, fontweight='bold')
ax2.invert_yaxis()

plt.tight_layout()
plt.savefig('viz_04_top_bottom_staedte.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"      [OK] Gespeichert: viz_04_top_bottom_staedte.png")

# Boxplot nach Stadtgroesse
print(f"    Stadtgroesse-Kategorien...")
fig, axes = plt.subplots(2, 2, figsize=(12, 10)) # 2x2 Subplots
fig.suptitle('Vergleich nach Stadtgroesse in NRW', fontsize=14, fontweight='bold')  # Gesamt-Titel

sns.boxplot(data=stadt_agg, x='Stadtgroesse', y='Sozialindex_Avg', ax=axes[0, 0])   # Boxplot Sozialindex
axes[0, 0].set_title('Sozialindex nach Stadtgroesse') # Titel setzen
axes[0, 0].set_ylabel('Sozialindex') # Y-Achsenbeschriftung
axes[0, 0].set_xlabel('') # Keine X-Achsenbeschriftung

sns.boxplot(data=stadt_agg, x='Stadtgroesse', y='Einkommen_Avg', ax=axes[0, 1])   # Boxplot Einkommen
axes[0, 1].set_title('Einkommen nach Stadtgroesse') # Titel setzen
axes[0, 1].set_ylabel('Einkommen (EUR)') # Y-Achsenbeschriftung
axes[0, 1].set_xlabel('') # Keine X-Achsenbeschriftung

sns.boxplot(data=stadt_agg, x='Stadtgroesse', y='Betreuungsrelation_Avg', ax=axes[1, 0])
axes[1, 0].set_title('Betreuungsrelation nach Stadtgroesse') # Titel setzen
axes[1, 0].set_ylabel('Schueler pro Lehrkraft') # Y-Achsenbeschriftung
axes[1, 0].set_xlabel('') # Keine X-Achsenbeschriftung

sns.boxplot(data=stadt_agg, x='Stadtgroesse', y='Bildungsausgaben_Avg', ax=axes[1, 1])
axes[1, 1].set_title('Bildungsausgaben nach Stadtgroesse') # Titel setzen
axes[1, 1].set_ylabel('Ausgaben (EUR)') # Y-Achsenbeschriftung
axes[1, 1].set_xlabel('') # Keine X-Achsenbeschriftung

plt.tight_layout() # Layout anpassen
plt.savefig('viz_05_stadtgroesse_vergleich.png', dpi=300, bbox_inches='tight') # Speichern der Abbildung
plt.close() # Schließe die Abbildung
print(f"      [OK] Gespeichert: viz_05_stadtgroesse_vergleich.png") # Ausgabe

# NRW-Karte (Sozialindex nach Kreis/Stadt)
print(f"    NRW-Karte (Sozialindex)...") 
GEO_URL = "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/master/4_kreise/4_niedrig.geo.json" # GeoJSON-Datenquelle

try:
    with urllib.request.urlopen(GEO_URL, timeout=30) as response: # Lade GeoJSON-Daten
        geojson_data = json.load(response) # JSON-Daten parsen

    nrw_features = [ # Filtere nur NRW-Kreise/Städte 
        feat for feat in geojson_data.get('features', []) # Alle Features durchlaufen
        if str(feat.get('properties', {}).get('RS', '')).startswith('05') # Nur NRW (Regierungsbezirk 05)
    ]

    # Lookup for Sozialindex per normalisiertem Namen
    stadt_lookup = stadt_agg.set_index('Stadt_norm')['Sozialindex_Avg'].to_dict() # Lookup für Sozialindex
    muenster_lookup = stadt_agg.set_index('Stadt_norm')['Ist_Muenster'].to_dict() # Lookup für Muenster

    vmin = stadt_agg['Sozialindex_Avg'].min() # Minimum Wert für Farbskala
    vmax = stadt_agg['Sozialindex_Avg'].max() # Maximum Wert für Farbskala
    cmap = plt.cm.viridis # Farbkarte
    norm = plt.Normalize(vmin=vmin, vmax=vmax) # Normalisierung für Farbskala

    fig, ax = plt.subplots(figsize=(8, 10)) # Figur und Achse erstellen

    def draw_geom(geom, color, edge='white'): 
        """""Draw geometry on the map."""
        gtype = geom.get('type') # Geometrietyp
        coords = geom.get('coordinates', []) # Koordinaten
        if gtype == 'Polygon': # Einzelnes Polygon
            poly_list = [coords] # In Liste verpacken
        elif gtype == 'MultiPolygon': # Mehrere Polygone
            poly_list = coords # Direkt verwenden
        else: 
            return
        for poly in poly_list: # Für jedes Polygon
            for ring in poly: # Für jeden Ring
                arr = np.array(ring) # In NumPy-Array umwandeln
                ax.fill(arr[:, 0], arr[:, 1], facecolor=color, edgecolor=edge, linewidth=0.5, alpha=0.9) # Polygon zeichnen

    muenster_centroid = None

    for feat in nrw_features: # Für jedes Feature in NRW
        props = feat.get('properties', {}) # Eigenschaften extrahieren
        name_raw = props.get('GEN', '') # Rohname der Stadt/Kreis
        name_norm = normalize_name(name_raw) # Normalisierter Name
        val = stadt_lookup.get(name_norm, np.nan) # Sozialindex-Wert abrufen
        is_muenster = muenster_lookup.get(name_norm, False) # Prüfen ob Muenster
        color = cmap(norm(val)) if not np.isnan(val) else '#f0f0f0'
        draw_geom(feat.get('geometry', {}), color)

        if is_muenster: # Finde Koordinaten für Muenster
            geom = feat.get('geometry', {}) # Geometrie extrahieren
            coords = geom.get('coordinates', []) # Koordinaten extrahieren
            if geom.get('type') == 'Polygon' and coords: # Einzelnes Polygon
                arr = np.array(coords[0]) # Erste Ring-Koordinaten
                muenster_centroid = (arr[:, 0].mean(), arr[:, 1].mean()) # Mittelpunkt berechnen
            elif geom.get('type') == 'MultiPolygon' and coords: # Mehrere Polygone
                arr = np.array(coords[0][0]) # Erste Polygon-Koordinaten
                muenster_centroid = (arr[:, 0].mean(), arr[:, 1].mean()) # Mittelpunkt berechnen

    # Add colorbar and formatting
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label('Durchschnitt Sozialindex')

    if muenster_centroid:
        ax.scatter(*muenster_centroid, s=80, c='#ff1493', marker='o', edgecolors='black', linewidths=1.2, zorder=5, label='Muenster')
        ax.text(muenster_centroid[0], muenster_centroid[1], 'Muenster', fontsize=9, fontweight='bold', color='black', ha='center', va='center', zorder=6)

    ax.set_title('NRW: Sozialindex nach Kreis/Stadt (Durchschnitt)', fontsize=12, fontweight='bold')
    ax.set_axis_off()
    ax.legend(loc='lower left')
    plt.tight_layout()
    plt.savefig('viz_06_nrw_karte_sozialindex.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      [OK] Gespeichert: viz_06_nrw_karte_sozialindex.png")
except Exception as e:
    print(f"      [WARNUNG] Konnte NRW-Karte nicht erstellen: {e}")

print(f"\n[6/6] Abgeschlossen!")
print("=" * 80)
print("ERFOLG! 6 Visualisierungen und CSV-Daten erstellt")
print("=" * 80)
print("\nErstellt:")
print("   1. viz_01_korrelation_heatmap.png")
print("   2. viz_02_einkommen_sozialindex.png")
print("   3. viz_03_sozialindex_betreuung.png")
print("   4. viz_04_top_bottom_staedte.png")
print("   5. viz_05_stadtgroesse_vergleich.png")
print("   6. viz_06_nrw_karte_sozialindex.png")
print("   * stadt_aggregiert.csv - Aggregierte Daten mit Muenster-Markierung\n")
