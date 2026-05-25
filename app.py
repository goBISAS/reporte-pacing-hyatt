import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Hyatt Regency Cartagena - Dashboard",
    page_icon="hyatt_logo.png",
    layout="wide"
)

# ESTILOS PREMIUM (Barra lateral y Branding)
st.markdown("""
    <style>
    .main { background-color: #0d0d0d; }
    [data-testid="stMetricValue"] { font-size: 32px; color: #d6b58e !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #f5f5f5 !important; }
    h1, h2, h3 { color: #ffffff; font-family: 'Georgia', serif; }
    .stSidebar { background-color: #1a1a1a; border-right: 1px solid #333; }
    .stPlotlyChart { border: 1px solid #333; border-radius: 8px; background-color: #1a1a1a; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES ---
def get_csv_url(url):
    return url.replace('/edit?gid=', '/export?format=csv&gid=').split('#')[0]

def encontrar_columna(lista_cols, palabras_clave):
    for col in lista_cols:
        if all(p.lower() in str(col).lower() for p in palabras_clave):
            return col
    return None

# --- SIDEBAR (IDENTIDAD) ---
with st.sidebar:
    st.image("hyatt_logo.png", use_container_width=True)
    st.markdown("---")
    st.markdown("### Control de Paid Media")
    st.write("Propiedad: **Cartagena de Indias**")
    st.info(f"Día actual: {datetime.now().day}")

# --- LOGICA DE DATOS ---
url_pacing = "https://docs.google.com/spreadsheets/d/1Ah5nzWzix7HXOhrLvRBRYRhHsZYX5tULKG9jF7sNer0/edit?gid=1262726872"

try:
    df_header = pd.read_csv(get_csv_url(url_pacing), nrows=5, header=None)
    presupuesto_mensual = df_header.iloc[1, 2] 

    df_pacing = pd.read_csv(get_csv_url(url_pacing), skiprows=5)
    df_pacing.columns = [str(c).strip() for c in df_pacing.columns]

    col_medio = 'Platform' if 'Platform' in df_pacing.columns else df_pacing.columns[0]
    col_spend = 'Spend (COP)'
    col_tipo = encontrar_columna(df_pacing.columns, ['Official', 'Conversions'])
    
    df_campañas = df_pacing[(df_pacing['Campaign'].notna()) & (~df_pacing['Campaign'].str.contains('TOTAL', na=False))].copy()
    df_campañas[col_spend] = pd.to_numeric(df_campañas[col_spend].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce').fillna(0)

    # CÁLCULO DE TOTALES Y ETIQUETAS
    resumen_plataformas = df_campañas.groupby(col_medio)[col_spend].sum()
    mapa_nombres = {plat: f"{plat} (${tot:,.0f})" for plat, tot in resumen_plataformas.items()}
    df_campañas['Medio_Labels'] = df_campañas[col_medio].map(mapa_nombres)
    gasto_total_calculado = df_campañas[col_spend].sum()
    
    col_fecha = encontrar_columna(df_pacing.columns, ['Actualizacion', 'Pacing']) or 'Actualización Pacing'
    fecha_update = df_pacing[col_fecha].dropna().iloc[-1]
    
    # --- INTERFAZ ---
    st.title("🏨 Dashboard Gerencial de Rendimiento")
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Presupuesto Mensual", f"{presupuesto_mensual}")
    with c2: st.metric("Inversión Ejecutada", f"${gasto_total_calculado:,.0f}")
    with c3: st.metric("Día de Medición", f"{datetime.now().day}")

    st.success(f"✅ Sincronizado con Google Sheets: {fecha_update}")
    st.divider()

    st.header("📊 Distribución por Canal y Objetivo")
    df_plot = df_campañas[df_campañas[col_spend] > 0]
    
    if not df_plot.empty:
        fig = px.treemap(df_plot, path=['Medio_Labels', col_tipo], values=col_spend, color=col_spend,
                         color_continuous_scale=['#d6b58e', '#5b3f8e'])
        fig.update_traces(texttemplate="<b>%{label}</b><br>$%{value:,.0f}", hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<extra></extra>", textposition="middle center")
        fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("📝 Detalle de Campañas"):
        col_res = encontrar_columna(df_campañas.columns, ['Platform', 'Conversions'])
        col_cpa = encontrar_columna(df_campañas.columns, ['CPA'])
        df_display = df_campañas[[col_medio, 'Campaign', col_tipo, col_res, col_cpa]].rename(columns={col_medio: 'Medio', 'Campaign': 'Campaña', col_tipo: 'Objetivo', col_res: 'Resultados', col_cpa: 'CPA'})
        st.dataframe(df_display.sort_values(by='Medio'), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")

st.caption(f"Hyatt Regency Cartagena | Strategic Analytics by goBIG")
