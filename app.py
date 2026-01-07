import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión de Turnos", layout="wide", page_icon="🏥")

# --- ESTILOS CSS (Modo Kiosco + Métricas) ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stMetricDelta"] svg { display: inline; }
</style>
""", unsafe_allow_html=True)

# --- CABECERA ---
col1, col2 = st.columns([1, 5])
with col1:
    # Asegúrate de tener el archivo logo.png en tu GitHub
    st.image("https://cemic.edu.ar/assets/img/logo/logo-cemic.png", width=100) 
with col2:
    st.title("Oferta de Turnos - CEMIC")
st.markdown("---")

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos_inteligentes():
    # LINK HISTORICO REAL
    url_historico = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSE_a5zehFJmJnMpGn5BMLTy3262nHEQDXgEe2Ad8T5fN3siBB4gv3ob7HwMyeS63eO5ve57HM0ZeGR/pub?gid=182727859&single=true&output=csv"
    # LINK MAESTRO REAL
    url_maestro = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSE_a5zehFJmJnMpGn5BMLTy3262nHEQDXgEe2Ad8T5fN3siBB4gv3ob7HwMyeS63eO5ve57HM0ZeGR/pub?gid=0&single=true&output=csv"
    
    df_hechos = pd.read_csv(url_historico)
    df_maestro = pd.read_csv(url_maestro)
    
    # Merge (Cruce de datos)
    df_final = pd.merge(df_hechos, df_maestro, on='PROFESIONAL/EQUIPO', how='left', suffixes=('_old', ''))
    return df_final

try:
    df = cargar_datos_inteligentes()
    
    # Limpieza
    df['PERIODO'] = pd.to_datetime(df['PERIODO'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['PERIODO'])
    
    # Rellenar vacíos
    cols_rellenar = ['SERVICIO', 'DEPARTAMENTO', 'SEDE']
    for col in cols_rellenar:
        if col in df.columns:
            df[col] = df[col].fillna("⚠️ Sin Asignar")

    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("🎛️ Panel de Control")
        
        # 1. INTERRUPTOR DE MODO (LA NOVEDAD)
        modo_analisis = st.radio(
            "Selecciona Modo:",
            ["📊 Análisis Global", "🆚 Comparativa Mensual"],
            horizontal=True
        )
        st.divider()

        # Lógica de Fechas según el modo
        fechas_disponibles = sorted(df['PERIODO'].dt.strftime('%Y-%m-%d').unique().tolist())
        
        if modo_analisis == "📊 Análisis Global":
            # Selección múltiple como siempre
            meses_sel = st.multiselect("Periodos:", options=fechas_disponibles, default=fechas_disponibles)
        else:
            # Selección única A vs B
            col_a, col_b = st.columns(2)
            with col_a:
                periodo_a = st.selectbox("Periodo A (Base):", options=fechas_disponibles, index=max(0, len(fechas_disponibles)-2))
            with col_b:
                periodo_b = st.selectbox("Periodo B (Actual):", options=fechas_disponibles, index=len(fechas_disponibles)-1)
            
            # Validamos para que la lógica de abajo no falle
            meses_sel = [periodo_a, periodo_b]

        st.divider()

        # Filtros Comunes (Funcionan en ambos modos)
        with st.expander("🔍 Filtros Específicos"):
            cols_texto = df.select_dtypes(include=['object']).columns.tolist()
            filtros_activos = {}
            for col in ['DEPARTAMENTO', 'SERVICIO', 'SEDE']:
                if col in cols_texto:
                    opciones = sorted(df[col].astype(str).unique())
                    filtros_activos[col] = st.multiselect(f"{col}:", options=opciones)

        # Configuración Visual
        default_fila = ['SERVICIO'] if 'SERVICIO' in df.columns else [cols_texto[0]]
        filas_sel = st.multiselect("Agrupar por:", options=cols_texto, default=default_fila)
        
        cols_num = df.select_dtypes(include=['float', 'int']).columns.tolist()
        metricas_posibles = [c for c in cols_num if c not in ['Year', 'Month']] # Filtro simple
        valores_sel = st.multiselect("Métrica:", options=metricas_posibles, default=[metricas_posibles[0]] if metricas_posibles else None)

        st.divider()
        st.caption("ℹ️ Nota del Sistema:")
        st.info("Sincronización automática c/ 5 min.")

    # --- LÓGICA DE FILTRADO COMÚN ---
    if not meses_sel or not filas_sel or not valores_sel:
        st.warning("Selecciona opciones para continuar.")
        st.stop()

    # 1. Filtramos por Fecha (Según modo)
    mask = df['PERIODO'].isin(pd.to_datetime(meses_sel))
    df_filtered = df[mask]
    
    # 2. Aplicamos Subfiltros
    for col, seleccion in filtros_activos.items():
        if seleccion:
            df_filtered = df_filtered[df_filtered[col].isin(seleccion)]

    # --- VISUALIZACIÓN SEGÚN MODO ---
    
    # CASO 1: MODO GLOBAL (El de siempre)
    if modo_analisis == "📊 Análisis Global":
        totales = df_filtered[valores_sel].sum()
        
        # KPIs Simples
        st.subheader(f"Resumen Global ({len(meses_sel)} periodos)")
        cols = st.columns(len(valores_sel))
        for i, metrica in enumerate(valores_sel):
            cols[i].metric(metrica, f"{totales[metrica]:,.0f}")
        
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["📊 Gráfico", "📄 Tabla"])
        with tab1:
            st.bar_chart(df_filtered.groupby(filas_sel[0])[valores_sel].sum())
        with tab2:
            tabla = pd.pivot_table(df_filtered, index=filas_sel, values=valores_sel, aggfunc='sum', margins=True, margins_name='TOTAL')
            st.dataframe(tabla.style.format("{:,.0f}").background_gradient(cmap='Blues'), use_container_width=True)

    # CASO 2: MODO COMPARATIVO (El Nuevo)
    else:
        st.subheader(f"🆚 Comparativa: {periodo_a} vs {periodo_b}")
        
        # Separamos los DataFrames
        df_a = df_filtered[df_filtered['PERIODO'] == periodo_a]
        df_b = df_filtered[df_filtered['PERIODO'] == periodo_b]
        
        # A. KPIs con Variación (DELTA)
        cols_kpi = st.columns(len(valores_sel))
        for i, metrica in enumerate(valores_sel):
            val_a = df_a[metrica].sum()
            val_b = df_b[metrica].sum()
            diferencia = val_b - val_a
            porcentaje = (diferencia / val_a * 100) if val_a != 0 else 0
            
            # El parámetro 'delta' hace aparecer la flechita verde/roja
            cols_kpi[i].metric(
                label=metrica, 
                value=f"{val_b:,.0f}", 
                delta=f"{diferencia:,.0f} ({porcentaje:.1f}%)"
            )
            
        st.markdown("---")

        # B. Tabla Cruzada para Gráficos
        # Agrupamos A y B por separado
        group_a = df_a.groupby(filas_sel[0])[valores_sel[0]].sum().rename(f"{periodo_a}")
        group_b = df_b.groupby(filas_sel[0])[valores_sel[0]].sum().rename(f"{periodo_b}")
        
        # Unimos para tener columnas lado a lado
        df_chart = pd.concat([group_a, group_b], axis=1).fillna(0)
        
        # C. Visualización
        tab1, tab2 = st.tabs(["📊 Comparación Visual", "📄 Detalle Numérico"])
        
        with tab1:
            st.markdown(f"**Comparativa por {filas_sel[0]} ({valores_sel[0]})**")
            # Gráfico de barras agrupadas automático
            st.bar_chart(df_chart, use_container_width=True)
            
        with tab2:
            # Calculamos diferencia en la tabla también
            df_chart['Diferencia'] = df_chart.iloc[:, 1] - df_chart.iloc[:, 0]
            df_chart['Var %'] = (df_chart['Diferencia'] / df_chart.iloc[:, 0]) * 100
            
            # Formato condicional para la tabla
            st.dataframe(
                df_chart.style.format("{:,.0f}", subset=[df_chart.columns[0], df_chart.columns[1], 'Diferencia'])
                .format("{:.1f}%", subset=['Var %'])
                .background_gradient(cmap='RdYlGn', subset=['Diferencia']), # Rojo si baja, Verde si sube
                use_container_width=True,
                height=600
            )

except Exception as e:
    st.error("Error cargando datos. Revisa los links.")
    st.expander("Detalle técnico").write(e)
