import streamlit as st

# Configuración de página para mantener el estilo visual
st.set_page_config(
    page_title="Hyatt - Rendimiento",
    page_icon="🏨",
    layout="wide"
)

# Estilos Premium GO BIG (Mismos de app.py)
st.markdown("""
    <style>
    .main { background-color: #0d0d0d; }
    h1, h2, h3 { color: #ffffff; font-family: 'Georgia', serif; }
    .stSidebar { background-color: #1a1a1a; border-right: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Reportes de Rendimiento")
st.write("¡Página creada con éxito! Aquí construiremos las nuevas lógicas y gráficas.")
