import streamlit as st
import pandas as pd
import urllib.parse

# CONFIGURACIÓN DE PÁGINA PREMIUM
st.set_page_config(
    page_title="Hyatt - Rendimiento",
    page_icon="🏨",
    layout="wide"
)

# ESTILOS PREMIUM GO BIG Y TARJETAS DE INSIGHTS
st.markdown("""
    <style>
    .main { background-color: #0d0d0d; }
    h1, h2, h3 { color: #ffffff; font-family: 'Georgia', serif; }
    .stSidebar { background-color: #1a1a1a; border-right: 1px solid #333; }
    
    /* Estilos para las tarjetas de reporte */
    .insight-card { background-color: #1a1a1a; padding: 25px; border-radius: 10px; border-left: 5px solid #d6b58e; margin-bottom: 25px; border-right: 1px solid #333; border-top: 1px solid #333; border-bottom: 1px solid #333; }
    .insight-title { color: #d6b58e; font-size: 1.3rem; font-weight: bold; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }
    .insight-text { color: #e0e0e0; font-size: 1rem; line-height: 1.6; text-align: justify; }
    .todo-section { background-color: #241c30; padding: 18px; border-radius: 8px; margin-top: 20px; border-left: 5px solid #8e6bc2; }
    .todo-title { color: #bca0e8; font-weight: 700; margin-bottom: 8px; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

def get_csv_url_by_sheet(url, sheet_name):
    try:
        id_publicacion = url.split("/d/")[1].split("/")[0]
        sheet_enc = urllib.parse.quote(sheet_name)
        return f"https://docs.google.com/spreadsheets/d/{id_publicacion}/gviz/tq?tqx=out:csv&sheet={sheet_enc}"
    except:
        return url

# --- UI HEADER ---
st.title("📈 Reportes de Rendimiento y Optimización")
st.write("Análisis cualitativo, pruebas de mercado y planes de acción estratégicos.")
st.markdown("---")

# --- CONEXIÓN DE DATOS ---
url_base = "https://docs.google.com/spreadsheets/d/1Ah5nzWzix7HXOhrLvRBRYRhHsZYX5tULKG9jF7sNer0/"
url_reporte = get_csv_url_by_sheet(url_base, "Reporte Mensual")

try:
    # 1. Carga cruda del CSV
    df_raw = pd.read_csv(url_reporte, dtype=str).fillna('')
    
    # 2. Validación de columnas mínimas esperadas (Año, Mes, Medio, Observación, Evidencia, To do)
    if len(df_raw.columns) >= 6:
        # Renombramos explícitamente las primeras 6 columnas para asegurar el mapeo correcto
        df_raw.columns = ["Año", "Mes", "Medio", "Observación", "Evidencia", "To_do"] + list(df_raw.columns[6:])
        
        # 3. Limpieza de datos (Omitir filas vacías o encabezados repetidos)
        df_clean = df_raw[(df_raw['Observación'] != '') & (df_raw['Observación'].str.lower() != 'observación')].copy()
        
        if not df_clean.empty:
            # --- FILTROS DE INTERFAZ ---
            c1, c2 = st.columns(2)
            with c1:
                lista_meses = [m for m in df_clean['Mes'].unique() if m.strip() != '']
                mes_filtro = st.selectbox("📅 Filtrar por Mes:", ["Todos"] + lista_meses)
            with c2:
                lista_medios = [m for m in df_clean['Medio'].unique() if m.strip() != '']
                medio_filtro = st.selectbox("🎯 Filtrar por Medio:", ["Todos"] + lista_medios)
            
            # --- APLICACIÓN DE FILTROS ---
            df_filtered = df_clean.copy()
            if mes_filtro != "Todos":
                df_filtered = df_filtered[df_filtered['Mes'] == mes_filtro]
            if medio_filtro != "Todos":
                df_filtered = df_filtered[df_filtered['Medio'] == medio_filtro]

            st.markdown("<br>", unsafe_allow_html=True)

            # --- RENDERIZADO VISUAL ---
            if not df_filtered.empty:
                for index, row in df_filtered.iterrows():
                    medio = row['Medio'].strip() if row['Medio'].strip() else "General"
                    mes = row['Mes'].strip()
                    ano = row['Año'].strip()
                    observacion = row['Observación'].strip()
                    todo = row['To_do'].strip()

                    # Construcción de la tarjeta HTML inyectada SIN sangrías para evitar bloque de código
                    html_card = f"""<div class="insight-card">
<div class="insight-title">{medio} | {mes} {ano}</div>
<div class="insight-text"><strong>Análisis:</strong><br>{observacion}</div>"""
                    
                    # Añadir la sección To-Do solo si existe texto
                    if todo and todo.lower() not in ['nan', 'none', '-']:
                        html_card += f"""
<div class="todo-section">
<div class="todo-title">⚡ Siguientes Pasos (To Do):</div>
<div class="insight-text">{todo}</div>
</div>"""
                    
                    html_card += "</div>"
                    st.markdown(html_card, unsafe_allow_html=True)
            else:
                st.info("No hay registros en la base de datos para los filtros seleccionados.")
        else:
            st.warning("No se detectaron observaciones válidas en la pestaña 'Reporte Mensual'.")
    else:
        st.error("Error estructural: La hoja de cálculo no tiene el número de columnas esperado.")

except Exception as e:
    st.error(f"Error detectado en el procesamiento de la pestaña de Reportes: {e}")
