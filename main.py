import streamlit as st
from fredapi import get_fred_data
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go


def get_index():
    PARAMS  = {
        'id': ['SOFR_IORB', 'DGS1MO_RRPONTSYAWARD', 'WLCFLL_WORAL', 'WALCL_WDTGAL_WLRRAL'],
        'start_date': ['2024-01-01'] * 4,
        'end_date': [datetime.today().strftime('%Y-%m-%d')] * 4,
        'transform': ['', '', 'chg', 'chg'],
        'formula': ['a-b', 'a-b', 'a+b', 'a-b-c']
        }

    df = get_fred_data(**PARAMS)
    df = df.ffill().bfill()

    df["observation_date"] = pd.to_datetime(df["observation_date"])
    df = df.set_index("observation_date")

    cols_daily  = ["SOFR_IORB", "DGS1MO_RRPONTSYAWARD"]
    cols_weekly = ["WLCFLL_CHG_WORAL_CHG", "WALCL_CHG_WDTGAL_CHG_WLRRAL_CHG"]

    # 1. Daily → diff abs
    for col in cols_daily:
            df[f"{col}_move"] = df[col].diff().abs()

    # 2. Weekly → abs
    for col in cols_weekly:
        df[f"{col}_move"] = df[col].abs()

    # 3. Rolling Z-score
    move_cols = [c for c in df.columns if c.endswith("_move")]

    for col in move_cols:
        mean = df[col].rolling(90, min_periods=10).mean()
        std  = df[col].rolling(90, min_periods=10).std()
        df[f"{col}_z"] = (df[col] - mean) / std

    # 4. Rank → 0–100
    z_cols = [c for c in df.columns if c.endswith("_z")]

    for col in z_cols:
        df[f"{col}_score"] = df[col].rank(pct=True) * 100

    # 5. FINAL INDEX: usar correctamente las columnas *_score
    score_cols = [c for c in df.columns if c.endswith("_score")]

    df["fun_index"] = df[score_cols].mean(axis=1)

    return df['fun_index']


# Streamlit Config
st.set_page_config(page_title="Federal Reserve Fun & Boredom Index", layout="wide", page_icon="📊")

