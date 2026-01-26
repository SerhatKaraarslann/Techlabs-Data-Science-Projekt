""""
Erweiterte interaktive NRW-Karte mit:
- Einzelne Schulmarker (geocoded)
- Schulform-Filter
- Top/Bottom Schulen pro Kreis
- Umfassende Popup-Infos (Adresse, Sozialindex, Betreuung, etc.)
- Einkommen-Overlay per Kreis
- Münster-Highlight

Ergebnis: viz_07_nrw_karte_advanced_folium.html
"""
import json
import os
import sys
import unicodedata
import urllib.request

import folium
from folium import plugins
import numpy as np
import pandas as pd

# Set working directory to data folder
code_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(code_dir)
data_dir = os.path.join(project_root, "data")

if not os.path.exists(data_dir):
    print(f"[ERROR] data-Verzeichnis nicht gefunden: {data_dir}")
    sys.exit(1)

os.chdir(data_dir)

DATA_FILE = os.path.join(data_dir, 'output', 'merged_schuldaten_extended.csv') 
OUTPUT_HTML = os.path.join(data_dir, 'output', 'viz_07_nrw_karte_advanced_folium.html')
CACHE_FILE = os.path.join(data_dir, 'output', 'gemeinde_geocode_cache.csv')


def normalize_name(name):
    """Normalize German Kreisnamen."""
    if name is None:
        return ''
    txt = unicodedata.normalize('NFKD', str(name)) # Normalisiere Unicode
    txt = ''.join(ch for ch in txt if not unicodedata.combining(ch)) # Entferne Akzente
    txt = txt.replace('kreisfreie stadt', '').replace('stadt', '').replace('-kreis', '').replace('kreis', '') # Entferne unnötige Wörter
    txt = txt.replace('stadtregion', '').replace('stdteregion', '').replace('städteregion', '') # Entferne weitere Wörter
    txt = ''.join(ch for ch in txt if ch.isalnum() or ch.isspace() or ch == '-') # Behalte nur alphanumerische Zeichen, Leerzeichen und Bindestriche
    return ' '.join(txt.lower().split()) # Kleinbuchstaben und überflüssige Leerzeichen entfernen


def get_kreis_coordinates():
    """Get approximate coordinates for NRW Kreise."""
    return {
        'ennepe-ruhr': [51.35, 7.0],
        'hochsauerlandkreis': [51.3, 8.2],
        'borken': [51.85, 6.75],
        'coesfeld': [51.85, 7.17],
        'dren': [50.8, 6.5],
        'euskirchen': [50.65, 6.72],
        'gtersloh': [52.05, 8.35],
        'heinsberg': [51.15, 6.0],
        'herford': [52.1, 8.68],
        'hxter': [51.75, 9.35],
        'kleve': [51.8, 6.3],
        'lippe': [52.0, 8.75],
        'mettmann': [51.25, 7.2],
        'minden-lbbecke': [52.3, 8.9],
        'olpe': [51.0, 7.88],
        'paderborn': [51.6, 8.75],
        'recklinghausen': [51.6, 7.25],
        'siegen-wittgenstein': [50.88, 8.25],
        'soest': [51.55, 8.1],
        'steinfurt': [52.15, 7.75],
        'unna': [51.65, 7.68],
        'viersen': [51.3, 6.38],
        'warendorf': [52.0, 7.7],
        'wesel': [51.65, 6.6],
        'wittgenstein': [50.88, 8.25],
        'aachen': [50.78, 6.08],
        'bielefeld': [52.02, 8.5],
        'bochum': [51.45, 7.22],
        'bonn': [50.73, 7.1],
        'bottrop': [51.52, 7.13],
        'cologne': [50.94, 6.96],
        'dortmund': [51.52, 7.45],
        'dsseldorf': [51.23, 6.78],
        'duisburg': [51.43, 6.77],
        'essen': [51.45, 7.01],
        'gelsenkirchen': [51.5, 7.08],
        'hagen': [51.35, 7.45],
        'hamm': [51.68, 7.82],
        'herne': [51.54, 7.23],
        'iserlohn': [51.38, 7.70],
        'krefeld': [51.35, 6.57],
        'leverkusen': [51.03, 7.0],
        'mnchen-gladbach': [51.15, 6.42],
        'munchengladbach': [51.15, 6.42],
        'mnster': [51.96, 7.63],
        'munster': [51.96, 7.63],
        'oberhausen': [51.46, 6.85],
        'remscheid': [51.18, 7.2],
        'rheine': [52.28, 7.45],
        'solingen': [51.17, 7.08],
        'wuppertal': [51.27, 7.18],
        'wupperthal': [51.27, 7.18],
        'stdteregion aachen': [50.78, 6.08],
        'rhein-erft': [50.9, 6.75],
        'rheinisch-bergischer': [51.0, 7.15],
        'rhein-sieg': [50.78, 7.3],
        'oberbergischer': [51.0, 7.55],
        'mrkischer': [51.25, 7.55],
    }


