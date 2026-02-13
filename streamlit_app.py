"""
Streamlit-Webapplikation zur interaktiven Darstellung von 17 Plotly-Visualisierungen
der NRW Bildungsanalyse. Bietet Dashboard- und Story-Modus mit Sidebar-Navigation.

VERWENDUNG:
streamlit run streamlit_app.py

ABHÄNGIGKEITEN:

streamlit, plotly, pandas, numpy

FEATURES:
- Sidebar mit Kategorien-Navigation
- 17 interaktive Plotly-Charts
- Dashboard- und Story-Modus
- Responsive Layout
- Dark/Light Theme Support

"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
import unicodedata
import warnings
import subprocess
import sys
warnings.filterwarnings('ignore')

#  GENERATE DATA ON STARTUP IF MISSING 
def ensure_data_exists():
    """Generate merged data if it doesn't exist."""
    data_path = os.path.join('data', 'output', 'merged_schuldaten_extended.csv')
    if not os.path.exists(data_path):
        st.info("📊 Generiere Daten beim ersten Start...")
        try:
            subprocess.run([sys.executable, 'code/data_merge_extended.py'], 
                          cwd=os.getcwd(), check=True, capture_output=True)
            st.success("✅ Daten erfolgreich generiert!")
        except Exception as e:
            st.error(f"❌ Fehler beim Generieren der Daten: {e}")
            return False
    return True

# Call at startup
if not ensure_data_exists():
    st.stop()

#  PAGE CONFIG 
st.set_page_config(
    page_title="NRW Bildungsanalyse Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

#  CUSTOM CSS 
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #64748b;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
    }
    .info-box {
        background: #f1f5f9;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

#  HELPER FUNCTIONS 
def normalize_name(name):
    """Normalize German city/county names."""
    if name is None:
        return ''
    txt = unicodedata.normalize('NFKD', str(name))
    txt = ''.join(ch for ch in txt if not unicodedata.combining(ch))
    txt = txt.replace('kreisfreie stadt', '').replace('stadt', '').replace('-kreis', '').replace('kreis', '')
    txt = ''.join(ch for ch in txt if ch.isalnum() or ch.isspace() or ch == '-')
    return ' '.join(txt.lower().split())

@st.cache_data
def load_data():
    """Load merged school data with caching."""
    try:
        data_path = os.path.join('data', 'output', 'merged_schuldaten_extended.csv')
        df = pd.read_csv(data_path, sep=';', decimal=',', encoding='utf-8-sig')
        df['Sozialindex'] = pd.to_numeric(df['Sozialindex'], errors='coerce')
        df['Schueler_Pro_Lehrkraft'] = pd.to_numeric(df['Schueler_Pro_Lehrkraft'], errors='coerce')
        df['Einkommen_Pro_Einwohner_Euro'] = pd.to_numeric(df['Einkommen_Pro_Einwohner_Euro'], errors='coerce')
        df['Bildungsausgaben_Euro'] = pd.to_numeric(df['Bildungsausgaben_Euro'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {e}")
        return None

# VISUALIZATION FUNCTIONS 

def create_correlation_heatmap(df):
    """VIZ 100: Korrelations-Heatmap"""
    stadt_agg = df.groupby('Kreis').agg({
        'Sozialindex': 'mean',
        'Schueler_Pro_Lehrkraft': 'mean',
        'Einkommen_Pro_Einwohner_Euro': 'mean',
        'Bildungsausgaben_Euro': 'mean'
    }).reset_index()
    
    corr_matrix = stadt_agg[['Sozialindex', 'Schueler_Pro_Lehrkraft', 
                              'Einkommen_Pro_Einwohner_Euro', 'Bildungsausgaben_Euro']].corr()
    
    labels = ['Sozialindex', 'Schüler pro Lehrkraft', 
              'Einkommen (€/Einw.)', 'Bildungsausgaben (€)']
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=labels,
        y=labels,
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.values.round(2),
        texttemplate='%{text}',
        textfont={"size": 14},
        colorbar=dict(title="Korrelation")
    ))
    
    fig.update_layout(
        title="Korrelationsmatrix: Bildungs- und Sozialindikatoren",
        height=600,
        xaxis_title="",
        yaxis_title=""
    )
    return fig

def create_einkommen_sozialindex(df):
    """VIZ 101: Einkommen vs. Sozialindex"""
    stadt_agg = df.groupby('Kreis').agg({
        'Sozialindex': 'mean',
        'Einkommen_Pro_Einwohner_Euro': 'mean'
    }).reset_index()
    
    fig = px.scatter(
        stadt_agg,
        x='Einkommen_Pro_Einwohner_Euro',
        y='Sozialindex',
        text='Kreis',
        title='Einkommen vs. Sozialindex pro Kreis/Stadt',
        labels={
            'Einkommen_Pro_Einwohner_Euro': 'Einkommen pro Einwohner (€)',
            'Sozialindex': 'Durchschnittlicher Sozialindex'
        },
        color='Sozialindex',
        color_continuous_scale='RdYlGn',
        size_max=15
    )
    
    fig.update_traces(textposition='top center', textfont_size=8)
    fig.update_layout(height=600, showlegend=False)
    return fig

def create_sozialindex_betreuung(df):
    """VIZ 102: Sozialindex vs. Betreuungsrelation"""
    stadt_agg = df.groupby('Kreis').agg({
        'Sozialindex': 'mean',
        'Schueler_Pro_Lehrkraft': 'mean'
    }).reset_index()
    
    fig = px.scatter(
        stadt_agg,
        x='Sozialindex',
        y='Schueler_Pro_Lehrkraft',
        text='Kreis',
        title='Sozialindex vs. Betreuungsrelation',
        labels={
            'Sozialindex': 'Durchschnittlicher Sozialindex',
            'Schueler_Pro_Lehrkraft': 'Schüler pro Lehrkraft'
        },
        color='Schueler_Pro_Lehrkraft',
        color_continuous_scale='Reds_r'
    )
    
    fig.update_traces(textposition='top center', textfont_size=8)
    fig.update_layout(height=600)
    return fig

def create_top_bottom_cities(df):
    """VIZ 103: Top & Bottom 10 Städte"""
    stadt_agg = df.groupby('Kreis').agg({
        'Sozialindex': 'mean'
    }).reset_index()
    
    top10 = stadt_agg.nlargest(10, 'Sozialindex')
    bottom10 = stadt_agg.nsmallest(10, 'Sozialindex')
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Top 10 Städte/Kreise', 'Bottom 10 Städte/Kreise')
    )
    
    fig.add_trace(
        go.Bar(x=top10['Sozialindex'], y=top10['Kreis'],
               orientation='h', marker_color='green', name='Top 10'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=bottom10['Sozialindex'], y=bottom10['Kreis'],
               orientation='h', marker_color='red', name='Bottom 10'),
        row=1, col=2
    )
    
    fig.update_layout(
        title_text="Top & Bottom 10 Kreise/Städte nach Sozialindex",
        height=600,
        showlegend=False
    )
    return fig

