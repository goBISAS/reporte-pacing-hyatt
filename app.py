import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Hyatt Regency Cartagena - Analytics",
    page_icon="🏨",
    layout="wide"
)

# ESTILOS PERSONALIZADOS
st.markdown("""
    <style>
    .main { background-color: #0d0d0d; }
    [data-testid="stMetricValue"] { font-size: 32px; color: #d6b58e !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #f5f5f5 !important; }
    h1, h2, h3 { color: #ffffff; font-family: 'Georgia', serif; }
    .stPlotlyChart { border: 1px solid #333; border-radius: 8px; padding: 10px; background-color: #1a1a1a; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE AYUDA ---
def get_csv_url(url):
    return url.replace('/edit?gid=', '/export?format=csv&gid=').split('#')[0]

def encontrar_columna(lista_cols, palabras_clave):
    for col in lista_cols:
        if all(p.lower() in str(col).lower() for p in palabras_clave):
            return col
    return None

# --- CONFIGURACIÓN DE DATOS ---
url_pacing = "https://docs.google.com/spreadsheets/d/1Ah5nzWzix7HXOhrLvRBRYRhHsZYX5tULKG9jF7sNer0/edit?gid=1262726872"

try:
    # 1. CARGA DE DATOS
    df_header = pd.read_csv(get_csv_url(url_pacing), nrows=5, header=None)
    presupuesto_mensual = df_header.iloc[1, 2] 

    df_pacing = pd.read_csv(get_csv_url(url_pacing), skiprows=5)
    df_pacing.columns = [str(c).strip() for c in df_pacing.columns]

    # 2. MÉTRICAS DE CABECERA
    fila_total = df_pacing[df_pacing['Campaign'].str.contains('TOTAL', na=False)].iloc[0]
    gasto_total = fila_total['Spend (COP)']
    
    col_fecha = encontrar_columna(df_pacing.columns, ['Actualizacion', 'Pacing']) or 'Actualización Pacing'
    fecha_update = df_pacing[col_fecha].dropna().iloc[-1]
    
    st.title("🏨 Dashboard de Rendimiento: Hyatt Regency")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Presupuesto Mensual", f"{presupuesto_mensual}")
    with c2:
        st.metric("Inversión Ejecutada", f"{gasto_total}")
    with c3:
        st.metric("Día del Mes", f"{datetime.now().day}")

    st.info(f"📅 Última sincronización: {fecha_update}")
    st.divider()

    # 3. FILTRADO PARA GRÁFICAS Y TABLAS
    df_campañas = df_pacing[
        (df_pacing['Campaign'].notna()) & 
        (~df_pacing['Campaign'].str.contains('TOTAL', na=False))
    ].copy()

    # Identificación de columnas
    col_medio = 'Platform' if 'Platform' in df_campañas.columns else df_campañas.columns[0]
    col_tipo = encontrar_columna(df_campañas.columns, ['Official', 'Conversions'])
    col_spend = 'Spend (COP)'

    # --- LIMPIEZA DE DATOS FINANCIEROS PARA LA GRÁFICA ---
    # Quitamos símbolos de dólar y comas, y convertimos a número real
    df_campañas[col_spend] = pd.to_numeric(
        df_campañas[col_spend].astype(str).str.replace(r'[$,]', '', regex=True), 
        errors='coerce'
    ).fillna(0)

    # --- 4. GRÁFICO DE ÁRBOL (TREEMAP) ---
    st.header("📊 Distribución de Inversión")
    
    # Filtramos para que solo intente graficar campañas que tengan gasto mayor a 0
    df_plot = df_campañas[df_campañas[col_spend] > 0]
    
    if not df_plot.empty:
        fig = px.treemap(
            df_plot, 
            path=[col_medio, col_tipo], 
            values=col_spend,
            color=col_spend,
            color_continuous_scale=['#d6b58e', '#5b3f8e'], 
            title="Inversión por Medio y Objetivo Estratégico"
        )
        
        fig.update_layout(
            margin=dict(t=50, l=10, r=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aún no hay datos numéricos de gasto registrados para graficar.")

    # 5. TABLA DE DETALLES
    with st.expander("📝 Ver desglose detallado de campañas"):
        col_res = encontrar_columna(df_campañas.columns, ['Platform', 'Conversions'])
        col_cpa = encontrar_columna(df_campañas.columns, ['CPA'])
        
        cols_finales = [col_medio, 'Campaign', col_tipo, col_res, col_cpa]
        nombres = {col_medio: 'Medio', 'Campaign': 'Campaña', col_tipo: 'Objetivo', col_res: 'Resultados', col_cpa: 'CPA'}
        
        # Para la tabla, devolvemos el formato de la columna original si lo deseas, o la dejamos limpia. 
        # En este caso mostramos el resto de variables.
        df_display = df_campañas[cols_finales].rename(columns=nombres)
        st.dataframe(df_display.sort_values(by='Medio'), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error técnico en visualización: {e}")

st.caption(f"Hyatt Regency Cartagena | Strategic Analytics by goBIG")
