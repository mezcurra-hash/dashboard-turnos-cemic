import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURACIÓN GLOBAL ---
st.set_page_config(page_title="Tablero de Gestión CEMIC", layout="wide", page_icon="🏥")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stMetricDelta"] svg { display: inline; }
    /* Estilo para tarjetas oscuras */
    div[data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #464b5f;
        padding: 10px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- MENÚ DE NAVEGACIÓN ---
with st.sidebar:
    st.image("https://cemic.edu.ar/assets/img/logo/logo-cemic.png", width=150)
    st.title("Navegación")
    app_mode = st.selectbox("Selecciona el Tablero:", 
                           ["🏥 Oferta de Turnos", "🎧 Call Center", "📉 Gestión de Ausentismo"])
    st.markdown("---")

# ==============================================================================
# APP 1: OFERTA DE TURNOS
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
        df.columns = df.columns.str.strip() # Limpieza de espacios
        df['PERIODO'] = pd.to_datetime(df['PERIODO'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['PERIODO'])

        def formato_fecha_linda(fecha):
            meses = {1:"Ene", 2:"Feb", 3:"Mar", 4:"Abr", 5:"May", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dic"}
            return f"{meses[fecha.month]}-{fecha.year}"

        with st.sidebar:
            st.header("🎛️ Filtros Turnos")
            modo_analisis = st.radio("Vista:", ["📊 Global", "🆚 Comparativa"], horizontal=True)
            fechas_unicas = sorted(df['PERIODO'].unique())
            
            if not fechas_unicas:
                st.error("No hay fechas válidas.")
                st.stop()

            if modo_analisis == "📊 Global":
                meses_sel = st.multiselect("Periodo:", options=fechas_unicas, default=[fechas_unicas[0]], format_func=formato_fecha_linda)
            else:
                c1, c2 = st.columns(2)
                idx_a = max(0, len(fechas_unicas)-2)
                periodo_a = c1.selectbox("Base:", fechas_unicas, index=idx_a, format_func=formato_fecha_linda)
                periodo_b = c2.selectbox("Actual:", fechas_unicas, index=len(fechas_unicas)-1, format_func=formato_fecha_linda)
                meses_sel = [periodo_a, periodo_b]

            with st.expander("🔍 Filtros Avanzados", expanded=False):
                filtro_tipo = st.radio("Modalidad:", ["Todos", "Programada (AP)", "No Programada (ANP)"], horizontal=True)
                depto = st.multiselect("Depto:", sorted(df['DEPARTAMENTO'].astype(str).unique()))
                serv = st.multiselect("Servicio:", sorted(df['SERVICIO'].astype(str).unique()))
                sede = st.multiselect("Sede:", sorted(df['SEDE'].astype(str).unique()))
                prof = st.multiselect("Profesional:", sorted(df['PROFESIONAL/EQUIPO'].astype(str).unique()))

        if not meses_sel: st.stop()
        df_f = df[df['PERIODO'].isin(meses_sel)]
        
        # Lógica de Tipo de Atención
        if filtro_tipo == "Programada (AP)" and 'TIPO_ATENCION' in df_f.columns:
            df_f = df_f[df_f['TIPO_ATENCION'] == 'AP']
        elif filtro_tipo == "No Programada (ANP)" and 'TIPO_ATENCION' in df_f.columns:
            df_f = df_f[df_f['TIPO_ATENCION'] == 'ANP']

        if depto: df_f = df_f[df_f['DEPARTAMENTO'].isin(depto)]
        if serv: df_f = df_f[df_f['SERVICIO'].isin(serv)]
        if sede: df_f = df_f[df_f['SEDE'].isin(sede)]
        if prof: df_f = df_f[df_f['PROFESIONAL/EQUIPO'].isin(prof)]

        if df_f.empty: st.error("Sin datos."); st.stop()

        # VISUALIZACIÓN
        metrica = 'TURNOS_MENSUAL'
        if modo_analisis == "📊 Global":
            total = df_f[metrica].sum()
            st.metric("Total Turnos", f"{total:,.0f}")
            st.bar_chart(df_f.groupby('SERVICIO')[metrica].sum())
        else:
            df_a, df_b = df_f[df_f['PERIODO']==periodo_a], df_f[df_f['PERIODO']==periodo_b]
            va, vb = df_a[metrica].sum(), df_b[metrica].sum()
            st.metric("Variación Turnos", f"{vb:,.0f}", f"{vb-va:,.0f} ({(vb-va)/va*100:.1f}%)")
            
            ga = df_a.groupby('SERVICIO')[metrica].sum().rename("Base")
            gb = df_b.groupby('SERVICIO')[metrica].sum().rename("Actual")
            st.bar_chart(pd.concat([ga, gb], axis=1).fillna(0))

    except Exception as e: st.error(f"Error en Turnos: {e}")

# ==============================================================================
# APP 2: CALL CENTER (LÓGICA ROBUSTA)
# ==============================================================================
elif app_mode == "🎧 Call Center":
    st.title("🎧 Call Center - CEMIC")
    st.markdown("---")

    @st.cache_data
    def cargar_datos_cc():
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTOxpr7RRNTLGO96pUK8HJ0iy2ZHeqNpiR7OelleljCVoWPuJCO26q5z66VisWB76khl7Tmsqh5CqNC/pub?gid=0&single=true&output=csv"
        df = pd.read_csv(url, dtype=str).fillna(0)
        cols = ['RECIBIDAS_FIN', 'ATENDIDAS_FIN', 'PERDIDAS_FIN', 'RECIBIDAS_PREPAGO', 'ATENDIDAS_PREPAGO', 'PERDIDAS_PREPAGO', 'TURNOS_TOTAL_TEL', 'TURNOS_CONS_TEL', 'TURNOS_PRACT_TEL']
        for c in cols: 
            if c in df.columns: df[c] = pd.to_numeric(df[c].str.replace('.','', regex=False), errors='coerce').fillna(0)
        return df

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
        
        df['TOTAL_LLAMADAS'] = df['RECIBIDAS_FIN'] + df['RECIBIDAS_PREPAGO']
        df['TOTAL_ATENDIDAS'] = df['ATENDIDAS_FIN'] + df['ATENDIDAS_PREPAGO']
        df['TOTAL_PERDIDAS'] = df['PERDIDAS_FIN'] + df['PERDIDAS_PREPAGO']
        
        # --- Sidebar CC ---
        with st.sidebar:
            st.header("📞 Filtros Call Center")
            modo = st.radio("Análisis:", ["📅 Mensual", "🔄 Interanual"])
            segmento = st.selectbox("Tipo:", ["Todo Unificado", "Solo Financiadores", "Solo Prepago"])

        # --- Visual CC ---
        if modo == "📅 Mensual":
            fechas = sorted(df['FECHA_REAL'].unique(), reverse=True)
            sel = st.selectbox("Mes:", fechas, format_func=lambda x: x.strftime("%B-%Y").capitalize())
            d = df[df['FECHA_REAL'] == sel].iloc[0]
            
            if segmento == "Solo Financiadores": rec, aten, perd = d['RECIBIDAS_FIN'], d['ATENDIDAS_FIN'], d['PERDIDAS_FIN']
            elif segmento == "Solo Prepago": rec, aten, perd = d['RECIBIDAS_PREPAGO'], d['ATENDIDAS_PREPAGO'], d['PERDIDAS_PREPAGO']
            else: rec, aten, perd = d['TOTAL_LLAMADAS'], d['TOTAL_ATENDIDAS'], d['TOTAL_PERDIDAS']
            
            sla = (aten/rec*100) if rec>0 else 0
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("📞 Recibidas", f"{rec:,.0f}")
            c2.metric("✅ Atendidas", f"{aten:,.0f}")
            c3.metric("❌ Perdidas", f"{perd:,.0f}", delta_color="inverse", delta=f"{(perd/rec*100):.1f}%")
            c4.metric("📊 SLA", f"{sla:.1f}%", delta="Meta >90%")
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Distribución")
                fig = px.pie(names=['Atendidas', 'Perdidas'], values=[aten, perd], color_discrete_sequence=['#4CAF50', '#FF5252'], hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.subheader("Tipos de Turnos (Tel)")
                dat_bar = {'Tipo': ['Consultorios', 'Prácticas'], 'Cant': [d['TURNOS_CONS_TEL'], d['TURNOS_PRACT_TEL']]}
                st.plotly_chart(px.bar(dat_bar, x='Tipo', y='Cant'), use_container_width=True)

        else: # Interanual
            meses_n = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            m_nom = st.selectbox("Mes a comparar:", meses_n)
            m_num = meses_n.index(m_nom) + 1
            df_i = df[df['FECHA_REAL'].dt.month == m_num].copy()
            if df_i.empty: st.warning("Sin datos."); st.stop()
            df_i['AÑO'] = df_i['FECHA_REAL'].dt.year.astype(str)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_i['AÑO'], y=df_i['TOTAL_ATENDIDAS'], name='Atendidas', marker_color='#4CAF50'))
            fig.add_trace(go.Bar(x=df_i['AÑO'], y=df_i['TOTAL_PERDIDAS'], name='Perdidas', marker_color='#FF5252'))
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e: st.error(f"Error en CC: {e}")

# ==============================================================================
# APP 3: GESTIÓN DE AUSENTISMO (¡CONECTADO!)
# ==============================================================================
elif app_mode == "📉 Gestión de Ausentismo":
    st.title("📉 Tablero de Ausentismo y Licencias")
    st.markdown("---")

    # 1. CARGA DE AUSENCIAS
    @st.cache_data
    def cargar_ausencias():
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=2132722842&single=true&output=csv"
        return pd.read_csv(url)

    # 2. CARGA DE AGENDA (Para saber qué días trabaja cada uno)
    @st.cache_data
    def cargar_agenda_profs():
        # Usamos el mismo link de la Oferta de Turnos que tiene la columna DIA_SEMANA
        url_agenda = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=1524527213&single=true&output=csv"
        return pd.read_csv(url_agenda)

    try:
        df_aus = cargar_ausencias()
        df_agenda = cargar_agenda_profs()
        
        # --- LIMPIEZA Y PREPARACIÓN ---
        df_aus.columns = df_aus.columns.str.strip()
        df_agenda.columns = df_agenda.columns.str.strip()

        # Convertir fechas
        df_aus['FECHA_INICIO'] = pd.to_datetime(df_aus['FECHA_INICIO'], dayfirst=True, errors='coerce')
        df_aus['FECHA_FIN'] = pd.to_datetime(df_aus['FECHA_FIN'], dayfirst=True, errors='coerce')
        
        # Mapeo de días de texto a número (Python: Lunes=0, Domingo=6)
        # Aseguramos que el texto esté limpio (Mayúsculas, sin tildes)
        mapa_dias = {
            'LUNES': 0, 'MARTES': 1, 'MIERCOLES': 2, 'MIÉRCOLES': 2, 
            'JUEVES': 3, 'VIERNES': 4, 'SABADO': 5, 'SÁBADO': 5, 'DOMINGO': 6
        }

        # Preparamos la Agenda: Creamos un diccionario {Profesional: [Lista de días que trabaja]}
        # Ejemplo: {'PEREZ JUAN': [0, 3]} (Lunes y Jueves)
        agenda_dict = {}
        
        # Normalizamos nombre del profesional y dia
        if 'PROFESIONAL/EQUIPO' in df_agenda.columns and 'DIA_SEMANA' in df_agenda.columns:
            # Iteramos para llenar el diccionario
            for _, row in df_agenda.iterrows():
                prof = str(row['PROFESIONAL/EQUIPO']).strip().upper()
                dia_txt = str(row['DIA_SEMANA']).strip().upper()
                dia_num = mapa_dias.get(dia_txt)
                
                if dia_num is not None:
                    if prof not in agenda_dict:
                        agenda_dict[prof] = []
                    # Agregamos el día (si trabaja doble turno el martes, agregamos dos veces el 1)
                    # Esto permite contar 2 consultorios cancelados si falta un martes.
                    agenda_dict[prof].append(dia_num)
        
        # --- FUNCIÓN MAESTRA DE CÁLCULO ---
        def calcular_consultorios_perdidos(row):
            prof = str(row['PROFESIONAL']).strip().upper()
            inicio = row['FECHA_INICIO']
            fin = row['FECHA_FIN']
            
            # Si faltan fechas, devolvemos 0
            if pd.isna(inicio) or pd.isna(fin): return 0
            
            # Si el profesional NO está en la agenda (ej: es nuevo o nombre mal escrito),
            # usamos el método "tonto" (días corridos).
            if prof not in agenda_dict:
                return (fin - inicio).days + 1
            
            # Si ESTÁ en agenda, hacemos el cálculo exacto
            dias_laborables = agenda_dict[prof] # Lista de días ej: [0, 3]
            consultorios_cancelados = 0
            
            # Recorremos cada día de la licencia
            dias_licencia = (fin - inicio).days + 1
            for i in range(dias_licencia):
                dia_actual = inicio + pd.Timedelta(days=i)
                dia_semana_actual = dia_actual.weekday() # 0=Lunes, etc.
                
                # Contamos cuántas veces aparece ese día en su agenda
                # Si trabaja 2 veces el martes, .count() sumará 2.
                coincidencias = dias_laborables.count(dia_semana_actual)
                consultorios_cancelados += coincidencias
                
            return consultorios_cancelados

        # APLICAMOS LA MAGIA 🪄
        # Creamos la columna real calculada
        df_aus['CONSULTORIOS_CANCELADOS'] = df_aus.apply(calcular_consultorios_perdidos, axis=1)

        # --- FILTROS (Igual que antes) ---
        with st.sidebar:
            st.header("🎛️ Filtros Ausentismo")
            
            # Filtro Año
            if not df_aus['FECHA_INICIO'].dropna().empty:
                años = sorted(df_aus['FECHA_INICIO'].dt.year.dropna().unique())
                año_sel = st.selectbox("Año:", años, index=len(años)-1)
                df_filtered = df_aus[df_aus['FECHA_INICIO'].dt.year == año_sel]
            else:
                df_filtered = df_aus

            # Filtro Mes
            mapa_meses_nombre = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
            df_filtered['MES_NUM'] = df_filtered['FECHA_INICIO'].dt.month
            meses_disponibles = sorted(df_filtered['MES_NUM'].dropna().unique())
            meses_sel = st.multiselect("Mes(es):", options=meses_disponibles, format_func=lambda x: mapa_meses_nombre.get(x, x), default=meses_disponibles)
            if meses_sel: df_filtered = df_filtered[df_filtered['MES_NUM'].isin(meses_sel)]

            st.divider()
            
            # Filtros extra
            if 'DEPARTAMENTO' in df_filtered.columns:
                depto = st.multiselect("Departamento:", sorted(df_filtered['DEPARTAMENTO'].astype(str).unique()))
                if depto: df_filtered = df_filtered[df_filtered['DEPARTAMENTO'].isin(depto)]
            if 'SERVICIO' in df_filtered.columns:
                servicio = st.multiselect("Servicio:", sorted(df_filtered['SERVICIO'].astype(str).unique()))
                if servicio: df_filtered = df_filtered[df_filtered['SERVICIO'].isin(servicio)]
            if 'PROFESIONAL' in df_filtered.columns:
                lista_profs = sorted(df_filtered['PROFESIONAL'].astype(str).unique())
                prof_sel = st.multiselect("Profesional:", lista_profs)
                if prof_sel: df_filtered = df_filtered[df_filtered['PROFESIONAL'].isin(prof_sel)]
            if 'MOTIVO' in df_filtered.columns:
                motivo = st.multiselect("Motivo:", sorted(df_filtered['MOTIVO'].astype(str).unique()))
                if motivo: df_filtered = df_filtered[df_filtered['MOTIVO'].isin(motivo)]

        if df_filtered.empty: st.warning("⚠️ Sin datos."); st.stop()

        # --- KPI PRINCIPALES ---
        col1, col2, col3, col4 = st.columns(4)
        
        # AQUI USAMOS LA NUEVA COLUMNA CALCULADA
        total_consultorios = df_filtered['CONSULTORIOS_CANCELADOS'].sum()
        total_eventos = len(df_filtered)
        total_personas = df_filtered['PROFESIONAL'].nunique()
        top_motivo = df_filtered['MOTIVO'].mode()[0] if not df_filtered['MOTIVO'].empty else "-"

        col1.metric("Consultorios Cancelados (Real)", f"{total_consultorios:,.0f}", help="Cálculo exacto cruzando días de licencia con días de agenda del profesional.")
        col2.metric("Eventos/Licencias", f"{total_eventos}")
        col3.metric("Profesionales Únicos", f"{total_personas}")
        col4.metric("Motivo Principal", str(top_motivo))
        
        st.markdown("---")

        # --- GRÁFICOS ---
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🍰 Motivos")
            # Usamos CONSULTORIOS_CANCELADOS como valor, para ver impacto real
            fig_pie = px.pie(df_filtered, values='CONSULTORIOS_CANCELADOS', names='MOTIVO', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            st.subheader("🏥 Impacto por Servicio")
            df_serv = df_filtered.groupby('SERVICIO')['CONSULTORIOS_CANCELADOS'].sum().reset_index().sort_values('CONSULTORIOS_CANCELADOS', ascending=True).tail(10)
            fig_bar = px.bar(df_serv, x='CONSULTORIOS_CANCELADOS', y='SERVICIO', orientation='h', text='CONSULTORIOS_CANCELADOS')
            fig_bar.update_traces(marker_color='#FF5252', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("🥇 Top Profesionales (Mayor impacto en oferta)")
        df_prof_rank = df_filtered.groupby('PROFESIONAL')['CONSULTORIOS_CANCELADOS'].sum().reset_index().sort_values('CONSULTORIOS_CANCELADOS', ascending=True).tail(15)
        fig_prof = px.bar(df_prof_rank, x='CONSULTORIOS_CANCELADOS', y='PROFESIONAL', orientation='h', text='CONSULTORIOS_CANCELADOS')
        fig_prof.update_traces(marker_color='#42A5F5', textposition='outside')
        fig_prof.update_layout(height=500)
        st.plotly_chart(fig_prof, use_container_width=True)

        with st.expander("📄 Ver Detalle (Cálculo)"):
            st.info("La columna 'CONSULTORIOS_CANCELADOS' muestra el impacto real según la agenda.")
            st.dataframe(df_filtered[['FECHA_INICIO', 'FECHA_FIN', 'PROFESIONAL', 'SERVICIO', 'MOTIVO', 'DIAS_CAIDOS', 'CONSULTORIOS_CANCELADOS']], use_container_width=True)

    except Exception as e:
        st.error("Error en el cálculo.")
        st.write(e)
