import streamlit as st
import pandas as pd
from datetime import datetime

# CONFIGURACIÓN DE PÁGINA (Identidad Hyatt Regency)
st.set_page_config(
    page_title="Hyatt Regency Cartagena - Control de Paid Media",
    page_icon="🏨",
    layout="wide"
)

# ESTILOS PERSONALIZADOS (Corrección de visibilidad y colores premium)
st.markdown("""
    <style>
    .main { background-color: #0d0d0d; }
    /* Ajuste de color para métricas: Oro Hyatt para máxima visibilidad */
    [data-testid="stMetricValue"] { font-size: 32px; color: #d6b58e !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #f5f5f5 !important; font-size: 18px; }
    h1, h2 { color: #ffffff; font-family: 'Georgia', serif; letter-spacing: 1px; }
    .stDataFrame { border: 1px solid #d6b58e; border-radius: 4px; }
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
cliente = "Hyatt Regency Cartagena"

st.title(f"🏨 Dashboard de Rendimiento: {cliente}")

try:
    # 1. CARGA DE DATOS
    df_header = pd.read_csv(get_csv_url(url_pacing), nrows=5, header=None)
    presupuesto_mensual = df_header.iloc[1, 2] 

    df_pacing = pd.read_csv(get_csv_url(url_pacing), skiprows=5)
    df_pacing.columns = [str(c).strip() for c in df_pacing.columns]

    # 2. MÉTRICAS DE CABECERA (Luminosas)
    fila_total = df_pacing[df_pacing['Campaign'].str.contains('TOTAL', na=False)].iloc[0]
    gasto_total = fila_total['Spend (COP)']
    
    col_fecha = encontrar_columna(df_pacing.columns, ['Actualizacion', 'Pacing']) or 'Actualización Pacing'
    fecha_update = df_pacing[col_fecha].dropna().iloc[-1]
    dias_hoy = datetime.now().day

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Presupuesto Mensual", f"{presupuesto_mensual}")
    with c2:
        st.metric("Inversión Ejecutada", f"{gasto_total}")
    with c3:
        st.metric("Día de Medición", f"{dias_hoy}")

    st.info(f"📅 Última sincronización de datos: {fecha_update}")
    st.divider()

    # 3. SECCIÓN DE RENDIMIENTO POR MEDIO (Agrupado)
    st.header("🎯 Análisis por Medio y Campaña")
    
    df_campañas = df_pacing[
        (df_pacing['Campaign'].notna()) & 
        (~df_pacing['Campaign'].str.contains('TOTAL', na=False))
    ].copy()

    if not df_campañas.empty:
        # Buscamos columnas clave incluyendo la Columna A (Platform/Medio)
        col_medio = 'Platform' if 'Platform' in df_campañas.columns else df_campañas.columns[0]
        col_res = encontrar_columna(df_campañas.columns, ['Platform', 'Conversions'])
        col_cpa = encontrar_columna(df_campañas.columns, ['CPA'])
        col_tipo = encontrar_columna(df_campañas.columns, ['Official', 'Conversions'])
        
        # Selección y renombrado para reporte gerencial
        cols_finales = [col_medio, 'Campaign']
        nombres_renombrar = {col_medio: 'Medio', 'Campaign': 'Campaña'}
        
        if col_tipo:
            cols_finales.append(col_tipo)
            nombres_renombrar[col_tipo] = 'Objetivo'
        if col_res:
            cols_finales.append(col_res)
            nombres_renombrar[col_res] = 'Resultados'
        if col_cpa:
            cols_finales.append(col_cpa)
            nombres_renombrar[col_cpa] = 'Costo x Res.'
            
        df_display = df_campañas[cols_finales].rename(columns=nombres_renombrar)
        
        # Ordenamos por Medio para que queden agrupadas (Facebook, Google, etc.)
        df_display = df_display.sort_values(by='Medio')
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.warning(f"No se detectan tácticas activas para {cliente}.")

except Exception as e:
    st.error(f"Error de visualización: {e}")

st.caption(f"Hyatt Regency Cartagena | Strategic Pacing by goBIG | {datetime.now().strftime('%Y')}")
