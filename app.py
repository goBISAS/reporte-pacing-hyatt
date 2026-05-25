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
    df_raw = pd.read_csv(url_pacing, header=None)
    
    # 1. RADAR: Buscar encabezados
    idx_header = None
    for i, row in df_raw.iterrows():
        valores_fila = row.dropna().astype(str).tolist()
        if any('Campaign' in val or 'Campaña' in val for val in valores_fila):
            idx_header = i
            break
    
    if idx_header is None:
        st.error(f"No se encontró la columna 'Campaign'. Verifica la pestaña '{mes_seleccionado}'.")
        st.stop()

    # 2. RADAR: Buscar Presupuesto
    presupuesto_mensual = "$0"
    for i, row in df_raw.iloc[:idx_header].iterrows():
        for col_idx, val in enumerate(row.dropna().astype(str)):
            if 'budget' in val.lower() or 'presupuesto' in val.lower():
                if col_idx + 1 < len(row):
                    presupuesto_mensual = str(row.iloc[col_idx + 1])
                break

    # 3. LIMPIEZA DE ENCABEZADOS (Anti-Float/NaN)
    df_pacing = df_raw.iloc[idx_header + 1:].copy()
    columnas_crudas = df_raw.iloc[idx_header].tolist()
    
    columnas_limpias = []
    for i, c in enumerate(columnas_crudas):
        val = re.sub(r'\s+', ' ', str(c)).strip() # str(c) bloquea el error de float
        if val.lower() in ['nan', 'none', '']:
            val = f"Columna_Oculta_{i}"
        columnas_limpias.append(val)
        
    df_pacing.columns = columnas_limpias

    # 4. IDENTIFICACIÓN DE COLUMNAS
    col_medio = 'Channel' if 'Channel' in df_pacing.columns else ('Platform' if 'Platform' in df_pacing.columns else df_pacing.columns[0])
    
    col_spend = 'Spend (COP)' 
    for i, c in enumerate(df_pacing.columns):
        if 'spend' in str(c).lower() or 'gasto' in str(c).lower() or 'inversión' in str(c).lower():
            col_spend = c; break
        if 'assigned' in str(c).lower() and 'budget' in str(c).lower():
            if i + 1 < len(df_pacing.columns): col_spend = df_pacing.columns[i+1]; break

    col_tipo = None
    for c in df_pacing.columns:
        if 'official' in str(c).lower() or 'conversions' in str(c).lower():
            col_tipo = c; break

    col_res = None
    for c in df_pacing.columns:
        if 'platform' in str(c).lower() and 'conversions' in str(c).lower():
            col_res = c; break

    col_cpa = None
    for c in df_pacing.columns:
        if 'cpa' in str(c).lower():
            col_cpa = c; break

    # 5. FILTRADO ESTRICTO ANTI-FLOAT
    df_campañas = df_pacing.copy()
    
    # Forzamos la columna Campaign a ser string puro, llenando vacíos con texto vacío
    df_campañas['Campaign'] = df_campañas['Campaign'].fillna('').astype(str)
    
    df_campañas = df_campañas[
        (df_campañas['Campaign'] != '') &
        (~df_campañas['Campaign'].str.upper().str.contains('TOTAL')) & 
        (df_campañas['Campaign'] != 'Campaign')
    ].copy()
    
    # Forzamos columnas de la gráfica a string puro para que Plotly no colapse
    df_campañas[col_medio] = df_campañas[col_medio].replace(['', ' ', 'nan', 'NaN'], pd.NA).ffill().fillna('Sin Medio').astype(str)
    if col_tipo:
        df_campañas[col_tipo] = df_campañas[col_tipo].fillna('Sin Objetivo').astype(str)
    else:
        col_tipo = 'Objetivo'
        df_campañas[col_tipo] = 'Sin Objetivo'

    # Matemáticas de Inversión
    df_campañas[col_spend] = pd.to_numeric(df_campañas[col_spend].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce').fillna(0)

    resumen_plataformas = df_campañas.groupby(col_medio)[col_spend].sum()
    mapa_nombres = {plat: f"{plat} (${tot:,.0f})" for plat, tot in resumen_plataformas.items()}
    df_campañas['Medio_Labels'] = df_campañas[col_medio].map(mapa_nombres).astype(str)
    gasto_total_calculado = df_campañas[col_spend].sum()
    
    col_fecha = 'Actualización Pacing'
    for c in df_pacing.columns:
        if 'actualizacion' in str(c).lower() or 'pacing' in str(c).lower():
            col_fecha = c; break
            
    fecha_update = df_pacing[col_fecha].dropna().iloc[-1] if col_fecha in df_pacing.columns and not df_pacing[col_fecha].dropna().empty else "N/D"
    
    # --- INTERFAZ ---
    st.title(f"🏨 Dashboard Gerencial: {mes_seleccionado.title()}")
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Presupuesto Mensual", f"{presupuesto_mensual}")
    with c2: st.metric("Inversión Ejecutada", f"${gasto_total_calculado:,.0f}")
    with c3:
        if mes_seleccionado == meses_disponibles[0]:
            st.metric("Día de Medición", f"Día {datetime.now().day}")
        else:
            st.metric("Estado del Mes", "Cerrado")

    st.success(f"✅ Sincronización exitosa con la pestaña [{mes_seleccionado}] | Último registro: {fecha_update}")
    st.divider()

    st.header("📊 Distribución por Canal y Objetivo")
    df_plot = df_campañas[df_campañas[col_spend] > 0]
    if not df_plot.empty:
        fig = px.treemap(df_plot, path=['Medio_Labels', col_tipo], values=col_spend, color=col_spend, color_continuous_scale=['#d6b58e', '#5b3f8e'])
        fig.update_traces(texttemplate="<b>%{label}</b><br>$%{value:,.0f}", hovertemplate="<b>%{label}</b><br>Inversión: $%{value:,.0f}<extra></extra>", textposition="middle center")
        fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se detectan datos de gasto para graficar en este periodo.")

    with st.expander("📝 Detalle de Campañas"):
        cols_mostrar = [col_medio, 'Campaign', col_tipo]
        renombrar = {col_medio: 'Medio', 'Campaign': 'Campaña', col_tipo: 'Objetivo'}
        if col_res: cols_mostrar.append(col_res); renombrar[col_res] = 'Resultados'
        if col_cpa: cols_mostrar.append(col_cpa); renombrar[col_cpa] = 'CPA'
        
        df_display = df_campañas[cols_mostrar].rename(columns=renombrar)
        st.dataframe(df_display.sort_values(by='Medio'), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error técnico de visualización: {e}")

st.caption(f"Hyatt Regency Cartagena | Strategic Analytics by goBIG")
