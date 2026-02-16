"""
Erstellt 4 erweiterte Plotly-Visualisierungen speziell für Gymnasien und
Gesamtschulen mit tieferen Analysen zu Verteilung, Ranking und Vergleichen.

Die Abitur-Excel-Dateien enthalten nur Bundesland-Aggregationen (BW, BY, NRW gesamt),
keine Schul- oder Kreis-spezifischen Abiturnoten. Daher nutzen wir die verfügbaren
Schuldaten (Sozialindex, Betreuung, etc.) für tiefere Gymnasium-Analysen.

ERWEITERTE GYMNASIUM-ANALYSEN (VIZ 200-203):
- viz_plotly_200_gymnasium_heatmap.html - Heatmap: Sozialindex nach Kreis & Schulform
- viz_plotly_201_gymnasium_top20.html - Top 20 Gymnasien mit besten Bedingungen
- viz_plotly_202_gym_vs_gesamtschule.html - Direkter Vergleich: Gymnasium vs. Gesamtschule
- viz_plotly_203_kreis_gymnasium_dichte.html - Scatterplot: Gymnasium-Dichte vs. Sozialindex


# WICHTIGE ERKENNTNISSE:
- Heatmap zeigt regionale Muster in Gymnasium-Verteilung
- Top 20 basiert auf niedrigstem Sozialindex (= beste Bedingungen)
- Vergleich zeigt signifikante Unterschiede zwischen Schulformen
- Kreis-Analyse zeigt Zusammenhang zwischen Gymnasium-Dichte, Sozialindex und Einkommen
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
print("ERWEITERTE GYMNASIUM-VISUALISIERUNGEN")
print("=" * 80)

output_dir = os.path.join(data_dir, 'output')
os.makedirs(output_dir, exist_ok=True)

# Lade Schuldaten
print(f"\n Lade Schuldaten...")
try:
    df = pd.read_csv(os.path.join(output_dir, 'merged_schuldaten_extended.csv'), 
                     sep=';', decimal=',', encoding='utf-8-sig')
    
    # Umlauts ersetzen in allen String-Spalten
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
    print(f"   [OK] {len(df)} Schulen geladen")
except FileNotFoundError as e:
    print(f"   [FEHLER] {e}")
    exit()

# Filtere Gymnasien und Gesamtschulen
gymnasien = df[df['Schulform'].isin(['Gymnasien', 'Gesamtschulen'])].copy()
print(f"   [OK] {len(gymnasien)} Gymnasien/Gesamtschulen gefunden")

# VIZ 1: Gymnasien - Sozialindex-Verteilung nach Kreis (Heatmap-Style)
print(f"\n [1/4] Erstelle: Gymnasium-Heatmap nach Kreis...")

# Berechne Durchschnitts-Sozialindex und Anzahl Gymnasien pro Kreis & Schulform
gym_kreis = gymnasien.groupby(['Kreis', 'Schulform']).agg({
    'Sozialindex': ['mean', 'count']
}).reset_index()

# Bereinige Spaltennamen
gym_kreis.columns = ['Kreis', 'Schulform', 'Ø_Sozialindex', 'Anzahl']

# Pivot für Heatmap (Zeilen = Kreis, Spalten = Schulform, Werte = Ø_Sozialindex)
pivot_data = gym_kreis.pivot(index='Kreis', columns='Schulform', values='Ø_Sozialindex')

# Erstelle Heatmap mit Plotly
fig1 = go.Figure(data=go.Heatmap(
    z=pivot_data.values,
    x=pivot_data.columns,
    y=pivot_data.index,
    colorscale='RdYlGn_r',
    hoverongaps=False,
    hovertemplate='<b>%{y}</b><br>%{x}<br>Ø Sozialindex: %{z:.2f}<extra></extra>',
    colorbar=dict(title='Sozialindex')
))

# Layout anpassen
fig1.update_layout(
    title='<b>Gymnasium/Gesamtschule: Sozialindex-Heatmap nach Kreis</b><br><sub>Rot = schwierige Bedingungen | Grün = gute Bedingungen</sub>',
    xaxis_title='Schulform',
    yaxis_title='Kreis/Stadt',
    width=800,
    height=1000,
    template='plotly_white'
)

fig1.write_html(os.path.join(output_dir, 'viz_plotly_200_gymnasium_heatmap.html'))
print(f"   [OK] Gespeichert: viz_plotly_200_gymnasium_heatmap.html")


# VIZ 2: Top 20 Gymnasien mit besten Bedingungen (niedrigster Sozialindex)
print(f"\n [2/4] Erstelle: Top 20 Gymnasien...")

top_gym = gymnasien.nsmallest(20, 'Sozialindex')[['Schulname', 'Kreis', 'Sozialindex', 'Schueler_Pro_Lehrkraft', 'Schulform']]

fig2 = go.Figure(go.Bar(
    y=top_gym['Schulname'],
    x=top_gym['Sozialindex'],
    orientation='h',
    marker=dict(
        color=top_gym['Schueler_Pro_Lehrkraft'],
        colorscale='Viridis',
        colorbar=dict(title='Schüler/Lehrer'),
        line=dict(color='darkblue', width=0.5)
    ),
    text=top_gym['Sozialindex'].round(2),
    textposition='outside',
    customdata=np.column_stack((top_gym['Kreis'], top_gym['Schueler_Pro_Lehrkraft'], top_gym['Schulform'])),
    hovertemplate='<b>%{y}</b><br>Kreis: %{customdata[0]}<br>Sozialindex: %{x:.2f}<br>Betreuung: %{customdata[1]:.1f}<br>Form: %{customdata[2]}<extra></extra>'
))

fig2.update_layout(
    title='<b>Top 20 Gymnasien/Gesamtschulen mit besten Bedingungen</b><br><sub>Niedrigster Sozialindex = beste sozioökonomische Bedingungen</sub>',
    xaxis_title='Sozialindex',
    yaxis_title='Schule',
    width=1000,
    height=700,
    template='plotly_white'
)

fig2.write_html(os.path.join(output_dir, 'viz_plotly_201_gymnasium_top20.html'))
print(f"   [OK] Gespeichert: viz_plotly_201_gymnasium_top20.html")


# VIZ 3: Gymnasium vs. Gesamtschule - Direkter Vergleich


print(f"\n [3/4] Erstelle: Gymnasium vs. Gesamtschule Vergleich...")

# Erstelle Subplots: Links = Sozialindex-Verteilung, Rechts = Betreuungsrelation
fig3 = make_subplots(
    rows=1, cols=2,
    subplot_titles=('Sozialindex-Verteilung', 'Betreuungsrelation'),
    specs=[[{'type': 'box'}, {'type': 'box'}]]
)

# Sozialindex 
for i, schulform in enumerate(['Gymnasien', 'Gesamtschulen']):
    data = gymnasien[gymnasien['Schulform'] == schulform]['Sozialindex'].dropna()
    color = '#1f77b4' if schulform == 'Gymnasien' else '#ff7f0e'
    
    fig3.add_trace(go.Box(
        y=data,
        name=f'{schulform} (n={len(data)})',
        marker_color=color,
        boxmean='sd',
        hovertemplate='<b>%{fullData.name}</b><br>Sozialindex: %{y:.2f}<extra></extra>'
    ), row=1, col=1)

# Betreuung 
for i, schulform in enumerate(['Gymnasien', 'Gesamtschulen']):
    data = gymnasien[gymnasien['Schulform'] == schulform]['Schueler_Pro_Lehrkraft'].dropna()
    color = '#1f77b4' if schulform == 'Gymnasien' else '#ff7f0e'
    
    fig3.add_trace(go.Box(
        y=data,
        name=f'{schulform}',
        marker_color=color,
        boxmean='sd',
        showlegend=False,
        hovertemplate='<b>%{fullData.name}</b><br>Schüler/Lehrer: %{y:.2f}<extra></extra>'
    ), row=1, col=2)

# Achsentitel hinzufügen und Layout anpassen
fig3.update_yaxes(title_text='Sozialindex', row=1, col=1)
fig3.update_yaxes(title_text='Schüler pro Lehrkraft', row=1, col=2)

# Layout anpassen
fig3.update_layout(
    title='<b>Gymnasium vs. Gesamtschule: Direkter Vergleich</b><br><sub>Vergleich der Rahmenbedingungen zwischen den beiden Schulformen</sub>',
    width=1200,
    height=600,
    template='plotly_white',
    hovermode='closest'
)

fig3.write_html(os.path.join(output_dir, 'viz_plotly_202_gym_vs_gesamtschule.html'))
print(f"   [OK] Gespeichert: viz_plotly_202_gym_vs_gesamtschule.html")


# VIZ 4: Kreis-Analyse - Gymnasium-Dichte und Sozialindex
print(f"\n [4/4] Erstelle: Kreis-Analyse Gymnasium-Dichte...")

# Berechne Anzahl Gymnasien pro Kreis, Durchschnitts-Sozialindex, Betreuung und Einkommen
kreis_gym = gymnasien.groupby('Kreis').agg({
    'Schulname': 'count',
    'Sozialindex': 'mean',
    'Schueler_Pro_Lehrkraft': 'mean',
    'Einkommen_Pro_Einwohner_Euro': 'mean'
}).reset_index()

kreis_gym.columns = ['Kreis', 'Anzahl_Gymnasien', 'Ø_Sozialindex', 'Ø_Betreuung', 'Ø_Einkommen']

kreis_einwohner = df.groupby('Kreis')['Einwohnerzahl'].mean().reset_index()
kreis_gym = kreis_gym.merge(kreis_einwohner, on='Kreis', how='left')
kreis_gym['Gym_Dichte_100k'] = (kreis_gym['Anzahl_Gymnasien'] / kreis_gym['Einwohnerzahl']) * 100000
kreis_gym = kreis_gym.replace([np.inf, -np.inf], np.nan).dropna(subset=['Gym_Dichte_100k'])

# Erstelle Scatterplot: X = Anzahl Gymnasien, Y = Ø Sozialindex, Größe = Ø Einkommen, Farbe = Ø Betreuung
fig4 = px.scatter(
    kreis_gym,
    x='Gym_Dichte_100k',
    y='Ø_Sozialindex',
    size='Ø_Einkommen',
    color='Ø_Betreuung',
    hover_name='Kreis',
    hover_data={
        'Anzahl_Gymnasien': True,
        'Gym_Dichte_100k': ':.2f',
        'Ø_Sozialindex': ':.2f',
        'Ø_Betreuung': ':.2f',
        'Ø_Einkommen': ':,.0f'
    },
    color_continuous_scale='RdYlGn_r',
    size_max=30,
    title='<b>Gymnasium-Dichte vs. Sozialindex nach Kreis</b><br><sub>Gymnasien pro 100.000 Ew. | Größe = Einkommen | Farbe = Betreuungsrelation</sub>',
    labels={
        'Gym_Dichte_100k': 'Gymnasien pro 100.000 Ew.',
        'Ø_Sozialindex': 'Durchschn. Sozialindex',
        'Ø_Betreuung': 'Ø Schüler/Lehrer',
        'Ø_Einkommen': 'Ø Einkommen'
    }
)

fig4.update_layout(
    width=1100,
    height=700,
    template='plotly_white'
)

fig4.write_html(os.path.join(output_dir, 'viz_plotly_203_kreis_gymnasium_dichte.html'))
print(f"   [OK] Gespeichert: viz_plotly_203_kreis_gymnasium_dichte.html")

print("\n" + "=" * 80)
print("ERFOLG! Erweiterte Gymnasium-Visualisierungen erstellt")
print("=" * 80)
print("\nNEUE VISUALISIERUNGEN:")
print("   1. viz_plotly_200_gymnasium_heatmap.html")
print("   2. viz_plotly_201_gymnasium_top20.html")
print("   3. viz_plotly_202_gym_vs_gesamtschule.html")
print("   4. viz_plotly_203_kreis_gymnasium_dichte.html")
print("\n Alle Dateien befinden sich im 'output' Verzeichnis")
print("\n HINWEIS: Abitur-Excel-Dateien enthalten nur Bundesland-Aggregationen,")
print("   keine Schul- oder Kreis-spezifischen Abiturnoten.")
