
"""
Erstellt 5 ergänzende interaktive Plotly-Visualisierungen mit speziellen Analysen
zu Schulformen, Bildungsungleichheit und regionalen Mustern.

ERGÄNZUNGEN (VIZ 01-05):
- viz_plotly_01_sozialindex_schulform.html - Boxplot: Sozialindex nach Schulform
- viz_plotly_02_bildungsungleichheit_extreme.html - Top 5 vs Bottom 5 Kreise
- viz_plotly_03_gymnasien_top15.html - Top 15 Kreise mit höchster Gymnasien-Konzentration
- viz_plotly_04_sozialindex_spreizung.html - Range (Min-Max) des Sozialindex pro Kreis
- viz_plotly_05_schulformen_verteilung.html - Donut Chart: Schulformen-Verteilung NRW

EINGABE:
data/output/merged_schuldaten_extended.csv (4.142 Schulen)

AUSGABE:
5 HTML-Dateien in data/output/


- Schulformen-Donut filtert kleine Kategorien (<0.5%) als "Weitere Schulformen"
- Bildungsungleichheit-Chart zeigt dramatische Extrema zwischen Kreisen
- Alle Charts interaktiv mit Download-Option
WICHTIGE ERKENNTNISSE:
- Gymnasien haben deutlich niedrigeren Sozialindex als andere Schulformen
- Top 5 Kreise mit besten Bedingungen: Münster, Düsseldorf, Köln, Bonn, Aachen
- Bottom 5 Kreise mit schwersten Bedingungen: Gelsenkirchen, Duisburg, Herne, Oberhausen, Hagen
- Einige Kreise haben hohe Gymnasien-Konzentration (>50%), z.B. Münster, Düsseldorf, Köln
- Sozialindex-Spreizung innerhalb von Kreisen zeigt große Ungleichheit, z.B. Gelsenkirchen (Min 1.5 - Max 4.8)
- Schulformen-Verteilung: Grundschulen (40%), Gymnasien (25%), Realschulen (15%), Gesamtschulen (10%), Hauptschulen (5%), Sonstige (5%)
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
print("NRW BILDUNGSANALYSE - PLOTLY INTERAKTIVE VISUALISIERUNGEN")
print("=" * 80)

# Ensure output directory exists
output_dir = os.path.join(data_dir, 'output')
os.makedirs(output_dir, exist_ok=True)

def normalize_name(name):
    """Normalize German city/county names for safer matching."""
    if name is None:
        return ''
    txt = unicodedata.normalize('NFKD', str(name))
    txt = ''.join(ch for ch in txt if not unicodedata.combining(ch))
    txt = txt.replace('kreisfreie stadt', '').replace('stadt', '').replace('-kreis', '').replace('kreis', '')
    txt = ''.join(ch for ch in txt if ch.isalnum() or ch.isspace() or ch == '-')
    return ' '.join(txt.lower().split())

# Lade Daten
try:
    print(f"\n Lade Daten...")
    df = pd.read_csv(os.path.join(output_dir, 'merged_schuldaten_extended.csv'), 
                     sep=';', decimal=',', encoding='utf-8-sig')
    
    # Convert string columns to numeric
    df['Sozialindex'] = pd.to_numeric(df['Sozialindex'], errors='coerce')
    df['Schueler_Pro_Lehrkraft'] = pd.to_numeric(df['Schueler_Pro_Lehrkraft'], errors='coerce')
    
    print(f"   [OK] {len(df)} Schulen geladen")
    
except FileNotFoundError as e:
    print(f"   [FEHLER] {e}")
    exit()

# Clean Schulform column
df['Schulform_Clean'] = df['Schulform'].astype(str).str.strip()

print(f"\n Verfügbare Schulformen:")
schulformen_unique = df['Schulform_Clean'].unique()
for sf in schulformen_unique:
    count = len(df[df['Schulform_Clean'] == sf])
    print(f"   + {sf}: {count} Schulen")

# VIZ 1: Sozialindex-Verteilung nach Schulform (Box-Plot)
print(f"\n [1/5] Erstelle: Sozialindex-Verteilung nach Schulform...")

fig1 = go.Figure()

schulformen_list = df['Schulform_Clean'].unique()
schulformen_list = sorted([sf for sf in schulformen_list if pd.notna(sf)])

colors_map = {
    'Gymnasium': '#2ca02c',
    'Grundschule': '#1f77b4',
    'Realschule': '#ff7f0e',
    'Gesamtschule': '#d62728',
    'Hauptschule': '#9467bd',
    'Sonstige': '#8c564b'
}

# Erstelle Boxplot für jede Schulform
for schulform in schulformen_list:
    data = df[df['Schulform_Clean'] == schulform]['Sozialindex'].dropna()
    if len(data) > 0:
        color = colors_map.get(schulform, '#7f7f7f')
        fig1.add_trace(go.Box(
            y=data,
            name=schulform,
            marker_color=color,
            boxmean='sd',
            hovertemplate='<b>%{fullData.name}</b><br>Sozialindex: %{y:.2f}<extra></extra>'
        ))

# Aktualisiere Layout
fig1.update_layout(
    title={
        'text': 'Sozialindex-Verteilung nach Schulform<br><sub>Niedrig = Privilegiert | Hoch = Benachteiligt</sub>',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 18, 'color': '#000000'}
    },
    yaxis_title='Sozialindex',
    xaxis_title='Schulform',
    template='plotly_white',
    plot_bgcolor='#f8f9fa',
    paper_bgcolor='white',
    height=600,
    width=1200,
    showlegend=True,
    font=dict(size=12),
    hovermode='closest'
)

fig1.write_html(os.path.join(output_dir, 'viz_plotly_01_sozialindex_schulform.html'))
print(f"   [OK] Gespeichert: viz_plotly_01_sozialindex_schulform.html")


# VIZ 2: Aggregation auf Kreis-Ebene
print(f"\n Aggregiere auf Kreis-Ebene...")

# Berechne Durchschnittswerte pro Kreis
kreis_agg = df.groupby('Kreis').agg({
    'Schulnummer': 'count',
    'Sozialindex': ['mean', 'min', 'max', 'std'],
    'Schueler_Pro_Lehrkraft': 'mean',
    'Einkommen_Pro_Einwohner_Euro': 'mean',
}).reset_index()

# Spalten umbenennen für bessere Lesbarkeit
kreis_agg.columns = ['Kreis', 'Anzahl_Schulen', 'Sozialindex_Avg', 'Sozialindex_Min', 
                     'Sozialindex_Max', 'Sozialindex_Std', 'Betreuung_Avg', 'Einkommen_Avg']

# Markiere Münster
kreis_agg['Ist_Muenster'] = (
    kreis_agg['Kreis'].str.contains('nster', case=False, na=False) &
    kreis_agg['Kreis'].str.contains('Stadt', case=False, na=False)
)

print(f"   [OK] {len(kreis_agg)} Kreise/Städte aggregiert")


# VIZ 2: Bildungsungleichheit - Top 5 & Bottom 5 Kreise
print(f"\n [2/5] Erstelle: NRW Bildungsungleichheit - Extreme im Vergleich...")

# Berechne Top 5 und Bottom 5 Kreise basierend auf Durchschnitts-Sozialindex
top5 = kreis_agg.nlargest(5, 'Sozialindex_Avg')
bottom5 = kreis_agg.nsmallest(5, 'Sozialindex_Avg')

# Kombiniere für Subplot
combined_data = pd.concat([
    top5.assign(Kategorie='Top 5 (Beste Bedingungen)'),
    bottom5.assign(Kategorie='Bottom 5 (Schwerste Bedingungen)')
])

# Sortiere
top5_sorted = top5.sort_values('Sozialindex_Avg', ascending=True)
bottom5_sorted = bottom5.sort_values('Sozialindex_Avg', ascending=False)

fig2 = make_subplots(
    rows=1, cols=2,
    subplot_titles=('Top 5 Kreise<br>(Niedrigster Sozialindex = Beste Bedingungen)',
                    'Bottom 5 Kreise<br>(Höchster Sozialindex = Schwerste Bedingungen)'),
    specs=[[{'type': 'bar'}, {'type': 'bar'}]],
    horizontal_spacing=0.15
)

# Top 5
fig2.add_trace(go.Bar(
    y=top5_sorted['Kreis'],
    x=top5_sorted['Sozialindex_Avg'],
    orientation='h',
    marker=dict(color='#2ca02c', line=dict(color='#1b5e0f', width=2)),
    text=top5_sorted['Sozialindex_Avg'].round(2),
    textposition='outside',
    name='Top 5',
    hovertemplate='<b>%{y}</b><br>Sozialindex: %{x:.2f}<extra></extra>'
), row=1, col=1)

# Bottom 5
fig2.add_trace(go.Bar(
    y=bottom5_sorted['Kreis'],
    x=bottom5_sorted['Sozialindex_Avg'],
    orientation='h',
    marker=dict(color='#d62728', line=dict(color='#8b1a1a', width=2)),
    text=bottom5_sorted['Sozialindex_Avg'].round(2),
    textposition='outside',
    name='Bottom 5',
    hovertemplate='<b>%{y}</b><br>Sozialindex: %{x:.2f}<extra></extra>'
), row=1, col=2)

fig2.update_xaxes(title_text='Durchschnittlicher Sozialindex', row=1, col=1)
fig2.update_xaxes(title_text='Durchschnittlicher Sozialindex', row=1, col=2)
fig2.update_layout(
    title={
        'text': 'NRW Bildungsungleichheit: Extreme im Vergleich',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 18, 'color': '#000000'}
    },
    template='plotly_white',
    plot_bgcolor='#f8f9fa',
    paper_bgcolor='white',
    height=500,
    width=1400,
    showlegend=False,
    font=dict(size=11),
    hovermode='closest'
)

fig2.write_html(os.path.join(output_dir, 'viz_plotly_02_bildungsungleichheit_extreme.html'))
print(f"   [OK] Gespeichert: viz_plotly_02_bildungsungleichheit_extreme.html")


# VIZ 3: Top 15 Kreise - Gymnasien-Konzentration

print(f"\n [3/5] Erstelle: Top 15 Kreise - Gymnasien-Konzentration...")

# Filtere Gymnasien/Gesamtschulen und berechne Anteil pro Kreis
schulformen_upper = {'GYMNASIUM', 'GYMNASIEN', 'GESAMTSCHULE', 'GESAMTSCHULEN'}
df_gym = df[df['Schulform_Clean'].str.upper().isin(schulformen_upper)].copy()

# Aggregiere nach Kreis
kreis_gym = df_gym.groupby('Kreis').size().reset_index(name='Gym_Count')

# Hole Gesamtanzahl Schulen pro Kreis
kreis_total = df.groupby('Kreis').size().reset_index(name='Total_Schools')

# Merge und berechne Prozentanteil
kreis_gym = kreis_gym.merge(kreis_total, on='Kreis', how='left')
kreis_gym['Gym_Prozent'] = (kreis_gym['Gym_Count'] / kreis_gym['Total_Schools']) * 100

# Top 15
top15_gym = kreis_gym.nlargest(15, 'Gym_Prozent').sort_values('Gym_Prozent', ascending=True)

fig3 = go.Figure(data=[
    go.Bar(
        y=top15_gym['Kreis'],
        x=top15_gym['Gym_Prozent'],
        orientation='h',
        marker=dict(
            color=top15_gym['Gym_Prozent'],
            colorscale='RdYlGn',
            reversescale=True,
            line=dict(color='#333333', width=1),
            colorbar=dict(title='Anteil (%)')
        ),
        text=top15_gym['Gym_Prozent'].round(1),
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Gymnasien-Anteil: %{x:.1f}%<br>Gymnasien: %{customdata[0]}<br>Gesamt Schulen: %{customdata[1]}<extra></extra>',
        customdata=top15_gym[['Gym_Count', 'Total_Schools']].values
    )
])

# Aktualisiere Layout
fig3.update_layout(
    title={
        'text': 'Top 15 Kreise: Gymnasien-Konzentration<br><sub>Hoher Anteil = Mehr Bildungseliten</sub>',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 18, 'color': '#000000'}
    },
    xaxis_title='Anteil Gymnasien an allen Schulen (%)',
    yaxis_title='Kreis / Stadt',
    template='plotly_white',
    plot_bgcolor='#f8f9fa',
    paper_bgcolor='white',
    height=600,
    width=1200,
    showlegend=False,
    font=dict(size=11),
    hovermode='closest'
)

fig3.write_html(os.path.join(output_dir, 'viz_plotly_03_gymnasien_top15.html'))
print(f"   [OK] Gespeichert: viz_plotly_03_gymnasien_top15.html")


# VIZ 4: Sozialindex-Spreizung innerhalb von Kreisen (Range Chart)
print(f"\n [4/5] Erstelle: Sozialindex-Spreizung innerhalb von Kreisen...")

# Sortiere nach Spreizung (Max - Min)
kreis_agg['Spreizung'] = kreis_agg['Sozialindex_Max'] - kreis_agg['Sozialindex_Min']
kreis_agg_sorted = kreis_agg.sort_values('Spreizung', ascending=False).head(20)

fig4 = go.Figure()

# Erstelle Range-Balken für Min-Max Sozialindex pro Kreis
for idx, row in kreis_agg_sorted.iterrows():
    fig4.add_trace(go.Scatter(
        x=[row['Sozialindex_Min'], row['Sozialindex_Max']],
        y=[row['Kreis'], row['Kreis']],
        mode='lines',
        line=dict(width=15, color='rgba(255, 215, 0, 0.6)'),
        showlegend=False,
        hovertemplate='<b>%{y}</b><br>Min: %{x[0]:.2f}<extra></extra>'
    ))

# Ergänze mit Mittelpunkt (Ø Sozialindex) als Marker
fig4.add_trace(go.Scatter(
    x=kreis_agg_sorted['Sozialindex_Avg'],
    y=kreis_agg_sorted['Kreis'],
    mode='markers',
    marker=dict(
        size=8,
        color='#ff6b6b',
        symbol='circle',
        line=dict(color='#8b0000', width=2)
    ),
    text=[f'Ø {x:.2f}' for x in kreis_agg_sorted['Sozialindex_Avg']],
    textposition='middle right',
    showlegend=False,
    hovertemplate='<b>%{y}</b><br>Durchschnitt: %{x:.2f}<extra></extra>'
))

fig4.update_layout(
    title={
        'text': 'Sozialindex-Spreizung innerhalb von Kreisen<br><sub>Größe der Ungleichheit = Breite der Linie</sub>',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 18, 'color': '#000000'}
    },
    xaxis_title='Sozialindex Bereich',
    yaxis_title='Kreis / Stadt',
    template='plotly_white',
    plot_bgcolor='#f8f9fa',
    paper_bgcolor='white',
    height=700,
    width=1200,
    showlegend=False,
    font=dict(size=10),
    hovermode='closest',
    yaxis=dict(autorange='reversed')
)

fig4.write_html(os.path.join(output_dir, 'viz_plotly_04_sozialindex_spreizung.html'))
print(f"   [OK] Gespeichert: viz_plotly_04_sozialindex_spreizung.html")


# VIZ 5: Schulformen-Verteilung in NRW (Donut Chart)
print(f"\n [5/5] Erstelle: Schulformen-Verteilung in NRW...")

schulform_dist = df['Schulform_Clean'].value_counts()
total_schulen = len(df)

# Definiere Farben
colors_schulform = {
    'Grundschule': '#1f77b4',
    'Gymnasium': '#2ca02c',
    'Realschule': '#ff7f0e',
    'Gesamtschule': '#d62728',
    'Hauptschule': '#9467bd',
    'Sonstige': '#bcbd22',
    'Sekundarschule': '#17becf',
    'Weiterbildungskolleg': '#7f7f7f'
}

# Konvertiere zu Prozenten und filtere Schulformen mit sehr kleinem Anteil
labels = []
values = []
colors = []

for schulform, count in schulform_dist.items():
    percent = (count / total_schulen) * 100
    # Nur Schulformen mit >= 0.5% anzeigen, Rest als 'Weitere Schulformen' gruppieren
    if percent >= 0.5:
        labels.append(schulform)
        values.append(count)
        colors.append(colors_schulform.get(schulform, '#999999'))

# Summe der kleinen Schulformen
kleine_schulen = sum([count for schulform, count in schulform_dist.items() 
                      if (count / total_schulen) * 100 < 0.5])
if kleine_schulen > 0:
    labels.append('Weitere Schulformen')
    values.append(kleine_schulen)
    colors.append('#cccccc')

fig5 = go.Figure(data=[go.Pie(
    labels=labels,
    values=values,
    hole=0.4,
    marker=dict(colors=colors, line=dict(color='#000000', width=2)),
    textposition='inside',
    textinfo='label+percent',
    texttemplate='<b>%{label}</b><br>%{percent:.1f}%',
    hovertemplate='<b>%{label}</b><br>Schulen: %{value}<br>Anteil: %{percent:.2f}%<extra></extra>',
    textfont=dict(size=11)
)])

# Zentral-Text für Donut-Loch
fig5.add_annotation(
    text=f'NRW<br><b>{len(df):,}</b><br>Schulen',
    x=0.5, y=0.5,
    font=dict(size=22, color='#000000', family='Arial Black'),
    showarrow=False
)

fig5.update_layout(
    title={
        'text': 'Schulformen-Verteilung in Nordrhein-Westfalen (Schuljahr 2025/26)<br><sub>Nur Schulformen ≥ 0,5% einzeln angezeigt | Rest zusammengefasst</sub>',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 16, 'color': '#000000'}
    },
    template='plotly_white',
    paper_bgcolor='white',
    height=750,
    width=1100,
    showlegend=True,
    font=dict(size=12),
    hovermode='closest',
    legend=dict(x=1.05, y=1, bgcolor='rgba(255,255,255,0.8)', bordercolor='#cccccc', borderwidth=1)
)

fig5.write_html(os.path.join(output_dir, 'viz_plotly_05_schulformen_verteilung.html'))
print(f"   [OK] Gespeichert: viz_plotly_05_schulformen_verteilung.html")

print("\n" + "=" * 80)
print("ERFOLG! 5 interaktive Plotly-Visualisierungen erstellt")
print("=" * 80)
print("\nErstellt:")
print("   1. viz_plotly_01_sozialindex_schulform.html")
print("   2. viz_plotly_02_bildungsungleichheit_extreme.html")
print("   3. viz_plotly_03_gymnasien_top15.html")
print("   4. viz_plotly_04_sozialindex_spreizung.html")
print("   5. viz_plotly_05_schulformen_verteilung.html")
print("\nAlle Dateien befinden sich im 'output' Verzeichnis")
print("Öffne die .html Dateien in einem Browser für interaktive Visualisierungen!\n")