def create_stadtgroesse_vergleich(df):
    """VIZ 104: Stadtgröße-Vergleich (basierend auf Schulanzahl)"""
    schulanzahl_pro_stadt = df.groupby('Kreis').size().reset_index(name='Schulanzahl')
    df_merged = df.merge(schulanzahl_pro_stadt, on='Kreis', how='left')
    
    def kategorisiere_groesse(anzahl):
        if anzahl <= 40:
            return '1: Klein (1-40 Schulen)'
        elif anzahl <= 80:
            return '2: Mittel (41-80 Schulen)'
        elif anzahl <= 120:
            return '3: Groß (81-120 Schulen)'
        else:
            return '4: Sehr Groß (>120 Schulen)'
    
    df_merged['Stadtgroesse'] = df_merged['Schulanzahl'].apply(kategorisiere_groesse)
    
    fig = go.Figure()
    
    for kategorie in sorted(df_merged['Stadtgroesse'].unique()):
        data_kat = df_merged[df_merged['Stadtgroesse'] == kategorie]
        fig.add_trace(go.Box(
            y=data_kat['Sozialindex'],
            name=kategorie,
            boxmean='sd'
        ))
    
    fig.update_layout(
        title='Sozialindex-Verteilung nach Regionsgröße (Schulanzahl)',
        yaxis_title='Sozialindex',
        xaxis_title='Kategorie',
        height=600
    )
    return fig

def create_gymnasium_top_bottom(df):
    """VIZ 105: Gymnasium Top/Bottom Kreise"""
    gym_df = df[df['Schulform'] == 'Gymnasien'].copy()
    gym_count = gym_df.groupby('Kreis').size().reset_index(name='Anzahl_Gymnasien')
    
    top10 = gym_count.nlargest(10, 'Anzahl_Gymnasien')
    bottom10 = gym_count.nsmallest(10, 'Anzahl_Gymnasien')
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Top 10 Kreise', 'Bottom 10 Kreise')
    )
    
    fig.add_trace(
        go.Bar(x=top10['Anzahl_Gymnasien'], y=top10['Kreis'],
               orientation='h', marker_color='darkblue', name='Top 10'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=bottom10['Anzahl_Gymnasien'], y=bottom10['Kreis'],
               orientation='h', marker_color='lightblue', name='Bottom 10'),
        row=1, col=2
    )
    
    fig.update_layout(
        title_text="Gymnasien-Dichte: Top & Bottom 10 Kreise",
        height=600,
        showlegend=False
    )
    fig.update_xaxes(title_text="Anzahl Gymnasien", row=1, col=1)
    fig.update_xaxes(title_text="Anzahl Gymnasien", row=1, col=2)
    return fig

def create_gymnasium_sozialindex(df):
    """VIZ 106: Gymnasium Sozialindex vs. Betreuung"""
    gym_df = df[df['Schulform'] == 'Gymnasien'].copy()
    gym_agg = gym_df.groupby('Kreis').agg({
        'Sozialindex': 'mean',
        'Schueler_Pro_Lehrkraft': 'mean'
    }).reset_index()
    
    fig = px.scatter(
        gym_agg,
        x='Sozialindex',
        y='Schueler_Pro_Lehrkraft',
        text='Kreis',
        title='Gymnasien: Sozialindex vs. Betreuungsrelation',
        labels={
            'Sozialindex': 'Durchschnittlicher Sozialindex',
            'Schueler_Pro_Lehrkraft': 'Schüler pro Lehrkraft'
        },
        color='Sozialindex',
        color_continuous_scale='Viridis'
    )
    
    fig.update_traces(textposition='top center', textfont_size=8)
    fig.update_layout(height=600)
    return fig

