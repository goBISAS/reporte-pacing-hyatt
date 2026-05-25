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
    df_raw = pd.read_csv(url_pacing, header=None, dtype=str).fillna('')
    
    # 1. RADAR: Buscar la fila de encabezados
    idx_header = None
    for i, row in df_raw.iterrows():
        if any('campaign' in val.lower() or 'campaña' in val.lower() for val in row.tolist()):
            idx_header = i
            break
    
    if idx_header is None:
        st.error(f"No se encontró la tabla de campañas. Verifica que la pestaña '{mes_seleccionado}' exista.")
        st.stop()

    # 2. LECTURA LINEAL (Gracias a tu estandarización)
    presupuesto_mensual = "$0"
    for i in range(idx_header):
        fila = df_raw.iloc[i].astype(str).tolist()
        for j, celda in enumerate(fila):
            celda_limpia = celda.lower().strip()
            # Busca la etiqueta exacta en la celda
            if 'approved budget' in celda_limpia or 'monthly budget' in celda_limpia or 'presupuesto' in celda_limpia:
                # Toma el valor exactamente a la derecha
                if j + 1 < len(fila) and fila[j+1].strip() not in ['', 'nan', '<na>']:
                    presupuesto_mensual = fila[j+1].strip()
                break
        if presupuesto_mensual != "$0":
            break

    # 3. CONSTRUIR TABLA LIMPIA
    df_pacing = df_raw.iloc[idx_header + 1:].copy()
    nombres_seguros = []
    for i, c in enumerate(df_raw.iloc[idx_header].tolist()):
        nombre = re.sub(r'\s+', ' ', str(c)).strip()
        if nombre == '': nombre = f"Columna_Vacia_{i}"
        nombres_seguros.append(nombre)
    df_pacing.columns = nombres_seguros

    # 4. MAPEADO DE COLUMNAS DE LA TABLA
    col_camp = next((c for c in df_pacing.columns if 'campaign' in c.lower() or 'campaña' in c.lower()), df_pacing.columns[1] if len(df_pacing.columns) > 1 else df_pacing.columns[0])
    col_medio = next((c for c in df_pacing.columns if 'channel' in c.lower() or 'platform' in c.lower() or 'canal' in c.lower()), df_pacing.columns[0])
    col_spend = next((c for c in df_pacing.columns if 'spend' in c.lower() or 'gasto' in c.lower() or 'cop' in c.lower()), df_pacing.columns[7] if len(df_pacing.columns) > 7 else df_pacing.columns[-1])
    col_tipo = next((c for c in df_pacing.columns if 'official' in c.lower() or 'conversions' in c.lower() or 'objetivo' in c.lower()), df_pacing.columns[15] if len(df_pacing.columns) > 15 else df_pacing.columns[-1])
    col_res = next((c for c in df_pacing.columns if 'platform' in c.lower() or 'resultados' in c.lower() or 'results' in c.lower()), df_pacing.columns[14] if len(df_pacing.columns) > 14 else df_pacing.columns[-1])
    col_cpa = next((c for c in df_pacing.columns if 'cpa' in c.lower()), df_pacing.columns[17] if len(df_pacing.columns) > 17 else df_pacing.columns[-1])
    col_fecha = next((c for c in df_pacing.columns if 'actualizaci' in c.lower() or 'pacing' in c.lower()), df_pacing.columns[18] if len(df_pacing.columns) > 18 else df_pacing.columns[-1])

    # 5. LIMPIEZA A PRUEBA DE FALLOS
    df_campañas = df_pacing.copy()
    
    df_campañas = df_campañas[df_campañas[col_camp].str.strip() != '']
    df_campañas = df_campañas[~df_campañas[col_camp].str.upper().str.contains('TOTAL')]
    df_campañas = df_campañas[df_campañas[col_camp].str.lower() != 'campaign']
    
    df_campañas[col_medio] = df_campañas[col_medio].replace('', pd.NA).ffill().fillna('Sin Medio')
    df_campañas[col_tipo] = df_campañas[col_tipo].replace('', 'Sin Objetivo')

    df_campañas[col_spend] = df_campañas[col_spend].str.replace(r'[^\d.-]', '', regex=True)
    df_campañas[col_spend] = pd.to_numeric(df_campañas[col_spend], errors='coerce').fillna(0)

    # 6. EXTRACCIÓN DE FECHA INTACTA
    fechas_validas = df_campañas[col_fecha].astype(str).str.strip()
    fechas_validas = fechas_validas[(fechas_validas != '') & (~fechas_validas.str.lower().str.contains('pacing|actualiz'))]
    fecha_update = fechas_validas.iloc[-1] if not fechas_validas.empty else "N/D"

    # 7. CÁLCULOS
    resumen_plataformas = df_campañas.groupby(col_medio)[col_spend].sum()
    mapa_nombres = {plat: f"{plat} (${tot:,.0f})" for plat, tot in resumen_plataformas.items()}
    df_campañas['Medio_Labels'] = df_campañas[col_medio].map(mapa_nombres).astype(str)
    gasto_total_calculado = df_campañas[col_spend].sum()
    
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
        st.warning("No se detectan datos de gasto mayores a $0 para graficar en este periodo.")

    with st.expander("📝 Detalle de Campañas"):
        df_display = df_campañas[[col_medio, col_camp, col_tipo, col_res, col_cpa]].rename(
            columns={col_medio: 'Medio', col_camp: 'Campaña', col_tipo: 'Objetivo', col_res: 'Resultados', col_cpa: 'CPA'}
        )
        st.dataframe(df_display.sort_values(by='Medio'), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error detectado: {e}")

st.caption(f"Hyatt Regency Cartagena | Strategic Analytics by goBIG")