def load_data():
    """Load and prepare school data."""
    df = pd.read_csv(DATA_FILE, sep=';', decimal=',', encoding='utf-8-sig') # Lade Schuldaten
    df['Sozialindex'] = pd.to_numeric(df['Sozialindex'], errors='coerce') # Konvertiere Sozialindex zu numerisch
    df['Schueler_Pro_Lehrkraft'] = pd.to_numeric(df['Schueler_Pro_Lehrkraft'], errors='coerce') # Konvertiere Betreuung zu numerisch
    df['Einkommen_Pro_Einwohner_Euro'] = pd.to_numeric(df['Einkommen_Pro_Einwohner_Euro'], errors='coerce') # Konvertiere Einkommen zu numerisch
    
    # Extract address from school name (format: "City, SchoolType StreetName")
    df['Adresse'] = df['Schulname'] + ', ' + df['Gemeinde'] + ', NRW, Germany' # Vollständige Adresse für Geocoding
    df['NAME_NORM'] = df['Kreis'].apply(normalize_name) # Normalisierte Kreisnamen
    df['Ist_Muenster'] = df['Kreis'].str.contains('nster', case=False, na=False) | df['Kreis'].str.contains('munster', case=False, na=False) # Markiere Münster
    
    return df


def get_gemeinde_coordinates():
    """Fast: Pre-calculated Gemeinde coordinates (no API calls needed)."""
    return {
        'Haan': [51.22, 7.08], 'Leverkusen': [51.03, 7.0], 'Herne': [51.54, 7.23],
        'Dsseldorf': [51.23, 6.78], 'Stolberg (Rhld.)': [50.78, 6.08], 'Hrth': [50.94, 6.96],
        'Kleve': [51.80, 6.30], 'Tnisvorst': [51.30, 6.38], 'Medebach': [51.30, 8.20],
        'Lengerich': [52.28, 8.17], 'Gronau (Westf.)': [52.22, 7.08], 'Bad Driburg': [51.68, 8.75],
        'Essen': [51.45, 7.01], 'Oberhausen': [51.46, 6.85], 'Kleve': [51.80, 6.30],
        'Kln': [50.94, 6.96], 'Ldenscheid': [51.22, 7.60], 'Geldern': [51.50, 6.30],
        'Bielefeld': [52.02, 8.50], 'Bochum': [51.45, 7.22], 'Hamm': [51.68, 7.82],
        'Neuss': [51.40, 6.68], 'Dorsten': [51.68, 6.85], 'Wuppertal': [51.27, 7.18],
        'Wesel': [51.65, 6.60], 'Bonn': [50.73, 7.10], 'Mnster': [51.96, 7.63],
        'Monheim am Rhein': [51.08, 6.99], 'Velbert': [51.35, 7.15], 'Dinslaken': [51.55, 6.75],
        'Duisburg': [51.43, 6.77], 'Bornheim': [50.77, 6.95], 'Beckum': [51.72, 8.05],
        'Rsrath': [51.00, 7.15], 'Ahlen': [51.75, 8.08], 'Rheinberg': [51.55, 6.60],
        'Neuenrade': [51.30, 7.70], 'Morsbach': [51.00, 7.55], 'Kalletal': [52.10, 8.75],
        'Langenberg': [51.35, 7.15], 'Ascheberg': [51.85, 7.17], 'Recklinghausen': [51.60, 7.25],
        'Herscheid': [51.35, 7.70], 'Neuenkirchen': [52.15, 7.75], 'Castrop-Rauxel': [51.60, 7.25],
        'Krefeld': [51.35, 6.57], 'Swisttal': [50.80, 6.90], 'Minden': [52.30, 8.90],
        'Mettmann': [51.25, 7.20], 'Dortmund': [51.52, 7.45], 'Gelsenkirchen': [51.50, 7.08],
        'Bergheim': [50.95, 6.75], 'Witten': [51.43, 7.35], 'Kamp-Lintfort': [51.50, 6.60],
        'Grevenbroich': [51.05, 6.60], 'Wermelskirchen': [51.15, 7.18], 'Alfter': [50.78, 6.95],
        'Siegen': [50.88, 8.25], 'Grefrath': [51.38, 6.38], 'Hagen': [51.35, 7.45],
        'Moers': [51.45, 6.62], 'Bad Salzuflen': [52.07, 8.75], 'Menden (Sauerland)': [51.38, 7.70],
        'Unna': [51.65, 7.68], 'Solingen': [51.17, 7.08], 'Mnchengladbach': [51.15, 6.42],
        'Mlheim a.d.Ruhr': [51.43, 6.88], 'Remscheid': [51.18, 7.20], 'Voerde (Niederrhein)': [51.65, 6.60],
        'Hnxe': [51.68, 6.70], 'Heiligenhaus': [51.35, 7.15], 'Hilden': [51.20, 7.10],
        'Ratingen': [51.30, 7.17], 'Wlfrath': [51.33, 7.10], 'Erkrath': [51.25, 7.13],
        'Issum': [51.50, 6.35], 'Kerken': [51.50, 6.33], 'Kevelaer': [51.57, 6.27],
        'Straelen': [51.48, 6.17], 'Wachtendonk': [51.63, 6.40], 'Weeze': [51.60, 6.25],
        'Dormagen': [51.10, 6.80], 'Jchen': [51.25, 6.85], 'Kaarst': [51.33, 6.87],
        'Korschenbroich': [51.20, 6.65], 'Meerbusch': [51.27, 6.70], 'Rommerskirchen': [51.15, 6.77],
        'Brggen': [51.35, 6.45], 'Kempen': [51.35, 6.35], 'Nettetal': [51.30, 6.28],
        'Schwalmtal': [51.32, 6.25], 'Viersen': [51.30, 6.38], 'Willich': [51.32, 6.60],
        'Bedburg-Hau': [51.63, 6.37], 'Goch': [51.65, 6.15], 'Kalkar': [51.73, 6.28],
        'Kranenburg': [51.78, 6.20], 'Uedem': [51.65, 6.40], 'Xanten': [51.65, 6.45],
        'Neukirchen-Vluyn': [51.47, 6.85], 'Alpen': [51.58, 6.70], 'Sonsbeck': [51.58, 6.58],
        'Rheurdt': [51.55, 6.55], 'Emmerich am Rhein': [51.80, 6.28], 'Isselburg': [51.95, 6.73],
        'Rees': [51.75, 6.40], 'Hamminkeln': [51.75, 6.75], 'Schermbeck': [51.65, 6.78],
        'Burscheid': [51.10, 7.25], 'Hckeswagen': [51.18, 7.30], 'Langenfeld (Rhld.)': [51.12, 7.13],
        'Leichlingen (Rhld.)': [51.08, 7.20], 'Radevormwald': [51.18, 7.35], 'Kerpen': [50.87, 6.73],
        'Frechen': [50.93, 6.83], 'Bedburg': [50.93, 6.60], 'Elsdorf': [50.92, 6.63],
        'Erftstadt': [50.80, 6.78], 'Euskirchen': [50.65, 6.72], 'Bad Mnstereifel': [50.55, 6.73],
        'Weilerswist': [50.72, 6.88], 'Zlpich': [50.65, 6.60], 'Blankenheim': [50.35, 6.65],
        'Dahlem': [50.43, 6.50], 'Hellenthal': [50.45, 6.40], 'Kall': [50.50, 6.58],
        'Mechernich': [50.65, 6.60], 'Nettersheim': [50.48, 6.65], 'Schleiden': [50.50, 6.38],
        'Pulheim': [50.93, 6.87], 'Wesseling': [50.85, 6.95], 'Bergneustadt': [51.05, 7.55],
        'Bad Honnef': [50.63, 7.22], 'Hückeswagen': [51.18, 7.30], 'Waldbröl': [51.08, 7.57],
        'Gummersbach': [51.00, 7.60], 'Much': [50.82, 7.37], 'Wiehl': [51.02, 7.65],
        'Reichshof': [50.95, 7.70], 'Lindlar': [50.98, 7.45], 'Engelskirchen': [51.00, 7.35],
        'Marienheide': [51.22, 7.55], 'Eckenhagen': [51.05, 7.65], 'Nümbrecht': [50.98, 7.58],
        'Haigerseelbach': [50.70, 8.15], 'Braubach': [50.27, 7.58], 'Haiger': [50.68, 8.28],
        'Bad Laasphe': [50.92, 8.42], 'Haigerseelbach': [50.70, 8.15], 'Biedenkopf': [50.88, 8.52],
        'Marburg': [50.80, 8.77], 'Cappel': [50.82, 8.75], 'Ebsdorfergrund': [50.72, 8.68],
    }


