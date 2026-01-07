import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Turnos", layout="wide")
st.title("🏥 Dashboard de Gestión - CEMIC")
st.markdown("---")

# --- CARGA DE DATOS (MÉTODO RÁPIDO PUBLICO) ---
@st.cache_data
def cargar_datos():
    # PEGA AQUI TU LINK LARGO ENTRE LAS COMILLAS
    url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSE_a5zehFJmJnMpGn5BMLTy3262nHEQDXgEe2Ad8T5fN3siBB4gv3ob7HwMyeS63eO5ve57HM0ZeGR/pub?gid=182727859&single=true&output=csv"
    
    # Leemos directo el CSV desde la web
    df = pd.read_csv(url_csv)
    return df

try:
    df = cargar_datos()

    # --- LIMPIEZA RÁPIDA ---
    # Convertimos fecha (asegurate que en tu Excel la fecha sea DD/MM/AAAA)
    df['PERIODO'] = pd.to_datetime(df['PERIODO'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['PERIODO'])

    # --- BARRA LATERAL ---
    st.sidebar.header("🎛️ Panel de Control")

    # Filtros
    fechas = sorted(df['PERIODO'].dt.strftime('%Y-%m-%d').unique().tolist())
    meses_sel = st.sidebar.multiselect("Periodo:", options=fechas, default=fechas[0] if fechas else None)
    
    cols_agrupables = list(df.columns) # Leemos todas las columnas para que elijas
    # Quitamos las numéricas de la lista de agrupar para limpiar un poco
    cols_agrupables = [c for c in cols_agrupables if df[c].dtype == 'O'] 
    
    filas_sel = st.sidebar.multiselect("Agrupar por:", options=cols_agrupables, default=['SERVICIO'])
    
    # Detectamos columnas numéricas automáticamente para sumar
    cols_numericas = df.select_dtypes(include=['float', 'int']).columns.tolist()
    valores_sel = st.sidebar.multiselect("Sumar métricas:", options=cols_numericas, default=cols_numericas[0] if cols_numericas else None)

    # --- REPORTE ---
    if st.sidebar.button("GENERAR TABLA"):
        if not meses_sel or not filas_sel or not valores_sel:
            st.warning("Selecciona al menos una opción en cada filtro.")
        else:
            mask = df['PERIODO'].isin(pd.to_datetime(meses_sel))
            df_filtered = df[mask]
            
            tabla = pd.pivot_table(df_filtered, index=filas_sel, values=valores_sel, aggfunc='sum', margins=True, margins_name='TOTAL')
            
            st.dataframe(tabla.style.format("{:,.0f}").background_gradient(cmap='Blues'), use_container_width=True)
            
            st.download_button("📥 Descargar CSV", tabla.to_csv().encode('utf-8'), "reporte.csv")

except Exception as e:
    st.error("Error al cargar datos:")
    st.write(e)
