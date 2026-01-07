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
    # Si tienes el logo subido, déjalo así. Si no, borra esta línea.
    try:
        st.image("logo.png", width=100)
    except:
        st.write("") # Espacio vacío si no encuentra el logo
with col2:
    st.title("Oferta de Turnos - CEMIC")
st.markdown("---")

# --- CARGA DE DATOS (SOLO HISTÓRICO) ---
@st.cache_data
def cargar_datos_simple():
    # --- PEGA TU LINK AQUÍ ABAJO ---
    url_historico = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=1524527213&single=true&output=csv"
    
    # Leemos solo un archivo
    df = pd.read_csv(url_historico)
    return df

try:
    df = cargar_datos_simple()
    
    # --- LIMPIEZA ---
    # Convertimos fecha (asegurate que en tu Excel la fecha sea DD/MM/AAAA)
    df['PERIODO'] = pd.to_datetime(df['PERIODO'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['PERIODO'])
    
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("🎛️ Panel de Control")
        
        # 1. INTERRUPTOR DE MODO
        modo_analisis = st.radio(
            "Selecciona Modo:",
            ["📊 Análisis Global", "🆚 Comparativa Mensual"],
            horizontal=True
        )
        st.divider()

        # Lógica de Fechas
        fechas_disponibles = sorted(df['PERIODO'].dt.strftime('%Y-%m-%d').unique().tolist())
        
        if not fechas_disponibles:
            st.error("No se encontraron fechas válidas en el Excel.")
            st.stop()

        if modo_analisis == "📊 Análisis Global":
            meses_sel = st.multiselect("Periodos:", options=fechas_disponibles, default=fechas_disponibles)
        else:
            # Comparativa A vs B
            col_a, col_b = st.columns(2)
            idx_a = max(0, len(fechas_disponibles)-2)
            idx_b = len(fechas_disponibles)-1
            
            with col_a:
                periodo_a = st.selectbox("Base:", options=fechas_disponibles, index=idx_a)
            with col_b:
                periodo_b = st.selectbox("Actual:", options=fechas_disponibles, index=idx_b)
            
            meses_sel = [periodo_a, periodo_b]

        st.divider()

        # Filtros Específicos (Dinámicos según lo que haya en el Excel)
        with st.expander("🔍 Filtros Específicos"):
            # Detectamos columnas de texto automáticamente
            cols_texto = df.select_dtypes(include=['object']).columns.tolist()
            # Columnas clave que nos interesan para filtrar
            claves = ['DEPARTAMENTO', 'SERVICIO', 'SEDE', 'PROFESIONAL', 'PROFESIONAL/EQUIPO']
            
            filtros_activos = {}
            for col in claves:
                if col in df.columns:
                    opciones = sorted(df[col].astype(str).unique())
                    filtros_activos[col] = st.multiselect(f"{col}:", options=opciones)

        # Configuración Visual
        # Si existe SERVICIO lo usa, si no, usa la primera columna de texto que encuentre
        default_fila = ['SERVICIO'] if 'SERVICIO' in df.columns else ([cols_texto[0]] if cols_texto else None)
        filas_sel = st.multiselect("Agrupar por:", options=cols_texto, default=default_fila)
        
        # Métricas (Solo numéricas)
        cols_num = df.select_dtypes(include=['float', 'int']).columns.tolist()
        metricas_posibles = [c for c in cols_num if c not in ['Year', 'Month']]
        default_val = [metricas_posibles[0]] if metricas_posibles else None
        valores_sel = st.multiselect("Métrica:", options=metricas_posibles, default=default_val)

        st.divider()
        st.caption("ℹ️ Nota del Sistema:")
        st.info("Sincronización automática c/ 5 min.")

    # --- LÓGICA PRINCIPAL ---
    if not meses_sel or not filas_sel or not valores_sel:
        st.warning("Selecciona opciones para continuar.")
        st.stop()

    # 1. Filtro de Fecha
    mask = df['PERIODO'].isin(pd.to_datetime(meses_sel))
    df_filtered = df[mask]
    
    # 2. Subfiltros
    for col, seleccion in filtros_activos.items():
        if seleccion:
            df_filtered = df_filtered[df_filtered[col].isin(seleccion)]

    # --- VISUALIZACIÓN ---
    
    # MODO 1: GLOBAL
    if modo_analisis == "📊 Análisis Global":
        totales = df_filtered[valores_sel].sum()
        
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

    # MODO 2: COMPARATIVO
    else:
        st.subheader(f"🆚 Comparativa: {periodo_a} vs {periodo_b}")
        
        df_a = df_filtered[df_filtered['PERIODO'] == periodo_a]
        df_b = df_filtered[df_filtered['PERIODO'] == periodo_b]
        
        # KPIs Comparativos
        cols_kpi = st.columns(len(valores_sel))
        for i, metrica in enumerate(valores_sel):
            val_a = df_a[metrica].sum()
            val_b = df_b[metrica].sum()
            diff = val_b - val_a
            pct = (diff / val_a * 100) if val_a != 0 else 0
            
            cols_kpi[i].metric(metrica, f"{val_b:,.0f}", f"{diff:,.0f} ({pct:.1f}%)")
            
        st.markdown("---")

        # Gráfico Comparativo
        group_a = df_a.groupby(filas_sel[0])[valores_sel[0]].sum().rename(f"{periodo_a}")
        group_b = df_b.groupby(filas_sel[0])[valores_sel[0]].sum().rename(f"{periodo_b}")
        df_chart = pd.concat([group_a, group_b], axis=1).fillna(0)
        
        tab1, tab2 = st.tabs(["📊 Comparación Visual", "📄 Tabla de Variación"])
        
        with tab1:
            st.bar_chart(df_chart, use_container_width=True)
            
        with tab2:
            df_chart['Diferencia'] = df_chart.iloc[:, 1] - df_chart.iloc[:, 0]
            df_chart['Var %'] = (df_chart['Diferencia'] / df_chart.iloc[:, 0]) * 100
            
            st.dataframe(
                df_chart.style.format("{:,.0f}", subset=[df_chart.columns[0], df_chart.columns[1], 'Diferencia'])
                .format("{:.1f}%", subset=['Var %'])
                .background_gradient(cmap='RdYlGn', subset=['Diferencia']),
                use_container_width=True, height=600
            )

except Exception as e:
    st.error("⚠️ Error al cargar datos. Verifica que el LINK sea correcto y público.")
    st.expander("Detalle del error").write(e)