def create_gymnasium_schulanzahl(df):
    """VIZ 107: Gymnasien pro Kreis"""
    gym_df = df[df['Schulform'] == 'Gymnasien'].copy()
    gym_count = gym_df.groupby('Kreis').size().reset_index(name='Anzahl_Gymnasien')
    gym_count_sorted = gym_count.sort_values('Anzahl_Gymnasien', ascending=True)
    
    fig = go.Figure(go.Bar(
        x=gym_count_sorted['Anzahl_Gymnasien'],
        y=gym_count_sorted['Kreis'],
        orientation='h',
        marker=dict(
            color=gym_count_sorted['Anzahl_Gymnasien'],
            colorscale='Blues',
            showscale=True
        )
    ))
    
    fig.update_layout(
        title='Anzahl Gymnasien pro Kreis/Stadt',
        xaxis_title='Anzahl Gymnasien',
        yaxis_title='Kreis/Stadt',
        height=1200
    )
    return fig

def create_schulformen_boxplot(df):
    """VIZ 01: Schulformen Boxplot"""
    schulformen = df['Schulform'].value_counts()
    top_schulformen = schulformen[schulformen >= 10].index.tolist()
    df_filtered = df[df['Schulform'].isin(top_schulformen)].copy()
    
    fig = go.Figure()
    for schulform in sorted(df_filtered['Schulform'].unique()):
        data = df_filtered[df_filtered['Schulform'] == schulform]
        fig.add_trace(go.Box(
            y=data['Sozialindex'],
            name=schulform,
            boxmean='sd'
        ))
    
    fig.update_layout(
        title='Sozialindex-Verteilung nach Schulform',
        yaxis_title='Sozialindex',
        xaxis_title='Schulform',
        height=600
    )
    return fig

def create_extrema_comparison(df):
    """VIZ 02: Extrema-Vergleich"""
    stadt_stats = df.groupby('Kreis').agg({
        'Sozialindex': ['mean', 'min', 'max', 'std']
    }).reset_index()
    stadt_stats.columns = ['Kreis', 'SI_Mean', 'SI_Min', 'SI_Max', 'SI_Std']
    stadt_stats['SI_Range'] = stadt_stats['SI_Max'] - stadt_stats['SI_Min']
    top_spread = stadt_stats.nlargest(15, 'SI_Range')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=top_spread['Kreis'],
        y=top_spread['SI_Max'],
        mode='markers',
        name='Maximum',
        marker=dict(color='green', size=10)
    ))
    fig.add_trace(go.Scatter(
        x=top_spread['Kreis'],
        y=top_spread['SI_Mean'],
        mode='markers',
        name='Durchschnitt',
        marker=dict(color='blue', size=10)
    ))
    fig.add_trace(go.Scatter(
        x=top_spread['Kreis'],
        y=top_spread['SI_Min'],
        mode='markers',
        name='Minimum',
        marker=dict(color='red', size=10)
    ))
    
    fig.update_layout(
        title='Top 15 Kreise mit größter Sozialindex-Spreizung',
        xaxis_title='Kreis/Stadt',
        yaxis_title='Sozialindex',
        height=600
    )
    return fig

def create_gymnasium_concentration(df):
    """VIZ 03: Gymnasien-Konzentration"""
    gym_count = df[df['Schulform'] == 'Gymnasien'].groupby('Kreis').size()
    total_count = df.groupby('Kreis').size()
    gym_percent = (gym_count / total_count * 100).reset_index(name='Gymnasium_Prozent')
    gym_percent_sorted = gym_percent.sort_values('Gymnasium_Prozent', ascending=False).head(20)
    
    fig = go.Figure(go.Bar(
        x=gym_percent_sorted['Kreis'],
        y=gym_percent_sorted['Gymnasium_Prozent'],
        marker_color='darkgreen'
    ))
    
    fig.update_layout(
        title='Top 20 Kreise: Gymnasien-Anteil (%)',
        xaxis_title='Kreis/Stadt',
        yaxis_title='Gymnasium-Anteil (%)',
        height=600
    )
    return fig