def geocode_schools(df):
    """Use pre-calculated Gemeinde coordinates (fast, no API calls)."""
    gemeinde_coords = get_gemeinde_coordinates() # Pre-calculated Gemeinde coordinates
    kreis_coords = get_kreis_coordinates() # Kreis center coordinates
    
    print("[INFO] Using pre-calculated Gemeinde coordinates (no API calls needed)")
    
    coords_list = [] # Liste für Koordinaten
    fallback_count = 0 # Zähler für Fallbacks
     
    for _, row in df.iterrows(): # Iteriere über jede Schule
        gemeinde = row['Gemeinde'] # Gemeinde-Name
        
        # Check pre-calculated Gemeinde coordinates first
        if gemeinde in gemeinde_coords: 
            base_lat, base_lon = gemeinde_coords[gemeinde]
        else:
            # Fallback to Kreis center
            kreis_norm = normalize_name(row['Kreis'])
            if kreis_norm in kreis_coords:
                base_lat, base_lon = kreis_coords[kreis_norm]
            else:
                base_lat, base_lon = 51.5, 7.6  # NRW center
            fallback_count += 1
        
        # Add small random offset (±0.005 degrees ≈ ±500m)
        lat = base_lat + np.random.uniform(-0.005, 0.005)
        lon = base_lon + np.random.uniform(-0.005, 0.005)
        coords_list.append((lat, lon))
    
    df['latitude'] = [c[0] for c in coords_list] 
    df['longitude'] = [c[1] for c in coords_list]
    
    print(f"[OK] {len(df) - fallback_count} Gemeinden mit echten Koordinaten")
    print(f"[OK] {fallback_count} Schulen mit Kreis-Fallback")
    
    return df


