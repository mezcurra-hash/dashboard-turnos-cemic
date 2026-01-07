import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Turnos", layout="wide", page_icon="🏥")

st.title("🏥 Oferta de Turnos de Consultorio - CEMIC")
st.markdown("---")
st.image("https://cemic.edu.ar/assets/img/logo/logo-cemic.png", width=200)

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
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
        
        # 1. FILTRO DE FECHA (Obligatorio)
        fechas = sorted(df['PERIODO'].dt.strftime('%Y-%m-%d').unique().tolist())
        meses_sel = st.multiselect("1. Periodo:", options=fechas, default=fechas[0] if fechas else None)
        
        st.divider()

        # 2. FILTROS ESPECÍFICOS (El "Subfiltro" que pediste)
        # Usamos un 'expander' para que no ocupe lugar si no se usa
        with st.expander("🔍 Filtros Específicos (Opcional)"):
            st.caption("Deja vacío para ver todo.")
            
            # Filtro por DEPARTAMENTO
            deptos_unicos = sorted(df['DEPARTAMENTO'].astype(str).unique())
            filtro_depto = st.multiselect("Filtrar Departamento:", options=deptos_unicos)
            
            # Filtro por SERVICIO
            servicios_unicos = sorted(df['SERVICIO'].astype(str).unique())
            filtro_servicio = st.multiselect("Filtrar Servicio:", options=servicios_unicos)
            
            # Filtro por SEDE
            sedes_unicas = sorted(df['SEDE'].astype(str).unique())
            filtro_sede = st.multiselect("Filtrar Sede:", options=sedes_unicas)
            
            # Filtro por PROFESIONAL (Útil para búsquedas puntuales)
            prof_unicos = sorted(df['PROFESIONAL/EQUIPO'].astype(str).unique())
            filtro_prof = st.multiselect("Filtrar Profesional:", options=prof_unicos)

        st.divider()
        
        # 3. CONFIGURACIÓN DE LA TABLA (Agrupación y Métricas)
        cols_texto = df.select_dtypes(include=['object']).columns.tolist()
        default_fila = ['SERVICIO'] if 'SERVICIO' in cols_texto else [cols_texto[0]]
        filas_sel = st.multiselect("2. Agrupar tabla por:", options=cols_texto, default=default_fila)
        
        cols_numericas = df.select_dtypes(include=['float', 'int']).columns.tolist()
        default_val = ['TURNOS_MENSUAL'] if 'TURNOS_MENSUAL' in cols_numericas else [cols_numericas[0]]
        valores_sel = st.multiselect("3. Métricas:", options=cols_numericas, default=default_val)

    # --- LÓGICA DE FILTRADO (El Cerebro) ---
    if not meses_sel or not filas_sel or not valores_sel:
        st.warning("👈 Selecciona opciones en el menú lateral.")
        st.stop()

    # A. Filtro por Fecha (Base)
    mask = df['PERIODO'].isin(pd.to_datetime(meses_sel))
    df_filtered = df[mask]

    # B. Aplicamos los "Subfiltros" solo si el usuario eligió algo
    if filtro_depto:
        df_filtered = df_filtered[df_filtered['DEPARTAMENTO'].isin(filtro_depto)]
    
    if filtro_servicio:
        df_filtered = df_filtered[df_filtered['SERVICIO'].isin(filtro_servicio)]
        
    if filtro_sede:
        df_filtered = df_filtered[df_filtered['SEDE'].isin(filtro_sede)]
        
    if filtro_prof:
        df_filtered = df_filtered[df_filtered['PROFESIONAL/EQUIPO'].isin(filtro_prof)]

    # Si después de filtrar no queda nada, avisamos
    if df_filtered.empty:
        st.error("⚠️ No hay datos que coincidan con esa combinación de filtros.")
        st.stop()

    # --- VISUALIZACIÓN ---
    totales = df_filtered[valores_sel].sum()

    # KPIs
    st.subheader(f"Resumen ({len(meses_sel)} periodos)")
    cols = st.columns(len(valores_sel))
    for i, metrica in enumerate(valores_sel):
        valor = totales[metrica]
        cols[i].metric(label=metrica, value=f"{valor:,.0f}")

    st.markdown("---")

    # TABS
    tab1, tab2 = st.tabs(["📊 Análisis Visual", "📄 Tabla Detallada"])

    with tab1:
        st.markdown(f"**Distribución por {filas_sel[0]}**")
        chart_data = df_filtered.groupby(filas_sel[0])[valores_sel].sum()
        st.bar_chart(chart_data, height=500, use_container_width=True)

    with tab2:
        tabla = pd.pivot_table(
            df_filtered, 
            index=filas_sel, 
            values=valores_sel, 
            aggfunc='sum', 
            margins=True, 
            margins_name='TOTAL GENERAL'
        )
        
        st.dataframe(
            tabla.style.format("{:,.0f}").background_gradient(cmap='Blues'), 
            use_container_width=True, 
            height=600
        )
        
        st.download_button(
            "📥 Descargar Excel (CSV)", 
            tabla.to_csv().encode('utf-8'), 
            "reporte_filtrado.csv",
            mime='text/csv'
        )

except Exception as e:
    st.error("Error técnico:")
    st.write(e)
