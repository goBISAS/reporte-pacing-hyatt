import streamlit as st
import pandas as pd
from datetime import datetime

# CONFIGURACIÓN DE PÁGINA (Estilo Hyatt)
st.set_page_config(
    page_title="Hyatt Regency Cartagena - Reporte",
    page_icon="🏨",
    layout="wide"
)

# ESTILOS PERSONALIZADOS
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #1a1a1a; }
    h1, h2 { color: #1a1a1a; font-family: 'Georgia', serif; }
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
    # 1. CARGA DE DATOS (Filas 1-5 Header, Fila 6+ Datos)
    df_header = pd.read_csv(get_csv_url(url_pacing), nrows=5, header=None)
    presupuesto_mensual = df_header.iloc[1, 2] 

    df_pacing = pd.read_csv(get_csv_url(url_pacing), skiprows=5)
    df_pacing.columns = [str(c).strip() for c in df_pacing.columns]

    # 2. MÉTRICAS DE CABECERA
    fila_total = df_pacing[df_pacing['Campaign'].str.contains('TOTAL', na=False)].iloc[0]
    gasto_total = fila_total['Spend (COP)']
    
    col_fecha = encontrar_columna(df_pacing.columns, ['Actualizacion', 'Pacing']) or 'Actualización Pacing'
    fecha_update = df_pacing[col_fecha].dropna().iloc[-1]
    dias_hoy = datetime.now().day

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Presupuesto Mes", f"{presupuesto_mensual}")
    with c2:
        st.metric("Gasto al Día", f"{gasto_total}")
    with c3:
        st.metric("Días del Mes", f"{dias_hoy}")

    st.success(f"📅 Última actualización de datos: {fecha_update}")
    st.divider()

    # 3. SECCIÓN DE RESULTADOS GENERALES (Todas las campañas)
    st.header("🎯 Rendimiento de Campañas")
    
    # Filtro: Campañas individuales (omitiendo totales)
    df_campañas = df_pacing[
        (df_pacing['Campaign'].notna()) & 
        (~df_pacing['Campaign'].str.contains('TOTAL', na=False))
    ].copy()

    if not df_campañas.empty:
        # Buscamos columnas O (Resultados), R (CPA) y P (Tipo de compra)
        col_res = encontrar_columna(df_campañas.columns, ['Platform', 'Conversions'])
        col_cpa = encontrar_columna(df_campañas.columns, ['CPA'])
        col_tipo = encontrar_columna(df_campañas.columns, ['Official', 'Conversions'])
        
        cols_finales = ['Campaign']
        nombres_renombrar = {'Campaign': 'Campaña'}
        
        if col_tipo:
            cols_finales.append(col_tipo)
            nombres_renombrar[col_tipo] = 'Tipo de Resultado'
        if col_res:
            cols_finales.append(col_res)
            nombres_renombrar[col_res] = 'Resultados (Cant.)'
        if col_cpa:
            cols_finales.append(col_cpa)
            nombres_renombrar[col_cpa] = 'Costo por Resultado'
            
        df_display = df_campañas[cols_finales].rename(columns=nombres_renombrar)
        
        # Mostramos la tabla completa
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.warning(f"No se detectan campañas activas para {cliente}.")

except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
    st.info("Asegúrate de que el archivo de Google Sheets tenga el acceso compartido como 'Cualquier persona con el enlace'.")

st.caption(f"{cliente} Dashboard | Desarrollado por goBIG | {datetime.now().strftime('%Y')}")
