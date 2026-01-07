import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Turnos", layout="wide", page_icon="🏥")

# Título con estilo
st.title("🏥 Dashboard de Gestión - CEMIC")
st.markdown("---")

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    # LINK YA CONFIGURADO
    url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSE_a5zehFJmJnMpGn5BMLTy3262nHEQDXgEe2Ad8T5fN3siBB4gv3ob7HwMyeS63eO5ve57HM0ZeGR/pub?gid=182727859&single=true&output=csv"
    
    df = pd.read_csv(url_csv)
    return df

try:
    df = cargar_datos()

    # --- LIMPIEZA ---
    # Convertimos la columna PERIODO a fecha
    df['PERIODO'] = pd.to_datetime(df['PERIODO'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['PERIODO'])

    # --- BARRA LATERAL (Filtros) ---
    with st.sidebar:
        st.header("🎛️ Panel de Control")
        
        # Filtro Fecha
        fechas = sorted(df['PERIODO'].dt.strftime('%Y-%m-%d').unique().tolist())
        meses_sel = st.multiselect("1. Periodo:", options=fechas, default=fechas[0] if fechas else None)
        
        st.divider() # Línea separadora
        
        # Filtro Agrupación
        # Excluimos columnas numéricas y de fecha para agrupar
        cols_texto = df.select_dtypes(include=['object']).columns.tolist()
        # Definimos 'SERVICIO' por defecto si existe, si no el primero de la lista
        default_fila = ['SERVICIO'] if 'SERVICIO' in cols_texto else [cols_texto[0]]
        filas_sel = st.multiselect("2. Agrupar por:", options=cols_texto, default=default_fila)
        
        # Filtro Métricas
        cols_numericas = df.select_dtypes(include=['float', 'int']).columns.tolist()
        # Definimos 'TURNOS_MENSUAL' por defecto si existe
        default_val = ['TURNOS_MENSUAL'] if 'TURNOS_MENSUAL' in cols_numericas else [cols_numericas[0]]
        valores_sel = st.multiselect("3. Métricas:", options=cols_numericas, default=default_val)

        st.info("💡 Consejo: Usa el botón de expandir en los gráficos para verlos en pantalla completa.")

    # --- LÓGICA PRINCIPAL ---
    if not meses_sel or not filas_sel or not valores_sel:
        st.warning("👈 Por favor, selecciona al menos una opción en cada filtro del menú lateral.")
        st.stop() # Detiene la ejecución hasta que elijas algo

    # 1. Aplicamos Filtro de Fecha
    mask = df['PERIODO'].isin(pd.to_datetime(meses_sel))
    df_filtered = df[mask]

    # 2. Calculamos los KPIs (Números Grandes)
    totales = df_filtered[valores_sel].sum()

    # --- SECCIÓN VISUAL (DASHBOARD) ---
    
    # A. TARJETAS DE MÉTRICAS (KPIs)
    st.subheader(f"Resumen del Periodo ({len(meses_sel)} fechas seleccionadas)")
    
    # Creamos columnas dinámicas según cuántas métricas elegiste
    cols = st.columns(len(valores_sel))
    
    for i, metrica in enumerate(valores_sel):
        valor = totales[metrica]
        # Mostramos la tarjeta con formato de miles (,)
        cols[i].metric(label=metrica, value=f"{valor:,.0f}")

    st.markdown("---")

    # B. PESTAÑAS PARA GRÁFICOS Y TABLA
    tab1, tab2 = st.tabs(["📊 Análisis Visual", "📄 Tabla Detallada"])

    with tab1:
        st.markdown(f"**Distribución por {filas_sel[0]}**")
        
        # Preparamos datos para el gráfico
        chart_data = df_filtered.groupby(filas_sel[0])[valores_sel].sum()
        
        # Gráfico de Barras Nativo
        st.bar_chart(chart_data, height=500, use_container_width=True)

    with tab2:
        # C. TABLA DINÁMICA
        tabla = pd.pivot_table(
            df_filtered, 
            index=filas_sel, 
            values=valores_sel, 
            aggfunc='sum', 
            margins=True, 
            margins_name='TOTAL GENERAL'
        )
        
        # Mostramos tabla coloreada
        st.dataframe(
            tabla.style.format("{:,.0f}").background_gradient(cmap='Blues'), 
            use_container_width=True, 
            height=600
        )
        
        # Botón de descarga
        st.download_button(
            "📥 Descargar Excel (CSV)", 
            tabla.to_csv().encode('utf-8'), 
            "reporte_dashboard.csv",
            mime='text/csv'
        )

except Exception as e:
    st.error("Hubo un error cargando los datos. Revisa el link público.")
    st.expander("Ver error técnico").write(e)
