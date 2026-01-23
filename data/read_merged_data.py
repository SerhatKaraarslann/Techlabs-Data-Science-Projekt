import pandas as pd
import os

# Arbeitsverzeichnis auf das Skript-Verzeichnis setzen
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------
# Einlesen der zusammengeführten Schuldaten
# ---------------------------------------------------------
print("Lade merged_schuldaten_final.csv...")
df = pd.read_csv('merged_schuldaten_final.csv', sep=';', decimal=',', encoding='utf-8-sig')

# ---------------------------------------------------------
# Übersicht über die Daten
# ---------------------------------------------------------
print("\n" + "="*60)
print("DATENÜBERSICHT")
print("="*60)
print(f"Anzahl Schulen: {len(df)}")
print(f"Anzahl Spalten: {len(df.columns)}")
print(f"\nSpalten: {', '.join(df.columns.tolist())}")

# ---------------------------------------------------------
# Erste Zeilen anzeigen
# ---------------------------------------------------------
print("\n" + "="*60)
print("ERSTE 10 ZEILEN")
print("="*60)
print(df.head(10).to_string())

# ---------------------------------------------------------
# Datenqualität prüfen
# ---------------------------------------------------------
print("\n" + "="*60)
print("DATENQUALITÄT")
print("="*60)
print("\nFehlende Werte pro Spalte:")
print(df.isnull().sum())

print("\nDatentypen:")
print(df.dtypes)

# ---------------------------------------------------------
# Statistische Zusammenfassung
# ---------------------------------------------------------
print("\n" + "="*60)
print("STATISTISCHE ZUSAMMENFASSUNG")
print("="*60)
print(df.describe())

# ---------------------------------------------------------
# Verteilung nach Schulformen
# ---------------------------------------------------------
print("\n" + "="*60)
print("VERTEILUNG NACH SCHULFORMEN")
print("="*60)
schulform_counts = df['Schulform'].value_counts()
print(schulform_counts)

# ---------------------------------------------------------
# Verteilung nach Sozialindex
# ---------------------------------------------------------
print("\n" + "="*60)
print("VERTEILUNG NACH SOZIALINDEX")
print("="*60)
sozialindex_counts = df['Sozialindex_Stufe'].value_counts().sort_index()
print(sozialindex_counts)

# ---------------------------------------------------------
# Durchschnittswerte nach Schulform
# ---------------------------------------------------------
print("\n" + "="*60)
print("DURCHSCHNITTSWERTE NACH SCHULFORM")
print("="*60)
gruppiert = df.groupby('Schulform')[['Sozialindex', 'Einkommen_Pro_Einwohner_Euro', 'Schueler_Pro_Lehrkraft']].mean()
print(gruppiert.round(2))

# ---------------------------------------------------------
# Korrelationen berechnen
# ---------------------------------------------------------
print("\n" + "="*60)
print("KORRELATIONEN")
print("="*60)
numerische_spalten = ['Sozialindex', 'Einkommen_Pro_Einwohner_Euro', 'Schueler_Pro_Lehrkraft']
korrelation = df[numerische_spalten].corr()
print(korrelation.round(3))

# ---------------------------------------------------------
# Beispiel: Filterung und Analyse
# ---------------------------------------------------------
print("\n" + "="*60)
print("BEISPIEL: GYMNASIEN MIT NIEDRIGEM SOZIALINDEX")
print("="*60)
gymnasien_niedrig = df[(df['Schulform'] == 'Gymnasien') & (df['Sozialindex'] <= 3)]
print(f"\nAnzahl: {len(gymnasien_niedrig)}")
if len(gymnasien_niedrig) > 0:
    print("\nBeispiele:")
    print(gymnasien_niedrig[['Schulname', 'Gemeinde', 'Sozialindex_Stufe', 'Einkommen_Pro_Einwohner_Euro']].head(5).to_string())

# ---------------------------------------------------------
# Speichern von gefilterten Daten (optional)
# ---------------------------------------------------------
# Beispiel: Alle Gymnasien in eine separate Datei speichern
# gymnasien = df[df['Schulform'] == 'Gymnasien']
# gymnasien.to_csv('nur_gymnasien.csv', index=False, sep=';', decimal=',', encoding='utf-8-sig')
# print("\nGymnasien wurden in 'nur_gymnasien.csv' gespeichert.")

print("\n" + "="*60)
print("FERTIG!")
print("="*60)
