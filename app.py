import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import urllib.parse
import re

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Hyatt Regency Cartagena - Dashboard",
    page_icon="hyatt_logo.png",
    layout="wide"
)

# ESTILOS PREMIUM
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

# --- LÓGICA HISTÓRICA DE MESES ---
def obtener_meses_disponibles():
    meses_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    start_year, start_month = 2026, 5
    now = datetime.now()
    lista = []
    ano, mes = start_year, start_month
    while (ano < now.year) or (ano == now.year and mes <= now.month):
        lista.append(f"{meses_es[mes-1]} {ano}")
        if mes == 12:
            mes = 1
            ano += 1
        else:
            mes += 1
    return list(reversed(lista))

def get_csv_url_by_sheet(url, sheet_name):
    try:
        id_publicacion = url.split("/d/")[1].split("/")[0]
        sheet_enc = urllib.parse.quote(sheet_name)
        return f"https://docs.google.com/spreadsheets/d/{id_publicacion}/gviz/tq?tqx=out:csv&sheet={sheet_enc}"
    except:
        return url

def encontrar_columna(lista_cols, palabras_clave):
    for col in lista_cols:
        if all(p.lower() in str(col).lower() for p in palabras_clave):
            return col
    return None

# --- SIDEBAR ---
meses_disponibles = obtener_meses_disponibles()
with st.sidebar:
    st.image("hyatt_logo.png", use_container_width=True)
    st.markdown("---")
    st.markdown("### Control de Paid Media")
    st.write("Propiedad: **Cartagena de Indias**")
    mes_seleccionado = st.selectbox("📅 Seleccione el Mes de Reporte:", options=meses_disponibles)

# --- CONEXIÓN DINÁMICA ---
url_base = "https://docs.google.com/spreadsheets/d/1Ah5nzWzix7HXOhrLvRBRYRhHsZYX5tULKG9jF7sNer0/"
url_pacing = get_csv_url_by_sheet(url_base, mes_seleccionado)

try:
    # LECTURA DE RADAR
    df_raw = pd.read_csv(url_pacing, header=None)
    
    # 1. RADAR: Buscar la cabecera de la tabla de campañas
    idx_header = None
    for i, row in df_raw.iterrows():
        valores_fila = row.dropna().astype(str).tolist()
        if any('Campaign' in val or 'Campaña' in val for val in valores_fila):
            idx_header = i
            break
    
    if idx_header is None:
        st.error(f"No se encontró la fila de encabezados con la columna 'Campaign'. Verifica que la pestaña '{mes_seleccionado}' tenga los datos correctos.")
        st.stop()

    # 2. RADAR: Buscar el Presupuesto
    presupuesto_mensual = "$0"
    for i, row in df_raw.iloc[:idx_header].iterrows():
        for col_idx, val in enumerate(row.dropna().astype(str)):
            if 'budget' in val.lower() or 'presupuesto' in val.lower():
                if col_idx + 1 < len(row):
                    presupuesto_mensual = row.iloc[col_idx + 1]
                break

    # 3. CONSTRUIR TABLA LIMPIA Y REPARAR ENCABEZADOS (AQUÍ ESTÁ LA SOLUCIÓN)
    df_pacing = df_raw.iloc[idx_header + 1:].copy()
    
    # Usamos Expresiones Regulares (re) para limpiar saltos de línea (\n) y dobles espacios ocultos
    df_pacing.columns = [re.sub(r'\s+', ' ', str(c)).strip() for c in df_raw.iloc[idx_header]]

    # Detección ultra-flexible de columnas
    col_medio = 'Channel' if 'Channel' in df_pacing.columns else ('Platform' if 'Platform' in df_pacing.columns else df_pacing.columns[0])
    
    # Búsqueda dinámica de la columna de Gasto por si tiene un nombre ligeramente distinto
    col_spend = 'Spend (COP)' # Default
    for c in df_pacing.columns:
        if 'spend' in c.lower() or 'gasto' in c.lower() or 'inversión' in c.lower():
            col_spend = c
            break
            
    col_tipo = encontrar_columna(df_pacing.columns, ['Official', 'Conversions'])
    
    # Filtro de filas y conversión segura
    df_campañas = df_pacing[df_pacing['Campaign'].notna()].copy()
    df_campañas['Campaign'] = df_campañas['Campaign'].astype(str)
    
    df_campañas = df_campañas[
        (~df_campañas['Campaign'].str.contains('TOTAL')) & 
        (~df_campañas['Campaign'].str.contains('Total')) & 
        (df_campañas['Campaign'] != 'Campaign')
    ].copy()
    
    df_campañas[col_medio] = df_campañas[col_medio].replace(['', ' ', 'nan', 'NaN'], pd.NA).ffill()
    df_campañas[col_spend] = pd.to_numeric(df_campañas[col_spend].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce').fillna(0)

    # Agrupaciones
    resumen_plataformas = df_campañas.groupby(col_medio)[col_spend].sum()
    mapa_nombres = {plat: f"{plat} (${tot:,.0f})" for plat, tot in resumen_plataformas.items()}
    df_campañas['Med