# Custom CSS - Responsive
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap');
    
    * {
        font-family: 'Roboto Mono', 'Courier New', monospace !important;
    }
    
    .stApp {
        background-color: #000000;
    }
    
    /* Responsive title */
    .main-title {
        text-align: center;
        font-size: clamp(1.5rem, 5vw, 3rem);
        font-weight: bold;
        margin-bottom: 1.5rem;
        padding: 0 1rem;
    }
    
    /* Responsive section titles - MÁS PEQUEÑOS */
    .section-title {
        text-align: center;
        font-size: clamp(0.85rem, 2.5vw, 1rem);
        font-weight: bold;
        margin-bottom: 0.75rem;
        color: #d4d4d8;
    }
    
    .metric-container {
        text-align: center;
        padding: 0.5rem;
    }
    
    .metric-container-horizontal {
        text-align: center;
        padding: 0.5rem;
        display: inline-block;
        width: 50%;
    }
    
    .metric-label {
        color: #a1a1aa;
        font-size: clamp(0.65rem, 2vw, 0.75rem);
        margin-bottom: 0.25rem;
    }
    
    .metric-value {
        font-size: clamp(1.5rem, 4vw, 2rem);
        font-weight: bold;
    }
    
    .horizontal-metrics {
        display: flex;
        justify-content: space-around;
        margin-top: 0.5rem;
    }
    
    /* Mobile adjustments */
    @media (max-width: 768px) {
        .stApp {
            padding: 0.5rem;
        }
        
        .main-title {
            margin-bottom: 1rem;
        }
        
        .section-title {
            margin-bottom: 0.5rem;
        }
        
        /* Stack columns on mobile */
        [data-testid="column"] {
            width: 100% !important;
            flex: 100% !important;
            max-width: 100% !important;
        }
        
        /* Reduce padding on mobile */
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def get_color_for_value(value):
    if value <= 20:
        return '#ef4444'
    elif value <= 40:
        return '#f97316'
    elif value <= 60:
        return '#eab308'
    elif value <= 80:
        return '#84cc16'
    else:
        return '#22c55e'
    
# Título
st.markdown('<h1 class="main-title">FEDERAL RESERVE FUN & BOREDOM INDEX</h1>', unsafe_allow_html=True)

# Cargar datos
@st.cache_data(ttl=3600)
def load_data():
    df_index = get_index()
    return df_index

df_index = load_data()

# Layout responsive - stack en móvil
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<h2 class="section-title">Current Index</h2>', unsafe_allow_html=True)
    
    current_value = df_index.iloc[-1]
    
    # Gauge semicircular
    fig_gauge = go.Figure()
    
    fig_gauge.add_trace(go.Indicator(
        mode="gauge+number",
        value=current_value,
        number={'font': {'size': 60, 'family': 'Cascadia Code'}},
        gauge={
            'axis': {
                'range': [0, 100],
                'tickwidth': 2,
                'tickcolor': "#52525b",
                'tickfont': {'family': 'Cascadia Code', 'color': '#71717a', 'size': 10}
            },
            'bar': {'color': "white", 'thickness': 0.3},
            'bgcolor': "black",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 20], 'color': '#ef4444'},
                {'range': [20, 40], 'color': '#f97316'},
                {'range': [40, 60], 'color': '#eab308'},
                {'range': [60, 80], 'color': '#84cc16'},
                {'range': [80, 100], 'color': '#22c55e'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 0},
                'thickness': 1,
                'value': current_value
            }
        }
    ))
    
    fig_gauge.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='black',
        plot_bgcolor='black',
        font={'family': 'Cascadia Code', 'color': 'white'}
    )
    
    st.plotly_chart(fig_gauge, width='stretch')
    
    # Historical Values - Nuevo layout
    st.markdown('<h2 class="section-title">Historical Values</h2>', unsafe_allow_html=True)
    
    yesterday = df_index.iloc[-2]
    last_week = df_index.iloc[-7]
    last_month = df_index.iloc[-30]
    
    # Yesterday arriba centrado
    color_yesterday = get_color_for_value(yesterday)
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-label">Yesterday</div>
        <div class="metric-value" style="color: {color_yesterday};">{yesterday:.1f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Last Week y Last Month en horizontal
    color_last_week = get_color_for_value(last_week)
    color_last_month = get_color_for_value(last_month)
    
    st.markdown(f"""
    <div class="horizontal-metrics">
        <div class="metric-container-horizontal">
            <div class="metric-label">Last Week</div>
            <div class="metric-value" style="color: {color_last_week};">{last_week:.1f}</div>
        </div>
        <div class="metric-container-horizontal">
            <div class="metric-label">Last Month</div>
            <div class="metric-value" style="color: {color_last_month};">{last_month:.1f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown('<h2 class="section-title">Historical Chart</h2>', unsafe_allow_html=True)
    
    timeframe = st.radio("Timeframe", ["30d", "6m", "1y", "All"], horizontal=True, label_visibility="collapsed")
    
    if timeframe == "30d":
        plot_data = df_index.iloc[-30:]
    elif timeframe == "6m":
        plot_data = df_index.iloc[-180:]
    elif timeframe == "1y":
        plot_data = df_index.iloc[-365:]
    else:
        plot_data = df_index
    
    # Crear gráfico con segmentos de colores
    fig = go.Figure()
    
    # Agregar segmentos con colores según el valor
    for i in range(len(plot_data) - 1):
        segment_data = plot_data.iloc[i:i+2]
        avg_value = segment_data.values.mean()
        color = get_color_for_value(avg_value)
        
        fig.add_trace(go.Scatter(
            x=segment_data.index,
            y=segment_data.values,
            mode='lines',
            line=dict(color=color, width=3),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Agregar una línea invisible para el hover
    fig.add_trace(go.Scatter(
        x=plot_data.index,
        y=plot_data.values,
        mode='lines',
        line=dict(color='rgba(0,0,0,0)', width=0),
        name='Federal Reserve Fun & Boredom Index',
        hovertemplate='%{y:.1f}<extra></extra>'
    ))
    
    fig.update_layout(
        showlegend=False,
        height=450,
        hovermode='x unified',
        yaxis=dict(
            range=[0, 100], 
            gridcolor='#27272a',
            tickfont={'size': 10}
        ),
        xaxis=dict(
            gridcolor='#27272a',
            tickfont={'size': 10}
        ),
        paper_bgcolor='black',
        plot_bgcolor='black',
        font={'family': 'Cascadia Code', 'color': '#71717a'},
        margin=dict(l=40, r=20, t=20, b=40)
    )
    
    st.plotly_chart(fig, width='stretch')

# Footer informativo (opcional)
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #71717a; font-size: 0.75rem; padding: 1rem;">
    <p>
    The Federal Reserve Fun & Boredom Index measures market activity and volatility based on interest rate spreads, 
    Fed balance sheet changes, and liquidity flows.
    </p>
    <p>
    This website is NOT a financial, investment, legal, or tax advice. This website is not affiliated with or related to the Federal Reserve.
    </p>
</div>
""", unsafe_allow_html=True)
