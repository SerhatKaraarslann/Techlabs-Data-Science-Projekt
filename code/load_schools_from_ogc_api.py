"""
Lade echte Schuladressen vom OGC API (NRW Ministerium für Schule und Bildung).
Deutlich schneller als Nominatim und offiziell aktualisiert.

API: https://ogc-api.nrw.de/inspire-us-schule/v1/api
Daten: Schulnummer, Schulname, Adresse, Gemeinde, Kreis, lat, lon (aktuell, täglich aktualisiert)
"""

import requests
import pandas as pd
import json
import os
from urllib.parse import quote

# Konfiguration und Konstanten
OGC_API_URL = "https://ogc-api.nrw.de/inspire-us-schule/v1/collections/governmentalservice/items"
OUTPUT_CACHE = 'data/output/schulen_adressen_ogc_cache.csv' 
BATCH_SIZE = 100  # Anzahl Schulen pro API-Anfrage (OGC API unterstützt Pagination)

def fetch_ogc_schools():
    """
    Lade alle Schulen von der OGC API (mit Pagination).
    Gibt DataFrame mit: schulnummer, schulname, adresse, gemeinde, kreis, lat, lon
    """
    
    all_features = [] # Alle Schulen sammeln
    skipped = 0 # Zähler für übersprungene Schulen (z.B. ohne Koordinaten)
    
    print("=" * 80)
    print("📡 SCHULADRESSEN VON OGC API (NRW Ministerium)")
    print("=" * 80)
    print(f"\nAPI: {OGC_API_URL}\n")
    
    offset = 0 # Pagination-Offset, startet bei 0 und erhöht sich um BATCH_SIZE pro Seite
    page = 0 # Seitennummer für Logging (startet bei 1)
    
    while True: # Endlosschleife, bis keine weiteren Schulen mehr gefunden werden
        page += 1 # Seitennummer erhöhen
        print(f"[Seite {page}] Lade Schulen (offset={offset})...")
        
        try: # API-Anfrage mit Pagination
            params = {
                'f': 'json',
                'limit': BATCH_SIZE,
                'offset': offset
            }
            
            response = requests.get(OGC_API_URL, params=params, timeout=30) # Timeout von 30 Sekunden pro Anfrage
            response.raise_for_status() # HTTP-Fehler werfen eine Ausnahme
            
            data = response.json() # JSON-Antwort parsen
            features = data.get('features', []) # Liste der Schulen auf dieser Seite
            
            if not features: # Keine Schulen mehr gefunden, Schleife beenden
                print(f"Keine weiteren Schulen gefunden (Gesamtseiten: {page-1})")
                break
            
            print(f"{len(features)} Schulen auf dieser Seite")
            
            # Parse Features
            for feature in features:
                try:
                    props = feature.get('properties', {}) # Eigenschaften der Schule
                    geometry = feature.get('geometry', {}) # Geometrie mit Koordinaten
                    coords = geometry.get('coordinates', [None, None]) # OGC API gibt GeoJSON-Standard: [lon, lat]
                    
                    schulnummer = feature.get('id')  # ID ist Schulnummer
                    schulname = props.get('shortName', props.get('name', '')) # Kurzname oder Name der Schule
                    schulform = props.get('schulform', '') # Schulform (z.B. Grundschule, Gesamtschule, etc.)
                    
                    # Adresse zusammenbauen
                    adresse_parts = [] # Straße + Hausnummer
                    thoroughfare = props.get('pointOfContact.address.thoroughfare') # Straße + Hausnummer (wenn vorhanden)
                    locator = props.get('pointOfContact.address.locatorDesignator') # Hausnummer (wenn separat vorhanden)
                    if thoroughfare: # Straße + Hausnummer ist vorhanden
                        adresse_parts.append(thoroughfare) # Straße + Hausnummer
                    if locator: # Hausnummer separat vorhanden
                        adresse_parts.append(locator) # Hausnummer hinzufügen (falls nicht schon in thoroughfare enthalten)
                    adresse = ', '.join(adresse_parts) if adresse_parts else '' # Adresse zusammenbauen
                    
                    gemeinde = props.get('pointOfContact.address.adminUnit', '') # Gemeinde (z.B. Stadt oder Gemeinde)
                    plz = props.get('pointOfContact.address.postCode', '') # Postleitzahl
                    
                    # Kreis von Schulnummer/Name extrahieren (nicht in API enthalten)
                    kreis = ''
                    
                    # OGC gibt lon, lat (GeoJSON standard)
                    lon = coords[0] if len(coords) > 0 else None # Längengrad (lon) ist erstes Element
                    lat = coords[1] if len(coords) > 1 else None # Breitengrad (lat) ist zweites Element
                    
                    # Nur hinzufügen wenn gültig
                    if schulnummer and lat and lon: # Nur Schulen mit gültiger Schulnummer und Koordinaten hinzufügen
                        all_features.append({ 
                            'Schulnummer': int(schulnummer),
                            'Schulname': schulname,
                            'Schulform': schulform,
                            'Adresse': adresse,
                            'PLZ': plz,
                            'Gemeinde': gemeinde,
                            'lat': float(lat),
                            'lon': float(lon),
                            'source': 'ogc-api-nrw'
                        })
                    else:
                        skipped += 1
                
                except Exception as e:
                    print(f"Feature-Fehler: {e}")
                    skipped += 1
            
            offset += BATCH_SIZE
            
        except requests.exceptions.RequestException as e:
            print(f"API-Fehler: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"JSON-Parse-Fehler: {e}")
            break
    
    print(f"\n {len(all_features)} Schulen erfolgreich geparsed")
    if skipped > 0:
        print(f"{skipped} Schulen übersprungen (unvollständige Daten)")
    
    return pd.DataFrame(all_features)

def main():
    print("\n Lade Schulen von OGC API...")
    df_ogc = fetch_ogc_schools() # Alle Schulen von OGC API laden (mit Pagination)
    
    if df_ogc.empty: # Keine Schulen geladen, API möglicherweise nicht erreichbar
        print("\n Keine Schulen geladen! API möglicherweise nicht erreichbar.")
        return
    
    # Speichere Cache
    print(f"\n Speichere Cache...")
    df_ogc.to_csv(OUTPUT_CACHE, index=False) # Cache mit echten Adressen und Koordinaten speichern
    print(f"Cache gespeichert: {OUTPUT_CACHE}")
    
    # Statistik
    print("\n" + "=" * 80)
    print("STATISTIK - OGC API")
    print("=" * 80)
    print(f"  Gesamt Schulen:           {len(df_ogc)}")
    print(f"  Mit Adressen:             {df_ogc['Adresse'].notna().sum()}")
    print(f"  Mit Koordinaten:          {(df_ogc['lat'].notna() & df_ogc['lon'].notna()).sum()}")
    
    # Top 5 Schulen zeigen
    print(f"\n BEISPIELE (erste 5 Schulen):")
    print("=" * 80)
    for idx, row in df_ogc.head(5).iterrows():
        print(f"\n  Schulnr:  {row['Schulnummer']}")
        print(f"  Name:     {row['Schulname']}")
        print(f"  Schulform:{row['Schulform']}")
        print(f"  Adresse:  {row['Adresse']}")
        print(f"  PLZ:      {row['PLZ']}")
        print(f"  Gemeinde: {row['Gemeinde']}")
        print(f"  GPS:      {row['lat']:.6f}, {row['lon']:.6f}")
    
    print("\n" + "=" * 80)
    print("FERTIG!")
    print("=" * 80)
    print(f"\nNächste Schritte:")
    print(f"  1. Überprüfe: {OUTPUT_CACHE}")
    print(f"  2. Merge mit merged_schuldaten_extended.csv")
    print(f"  3. Starte: streamlit run streamlit_app.py")
    print(f"\nBranch: feature/geocode-schools-addresses")
    print("=" * 80)

if __name__ == '__main__':
    main()