def create_spreizung_ranking(df):
    """VIZ 04: Spreizungs-Ranking"""
    stadt_stats = df.groupby('Kreis').agg({
        'Sozialindex': ['std', 'mean']
    }).reset_index()
    stadt_stats.columns = ['Kreis', 'SI_Std', 'SI_Mean']
    top_std = stadt_stats.nlargest(20, 'SI_Std')
    
    fig = go.Figure(go.Bar(
        x=top_std['Kreis'],
        y=top_std['SI_Std'],
        marker=dict(
            color=top_std['SI_Mean'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Ø SI")
        )
    ))
    
    fig.update_layout(
        title='Top 20 Kreise: Größte Sozialindex-Standardabweichung',
        xaxis_title='Kreis/Stadt',
        yaxis_title='Standardabweichung Sozialindex',
        height=600
    )
    return fig

def create_schulformen_donut(df):
    """VIZ 05: Schulformen-Verteilung Donut"""
    schulformen_counts = df['Schulform'].value_counts()
    threshold_percent = 0.5
    threshold_count = len(df) * threshold_percent / 100
    
    main_schulformen = schulformen_counts[schulformen_counts >= threshold_count]
    other_count = schulformen_counts[schulformen_counts < threshold_count].sum()
    
    if other_count > 0:
        main_schulformen['Weitere Schulformen'] = other_count
    
    fig = go.Figure(data=[go.Pie(
        labels=main_schulformen.index,
        values=main_schulformen.values,
        hole=0.4,
        textinfo='label+percent',
        textposition='outside'
    )])
    
    fig.update_layout(
        title=f'Verteilung der Schulformen (≥{threshold_percent}% angezeigt)',
        height=600
    )
    return fig

def create_gymnasium_heatmap(df):
    """VIZ 200: Gymnasium Heatmap nach Kreis"""
    gymnasien = df[df['Schulform'].isin(['Gymnasien', 'Gesamtschulen'])].copy()
    
    gym_kreis = gymnasien.groupby(['Kreis', 'Schulform']).agg({
        'Sozialindex': ['mean', 'count']
    }).reset_index()
    
    gym_kreis.columns = ['Kreis', 'Schulform', 'Ø_Sozialindex', 'Anzahl']
    
    # Pivot für Heatmap
    pivot_data = gym_kreis.pivot(index='Kreis', columns='Schulform', values='Ø_Sozialindex')
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='RdYlGn_r',
        hoverongaps=False,
        hovertemplate='<b>%{y}</b><br>%{x}<br>Ø Sozialindex: %{z:.2f}<extra></extra>',
        colorbar=dict(title='Sozialindex')
    ))
    
    fig.update_layout(
        title='Gymnasium/Gesamtschule: Sozialindex-Heatmap nach Kreis<br><sub>Rot = schwierige Bedingungen | Grün = gute Bedingungen</sub>',
        xaxis_title='Schulform',
        yaxis_title='Kreis/Stadt',
        height=1000
    )
    return fig

