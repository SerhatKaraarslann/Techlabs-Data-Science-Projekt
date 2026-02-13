"""
VISUALIZE PLOTLY ALL - Stadt- und Gymnasium-Ebene Visualisierungen
Erstellt 8 interaktive Plotly-Visualisierungen für Stadt- und Gymnasium-Ebene.
Diese bilden das Kernstück des Online-Dashboards.

STADT-EBENE (VIZ 100-104):
- viz_plotly_100_korrelation_heatmap.html - Korrelationen aller Indikatoren
- viz_plotly_101_einkommen_sozialindex.html - Scatterplot Einkommen vs. Sozialindex
- viz_plotly_102_sozialindex_betreuung.html - Scatterplot Sozialindex vs. Betreuung
- viz_plotly_103_top_bottom_staedte.html - Top/Bottom 10 Städte nach Sozialindex
- viz_plotly_104_stadtgroesse_vergleich.html - Boxplots nach Regionsgröße (Schulanzahl)

GYMNASIUM-EBENE (VIZ 105-107):
- viz_plotly_105_gymnasien_top_bottom.html - Top/Bottom Gymnasien-Kreise
- viz_plotly_106_gymnasien_sozialindex_betreuung.html - Gymnasium Scatterplot
- viz_plotly_107_gymnasien_schulanzahl.html - Schulanzahl pro Kreis

AUSGABE:
8 HTML-Dateien in data/output/

WICHTIGE HINWEISE:
- Nutzt Schulanzahl statt Einwohnerzahl für Stadtgröße (Einwohnerzahl-Daten fehlerhaft)
- Alle Charts sind interaktiv mit Hover, Zoom, Pan, Download-Funktion
- Münster wird in manchen Charts als Referenz hervorgehoben
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')
import os
import sys
import unicodedata

# Set working directory
code_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(code_dir)
data_dir = os.path.join(project_root, "data")

if not os.path.exists(data_dir):
    print(f"[ERROR] data-Verzeichnis nicht gefunden: {data_dir}")
    sys.exit(1)

os.chdir(data_dir)

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("NRW BILDUNGSANALYSE - ALLE PLOTLY VISUALISIERUNGEN")
print("=" * 80)

output_dir = os.path.join(data_dir, 'output')
os.makedirs(output_dir, exist_ok=True)

def normalize_name(name):
    """
    Normalize German city/county names.
    - Remove common suffixes like "Kreis", "Stadt", "Regierungsbezirk
    - Correct common encoding issues
    - Remove special characters and extra spaces
    - Convert to lowercase
    return: Normalized name, e.g. "Kreis M nster" → "munster", "D sseldorf" → "dusseldorf", "K ln" → "koln", etc.
    """

    if name is None:
        return ''
    txt = unicodedata.normalize('NFKD', str(name))
    txt = ''.join(ch for ch in txt if not unicodedata.combining(ch))
    txt = txt.replace('kreisfreie stadt', '').replace('stadt', '').replace('-kreis', '').replace('kreis', '')
    txt = ''.join(ch for ch in txt if ch.isalnum() or ch.isspace() or ch == '-')
    return ' '.join(txt.lower().split())

# Lade Daten
print(f"\n Lade Daten...")
try:
    df = pd.read_csv(os.path.join(output_dir, 'merged_schuldaten_extended.csv'), 
                     sep=';', decimal=',', encoding='utf-8-sig')
    df['Sozialindex'] = pd.to_numeric(df['Sozialindex'], errors='coerce')
    df['Schueler_Pro_Lehrkraft'] = pd.to_numeric(df['Schueler_Pro_Lehrkraft'], errors='coerce')
    print(f"   [OK] {len(df)} Schulen geladen")
except FileNotFoundError as e:
    print(f"   [FEHLER] {e}")
    exit()

# Clean Schulform
df['Schulform_Clean'] = df['Schulform'].astype(str).str.strip()

# STADT-EBENE AGGREGATION
print(f"\n Aggregiere auf Stadt-Ebene...")

stadt_agg = df.groupby('Kreis').agg({
    'Schulnummer': 'count', # Anzahl Schulen pro Stadt
    'Sozialindex': 'mean', # Durchschnitt Sozialindex pro Stadt
    'Einkommen_Pro_Einwohner_Euro': 'mean', # Durchschnitt Einkommen pro Einwohner pro Stadt
    'Einwohnerzahl': 'max',  # Nutze max statt first um sicherzustellen, dass Wert vorhanden ist
    'Bildungsausgaben_Euro': 'mean', # Durchschnitt Bildungsausgaben pro Stadt
    'Schueler_Pro_Lehrkraft': 'mean' # Durchschnitt Betreuung pro Stadt
}).reset_index()

stadt_agg.columns = ['Stadt', 'Anzahl_Schulen', 'Sozialindex_Avg', 'Einkommen_Avg', 
                     'Einwohnerzahl', 'Bildungsausgaben_Avg', 'Betreuungsrelation_Avg']

# Zeige Einwohnerzahl-Werte
print(f"\n   DEBUG - Einwohnerzahl-Statistik:")
print(f"   Min: {stadt_agg['Einwohnerzahl'].min():.0f}")
print(f"   Max: {stadt_agg['Einwohnerzahl'].max():.0f}")
print(f"   Mean: {stadt_agg['Einwohnerzahl'].mean():.0f}")
print(f"   NaN-Werte: {stadt_agg['Einwohnerzahl'].isna().sum()}")

# Einwohnerzahl ist fehlerhaft (nur 134-616) - nutze Schulanzahl stattdessen
# Kategorisiere nach Anzahl der Schulen statt Einwohnerzahl
def schulanzahl_kategorie(anzahl):
    if anzahl <= 40:
        return 'Kleine Region (1-40 Schulen)'
    elif anzahl <= 80:
        return 'Mittlere Region (41-80 Schulen)'
    elif anzahl <= 120:
        return 'Große Region (81-120 Schulen)'
    else:
        return 'Sehr große Region (>120 Schulen)'

stadt_agg['Stadtgroesse'] = stadt_agg['Anzahl_Schulen'].apply(schulanzahl_kategorie)

print(f"   Verteilung Schulanzahl-Kategorien:")
print(stadt_agg['Stadtgroesse'].value_counts())

# Markiere Münster
stadt_agg['Ist_Muenster'] = (
    stadt_agg['Stadt'].str.contains('nster', case=False, na=False) &
    stadt_agg['Stadt'].str.contains('Stadt', case=False, na=False)
)

print(f"   [OK] {len(stadt_agg)} Städte aggregiert")

# VIZ 1: Korrelations-Heatmap
print(f"\n [1/11] Erstelle: Korrelations-Heatmap...")

# Berechne Korrelationen zwischen den Indikatoren auf Stadt-Ebene
corr_data = stadt_agg[['Sozialindex_Avg', 'Einkommen_Avg', 'Einwohnerzahl', 
                        'Bildungsausgaben_Avg', 'Betreuungsrelation_Avg']].corr()

# Erstelle Heatmap mit Plotly und zeige Korrelationswerte als Text an
fig1 = go.Figure(data=go.Heatmap(
    z=corr_data.values,
    x=['Sozialindex', 'Einkommen', 'Einwohnerzahl', 'Bildungsausgaben', 'Betreuung'],
    y=['Sozialindex', 'Einkommen', 'Einwohnerzahl', 'Bildungsausgaben', 'Betreuung'],
    colorscale='RdBu',
    zmid=0,
    text=corr_data.values,
    texttemplate='%{text:.2f}',
    textfont={"size": 11},
    colorbar=dict(title='Korrelation')
))

fig1.update_layout(
    title='Korrelationen zwischen NRW Bildungsindikatoren',
    width=700,
    height=600,
    template='plotly_white'
)

fig1.write_html(os.path.join(output_dir, 'viz_plotly_100_korrelation_heatmap.html'))
print(f"   [OK] Gespeichert: viz_plotly_100_korrelation_heatmap.html")


# VIZ 2: Einkommen vs. Sozialindex
print(f"\n [2/11] Erstelle: Einkommen vs. Sozialindex...")

colors = ['#d62728' if m else '#1f77b4' for m in stadt_agg['Ist_Muenster']]

fig2 = go.Figure()

# Alle Punkte außer Münster (Referenz) in Blau, Münster in Grün mit Hervorhebung
fig2.add_trace(go.Scatter(
    x=stadt_agg[~stadt_agg['Ist_Muenster']]['Einkommen_Avg'], # Durchschnitt Einkommen pro Einwohner
    y=stadt_agg[~stadt_agg['Ist_Muenster']]['Sozialindex_Avg'], # Durchschnitt Sozialindex
    mode='markers', 
    marker=dict(size=10, color='#1f77b4', opacity=0.6, line=dict(color='black', width=1)), # Blau für andere Städte
    text=stadt_agg[~stadt_agg['Ist_Muenster']]['Stadt'], # Stadtname als Hover-Text
    hovertemplate='<b>%{text}</b><br>Einkommen: €%{x:.0f}<br>Sozialindex: %{y:.2f}<extra></extra>', # Hover-Template mit Stadtname, Einkommen und Sozialindex
    name='Andere Städte' 
))

# Münster hervorheben
muenster = stadt_agg[stadt_agg['Ist_Muenster']]
if not muenster.empty:
    fig2.add_trace(go.Scatter(
        x=muenster['Einkommen_Avg'],
        y=muenster['Sozialindex_Avg'],
        mode='markers+text',
        marker=dict(size=15, color="#14ff27", line=dict(color='darkred', width=2)),
        text=['Münster (Referenz)'],
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>Einkommen: €%{x:.0f}<br>Sozialindex: %{y:.2f}<extra></extra>',
        name='Münster'
    ))

# Layout anpassen und Achsen beschriften
fig2.update_layout( 
    title='Einkommen vs. Sozialindex in NRW Städten',
    xaxis_title='Durchschnitt Einkommen pro Einwohner (EUR)',
    yaxis_title='Durchschnitt Sozialindex',
    width=1000,
    height=600,
    template='plotly_white',
    hovermode='closest'
)

fig2.write_html(os.path.join(output_dir, 'viz_plotly_101_einkommen_sozialindex.html'))
print(f"   [OK] Gespeichert: viz_plotly_101_einkommen_sozialindex.html")


# VIZ 3: Sozialindex vs. Betreuungsrelation
print(f"\n [3/11] Erstelle: Sozialindex vs. Betreuungsrelation...")

fig3 = go.Figure()

# Alle Punkte außer Münster (Referenz) in Blau, Münster in Pink mit Hervorhebung
fig3.add_trace(go.Scatter(
    x=stadt_agg[~stadt_agg['Ist_Muenster']]['Sozialindex_Avg'], # Durchschnitt Sozialindex
    y=stadt_agg[~stadt_agg['Ist_Muenster']]['Betreuungsrelation_Avg'], # Durchschnitt Betreuung (Schüler/Lehrer)
    mode='markers', 
    marker=dict(size=10, color='#1f77b4', opacity=0.6, line=dict(color='black', width=1)),
    text=stadt_agg[~stadt_agg['Ist_Muenster']]['Stadt'],
    hovertemplate='<b>%{text}</b><br>Sozialindex: %{x:.2f}<br>Betreuung: %{y:.2f}<extra></extra>',
    name='Andere Städte'
))

if not muenster.empty: 
    fig3.add_trace(go.Scatter(
        x=muenster['Sozialindex_Avg'],
        y=muenster['Betreuungsrelation_Avg'],
        mode='markers+text',
        marker=dict(size=15, color="#14ff4f", line=dict(color='darkred', width=2)),
        text=['Münster'],
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>Sozialindex: %{x:.2f}<br>Betreuung: %{y:.2f}<extra></extra>',
        name='Münster'
    ))

fig3.update_layout(
    title='Sozialindex vs. Betreuungsrelation in NRW Städten',
    xaxis_title='Sozialindex',
    yaxis_title='Betreuungsrelation (Schüler/Lehrer)',
    width=1000,
    height=600,
    template='plotly_white',
    hovermode='closest'
)

fig3.write_html(os.path.join(output_dir, 'viz_plotly_102_sozialindex_betreuung.html'))
print(f"   [OK] Gespeichert: viz_plotly_102_sozialindex_betreuung.html")


# VIZ 4: Top 10 & Bottom 10 Städte
print(f"\n [4/11] Erstelle: Top/Bottom 10 Städte...")

# Top 10 Städte mit niedrigstem Sozialindex (besser) und Bottom 10 mit höchstem Sozialindex (schlechter)
top10 = stadt_agg.nlargest(10, 'Sozialindex_Avg').sort_values('Sozialindex_Avg', ascending=True)
bottom10 = stadt_agg.nsmallest(10, 'Sozialindex_Avg').sort_values('Sozialindex_Avg', ascending=False)

fig4 = make_subplots(
    rows=1, cols=2,
    subplot_titles=('Top 10 (Best)', 'Bottom 10 (Worst)'),
    specs=[[{'type': 'bar'}, {'type': 'bar'}]],
    horizontal_spacing=0.12
)

# Bar-Charts für Top 10 und Bottom 10 Städte mit Hover-Text und Beschriftungen
fig4.add_trace(go.Bar(
    y=top10['Stadt'],
    x=top10['Sozialindex_Avg'],
    orientation='h',
    marker=dict(color='#2ca02c', line=dict(color='#1b5e0f', width=1)),
    text=top10['Sozialindex_Avg'].round(2),
    textposition='outside',
    hovertemplate='<b>%{y}</b><br>Sozialindex: %{x:.2f}<extra></extra>',
    showlegend=False
), row=1, col=1)

# Bar-Chart für Bottom 10 Städte mit Hervorhebung in Orange und Hover-Text
fig4.add_trace(go.Bar(
    y=bottom10['Stadt'],
    x=bottom10['Sozialindex_Avg'],
    orientation='h',
    marker=dict(color='#ff7f0e', line=dict(color='#8b5a00', width=1)),
    text=bottom10['Sozialindex_Avg'].round(2),
    textposition='outside',
    hovertemplate='<b>%{y}</b><br>Sozialindex: %{x:.2f}<extra></extra>',
    showlegend=False
), row=1, col=2)

fig4.update_xaxes(title_text='Sozialindex', row=1, col=1)
fig4.update_xaxes(title_text='Sozialindex', row=1, col=2)

fig4.update_layout(
    title='Top 10 und Bottom 10 Städte nach Sozialindex',
    width=1400,
    height=600,
    template='plotly_white'
)

fig4.write_html(os.path.join(output_dir, 'viz_plotly_103_top_bottom_staedte.html'))
print(f"   [OK] Gespeichert: viz_plotly_103_top_bottom_staedte.html")

# VIZ 5: Boxplots nach Stadtgröße (mit Original-Schulendaten!)
print(f"\n [5/11] Erstelle: Vergleich nach Stadtgröße...")

# Wir müssen die Kategorisierung auch auf Original-Schulendaten anwenden
# um genug Datenpunkte für Boxplots zu haben!

df['Schulanzahl_Kreis'] = df.groupby('Kreis')['Kreis'].transform('count') # Anzahl Schulen pro Kreis als neue Spalte
df['Stadtgroesse_Schulen'] = df['Schulanzahl_Kreis'].apply(schulanzahl_kategorie) # Kategorisiere nach Anzahl der Schulen pro Kreis

# Erstelle Boxplots für Sozialindex, Einkommen, Betreuung und Bildungsausgaben nach Stadtgröße (Schulanzahl-Kategorien)
fig5 = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        '<b>1. Sozialindex</b><br><sub>Niedrig = besser</sub>',
        '<b>2. Einkommen pro Einwohner</b><br><sub>Höher = besser</sub>',
        '<b>3. Betreuungsrelation</b><br><sub>Niedriger = besser</sub>',
        '<b>4. Bildungsausgaben</b><br><sub>Höher = bessere Ausstattung</sub>'
    ),
    specs=[[{'type': 'box'}, {'type': 'box'}],
           [{'type': 'box'}, {'type': 'box'}]],
    vertical_spacing=0.18,
    horizontal_spacing=0.12
)

# Definiere Farben für die Stadtgrößen-Kategorien
stadtgroessen = ['Kleine Region (1-40 Schulen)', 'Mittlere Region (41-80 Schulen)', 'Große Region (81-120 Schulen)', 'Sehr große Region (>120 Schulen)']
colors_sg = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

# Sozialindex 
for i, sg in enumerate(stadtgroessen):
    data = df[df['Stadtgroesse_Schulen'] == sg]['Sozialindex'].dropna()
    if len(data) > 0:
        fig5.add_trace(go.Box(
            y=data, name=sg, marker_color=colors_sg[i], showlegend=False,
            hovertemplate='<b>%{fullData.name}</b><br>Sozialindex: %{y:.2f}<extra></extra>',
            boxmean='sd'
        ), row=1, col=1)

# Einkommen
for i, sg in enumerate(stadtgroessen):
    data = df[df['Stadtgroesse_Schulen'] == sg]['Einkommen_Pro_Einwohner_Euro'].dropna()
    if len(data) > 0:
        fig5.add_trace(go.Box(
            y=data, name=sg, marker_color=colors_sg[i], showlegend=False,
            hovertemplate='<b>%{fullData.name}</b><br>Einkommen: €%{y:.0f}<extra></extra>',
            boxmean='sd'
        ), row=1, col=2)

# Betreuung 
for i, sg in enumerate(stadtgroessen):
    data = df[df['Stadtgroesse_Schulen'] == sg]['Schueler_Pro_Lehrkraft'].dropna()
    if len(data) > 0:
        fig5.add_trace(go.Box(
            y=data, name=sg, marker_color=colors_sg[i], showlegend=False,
            hovertemplate='<b>%{fullData.name}</b><br>Schüler/Lehrer: %{y:.2f}<extra></extra>',
            boxmean='sd'
        ), row=2, col=1)

# Bildungsausgaben 
for i, sg in enumerate(stadtgroessen):
    data = df[df['Stadtgroesse_Schulen'] == sg]['Bildungsausgaben_Euro'].dropna()
    if len(data) > 0:
        fig5.add_trace(go.Box(
            y=data, name=sg, marker_color=colors_sg[i], showlegend=False,
            hovertemplate='<b>%{fullData.name}</b><br>Ausgaben: €%{y:.0f}<extra></extra>',
            boxmean='sd'
        ), row=2, col=2)

fig5.update_yaxes(title_text='Sozialindex', row=1, col=1)
fig5.update_yaxes(title_text='Einkommen (EUR)', row=1, col=2)
fig5.update_yaxes(title_text='Schüler/Lehrer', row=2, col=1)
fig5.update_yaxes(title_text='Ausgaben (EUR)', row=2, col=2)

fig5.update_xaxes(title_text='', row=1, col=1)
fig5.update_xaxes(title_text='', row=1, col=2)
fig5.update_xaxes(title_text='', row=2, col=1)
fig5.update_xaxes(title_text='', row=2, col=2)

fig5.update_layout(
    title={
        'text': 'Vergleich nach Stadtgröße in NRW<br><sub>Jede Box zeigt Min, Quartile, Median (Linie), Mittelwert (Raute) und Max einer Stadtgröße-Kategorie</sub>',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 16, 'color': '#000000'}
    },
    width=1400,
    height=950,
    template='plotly_white',
    showlegend=False,
    font=dict(size=11)
)

fig5.write_html(os.path.join(output_dir, 'viz_plotly_104_stadtgroesse_vergleich.html'))
print(f"   [OK] Gespeichert: viz_plotly_104_stadtgroesse_vergleich.html")


# GYMNASIUM-EBENE AGGREGATION
print(f"\n Aggregiere auf Gymnasium-Ebene...")

# Filtere nur Gymnasien und Gesamtschulen (inkl. Varianten) für die Gymnasium-Ebene Analysen
schulformen = {'gymnasium', 'gymnasien', 'gesamtschule', 'gesamtschulen'}
df['Schulform_Clean_Lower'] = df['Schulform_Clean'].str.lower()
df_gymnasien = df[df['Schulform_Clean_Lower'].isin(schulformen)].copy()

kreis_stats = df_gymnasien.groupby('Kreis').agg({
    'Schulnummer': 'count',
    'Sozialindex': 'mean',
    'Einkommen_Pro_Einwohner_Euro': 'mean',
    'Schueler_Pro_Lehrkraft': 'mean'
}).reset_index()

# Benenne Spalten um für Klarheit
kreis_stats.columns = ['Kreis', 'Anzahl_Schulen', 'Sozialindex_Avg', 'Einkommen_Avg', 'Betreuung_Avg']

# Markiere Münster in Gymnasium-Datensatz
kreis_stats['Ist_Muenster'] = (
    kreis_stats['Kreis'].str.contains('nster', case=False, na=False) &
    kreis_stats['Kreis'].str.contains('Stadt', case=False, na=False)
)

print(f"   [OK] {len(df_gymnasien)} Gymnasien/Gesamtschulen in {len(kreis_stats)} Kreisen")


# VIZ 6: Gymnasien Top/Bottom
print(f"\n [6/11] Erstelle: Gymnasien Top/Bottom Rankings...")

# Top 10 Kreise mit niedrigstem Sozialindex (besser) und Bottom 10 mit höchstem Sozialindex (schlechter)
top10_gym = kreis_stats.nlargest(10, 'Sozialindex_Avg').sort_values('Sozialindex_Avg', ascending=True)
bottom10_gym = kreis_stats.nsmallest(10, 'Sozialindex_Avg').sort_values('Sozialindex_Avg', ascending=False)

# Erstelle horizontale Bar-Charts für Top 10 und Bottom 10 Kreise mit Gymnasien/Gesamtschulen, zeige Sozialindex-Werte als Text an und füge Hover-Informationen hinzu
fig6 = make_subplots(
    rows=1, cols=2,
    subplot_titles=('Top 10 (Best)', 'Bottom 10 (Worst)'),
    specs=[[{'type': 'bar'}, {'type': 'bar'}]],
    horizontal_spacing=0.12
)

# Bar-Chart für Top 10 Kreise mit Gymnasien/Gesamtschulen in Grün mit Hover-Text und Beschriftungen
fig6.add_trace(go.Bar(
    y=top10_gym['Kreis'],
    x=top10_gym['Sozialindex_Avg'],
    orientation='h',
    marker=dict(color='#2ca02c', line=dict(color='#1b5e0f', width=1)),
    text=top10_gym['Sozialindex_Avg'].round(2),
    textposition='outside',
    hovertemplate='<b>%{y}</b><br>Sozialindex: %{x:.2f}<extra></extra>',
    showlegend=False
), row=1, col=1)

# Bar-Chart für Bottom 10 Kreise mit Gymnasien/Gesamtschulen in Orange mit Hover-Text und Beschriftungen
fig6.add_trace(go.Bar(
    y=bottom10_gym['Kreis'],
    x=bottom10_gym['Sozialindex_Avg'],
    orientation='h',
    marker=dict(color='#ff7f0e', line=dict(color='#8b5a00', width=1)),
    text=bottom10_gym['Sozialindex_Avg'].round(2),
    textposition='outside',
    hovertemplate='<b>%{y}</b><br>Sozialindex: %{x:.2f}<extra></extra>',
    showlegend=False
), row=1, col=2)

fig6.update_xaxes(title_text='Sozialindex', row=1, col=1)
fig6.update_xaxes(title_text='Sozialindex', row=1, col=2)

fig6.update_layout(
    title='Gymnasien/Gesamtschulen: Top 10 und Bottom 10 nach Sozialindex',
    width=1400,
    height=600,
    template='plotly_white'
)

fig6.write_html(os.path.join(output_dir, 'viz_plotly_105_gymnasien_top_bottom.html'))
print(f"   [OK] Gespeichert: viz_plotly_105_gymnasien_top_bottom.html")


# VIZ 7: Gymnasien Sozialindex vs. Betreuung
print(f"\n [7/11] Erstelle: Gymnasien Sozialindex vs. Betreuung...")

fig7 = go.Figure()

# Alle Punkte außer Münster (Referenz) in Blau, Münster in Grün mit Hervorhebung
fig7.add_trace(go.Scatter(
    x=kreis_stats[~kreis_stats['Ist_Muenster']]['Sozialindex_Avg'],
    y=kreis_stats[~kreis_stats['Ist_Muenster']]['Betreuung_Avg'],
    mode='markers',
    marker=dict(size=10, color='#1f77b4', opacity=0.6, line=dict(color='black', width=1)),
    text=kreis_stats[~kreis_stats['Ist_Muenster']]['Kreis'],
    hovertemplate='<b>%{text}</b><br>Sozialindex: %{x:.2f}<br>Betreuung: %{y:.2f}<extra></extra>',
    name='Andere Kreise'
))

muenster_gym = kreis_stats[kreis_stats['Ist_Muenster']]
if not muenster_gym.empty:
    fig7.add_trace(go.Scatter(
        x=muenster_gym['Sozialindex_Avg'],
        y=muenster_gym['Betreuung_Avg'],
        mode='markers+text',
        marker=dict(size=15, color="#1bd86a", line=dict(color='black', width=2)),
        text=['Münster'],
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>Sozialindex: %{x:.2f}<br>Betreuung: %{y:.2f}<extra></extra>',
        name='Münster'
    ))

fig7.update_layout(
    title='Gymnasien/Gesamtschulen: Sozialindex vs. Betreuungsrelation',
    xaxis_title='Sozialindex',
    yaxis_title='Betreuungsrelation (Schüler/Lehrer)',
    width=1000,
    height=600,
    template='plotly_white',
    hovermode='closest'
)

fig7.write_html(os.path.join(output_dir, 'viz_plotly_106_gymnasien_sozialindex_betreuung.html'))
print(f"   [OK] Gespeichert: viz_plotly_106_gymnasien_sozialindex_betreuung.html")


# VIZ 8: Gymnasien Schulanzahl nach Kreis

print(f"\n [8/11] Erstelle: Gymnasien Schulanzahl nach Kreis...")

# Erstelle horizontalen Bar-Chart mit Anzahl Gymnasien/Gesamtschulen pro Kreis, sortiert nach Anzahl, mit Hervorhebung von Münster und Hover-Informationen
sorted_kreis = kreis_stats.sort_values('Anzahl_Schulen', ascending=True)
colors_gym = ['#d81b60' if m else '#1f77b4' for m in sorted_kreis['Ist_Muenster']]

fig8 = go.Figure(data=[
    go.Bar(
        y=sorted_kreis['Kreis'],
        x=sorted_kreis['Anzahl_Schulen'],
        orientation='h',
        marker=dict(color=colors_gym, line=dict(color='black', width=1)),
        text=sorted_kreis['Anzahl_Schulen'],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Anzahl: %{x:.0f}<extra></extra>'
    )
])

fig8.update_layout(
    title='Anzahl Gymnasien/Gesamtschulen nach Kreis in NRW',
    xaxis_title='Anzahl Schulen',
    yaxis_title='Kreis / Stadt',
    width=1000,
    height=700,
    template='plotly_white'
)

fig8.write_html(os.path.join(output_dir, 'viz_plotly_107_gymnasien_schulanzahl.html'))
print(f"   [OK] Gespeichert: viz_plotly_107_gymnasien_schulanzahl.html")

# VIZ 9-11: Bereits erstellt in visualize_plotly_interactive.py
print(f"\n [9/11] Bereits vorhanden: viz_plotly_01_sozialindex_schulform.html")
print(f" [10/11] Bereits vorhanden: viz_plotly_02_bildungsungleichheit_extreme.html")
print(f" [11/11] Bereits vorhanden: viz_plotly_03_gymnasien_top15.html")

print("\n" + "=" * 80)
print("ERFOLG! Alle Plotly-Visualisierungen erstellt")
print("=" * 80)
print("\nSTADT-EBENE (Visualisierungen 100-104):")
print("   1. viz_plotly_100_korrelation_heatmap.html")
print("   2. viz_plotly_101_einkommen_sozialindex.html")
print("   3. viz_plotly_102_sozialindex_betreuung.html")
print("   4. viz_plotly_103_top_bottom_staedte.html")
print("   5. viz_plotly_104_stadtgroesse_vergleich.html")
print("\nGYMNASIUM-EBENE (Visualisierungen 105-107):")
print("   6. viz_plotly_105_gymnasien_top_bottom.html")
print("   7. viz_plotly_106_gymnasien_sozialindex_betreuung.html")
print("   8. viz_plotly_107_gymnasien_schulanzahl.html")
print("\nERGÄNZUNGEN (Visualisierungen 01-03):")
print("   9. viz_plotly_01_sozialindex_schulform.html")
print("   10. viz_plotly_02_bildungsungleichheit_extreme.html")
print("   11. viz_plotly_03_gymnasien_top15.html")
print("   12. viz_plotly_04_sozialindex_spreizung.html")
print("   13. viz_plotly_05_schulformen_verteilung.html")
print("\n Alle Dateien befinden sich im 'output' Verzeichnis\n")
