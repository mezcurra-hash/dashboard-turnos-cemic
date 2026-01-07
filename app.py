import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Turnos", layout="wide", page_icon="🏥")

# Estilos CSS (Modo Kiosco + Flechitas de KPIs)
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            [data-testid="stMetricDelta"] svg { display: inline; }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Cabecera
st.title("🏥 Oferta de Turnos de Consultorio - CEMIC")
st.markdown("---")
# Usamos tu link de imagen original
st.image("https://cemic.edu.ar/assets/img/logo/logo-cemic.png", width=200)

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    # TU LINK ORIGINAL (No lo tocamos)
    url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=1524527213&single=true&output=csv"
    df = pd.read_csv(url_csv)
    return df

try:
    df = cargar_datos()

    # --- LIMPIEZA ---
    df['PERIODO'] = pd.to_datetime(df['PERIODO'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['PERIODO'])

    # --- BARRA LATERAL (Filtros) ---
    with st.sidebar:
        st.header("🎛️ Panel de Control")
        
        # === NUEVO: INTERRUPTOR DE MODO ===
        modo_analisis = st.radio(
            "Selecciona Modo de Vista:",
            ["📊 Análisis Global", "🆚 Comparativa Mensual"],
            horizontal=True
        )
        st.divider()

        # Lógica de Fechas (Cambia según el modo)
        fechas = sorted(df['PERIODO'].dt.strftime('%Y-%m-%d').unique().tolist())
        
        if not fechas:
            st.error("No hay fechas en el Excel.")
            st.stop()

        if modo_analisis == "📊 Análisis Global":
            # TU LÓGICA ORIGINAL
            meses_sel = st.multiselect("1. Periodo:", options=fechas, default=fechas[0] if fechas else None)
        else:
            # NUEVA LÓGICA COMPARATIVA (A vs B)
            col1, col2 = st.columns(2)
            # Por defecto seleccionamos el anteúltimo y el último mes
            idx_a = max(0, len(fechas)-2)
            idx_b = len(fechas)-1
            
            with col1:
                periodo_a = st.selectbox("Periodo Base:", options=fechas, index=idx_a)
            with col2:
                periodo_b = st.selectbox("Periodo Actual:", options=fechas, index=idx_b)
            
            # Engañamos al sistema para que filtre estos dos meses
            meses_sel = [periodo_a, periodo_b]

        st.caption("ℹ️ Nota del Sistema:")
        st.info("Sincronización automática c/ 5 min. Si cargaste un profesional, espera unos instantes.")
        st.divider()

        # 2. FILTROS ESPECÍFICOS (Tu código original)
        with st.expander("🔍 Filtros Específicos (Opcional)"):
            st.caption("Deja vacío para ver todo.")
            deptos_unicos = sorted(df['DEPARTAMENTO'].astype(str).unique())
            filtro_depto = st.multiselect("Filtrar Departamento:", options=deptos_unicos)
            
            servicios_unicos = sorted(df['SERVICIO'].astype(str).unique())
            filtro_servicio = st.multiselect("Filtrar Servicio:", options=servicios_unicos)
            
            sedes_unicas = sorted(df['SEDE'].astype(str).unique())
            filtro_sede = st.multiselect("Filtrar Sede:", options=sedes_unicas)
            
            prof_unicos = sorted(df['PROFESIONAL/EQUIPO'].astype(str).unique())
            filtro_prof = st.multiselect("Filtrar Profesional:", options=prof_unicos)

        st.divider()
        
        # 3. CONFIGURACIÓN
        cols_texto = df.select_dtypes(include=['object']).columns.tolist()
        default_fila = ['SERVICIO'] if 'SERVICIO' in cols_texto else [cols_texto[0]]
        filas_sel = st.multiselect("2. Agrupar tabla por:", options=cols_texto, default=default_fila)
        
        cols_numericas = df.select_dtypes(include=['float', 'int']).columns.tolist()
        default_val = ['TURNOS_MENSUAL'] if 'TURNOS_MENSUAL' in cols_numericas else [cols_numericas[0]]
        valores_sel = st.multiselect("3. Métricas:", options=cols_numericas, default=default_val)

    # --- LÓGICA DE FILTRADO (Común para ambos modos) ---
    if not meses_sel or not filas_sel or not valores_sel:
        st.warning("👈 Selecciona opciones en el menú lateral.")
        st.stop()

    # A. Filtro por Fecha
    mask = df['PERIODO'].isin(pd.to_datetime(meses_sel))
    df_filtered = df[mask]

    # B. Aplicamos los "Subfiltros" (Tu código original)
    if filtro_depto:
        df_filtered = df_filtered[df_filtered['DEPARTAMENTO'].isin(filtro_depto)]
    if filtro_servicio:
        df_filtered = df_filtered[df_filtered['SERVICIO'].isin(filtro_servicio)]
    if filtro_sede:
        df_filtered = df_filtered[df_filtered['SEDE'].isin(filtro_sede)]
    if filtro_prof:
        df_filtered = df_filtered[df_filtered['PROFESIONAL/EQUIPO'].isin(filtro_prof)]

    if