def create_gymnasium_top20(df):
    """VIZ 201: Top 20 Gymnasien mit besten Bedingungen"""
    gymnasien = df[df['Schulform'].isin(['Gymnasien', 'Gesamtschulen'])].copy()
    top_gym = gymnasien.nsmallest(20, 'Sozialindex')[['Schulname', 'Kreis', 'Sozialindex', 'Schueler_Pro_Lehrkraft', 'Schulform']]
    
    fig = go.Figure(go.Bar(
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
    
    fig.update_layout(
        title='Top 20 Gymnasien/Gesamtschulen mit besten Bedingungen<br><sub>Niedrigster Sozialindex = beste sozioökonomische Bedingungen</sub>',
        xaxis_title='Sozialindex',
        yaxis_title='Schule',
        height=700
    )
    return fig

def create_gym_vs_gesamtschule(df):
    """VIZ 202: Gymnasium vs. Gesamtschule Vergleich"""
    gymnasien = df[df['Schulform'].isin(['Gymnasien', 'Gesamtschulen'])].copy()
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Sozialindex-Verteilung', 'Betreuungsrelation'),
        specs=[[{'type': 'box'}, {'type': 'box'}]]
    )
    
    # Sozialindex
    for schulform in ['Gymnasien', 'Gesamtschulen']:
        data = gymnasien[gymnasien['Schulform'] == schulform]['Sozialindex'].dropna()
        color = '#1f77b4' if schulform == 'Gymnasien' else '#ff7f0e'
        
        fig.add_trace(go.Box(
            y=data,
            name=f'{schulform} (n={len(data)})',
            marker_color=color,
            boxmean='sd',
            hovertemplate='<b>%{fullData.name}</b><br>Sozialindex: %{y:.2f}<extra></extra>'
        ), row=1, col=1)
    
    # Betreuung
    for schulform in ['Gymnasien', 'Gesamtschulen']:
        data = gymnasien[gymnasien['Schulform'] == schulform]['Schueler_Pro_Lehrkraft'].dropna()
        color = '#1f77b4' if schulform == 'Gymnasien' else '#ff7f0e'
        
        fig.add_trace(go.Box(
            y=data,
            name=f'{schulform}',
            marker_color=color,
            boxmean='sd',
            showlegend=False,
            hovertemplate='<b>%{fullData.name}</b><br>Schüler/Lehrer: %{y:.2f}<extra></extra>'
        ), row=1, col=2)
    
    fig.update_yaxes(title_text='Sozialindex', row=1, col=1)
    fig.update_yaxes(title_text='Schüler pro Lehrkraft', row=1, col=2)
    
    fig.update_layout(
        title='Gymnasium vs. Gesamtschule: Direkter Vergleich<br><sub>Vergleich der Rahmenbedingungen zwischen den beiden Schulformen</sub>',
        height=600,
        hovermode='closest'
    )
    return fig

def create_kreis_gymnasium_dichte(df):
    """VIZ 203: Kreis-Analyse Gymnasium-Dichte"""
    gymnasien = df[df['Schulform'].isin(['Gymnasien', 'Gesamtschulen'])].copy()
    
    kreis_gym = gymnasien.groupby('Kreis').agg({
        'Schulname': 'count',
        'Sozialindex': 'mean',
        'Schueler_Pro_Lehrkraft': 'mean',
        'Einkommen_Pro_Einwohner_Euro': 'mean'
    }).reset_index()
    
    kreis_gym.columns = ['Kreis', 'Anzahl_Gymnasien', 'Ø_Sozialindex', 'Ø_Betreuung', 'Ø_Einkommen']
    
    fig = px.scatter(
        kreis_gym,
        x='Anzahl_Gymnasien',
        y='Ø_Sozialindex',
        size='Ø_Einkommen',
        color='Ø_Betreuung',
        hover_name='Kreis',
        hover_data={
            'Anzahl_Gymnasien': True,
            'Ø_Sozialindex': ':.2f',
            'Ø_Betreuung': ':.2f',
            'Ø_Einkommen': ':,.0f'
        },
        color_continuous_scale='RdYlGn_r',
        size_max=30,
        title='Gymnasium-Dichte vs. Sozialindex nach Kreis<br><sub>Größe = Einkommen | Farbe = Betreuungsrelation</sub>',
        labels={
            'Anzahl_Gymnasien': 'Anzahl Gymnasien/Gesamtschulen',
            'Ø_Sozialindex': 'Durchschn. Sozialindex',
            'Ø_Betreuung': 'Ø Schüler/Lehrer',
            'Ø_Einkommen': 'Ø Einkommen'
        }
    )
    
    fig.update_layout(
        height=700
    )
    return fig

#  MAIN APP 
def main():
    # Sidebar Navigation
    st.sidebar.title("📊 Navigation")
    
    app_mode = st.sidebar.radio(
        "Modus auswählen:",
        ["🏠 Übersicht", "📈 Dashboard", "📖 Story"]
    )
    
    # Load data
    df = load_data()
    
    if df is None:
        st.error("❌ Daten konnten nicht geladen werden!")
        return
    
    #  OVERVIEW MODE 
    if app_mode == "🏠 Übersicht":
        st.markdown('<h1 class="main-header">🎓 NRW Bildungsanalyse</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Interaktives Dashboard mit 17 Plotly-Visualisierungen</p>', unsafe_allow_html=True)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏫 Schulen gesamt", f"{len(df):,}")
        with col2:
            st.metric("📍 Kreise/Städte", df['Kreis'].nunique())
        with col3:
            st.metric("🎯 Gymnasien", len(df[df['Schulform'] == 'Gymnasien']))
        with col4:
            st.metric("📚 Schulformen", df['Schulform'].nunique())
        
        st.markdown("---")
        
        # Info boxes
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="info-box">
                <h3>📈 Dashboard-Modus</h3>
                <p>Erkunde alle 17 interaktiven Visualisierungen organisiert nach Kategorien:</p>
                <ul>
                    <li><b>Stadt-Ebene:</b> Korrelationen, Rankings, Vergleiche (VIZ 100-104)</li>
                    <li><b>Gymnasium-Ebene:</b> Spezialisierte Analysen (VIZ 105-107, 200-203)</li>
                    <li><b>Ergänzungen:</b> Schulformen, Extrema, Spreizung (VIZ 01-05)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="info-box">
                <h3>📖 Story-Modus</h3>
                <p>Erlebe die Daten in einer narrativen Präsentation:</p>
                <ul>
                    <li>Scroll-basierte Visualisierung</li>
                    <li>Kontextuelle Erklärungen</li>
                    <li>Highlight wichtiger Erkenntnisse</li>
                    <li>Optimiert für Präsentationen</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Key findings
        st.subheader("🔍 Kernerkenntnisse")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **💰 Einkommenseffekte**
            - Negative Korrelation: Einkommen ↔ Sozialindex
            - Wohlhabendere Regionen: bessere Sozialindizes
            - Unterschiede bis zu 5 Punkte
            """)
        
        with col2:
            st.markdown("""
            **👥 Betreuungsqualität**
            - Ärmere Gebiete: schlechtere Betreuung
            - Unterschiede: 10-12 vs. 13-15 S/L
            - Nachweisbare soziale Ungerechtigkeit
            """)
        
        with col3:
            st.markdown("""
            **🏫 Schulform-Segregation**
            - Gymnasien in wohlhabenderen Kreisen
            - Gesamtschulen in benachteiligten Gebieten
            - Zugang abhängig von sozialer Lage
            """)
        
        # Sozialindex distribution
        st.markdown("---")
        st.subheader("📊 Sozialindex-Verteilung")
        
        si_dist = df['Sozialindex'].value_counts().sort_index()
        
        fig = go.Figure(data=[go.Bar(
            x=si_dist.index,
            y=si_dist.values,
            marker_color='steelblue'
        )])
        
        fig.update_layout(
            title='Verteilung der Schulen nach Sozialindex',
            xaxis_title='Sozialindex',
            yaxis_title='Anzahl Schulen',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Stats
        col1, col2, col3 = st.columns(3)
        with col1:
            si_low = len(df[df['Sozialindex'] <= 3])
            st.info(f"**SI 1-3 (niedrig):** {si_low} Schulen ({si_low/len(df)*100:.1f}%)")
        with col2:
            si_mid = len(df[(df['Sozialindex'] >= 4) & (df['Sozialindex'] <= 6)])
            st.warning(f"**SI 4-6 (mittel):** {si_mid} Schulen ({si_mid/len(df)*100:.1f}%)")
        with col3:
            si_high = len(df[df['Sozialindex'] >= 7])
            st.success(f"**SI 7-9 (hoch):** {si_high} Schulen ({si_high/len(df)*100:.1f}%)")
    
    #  DASHBOARD MODE 
    elif app_mode == "📈 Dashboard":
        st.title("📈 Interaktives Dashboard")
        
        # Category selection
        category = st.sidebar.selectbox(
            "Kategorie wählen:",
            ["Stadt-Ebene (VIZ 100-104)", 
             "Gymnasium-Ebene (VIZ 105-107)",
             "Gymnasium Extended (VIZ 200-203)",
             "Ergänzungen (VIZ 01-05)"]
        )
        
        # Stadt-Ebene
        if category == "Stadt-Ebene (VIZ 100-104)":
            viz = st.sidebar.radio(
                "Visualisierung:",
                ["VIZ 100: Korrelations-Heatmap",
                 "VIZ 101: Einkommen vs. Sozialindex",
                 "VIZ 102: Sozialindex vs. Betreuung",
                 "VIZ 103: Top & Bottom 10 Städte",
                 "VIZ 104: Stadtgröße-Vergleich"]
            )
            
            if "100" in viz:
                st.subheader("VIZ 100: Korrelations-Heatmap")
                st.plotly_chart(create_correlation_heatmap(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - **Negative Korrelation** zwischen Einkommen und Sozialindex (höheres Einkommen = niedrigerer SI)
                    - Betreuungsrelation korreliert positiv mit Sozialindex (schlechtere Betreuung in benachteiligten Gebieten)
                    - Bildungsausgaben zeigen schwächere, aber erkennbare Zusammenhänge
                    """)
            
            elif "101" in viz:
                st.subheader("VIZ 101: Einkommen vs. Sozialindex")
                st.plotly_chart(create_einkommen_sozialindex(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - Wohlhabendere Kreise haben tendenziell **bessere Sozialindizes**
                    - Unterschiede von bis zu **5 Punkten** zwischen reichsten und ärmsten Regionen
                    - Münster, Bonn, Düsseldorf führen bei Einkommen und Sozialindex
                    """)
            
            elif "102" in viz:
                st.subheader("VIZ 102: Sozialindex vs. Betreuungsrelation")
                st.plotly_chart(create_sozialindex_betreuung(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - Sozial benachteiligte Gebiete haben **schlechtere Betreuungsverhältnisse**
                    - 10-12 Schüler/Lehrkraft in wohlhabenden vs. 13-15 in ärmeren Regionen
                    - Verstärkung sozialer Ungleichheit durch strukturelle Unterschiede
                    """)
            
            elif "103" in viz:
                st.subheader("VIZ 103: Top & Bottom 10 Städte")
                st.plotly_chart(create_top_bottom_cities(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - **Top-Städte:** Münster, Bonn, Coesfeld führen mit SI ~2.5-3.0
                    - **Bottom-Städte:** Gelsenkirchen, Duisburg, Herne mit SI ~5.5-6.5
                    - Deutliche regionale Disparitäten sichtbar
                    """)
            
            elif "104" in viz:
                st.subheader("VIZ 104: Stadtgröße-Vergleich")
                st.plotly_chart(create_stadtgroesse_vergleich(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - Kategorisierung basiert auf **Schulanzahl** (nicht Einwohnerzahl)
                    - Sehr große Städte (>120 Schulen) zeigen breitere SI-Streuung
                    - Kleinere Regionen homogener in Sozialstruktur
                    """)
        
        # Gymnasium-Ebene
        elif category == "Gymnasium-Ebene (VIZ 105-107)":
            viz = st.sidebar.radio(
                "Visualisierung:",
                ["VIZ 105: Top & Bottom Gymnasien-Kreise",
                 "VIZ 106: Gymnasium Sozialindex vs. Betreuung",
                 "VIZ 107: Gymnasien pro Kreis"]
            )
            
            if "105" in viz:
                st.subheader("VIZ 105: Top & Bottom Gymnasien-Kreise")
                st.plotly_chart(create_gymnasium_top_bottom(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - **Köln** führt mit über 40 Gymnasien
                    - Ländliche Kreise haben oft nur 1-3 Gymnasien
                    - Zugang zu Gymnasialbildung stark regional unterschiedlich
                    """)
            
            elif "106" in viz:
                st.subheader("VIZ 106: Gymnasium Sozialindex vs. Betreuung")
                st.plotly_chart(create_gymnasium_sozialindex(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - Gymnasien in wohlhabenden Kreisen haben **bessere Betreuung**
                    - Auch innerhalb Gymnasien zeigt sich soziale Segregation
                    - Verstärkung von Bildungsungleichheit
                    """)
            
            elif "107" in viz:
                st.subheader("VIZ 107: Gymnasien pro Kreis")
                st.plotly_chart(create_gymnasium_schulanzahl(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - Städte dominieren Gymnasium-Angebot
                    - Ländliche Regionen deutlich unterversorgt
                    - Mobilität/Pendeln notwendig für Gymnasialzugang
                    """)
        
        # Gymnasium Extended
        elif category == "Gymnasium Extended (VIZ 200-203)":
            st.info("💡 Diese Analysen wurden erstellt, da Abitur-Daten nur Bundesland-Ebene enthalten (nicht schulspezifisch)")
            
            viz = st.sidebar.radio(
                "Visualisierung:",
                ["VIZ 200: Gymnasium Heatmap",
                 "VIZ 201: Top 20 Gymnasium-Kreise",
                 "VIZ 202: Gymnasium vs. Gesamtschule",
                 "VIZ 203: Gymnasium-Dichte Scatterplot"]
            )
            
            if "200" in viz:
                st.subheader("VIZ 200: Gymnasium Heatmap nach Kreis")
                st.plotly_chart(create_gymnasium_heatmap(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - **Regionale Muster:** Gymnasium-Sozialindex variiert stark zwischen Kreisen
                    - **Grüne Bereiche:** Privilegierte Bedingungen in wohlhabenden Kreisen
                    - **Rote Bereiche:** Schwierigere Bedingungen in benachteiligten Regionen
                    - Gesamtschulen zeigen systematisch höhere Sozialindizes
                    """)
            
            elif "201" in viz:
                st.subheader("VIZ 201: Top 20 Gymnasien mit besten Bedingungen")
                st.plotly_chart(create_gymnasium_top20(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - **Niedrigster Sozialindex** = beste sozioökonomische Ausgangsbedingungen
                    - Farbskala zeigt **Betreuungsrelation** (dunkel = besser)
                    - Top-Schulen konzentrieren sich in Münster, Bonn, Düsseldorf-Umland
                    - Elite-Gymnasien haben oft SI < 2.0
                    """)
            
            elif "202" in viz:
                st.subheader("VIZ 202: Gymnasium vs. Gesamtschule - Direkter Vergleich")
                st.plotly_chart(create_gym_vs_gesamtschule(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - **Gymnasien:** Median SI ~3.5, bessere Betreuung (~11-12 S/L)
                    - **Gesamtschulen:** Median SI ~5.0, schlechtere Betreuung (~13-14 S/L)
                    - Systematische **Segregation** zwischen Schulformen
                    - Gesamtschulen übernehmen sozial schwierigere Schülerschaft
                    """)
            
            elif "203" in viz:
                st.subheader("VIZ 203: Gymnasium-Dichte vs. Sozialindex")
                st.plotly_chart(create_kreis_gymnasium_dichte(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - **Bubble-Größe:** Einkommen pro Einwohner
                    - **Farbe:** Betreuungsrelation (grün = besser, rot = schlechter)
                    - Kreise mit vielen Gymnasien haben tendenziell **bessere Sozialindizes**
                    - Wohlhabende Großstädte (große grüne Bubbles) dominieren
                    - Ländliche Regionen mit wenigen Gymnasien oft benachteiligt
                    """)
        
        # Ergänzungen
        else:  # Ergänzungen (VIZ 01-05)
            viz = st.sidebar.radio(
                "Visualisierung:",
                ["VIZ 01: Schulformen Boxplot",
                 "VIZ 02: Extrema-Vergleich",
                 "VIZ 03: Gymnasien-Konzentration",
                 "VIZ 04: Spreizungs-Ranking",
                 "VIZ 05: Schulformen Donut"]
            )
            
            if "01" in viz:
                st.subheader("VIZ 01: Schulformen Boxplot")
                st.plotly_chart(create_schulformen_boxplot(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - **Gymnasien** haben deutlich bessere durchschnittliche Sozialindizes
                    - **Gesamtschulen** und **Sekundarschulen** in sozial schwierigeren Lagen
                    - Schulformsegregation entlang sozialer Linien
                    """)
            
            elif "02" in viz:
                st.subheader("VIZ 02: Extrema-Vergleich")
                st.plotly_chart(create_extrema_comparison(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - Große **Spreizung** innerhalb einzelner Kreise
                    - Unterschiede von bis zu 6-7 SI-Punkten innerhalb eines Kreises
                    - Hinweis auf kleinräumige Segregation
                    """)
            
            elif "03" in viz:
                st.subheader("VIZ 03: Gymnasien-Konzentration")
                st.plotly_chart(create_gymnasium_concentration(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - Einige Kreise haben über **30% Gymnasien-Anteil**
                    - Andere Regionen unter 10%
                    - Zugang zu höherer Bildung regional stark unterschiedlich
                    """)
            
            elif "04" in viz:
                st.subheader("VIZ 04: Spreizungs-Ranking")
                st.plotly_chart(create_spreizung_ranking(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - Große Städte zeigen **höchste Standardabweichungen**
                    - Indikator für soziale Heterogenität
                    - Mischung aus privilegierten und benachteiligten Schulen
                    """)
            
            elif "05" in viz:
                st.subheader("VIZ 05: Schulformen Donut")
                st.plotly_chart(create_schulformen_donut(df), use_container_width=True)
                with st.expander("ℹ️ Interpretation"):
                    st.write("""
                    - **Grundschulen** dominieren (>50% aller Schulen)
                    - Gymnasien und Gesamtschulen je ~20%
                    - Vielfältiges Schulformangebot in NRW
                    """)
    
    #  STORY MODE 
    else:  # Story Mode
        st.title("📖 NRW Bildungsanalyse Story")
        
        st.markdown("""
        ## 🎓 Bildung und soziale Ungleichheit in Nordrhein-Westfalen
        
        Diese Analyse untersucht **4.142 Schulen** aus **53 Kreisen und kreisfreien Städten** in NRW
        und deckt strukturelle Zusammenhänge zwischen Einkommen, Sozialindex und Bildungsqualität auf.
        """)
        
        st.markdown("---")
        
        # Chapter 1
        st.header("1️⃣ Die Datenbasis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.plotly_chart(create_correlation_heatmap(df), use_container_width=True)
        
        with col2:
            st.markdown("""
            ### Kernzusammenhänge
            
            Die Korrelationsmatrix zeigt:
            
            - ⚠️ **Negative Korrelation** zwischen Einkommen und Sozialindex
            - 📉 Ärmere Regionen = höherer Sozialindex (schlechtere soziale Lage)
            - 👥 Schlechtere Betreuungsrelationen in benachteiligten Gebieten
            """)
        
        st.markdown("---")
        
        # Chapter 2
        st.header("2️⃣ Regionale Disparitäten")
        
        st.plotly_chart(create_einkommen_sozialindex(df), use_container_width=True)
        
        st.markdown("""
        ### 💰 Der Einkommenseffekt
        
        - **Münster, Bonn, Düsseldorf:** Hohe Einkommen (>30.000 €/Einwohner), niedrige Sozialindizes (~2.5)
        - **Gelsenkirchen, Duisburg, Herne:** Niedrige Einkommen (<25.000 €), hohe Sozialindizes (~6.0)
        - **Unterschied:** Bis zu **5 Sozialindex-Punkte** zwischen reichsten und ärmsten Regionen
        """)
        
        st.markdown("---")
        
        # Chapter 3
        st.header("3️⃣ Strukturelle Benachteiligung")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(create_sozialindex_betreuung(df), use_container_width=True)
        
        with col2:
            st.plotly_chart(create_top_bottom_cities(df), use_container_width=True)
        
        st.markdown("""
        ### 👥 Betreuung und Ressourcen
        
        - **Wohlhabende Kreise:** 10-12 Schüler pro Lehrkraft
        - **Ärmere Kreise:** 13-15 Schüler pro Lehrkraft
        - **Fazit:** Sozial benachteiligte Schüler erhalten weniger individuelle Betreuung
        """)
        
        st.markdown("---")
        
        # Chapter 4
        st.header("4️⃣ Schulform-Segregation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(create_schulformen_boxplot(df), use_container_width=True)
        
        with col2:
            st.plotly_chart(create_gymnasium_concentration(df), use_container_width=True)
        
        st.markdown("""
        ### 🏫 Ungleicher Zugang zu Bildung
        
        - **Gymnasien** konzentrieren sich in wohlhabenden Kreisen
        - **Gesamtschulen** überproportional in benachteiligten Gebieten
        - Gymnasium-Anteil: **5-30%** je nach Region
        - **Konsequenz:** Zugang zu höherer Bildung abhängig vom Wohnort
        """)
        
        st.markdown("---")
        
        # Conclusion
        st.header("🎯 Fazit")
        
        st.success("""
        ### Kernerkenntnisse der Analyse:
        
        1. **Strukturelle Ungleichheit:** Sozioökonomischer Status determiniert Bildungschancen
        2. **Ressourcen-Segregation:** Benachteiligte Schulen erhalten weniger Betreuung
        3. **Regionale Disparitäten:** Bis zu 5 Punkte Unterschied im Sozialindex
        4. **Schulform-Segregation:** Gymnasium-Zugang abhängig vom Wohnort
        5. **Handlungsbedarf:** Gezielte Förderung benachteiligter Regionen erforderlich
        """)
        
        st.info("""
        💡 **Politische Implikationen:**
        - Erhöhung der Bildungsausgaben in benachteiligten Regionen
        - Verbesserung der Betreuungsrelationen in Problemvierteln
        - Förderung schulischer Diversität in allen Kreisen
        - Abbau struktureller Zugangsbarrieren zu Gymnasien
        """)
    
    # Footer
    st.markdown("---")
    st.caption("📊 TechLabs Data Science Projekt Gruppe 4")
    st.caption("Andreas Ahrens, Franka Eberhardt, Chantal Reerink, Serhat Karaarslan")

if __name__ == "__main__":
    main()
