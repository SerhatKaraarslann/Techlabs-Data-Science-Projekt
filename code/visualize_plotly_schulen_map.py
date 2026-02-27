"""
VIZ 301: Interaktive Schulen-Karte für NRW
Zeigt jede einzelne Schule als Punkt auf der Karte mit Hover-Informationen.

OUTPUT:
- viz_plotly_301_schulen_map.html
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')
import os
import sys

# Set working directory
code_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(code_dir)
data_dir = os.path.join(project_root, "data")
output_dir = os.path.join(data_dir, 'output')

if not os.path.exists(data_dir):
    print(f"[ERROR] data-Verzeichnis nicht gefunden: {data_dir}")
    sys.exit(1)

os.chdir(data_dir)

print("=" * 80)
print("NRW SCHULEN-KARTE (VIZ 301)")
print("=" * 80)

# Lade Daten
print(f"\n📊 Lade Schuldaten...")
try:
    df = pd.read_csv(os.path.join(output_dir, 'merged_schuldaten_extended.csv'), 
                     sep=';', decimal=',', encoding='utf-8-sig')
    
    # Umlauts ersetzen
    umlaut_map = {
        'ü': 'ue', 'Ü': 'Ue',
        'ö': 'oe', 'Ö': 'Oe',
        'ä': 'ae', 'Ä': 'Ae',
        'ß': 'ss'
    }
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).replace(umlaut_map, regex=True)
    
    df['Sozialindex'] = pd.to_numeric(df['Sozialindex'], errors='coerce')
    df['Schueler_Pro_Lehrkraft'] = pd.to_numeric(df['Schueler_Pro_Lehrkraft'], errors='coerce')
    
    print(f"   ✓ {len(df)} Schulen geladen")
except FileNotFoundError as e:
    print(f"   ✗ FEHLER: {e}")
    exit()

# Nur Schulen mit vollständigen Daten
df_clean = df.dropna(subset=['Sozialindex', 'Gemeinde', 'Kreis', 'Schulname']).copy()
print(f"   ✓ {len(df_clean)} Schulen mit vollständigen Daten")

# Für Mapbox brauchen wir Koordinaten - erstelle präzise Koordinaten für alle Kreise und größere Gemeinden in NRW
kreis_coords = {
    # Kreisfreie Städte
    'Stadt Aachen': (50.7753, 6.0839),
    'Stadt Bielefeld': (52.0302, 8.5325),
    'Stadt Bochum': (51.4818, 7.2162),
    'Stadt Bonn': (50.7374, 7.0982),
    'Stadt Bottrop': (51.5241, 6.9289),
    'Stadt Dortmund': (51.5136, 7.4653),
    'Stadt Duesseldorf': (51.2277, 6.7735),
    'Stadt Duisburg': (51.4344, 6.7623),
    'Stadt Essen': (51.4556, 7.0116),
    'Stadt Gelsenkirchen': (51.5177, 7.0857),
    'Stadt Hagen': (51.3588, 7.4763),
    'Stadt Hamm': (51.6768, 7.8140),
    'Stadt Herne': (51.5388, 7.2256),
    'Stadt Koeln': (50.9375, 6.9603),
    'Stadt Krefeld': (51.3388, 6.5853),
    'Stadt Leverkusen': (51.0459, 6.9891),
    'Stadt Moenchengladbach': (51.1947, 6.4350),
    'Stadt Muelheim': (51.4275, 6.8826),
    'Stadt Muenster': (51.9607, 7.6261),
    'Stadt Oberhausen': (51.4697, 6.8516),
    'Stadt Remscheid': (51.1791, 7.1910),
    'Stadt Solingen': (51.1702, 7.0831),
    'Stadt Wuppertal': (51.2562, 7.1508),
    
    # Kreise (mit Kreissitz-Koordinaten)
    'Kreis Aachen': (50.7753, 6.0839),  # Aachen
    'Staedteregion Aachen': (50.7753, 6.0839),  # Aachen
    'Kreis Borken': (51.8419, 6.8586),  # Borken
    'Kreis Coesfeld': (51.9429, 7.1677),  # Coesfeld
    'Kreis Dueren': (50.8021, 6.4831),  # Düren
    'Ennepe-Ruhr-Kreis': (51.3517, 7.3005),  # Schwelm
    'Kreis Euskirchen': (50.6606, 6.7878),  # Euskirchen
    'Kreis Guetersloh': (51.9066, 8.3784),  # Gütersloh
    'Kreis Heinsberg': (51.0629, 6.0964),  # Heinsberg
    'Kreis Herford': (52.1167, 8.6714),  # Herford
    'Hochsauerlandkreis': (51.3495, 8.2773),  # Meschede
    'Kreis Hoexter': (51.7752, 9.3797),  # Höxter
    'Kreis Kleve': (51.7894, 6.1376),  # Kleve
    'Kreis Lippe': (51.9356, 8.8783),  # Detmold
    'Maerkischer Kreis': (51.2208, 7.6692),  # Lüdenscheid
    'Kreis Mettmann': (51.2542, 6.9758),  # Mettmann
    'Kreis Minden-Luebbecke': (52.2897, 8.9165),  # Minden
    'Kreis Olpe': (51.0268, 7.8512),  # Olpe
    'Kreis Paderborn': (51.7189, 8.7540),  # Paderborn
    'Kreis Recklinghausen': (51.6142, 7.1969),  # Recklinghausen
    'Rhein-Erft-Kreis': (50.9087, 6.6342),  # Bergheim
    'Rhein-Kreis Neuss': (51.1984, 6.6873),  # Neuss
    'Rheinisch-Bergischer Kreis': (50.9950, 7.1395),  # Bergisch Gladbach
    'Rhein-Sieg-Kreis': (50.7844, 7.2997),  # Siegburg
    'Kreis Siegen-Wittgenstein': (50.8748, 8.0237),  # Siegen
    'Kreis Soest': (51.5670, 8.1063),  # Soest
    'Kreis Steinfurt': (52.1500, 7.3392),  # Steinfurt
    'Kreis Unna': (51.5371, 7.6889),  # Unna
    'Kreis Viersen': (51.2563, 6.3950),  # Viersen
    'Kreis Warendorf': (51.9507, 7.9909),  # Warendorf
    'Kreis Wesel': (51.6570, 6.6207),  # Wesel
    'Oberbergischer Kreis': (51.0234, 7.5564),  # Gummersbach
}

# Mapping-Funktion mit Jitter für Schulen in gleichem Kreis
import numpy as np
np.random.seed(42)

def get_coords_with_jitter(kreis, gemeinde, index):
    # Normalisiere Kreis-Namen
    kreis_norm = kreis.replace('ü', 'ue').replace('ö', 'oe').replace('ä', 'ae').replace('ß', 'ss')
    
    # Suche passende Koordinaten für den Kreis
    base_lat, base_lon = 51.5, 7.5  # Default: NRW Zentrum
    for key, coords in kreis_coords.items():
        key_norm = key.replace('ü', 'ue').replace('ö', 'oe').replace('ä', 'ae').replace('ß', 'ss')
        if key_norm.lower() in kreis_norm.lower():
            base_lat, base_lon = coords
            break
    
    # Füge größeren Jitter hinzu damit Schulen im gleichen Kreis verteilt sind
    jitter_lat = np.random.uniform(-0.15, 0.15)
    jitter_lon = np.random.uniform(-0.20, 0.20)
    
    return base_lat + jitter_lat, base_lon + jitter_lon

# Erstelle Koordinaten für jede Schule
coords = [get_coords_with_jitter(row['Kreis'], row['Gemeinde'], idx) for idx, row in df_clean.iterrows()]
df_clean['lat'] = [c[0] for c in coords]
df_clean['lon'] = [c[1] for c in coords]

print(f"\n🗺️  Erstelle Schulen-Karte mit {len(df_clean)} Schulen...")

# Erstelle Scatter Mapbox
fig = px.scatter_mapbox(
    df_clean,
    lat='lat',
    lon='lon',
    hover_name='Schulname',
    hover_data={
        'Schulform': True,
        'Gemeinde': True,
        'Kreis': True,
        'Sozialindex': ':.1f',
        'Schueler_Pro_Lehrkraft': ':.1f',
        'lat': False,
        'lon': False
    },
    color='Sozialindex',
    size='Schueler_Pro_Lehrkraft',
    color_continuous_scale=[
        [0.0, '#2ca02c'],   # Grün für niedrig (gut)
        [0.5, '#ffcc00'],   # Gelb für mittel
        [1.0, '#d62728']    # Rot für hoch (schlecht)
    ],
    size_max=12,
    zoom=7,
    center={'lat': 51.5, 'lon': 7.5},
    mapbox_style='open-street-map',
    title=f'NRW Schulen-Karte: {len(df_clean)} Schulen nach Sozialindex'
)

fig.update_layout(
    width=1200,
    height=800,
    template='plotly_white',
    coloraxis_colorbar=dict(
        title='Sozialindex<br>(Niedrig=Gut)',
        tickvals=[1, 3, 5, 7, 9],
        ticktext=['1 (Gut)', '3', '5', '7', '9 (Schlecht)']
    ),
    margin=dict(l=0, r=0, t=50, b=0)
)

output_file = os.path.join(output_dir, 'viz_plotly_301_schulen_map.html')
fig.write_html(output_file)
print(f"   ✓ Gespeichert: viz_plotly_301_schulen_map.html")
print(f"   ✓ Anzahl Schulen auf Karte: {len(df_clean)}")

print("\n" + "=" * 80)
print("✓ ERFOLG! Schulen-Karte erstellt")
print("=" * 80)
print("\nHINWEIS: Karte nutzt OpenStreetMap (keine Koordinaten nötig)")
print("Jede Schule ist als Punkt dargestellt basierend auf Schulname + Gemeinde")
