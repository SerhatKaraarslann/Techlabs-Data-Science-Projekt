"""
Überprüfe wie viele Schulen aus merged_schuldaten_extended.csv 
in der OGC API gefunden wurden.
"""

import pandas as pd

# Lade beide Dateien
merged = pd.read_csv('data/output/merged_schuldaten_extended.csv', sep=';')
ogc = pd.read_csv('data/output/schulen_adressen_ogc_cache.csv')

print("=" * 80)
print("COVERAGE ANALYSE")
print("=" * 80)

print(f"\n Datensätze:")
print(f" Merged Schuldaten:  {len(merged):,} Schulen (mit Sozialindex)")
print(f" OGC API:            {len(ogc):,} Schulen (alle NRW Schulen)")

# Erstelle Set der Schulnummern
merged_ids = set(merged['Schulnummer'].dropna().astype(int))
ogc_ids = set(ogc['Schulnummer'].dropna().astype(int))

# Finde Überschneidung
gefunden = merged_ids & ogc_ids # Schulen, die in beiden Dateien vorkommen
nicht_gefunden = merged_ids - ogc_ids # Schulen, die in merged sind, aber nicht in OGC
nur_in_ogc = ogc_ids - merged_ids # Schulen, die in OGC sind, aber nicht in merged (z.B. ohne Sozialindex)

print(f"\n Coverage:")
print(f"  • Schulen in beiden Dateien:  {len(gefunden):,} / {len(merged_ids):,} ({len(gefunden)/len(merged_ids)*100:.1f}%)")
print(f"  • Nicht in OGC gefunden:      {len(nicht_gefunden):,}")
print(f"  • Nur in OGC (nicht in Merged): {len(nur_in_ogc):,}")

if nicht_gefunden:
    print(f"\nNICHT GEFUNDEN in OGC API ({len(nicht_gefunden)} Schulen):")
    for schulnr in sorted(list(nicht_gefunden))[:20]:
        schule = merged[merged['Schulnummer'] == schulnr].iloc[0]
        print(f"  • {schulnr:6d} | {schule['Schulname'][:60]:<60} | {schule['Gemeinde']}")
    if len(nicht_gefunden) > 20:
        print(f"  ... und {len(nicht_gefunden)-20} weitere")

print("\n" + "=" * 80)
print("FAZIT:")
print("=" * 80)

if len(gefunden) == len(merged_ids): # Alle Schulen gefunden
    print("PERFEKT! Alle Schulen haben echte GPS-Koordinaten von OGC API!")
elif len(gefunden) / len(merged_ids) >= 0.95: # 95% oder mehr gefunden
    print(f"SEHR GUT! {len(gefunden)/len(merged_ids)*100:.1f}% haben echte Koordinaten.")
    print(f"   {len(nicht_gefunden)} Schulen nutzen Gemeinde-Fallback.")
else: # Weniger als 95% gefunden
    print(f"{len(gefunden)/len(merged_ids)*100:.1f}% haben echte Koordinaten.")
    print(f"   {len(nicht_gefunden)} Schulen nutzen Gemeinde-Fallback.")

print("=" * 80)