def build_advanced_map(df, agg_df):
    """Build advanced folium map with multiple layers."""
    print("[INFO] Building map...")
    
    # Create base map
    m = folium.Map(
        location=[51.5, 7.6],
        zoom_start=7,
        tiles='CartoDB positron',
        max_bounds=True
    )

    # ========== COLOR SCHEMES ==========
    # Folium Icon colors are limited to specific values
    schulform_colors = {
        'gymnasium': 'red',
        'gymnasien': 'red',
        'gesamtschule': 'blue',
        'gesamtschulen': 'blue',
        'grundschule': 'green',
        'grundschulen': 'green',
        'hauptschule': 'orange',
        'hauptschulen': 'orange',
        'realschule': 'purple',
        'realschulen': 'purple',
        'sekundarschule': 'darkblue',
        'sekundarschulen': 'darkblue',
        'sonstige': 'gray'
    }

    def get_schulform_color(schulform):
        """"
        Get color for a given Schulform.
        """
        if pd.isna(schulform):
            return 'gray'
        sf_lower = schulform.lower().strip() # Normalize
        for key, color in schulform_colors.items(): # Match key
            if key in sf_lower: #   Found match
                return color
        return 'gray' # Default color
    
    def get_schulform_key(schulform):
        """"
        Get key for a given Schulform.
        """
        if pd.isna(schulform):
            return 'sonstige'
        sf_lower = schulform.lower().strip() # Normalize
        if 'gymnasium' in sf_lower or 'gymnasien' in sf_lower: 
            return 'gymnasien'
        elif 'gesamtschule' in sf_lower:
            return 'gesamtschulen'
        elif 'grundschule' in sf_lower:
            return 'grundschulen'
        elif 'hauptschule' in sf_lower:
            return 'hauptschulen'
        elif 'realschule' in sf_lower:
            return 'realschulen'
        elif 'sekundarschule' in sf_lower:
            return 'sekundarschulen'
        return 'sonstige'

    # ========== LAYER GROUPS ==========
    layer_schulform = { # Schulform layers
        'gymnasien': folium.FeatureGroup(name='🔴 Gymnasien'),
        'gesamtschulen': folium.FeatureGroup(name='🔵 Gesamtschulen'),
        'grundschulen': folium.FeatureGroup(name='🟢 Grundschulen'),
        'hauptschulen': folium.FeatureGroup(name='🟠 Hauptschulen'),
        'realschulen': folium.FeatureGroup(name='🟣 Realschulen'),
        'sekundarschulen': folium.FeatureGroup(name='🔷 Sekundarschulen'),
        'sonstige': folium.FeatureGroup(name='⚪ Sonstige')
    }

    # ========== ADD SCHOOL MARKERS ==========
    schools_with_coords = df[df['latitude'].notna() & df['longitude'].notna()] # Schulen mit Koordinaten
    
    print(f"[INFO] Adding {len(schools_with_coords)} school markers...") 
    
    for _, school in schools_with_coords.iterrows(): # Iteriere über jede Schule
        color = get_schulform_color(school['Schulform']) # Farbe basierend auf Schulform
        sf_key = get_schulform_key(school['Schulform']) # Schulform Schlüssel
        
        # Build popup content
        popup_text = f"""
        <b>{school['Schulname']}</b><br>
        <hr style="margin: 5px 0;">
        <b>Schulform:</b> {school['Schulform']}<br>
        <b>Kreis:</b> {school['Kreis']}<br>
        <b>Gemeinde:</b> {school['Gemeinde']}<br>
        <br>
        <b> Sozialindex:</b> {school['Sozialindex']:.2f}<br>
        <b> Schüler/Lehrer:</b> {school['Schueler_Pro_Lehrkraft']:.2f}<br>
        <b> Einkommen:</b> € {school['Einkommen_Pro_Einwohner_Euro']:.0f}<br>
        """
        
        if school['Ist_Muenster']:
            popup_text += "<br><b style='color:red;'> MÜNSTER (Referenzstadt)</b>"
        
        # Use CircleMarker instead of Icon for better performance
        folium.CircleMarker(
            location=[school['latitude'], school['longitude']],
            radius=3,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=school['Schulname'],
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6,
            weight=1
        ).add_to(layer_schulform[sf_key])

    # ========== ADD KREIS CIRCLES (Sozialindex) ==========
    layer_kreis = folium.FeatureGroup(name="🔵 Sozialindex pro Kreis")
    
    nrw_coords = {
        'ennepe-ruhr': [51.35, 7.0],
        'hochsauerlandkreis': [51.3, 8.2],
        'kreis borken': [51.85, 6.75],
        'kreis coesfeld': [51.85, 7.17],
        'kreis dren': [50.8, 6.5],
        'kreis euskirchen': [50.65, 6.72],
        'kreis gtersloh': [52.05, 8.35],
        'kreis heinsberg': [51.15, 6.0],
        'kreis herford': [52.1, 8.68],
        'kreis hxter': [51.75, 9.35],
        'kreis kleve': [51.8, 6.3],
        'kreis lippe': [52.0, 8.75],
        'kreis mettmann': [51.25, 7.2],
        'kreis minden-lbbecke': [52.3, 8.9],
        'kreis olpe': [51.0, 7.88],
        'kreis paderborn': [51.6, 8.75],
        'kreis recklinghausen': [51.6, 7.25],
        'kreis siegen-wittgenstein': [50.88, 8.25],
        'kreis soest': [51.55, 8.1],
        'kreis steinfurt': [52.15, 7.75],
        'kreis unna': [51.65, 7.68],
        'kreis viersen': [51.3, 6.38],
        'kreis warendorf': [52.0, 7.7],
        'kreis wesel': [51.65, 6.6],
        'kreis wittgenstein': [50.88, 8.25],
        'stadt aachen': [50.78, 6.08],
        'stadt bielefeld': [52.02, 8.5],
        'stadt bochum': [51.45, 7.22],
        'stadt bonn': [50.73, 7.1],
        'stadt bottrop': [51.52, 7.13],
        'stadt cologne': [50.94, 6.96],
        'stadt dortmund': [51.52, 7.45],
        'stadt dsseldorf': [51.23, 6.78],
        'stadt duisburg': [51.43, 6.77],
        'stadt essen': [51.45, 7.01],
        'stadt gelsenkirchen': [51.5, 7.08],
        'stadt hagen': [51.35, 7.45],
        'stadt hamm': [51.68, 7.82],
        'stadt herne': [51.54, 7.23],
        'stadt iserlohn': [51.38, 7.70],
        'stadt krefeld': [51.35, 6.57],
        'stadt leverkusen': [51.03, 7.0],
        'stadt mnchen-gladbach': [51.15, 6.42],
        'stadt munchengladbach': [51.15, 6.42],
        'stadt mnster': [51.96, 7.63],
        'stadt munster': [51.96, 7.63],
        'stadt oberhausen': [51.46, 6.85],
        'stadt remscheid': [51.18, 7.2],
        'stadt rheine': [52.28, 7.45],
        'stadt solingen': [51.17, 7.08],
        'stadt wuppertal': [51.27, 7.18],
        'stadt wupperthal': [51.27, 7.18],
        'stdteregion aachen': [50.78, 6.08],
    }

    def get_color_sozial(value, vmin, vmax):
        if value < vmin + (vmax - vmin) * 0.2:
            return '#440154'
        elif value < vmin + (vmax - vmin) * 0.4:
            return '#31688e'
        elif value < vmin + (vmax - vmin) * 0.6:
            return '#35b779'
        elif value < vmin + (vmax - vmin) * 0.8:
            return '#fde724'
        return '#fde724'

    vmin = agg_df['Sozialindex_Avg'].min()
    vmax = agg_df['Sozialindex_Avg'].max()

    for _, row in agg_df.iterrows():
        norm_name = row['NAME_NORM']
        for key, coord in nrw_coords.items():
            if key in norm_name:
                color = get_color_sozial(row['Sozialindex_Avg'], vmin, vmax)
                
                popup_text = f"""
                <b>{row['Kreis']}</b><br>
                <hr style="margin: 5px 0;">
                <b>Sozialindex:</b> {row['Sozialindex_Avg']:.2f}<br>
                <b>Schulen:</b> {int(row['Anzahl_Schulen'])}<br>
                <b>Einkommen:</b> € {row['Einkommen_Avg']:.0f}<br>
                <b>Schüler/Lehrer:</b> {row['Betreuungsrelation_Avg']:.2f}
                """
                
                if row['Ist_Muenster']:
                    popup_text += "<br><br><b style='color:red;'> MÜNSTER</b>"
                
                folium.CircleMarker(
                    location=coord,
                    radius=8,
                    color='black' if row['Ist_Muenster'] else '#666',
                    weight=2.5 if row['Ist_Muenster'] else 1,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    popup=folium.Popup(popup_text, max_width=250),
                    tooltip=row['Kreis']
                ).add_to(layer_kreis)
                break

    # ========== ADD LAYERS TO MAP ==========
    for layer in layer_schulform.values():
        m.add_child(layer)
    m.add_child(layer_kreis)

    # ========== LEGEND ==========
    legend_html = '''
    <div style="position: fixed; bottom: 50px; right: 50px; width: 280px; max-height: 500px; 
                background-color: white; border: 2px solid #333; z-index: 9999; font-size: 12px; 
                padding: 10px; border-radius: 5px; overflow-y: auto;">
        <h4 style="margin-top: 0; text-align: center; border-bottom: 2px solid #333; padding-bottom: 5px;">
            📍 NRW Schulen & Sozialindex
        </h4>
        
        <p style="margin: 8px 0; font-weight: bold;">Schulformen (Toggle Layer):</p>
        <p style="margin: 4px 0;">🔴 Gymnasien</p>
        <p style="margin: 4px 0;">🔵 Gesamtschulen</p>
        <p style="margin: 4px 0;">🟢 Grundschulen</p>
        <p style="margin: 4px 0;">🟠 Hauptschulen</p>
        <p style="margin: 4px 0;">🟣 Realschulen</p>
        <p style="margin: 4px 0;">🔷 Sekundarschulen</p>
        
        <hr style="margin: 8px 0;">
        <p style="margin: 8px 0; font-weight: bold;">Kreis-Sozialindex:</p>
        <p style="margin: 4px 0;"><span style="display:inline-block; width:12px; height:12px; background:#440154; border-radius:2px;"></span> Niedrig (2.1-3.0)</p>
        <p style="margin: 4px 0;"><span style="display:inline-block; width:12px; height:12px; background:#31688e; border-radius:2px;"></span> Mittel-Niedrig (3.0-4.0)</p>
        <p style="margin: 4px 0;"><span style="display:inline-block; width:12px; height:12px; background:#35b779; border-radius:2px;"></span> Mittel-Hoch (4.0-5.0)</p>
        <p style="margin: 4px 0;"><span style="display:inline-block; width:12px; height:12px; background:#fde724; border-radius:2px;"></span> Hoch (5.0-6.3)</p>
        
        <hr style="margin: 8px 0;">
        <p style="margin: 4px 0;"><b>⭐ Münster</b> = Referenzstadt (dicke Grenze)</p>
        <p style="margin: 4px 0; font-size: 10px; color: #666;">💡 Tipp: Layer Control oben rechts für Filter</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Layer control
    folium.LayerControl().add_to(m)

    return m


def main():
    """"Main function to execute the advanced map visualization."""
    print("=" * 70)
    print("ERWEITERTE NRW-KARTE MIT SCHULEN & SOZIALINDEX")
    print("=" * 70)
    
    # Load data
    df = load_data()
    print(f"[OK] {len(df)} Schulen geladen") 
    
    # Geocode
    df = geocode_schools(df) # Geocode Schulen
    
    # Aggregate by Kreis
    agg_df = df.groupby('Kreis').agg( # Aggregation pro Kreis
        Anzahl_Schulen=('Schulnummer', 'count'), # Anzahl Schulen
        Sozialindex_Avg=('Sozialindex', 'mean'), # Durchschnittlicher Sozialindex
        Einkommen_Avg=('Einkommen_Pro_Einwohner_Euro', 'mean'), # Durchschnittliches Einkommen
        Betreuungsrelation_Avg=('Schueler_Pro_Lehrkraft', 'mean'), # Durchschnittliche Betreuungsrelation
        Ist_Muenster=('Ist_Muenster', 'max') # Ob Münster im Kreis ist
    ).reset_index() # Reset index nach Gruppierung
    agg_df['NAME_NORM'] = agg_df['Kreis'].apply(normalize_name) # Normalisierte Kreisnamen
    
    # Build map
    m = build_advanced_map(df, agg_df) # Erstelle Karte
    m.save(OUTPUT_HTML) # Speichere Karte als HTML
    
    print(f"[OK] Karte gespeichert: {OUTPUT_HTML}") 
    print("=" * 70)


if __name__ == '__main__':
    main()
