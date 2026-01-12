import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Turnos", layout="wide", page_icon="🏥")

# Estilos CSS
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            /* header {visibility: hidden;} Borramos esto para ver la flechita */
            [data-testid="stMetricDelta"] svg { display: inline; }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Cabecera
st.title("🏥 Oferta de Turnos de Consultorio - CEMIC")
st.markdown("---")
# Si tienes logo.png en GitHub usa st.image("logo.png"), sino el link
st.image("https://cemic.edu.ar/assets/img/logo/logo-cemic.png", width=200)

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    # TU LINK DEL HISTÓRICO
    url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=1524527213&single=true&output=csv"
    df = pd.read_csv(url_csv)
    return df

try:
    df = cargar_datos()

    # --- LIMPIEZA ---
    df['PERIODO'] = pd.to_datetime(df['PERIODO'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['PERIODO'])

    # === NUEVO: FUNCIÓN PARA EMBELLECER FECHAS ===
    # Esto traduce "2026-01-01" a "Enero-2026"
    def formato_fecha_linda(fecha):
        meses = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        return f"{meses[fecha.month]}-{fecha.year}"

    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("🎛️ Panel de Control")
        
        modo_analisis = st.radio(
            "Selecciona Modo de Vista:",
            ["📊 Análisis Global", "🆚 Comparativa Mensual"],
            horizontal=True
        )
        st.divider()

        # OBTENEMOS LAS FECHAS ÚNICAS (Objetos de fecha real, no texto)
        fechas_unicas = sorted(df['PERIODO'].unique())
        
        if len(fechas_unicas) == 0:
            st.error("No hay fechas en el Excel.")
            st.stop()

        if modo_analisis == "📊 Análisis Global":
            # Usamos format_func para que se vea bonito
            meses_sel = st.multiselect(
                "1. Periodo:", 
                options=fechas_unicas, 
                default=[fechas_unicas[0]], 
                format_func=formato_fecha_linda
            )
        else:
            col1, col2 = st.columns(2)
            idx_a = max(0, len(fechas_unicas)-2)
            idx_b = len(fechas_unicas)-1
            
            with col1:
                periodo_a = st.selectbox(
                    "Base:", 
                    options=fechas_unicas, 
                    index=idx_a,
                    format_func=formato_fecha_linda
                )
            with col2:
                periodo_b = st.selectbox(
                    "Actual:", 
                    options=fechas_unicas, 
                    index=idx_b,
                    format_func=formato_fecha_linda
                )
            
            meses_sel = [periodo_a, periodo_b]

        st.caption("ℹ️ Nota del Sistema:")
        st.info("Sincronización automática c/ 5 min.")
        st.divider()

        # Filtros Específicos
        with st.expander("🔍 Filtros Específicos", expanded=True):
            
            # === AQUÍ AGREGUÉ EL FILTRO DE TIPO DE ATENCIÓN ===
            st.subheader("Tipo de Prestación")
            filtro_tipo_atencion = st.radio(
                "Modalidad:",
                ["Todos", "Programada (AP)", "No Programada (ANP)"],
                index=0, # Por defecto muestra Todos
                horizontal=True
            )
            st.divider()
            # ==================================================

            deptos = sorted(df['DEPARTAMENTO'].astype(str).unique())
            filtro_depto = st.multiselect("Depto:", deptos)
            
            servicios = sorted(df['SERVICIO'].astype(str).unique())
            filtro_servicio = st.multiselect("Servicio:", servicios)
            
            sedes = sorted(df['SEDE'].astype(str).unique())
            filtro_sede = st.multiselect("Sede:", sedes)
            
            profs = sorted(df['PROFESIONAL/EQUIPO'].astype(str).unique())
            filtro_prof = st.multiselect("Profesional:", profs)

        st.divider()
        
        # Configuración Tabla
        cols_texto = df.select_dtypes(include=['object']).columns.tolist()
        default_fila = ['SERVICIO'] if 'SERVICIO' in cols_texto else [cols_texto[0]]
        filas_sel = st.multiselect("Agrupar por:", cols_texto, default=default_fila)
        
        cols_num = df.select_dtypes(include=['float', 'int']).columns.tolist()
        val_sel = st.multiselect("Métricas:", cols_num, default=['TURNOS_MENSUAL'] if 'TURNOS_MENSUAL' in cols_num else [cols_num[0]])

    # --- LÓGICA DE FILTRADO ---
    if not meses_sel or not filas_sel or not val_sel:
        st.warning("Selecciona opciones.")
        st.stop()

    # 1. Filtro de Fechas
    mask = df['PERIODO'].isin(meses_sel)
    df_filtered = df[mask]

    # 2. === NUEVO FILTRO DE TIPO DE ATENCIÓN ===
    if filtro_tipo_atencion == "Programada (AP)":
        # Asegurarse que la columna en Excel se llame exactamente TIPO_ATENCION
        if 'TIPO_ATENCION' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['TIPO_ATENCION'] == 'AP']
        else:
            st.error("⚠️ No encuentro la columna 'TIPO_ATENCION' en el Excel.")
            
    elif filtro_tipo_atencion == "No Programada (ANP)":
        if 'TIPO_ATENCION' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['TIPO_ATENCION'] == 'ANP']
        else:
            st.error("⚠️ No encuentro
