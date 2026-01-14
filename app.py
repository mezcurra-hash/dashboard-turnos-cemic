import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURACIÓN GLOBAL ---
st.set_page_config(page_title="Tablero de Gestión CEMIC", layout="wide", page_icon="🏥")

# Estilos CSS
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stMetricDelta"] svg { display: inline; }
    div[data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #464b5f;
        padding: 10px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- MENÚ LATERAL ---
with st.sidebar:
    st.image("https://cemic.edu.ar/assets/img/logo/logo-cemic.png", width=150)
    st.title("Navegación")
    app_mode = st.selectbox("Ir a:", 
                           ["🏥 Oferta de Turnos", "🎧 Call Center", "📉 Gestión de Ausentismo"])
    st.markdown("---")

# ==============================================================================
# APP 1: OFERTA DE TURNOS (CORREGIDA: SIN DUPLICADOS EN SEDES ✅)
# ==============================================================================
if app_mode == "🏥 Oferta de Turnos":
    st.title("🏥 Oferta de Turnos de Consultorio")
    st.markdown("---")

    @st.cache_data
    def cargar_datos_oferta():
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=1524527213&single=true&output=csv"
        return pd.read_csv(url)

    try:
        df = cargar_datos_oferta()
        df.columns = df.columns.str.strip() # Limpieza de títulos de columnas
        
        # --- CORRECCIÓN DE DUPLICADOS (SEDES Y DEPTOS) ---
        # Esto elimina los espacios vacíos al final que duplicaban "BELGRANO"
        if 'SEDE' in df.columns:
            df['SEDE'] = df['SEDE'].astype(str).str.strip().str.upper()
        
        if 'DEPARTAMENTO' in df.columns:
            df['DEPARTAMENTO'] = df['DEPARTAMENTO'].astype(str).str.strip().str.upper()
            
        if 'SERVICIO' in df.columns:
            df['SERVICIO'] = df['SERVICIO'].astype(str).str.strip().str.upper()
        # --------------------------------------------------

        df['PERIODO'] = pd.to_datetime(df['PERIODO'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['PERIODO'])

        def formato_fecha_linda(fecha):
            meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
            return f"{meses[fecha.month]}-{fecha.year}"

        # --- FILTROS COMPLETOS ---
        with st.sidebar:
            st.header("🎛️ Configuración Turnos")
            modo_analisis = st.radio("Vista:", ["📊 Global", "🆚 Comparativa"], horizontal=True)
            fechas_unicas = sorted(df['PERIODO'].unique())
            
            if not fechas_unicas: st.error("Error en fechas."); st.stop()

            if modo_analisis == "📊 Global":
                meses_sel = st.multiselect("Periodo:", options=fechas_unicas, default=[fechas_unicas[0]], format_func=formato_fecha_linda)
            else:
                c1, c2 = st.columns(2)
                idx_a = max(0, len(fechas_unicas)-2)
                periodo_a = c1.selectbox("Base:", fechas_unicas, index=idx_a, format_func=formato_fecha_linda)
                periodo_b = c2.selectbox("Actual:", fechas_unicas, index=len(fechas_unicas)-1, format_func=formato_fecha_linda)
                meses_sel = [periodo_a, periodo_b]

            st.divider()

            # FILTROS ESPECÍFICOS
            with st.expander("🔍 Filtros Avanzados", expanded=False):
                filtro_tipo = st.radio("Modalidad:", ["Todos", "Programada (AP)", "No Programada (ANP)"], horizontal=True)
                depto = st.multiselect("Depto:", sorted(df['DEPARTAMENTO'].unique()))
                serv = st.multiselect("Servicio:", sorted(df['SERVICIO'].unique()))
                sede = st.multiselect("Sede:", sorted(df['SEDE'].unique())) # Ahora saldrá limpio
                prof = st.multiselect("Profesional:", sorted(df['PROFESIONAL/EQUIPO'].astype(str).unique()))

            st.divider()

            # SELECTORES DE AGRUPACIÓN
            cols_texto = df.select_dtypes(include=['object']).columns.tolist()
            default_fila = ['SERVICIO'] if 'SERVICIO' in cols_texto else [cols_texto[0]]
            filas_sel = st.multiselect("Agrupar por:", cols_texto, default=default_fila)
            
            cols_num = df.select_dtypes(include=['float', 'int']).columns.tolist()
            val_sel = st.multiselect("Métricas:", cols_num, default=['TURNOS_MENSUAL'] if 'TURNOS_MENSUAL' in cols_num else [cols_num[0]])

        # --- LÓGICA DE FILTRADO ---
        if not meses_sel or not filas_sel or not val_sel: st.warning("Selecciona opciones."); st.stop()

        df_f = df[df['PERIODO'].isin(meses_sel)]

        if filtro_tipo == "Programada (AP)" and 'TIPO_ATENCION' in df_f.columns:
            df_f = df_f[df_f['TIPO_ATENCION'] == 'AP']
        elif filtro_tipo == "No Programada (ANP)" and 'TIPO_ATENCION' in df_f.columns:
            df_f = df_f[df_f['TIPO_ATENCION'] == 'ANP']

        if depto: df_f = df_f[df_f['DEPARTAMENTO'].isin(depto)]
        if serv: df_f = df_f[df_f['SERVICIO'].isin(serv)]
        if sede: df_f = df_f[df_f['SEDE'].isin(sede)]
        if prof: df_f = df_f[df_f['PROFESIONAL/EQUIPO'].isin(prof)]

        if df_f.empty: st.error("Sin datos."); st.stop()

        # --- VISUALIZACIÓN ORIGINAL ---
        if modo_analisis == "📊 Global":
            totales = df_f[val_sel].sum()
            nombres_meses = [formato_fecha_linda(m) for m in meses_sel]
            st.subheader(f"Resumen ({filtro_tipo}): {', '.join(nombres_meses)}")
            
            cols = st.columns(len(val_sel))
            for i, metrica in enumerate(val_sel):
                cols[i].metric(metrica, f"{totales[metrica]:,.0f}")
            
            st.markdown("---")
            t1, t2 = st.tabs(["📊 Gráfico", "📄 Tabla Dinámica"])
            with t1:
                st.bar_chart(df_f.groupby(filas_sel[0])[val_sel].sum())
            with t2:
                tabla = pd.pivot_table(df_f, index=filas_sel, values=val_sel, aggfunc='sum', margins=True, margins_name='TOTAL')
                st.dataframe(tabla.style.format("{:,.0f}").background_gradient(cmap='Blues'), use_container_width=True)

        else: # Comparativa
            nombre_a = formato_fecha_linda(periodo_a)
            nombre_b = formato_fecha_linda(periodo_b)
            st.subheader(f"🆚 Comparativa ({filtro_tipo}): {nombre_a} vs {nombre_b}")
            
            df_a, df_b = df_f[df_f['PERIODO']==periodo_a], df_f[df_f['PERIODO']==periodo_b]
            
            cols = st.columns(len(val_sel))
            for i, metrica in enumerate(val_sel):
                va, vb = df_a[metrica].sum(), df_b[metrica].sum()
                delta = vb - va
                pct = (delta/va*100) if va>0 else 0
                cols[i].metric(metrica, f"{vb:,.0f}", f"{delta:,.0f} ({pct:.1f}%)")
            
            st.markdown("---")
            ga = df_a.groupby(filas_sel[0])[val_sel[0]].sum().rename(nombre_a)
            gb = df_b.groupby(filas_sel[0])[val_sel[0]].sum().rename(nombre_b)
            df_chart = pd.concat([ga, gb], axis=1).fillna(0)
            
            t1, t2 = st.tabs(["📊 Comparación", "📄 Variación"])
            with t1:
                st.bar_chart(df_chart)
            with t2:
                df_chart['Diferencia'] = df_chart.iloc[:,1] - df_chart.iloc[:,0]
                st.dataframe(df_chart.style.format("{:,.0f}").background_gradient(cmap='RdYlGn', subset=['Diferencia']), use_container_width=True)

    except Exception as e: st.error(f"Error en Turnos: {e}")

# ==============================================================================
# APP 2: CALL CENTER (RESTAURADO AL DISEÑO ORIGINAL 🎨)
# ==============================================================================
elif app_mode == "🎧 Call Center":
    st.title("🎧 Call Center - CEMIC")
    st.markdown("---")

    @st.cache_data
    def cargar_datos_cc():
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTOxpr7RRNTLGO96pUK8HJ0iy2ZHeqNpiR7OelleljCVoWPuJCO26q5z66VisWB76khl7Tmsqh5CqNC/pub?gid=0&single=true&output=csv"
        df = pd.read_csv(url, dtype=str).fillna(0)
        # Limpieza de columnas numéricas
        cols = ['RECIBIDAS_FIN', 'ATENDIDAS_FIN', 'PERDIDAS_FIN', 'RECIBIDAS_PREPAGO', 'ATENDIDAS_PREPAGO', 'PERDIDAS_PREPAGO', 'TURNOS_TOTAL_TEL', 'TURNOS_CONS_TEL', 'TURNOS_PRACT_TEL']
        for c in cols: 
            if c in df.columns: df[c] = pd.to_numeric(df[c].str.replace('.','', regex=False), errors='coerce').fillna(0)
        return df

    # Función para leer fechas tipo "Ene-2025" o "Jan-2025"
    def parsear_fecha_custom(texto_fecha):
        if pd.isna(texto_fecha): return None
        texto = str(texto_fecha).lower().strip().replace(".", "")
        meses = {'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12, 'jan': 1, 'apr': 4, 'aug': 8, 'dec': 12}
        partes = texto.replace("-", " ").split()
        if len(partes) < 2: return None
        mes_txt = partes[0][:3] 
        anio_txt = partes[1]
        if len(anio_txt) == 2: anio_txt = "20" + anio_txt
        num_mes = meses.get(mes_txt)
        if num_mes: return pd.Timestamp(year=int(anio_txt), month=num_mes, day=1)
        return None

    try:
        df = cargar_datos_cc()
        df['FECHA_REAL'] = df['MES'].apply(parsear_fecha_custom)
        df = df.dropna(subset=['FECHA_REAL']).sort_values('FECHA_REAL')
        
        # Totales calculados
        df['TOTAL_LLAMADAS'] = df['RECIBIDAS_FIN'] + df['RECIBIDAS_PREPAGO']
        df['TOTAL_ATENDIDAS'] = df['ATENDIDAS_FIN'] + df['ATENDIDAS_PREPAGO']
        df['TOTAL_PERDIDAS'] = df['PERDIDAS_FIN'] + df['PERDIDAS_PREPAGO']
        
        with st.sidebar:
            st.header("📞 Panel de Control") # Volvimos al nombre viejo
            
            # Selector de Modo con Iconos como en la foto
            modo = st.radio("Modo de Análisis:", ["📅 Evolución Mensual", "🔄 Comparativa Interanual"])
            
            st.divider()
            
            # Filtro de Tipo (Cosmético por ahora si no hay datos desagregados, pero mantiene la estética)
            segmento = st.selectbox("Filtrar por Tipo:", ["Todo Unificado", "Solo Financiadores", "Solo Prepago"])

        # ---------------------------------------------------------
        # VISTA 1: EVOLUCIÓN MENSUAL (La clásica)
        # ---------------------------------------------------------
        if modo == "📅 Evolución Mensual":
            # Selector de Mes
            fechas = sorted(df['FECHA_REAL'].unique(), reverse=True)
            sel = st.selectbox("Seleccionar Mes:", fechas, format_func=lambda x: x.strftime("%B-%Y").capitalize())
            
            # Filtramos la fila exacta
            d = df[df['FECHA_REAL'] == sel].iloc[0]
            
            # Lógica de segmentos
            if segmento == "Solo Financiadores": rec, aten, perd = d['RECIBIDAS_FIN'], d['ATENDIDAS_FIN'], d['PERDIDAS_FIN']
            elif segmento == "Solo Prepago": rec, aten, perd = d['RECIBIDAS_PREPAGO'], d['ATENDIDAS_PREPAGO'], d['PERDIDAS_PREPAGO']
            else: rec, aten, perd = d['TOTAL_LLAMADAS'], d['TOTAL_ATENDIDAS'], d['TOTAL_PERDIDAS']
            
            sla = (aten/rec*100) if rec>0 else 0
            
            # TARJETAS DE KPIs (Con colores oscuros como en la foto)
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("📞 Llamadas Recibidas", f"{rec:,.0f}")
            k2.metric("✅ Atendidas", f"{aten:,.0f}", f"{(aten/rec*100):.1f}% Eficiencia")
            k3.metric("❌ Perdidas (Abandono)", f"{perd:,.0f}", f"-{(perd/rec*100):.1f}%", delta_color="inverse")
            k4.metric("📊 Nivel de Servicio", f"{sla:.1f}%", "Meta > 90%")
            
            st.markdown("---")
            
            # GRÁFICOS (Recuperando el diseño de 3 barras)
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Nivel de Atención")
                # Gráfico de Dona Verde/Rojo
                fig_pie = px.pie(names=['Atendidas', 'Perdidas'], values=[aten, perd], 
                             color_discrete_sequence=['#4CAF50', '#FF5252'], hole=0.4)
                fig_pie.update_layout(showlegend=True)
                st.plotly_chart(fig_pie, use_container_width=True)

            with col2:
                st.subheader("Cantidad de turnos (Ts y AS)")
                # AQUÍ ESTÁ LA MAGIA: Recuperamos la barra 'TOTAL' y los colores exactos
                dat_bar = {
                    'Concepto': ['Consultorios (Tel)', 'Prácticas (Tel)', 'Total (Tel)'],
                    'Cantidad': [d['TURNOS_CONS_TEL'], d['TURNOS_PRACT_TEL'], d['TURNOS_TOTAL_TEL']],
                    'Color': ['#64B5F6', '#1976D2', '#FF8A80'] # Celeste, Azul, Rosa (Como en tu foto)
                }
                
                fig_bar = px.bar(dat_bar, x='Concepto', y='Cantidad', text='Cantidad')
                fig_bar.update_traces(marker_color=['#64B5F6', '#0D47A1', '#FF8A80'], textposition='auto')
                st.plotly_chart(fig_bar, use_container_width=True)

        # ---------------------------------------------------------
        # VISTA 2: COMPARATIVA INTERANUAL (La del gráfico de barras agrupado)
        # ---------------------------------------------------------
        else: 
            st.subheader("🔄 Análisis Interanual (Mismo mes, distintos años)")
            
            meses_n = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            m_nom = st.selectbox("¿Qué mes quieres comparar?", meses_n)
            m_num = meses_n.index(m_nom) + 1
            
            # Filtramos todos los años para ese mes
            df_i = df[df['FECHA_REAL'].dt.month == m_num].copy()
            
            if df_i.empty:
                st.warning("No hay datos históricos para este mes todavía.")
            else:
                df_i['AÑO'] = df_i['FECHA_REAL'].dt.year.astype(str)
                
                # Gráfico Comparativo (Barras Agrupadas: Verde vs Rojo)
                fig = go.Figure()
                fig.add_trace(go.Bar(x=df_i['AÑO'], y=df_i['TOTAL_ATENDIDAS'], name='Atendidas', marker_color='#4CAF50'))
                fig.add_trace(go.Bar(x=df_i['AÑO'], y=df_i['TOTAL_PERDIDAS'], name='Perdidas', marker_color='#FF5252'))
                
                fig.update_layout(barmode='group', title=f"Desempeño en {m_nom} (2023 - 2026)")
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("Ver Datos Históricos"):
                    st.dataframe(df_i[['AÑO', 'TOTAL_LLAMADAS', 'TOTAL_ATENDIDAS', 'TOTAL_PERDIDAS']], use_container_width=True)

    except Exception as e: st.error(f"Error en CC: {e}")

# ==============================================================================
# APP 3: GESTIÓN DE AUSENTISMO (LEEMOS TU COLUMNA MANUAL EXCEL)
# ==============================================================================
elif app_mode == "📉 Gestión de Ausentismo":
    st.title("📉 Tablero de Ausentismo y Licencias")
    st.markdown("---")

    @st.cache_data
    def cargar_ausencias():
        # Link BD_AUSENCIAS
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=2132722842&single=true&output=csv"
        return pd.read_csv(url)

    try:
        df_aus = cargar_ausencias()
        df_aus.columns = df_aus.columns.str.strip()
        df_aus['FECHA_INICIO'] = pd.to_datetime(df_aus['FECHA_INICIO'], dayfirst=True, errors='coerce')
        
        # BUSCAMOS TU COLUMNA MANUAL 'CONSULTORIOS_REALES'
        col_target = 'CONSULTORIOS_REALES'
        if col_target not in df_aus.columns:
            col_target = 'DIAS_CAIDOS' # Fallback si no está la columna
            st.warning("⚠️ Usando 'DIAS_CAIDOS' porque no encontré 'CONSULTORIOS_REALES'.")
        
        # Limpieza de números
        if df_aus[col_target].dtype == 'object':
            df_aus[col_target] = pd.to_numeric(df_aus[col_target].str.replace('.', '', regex=False), errors='coerce').fillna(0)
        else:
            df_aus[col_target] = pd.to_numeric(df_aus[col_target], errors='coerce').fillna(0)

        with st.sidebar:
            st.header("🎛️ Filtros Ausentismo")
            # Año
            if not df_aus['FECHA_INICIO'].dropna().empty:
                años = sorted(df_aus['FECHA_INICIO'].dt.year.dropna().unique())
                año_sel = st.selectbox("Año:", años, index=len(años)-1)
                df_filtered = df_aus[df_aus['FECHA_INICIO'].dt.year == año_sel]
            else:
                df_filtered = df_aus

            # Mes
            mapa_meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
            df_filtered['MES_NUM'] = df_filtered['FECHA_INICIO'].dt.month
            meses_disp = sorted(df_filtered['MES_NUM'].dropna().unique())
            meses_sel = st.multiselect("Mes(es):", options=meses_disp, format_func=lambda x: mapa_meses.get(x,x), default=meses_disp)
            if meses_sel: df_filtered = df_filtered[df_filtered['MES_NUM'].isin(meses_sel)]
            
            st.divider()
            for col in ['DEPARTAMENTO', 'SERVICIO', 'MOTIVO', 'PROFESIONAL']:
                if col in df_filtered.columns:
                    opciones = sorted(df_filtered[col].astype(str).unique())
                    sel = st.multiselect(f"{col.title()}:", opciones)
                    if sel: df_filtered = df_filtered[df_filtered[col].isin(sel)]

        if df_filtered.empty: st.warning("Sin datos."); st.stop()

        col1, col2, col3, col4 = st.columns(4)
        total_consultorios = df_filtered[col_target].sum()
        top_motivo = df_filtered['MOTIVO'].mode()[0] if not df_filtered['MOTIVO'].empty else "-"

        col1.metric("Consultorios Cancelados", f"{total_consultorios:,.0f}", help="Suma de la columna manual del Excel.")
        col2.metric("Eventos/Licencias", f"{len(df_filtered)}")
        col3.metric("Profesionales Que Cancelaron", f"{df_filtered['PROFESIONAL'].nunique()}")
        col4.metric("Motivo Principal", str(top_motivo))
        st.markdown("---")

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(df_filtered, values=col_target, names='MOTIVO', hole=0.4), use_container_width=True)
        with c2:
            d_serv = df_filtered.groupby('SERVICIO')[col_target].sum().reset_index().sort_values(col_target).tail(10)
            fig_bar = px.bar(d_serv, x=col_target, y='SERVICIO', orientation='h', text=col_target)
            fig_bar.update_traces(marker_color='#FF5252', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("🥇 Top Profesionales")
        d_prof = df_filtered.groupby('PROFESIONAL')[col_target].sum().reset_index().sort_values(col_target).tail(15)
        fig_prof = px.bar(d_prof, x=col_target, y='PROFESIONAL', orientation='h', text=col_target)
        fig_prof.update_traces(marker_color='#42A5F5', textposition='outside')
        fig_prof.update_layout(height=500)
        st.plotly_chart(fig_prof, use_container_width=True)

        with st.expander("📄 Ver Datos"):
            st.dataframe(df_filtered, use_container_width=True)

    except Exception as e: st.error(f"Error: {e}")
