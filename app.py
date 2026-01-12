import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURACIÓN GLOBAL (Solo se pone una vez) ---
st.set_page_config(page_title="Tablero de Gestión CEMIC", layout="wide", page_icon="🏥")

# Estilos CSS Globales
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stMetricDelta"] svg { display: inline; }
    
    /* Estilo para tarjetas oscuras (usado en Call Center) */
    div[data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #464b5f;
        padding: 10px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- MENÚ DE NAVEGACIÓN PRINCIPAL ---
with st.sidebar:
    st.image("https://cemic.edu.ar/assets/img/logo/logo-cemic.png", width=150)
    st.title("Navegación")
    app_mode = st.selectbox("Selecciona el Tablero:", 
                           ["🏥 Oferta de Turnos (Consultorios)", "🎧 Call Center (Llamados)"])
    st.markdown("---")

# ==============================================================================
# APP 1: OFERTA DE TURNOS (CONSULTORIOS)
# ==============================================================================
if app_mode == "🏥 Oferta de Turnos (Consultorios)":
    
    st.title("🏥 Oferta de Turnos de Consultorio - CEMIC")
    st.markdown("---")

    # --- CARGA DE DATOS OFERTA ---
    @st.cache_data
    def cargar_datos_oferta():
        url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=1524527213&single=true&output=csv"
        df = pd.read_csv(url_csv)
        return df

    try:
        df = cargar_datos_oferta()
        
        # --- LIMPIEZA ---
        # Limpieza de nombres de columnas por seguridad
        df.columns = df.columns.str.strip() 

        df['PERIODO'] = pd.to_datetime(df['PERIODO'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['PERIODO'])

        def formato_fecha_linda(fecha):
            meses = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
                9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            return f"{meses[fecha.month]}-{fecha.year}"

        # --- BARRA LATERAL ESPECÍFICA ---
        with st.sidebar:
            st.header("🎛️ Filtros de Turnos")
            
            modo_analisis = st.radio(
                "Vista:",
                ["📊 Análisis Global", "🆚 Comparativa Mensual"],
                horizontal=True
            )
            st.divider()

            fechas_unicas = sorted(df['PERIODO'].unique())
            
            if len(fechas_unicas) == 0:
                st.error("No hay fechas en el Excel.")
                st.stop()

            if modo_analisis == "📊 Análisis Global":
                meses_sel = st.multiselect(
                    "Periodo:", 
                    options=fechas_unicas, 
                    default=[fechas_unicas[0]], 
                    format_func=formato_fecha_linda
                )
            else:
                col1, col2 = st.columns(2)
                idx_a = max(0, len(fechas_unicas)-2)
                idx_b = len(fechas_unicas)-1
                
                with col1:
                    periodo_a = st.selectbox("Base:", options=fechas_unicas, index=idx_a, format_func=formato_fecha_linda)
                with col2:
                    periodo_b = st.selectbox("Actual:", options=fechas_unicas, index=idx_b, format_func=formato_fecha_linda)
                meses_sel = [periodo_a, periodo_b]

            with st.expander("🔍 Filtros Específicos", expanded=True):
                st.subheader("Tipo de Prestación")
                filtro_tipo_atencion = st.radio(
                    "Modalidad:",
                    ["Todos", "Programada (AP)", "No Programada (ANP)"],
                    index=0,
                    horizontal=True
                )
                st.divider()

                deptos = sorted(df['DEPARTAMENTO'].astype(str).unique())
                filtro_depto = st.multiselect("Depto:", deptos)
                
                servicios = sorted(df['SERVICIO'].astype(str).unique())
                filtro_servicio = st.multiselect("Servicio:", servicios)
                
                sedes = sorted(df['SEDE'].astype(str).unique())
                filtro_sede = st.multiselect("Sede:", sedes)
                
                profs = sorted(df['PROFESIONAL/EQUIPO'].astype(str).unique())
                filtro_prof = st.multiselect("Profesional:", profs)

            st.divider()
            
            cols_texto = df.select_dtypes(include=['object']).columns.tolist()
            default_fila = ['SERVICIO'] if 'SERVICIO' in cols_texto else [cols_texto[0]]
            filas_sel = st.multiselect("Agrupar por:", cols_texto, default=default_fila)
            
            cols_num = df.select_dtypes(include=['float', 'int']).columns.tolist()
            val_sel = st.multiselect("Métricas:", cols_num, default=['TURNOS_MENSUAL'] if 'TURNOS_MENSUAL' in cols_num else [cols_num[0]])

        # --- LÓGICA DE FILTRADO ---
        if not meses_sel or not filas_sel or not val_sel:
            st.warning("Selecciona opciones.")
            st.stop()

        mask = df['PERIODO'].isin(meses_sel)
        df_filtered = df[mask]

        if filtro_tipo_atencion == "Programada (AP)":
            if 'TIPO_ATENCION' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['TIPO_ATENCION'] == 'AP']
            else:
                st.error("⚠️ No encuentro la columna 'TIPO_ATENCION'.")
                
        elif filtro_tipo_atencion == "No Programada (ANP)":
            if 'TIPO_ATENCION' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['TIPO_ATENCION'] == 'ANP']
            else:
                st.error("⚠️ No encuentro la columna 'TIPO_ATENCION'.")

        if filtro_depto: df_filtered = df_filtered[df_filtered['DEPARTAMENTO'].isin(filtro_depto)]
        if filtro_servicio: df_filtered = df_filtered[df_filtered['SERVICIO'].isin(filtro_servicio)]
        if filtro_sede: df_filtered = df_filtered[df_filtered['SEDE'].isin(filtro_sede)]
        if filtro_prof: df_filtered = df_filtered[df_filtered['PROFESIONAL/EQUIPO'].isin(filtro_prof)]

        if df_filtered.empty:
            st.error("⚠️ No hay datos para esa selección.")
            st.stop()

        # --- VISUALIZACIÓN ---
        if modo_analisis == "📊 Análisis Global":
            totales = df_filtered[val_sel].sum()
            nombres_meses = [formato_fecha_linda(m) for m in meses_sel]
            st.subheader(f"Resumen ({filtro_tipo_atencion}): {', '.join(nombres_meses)}")
            
            cols = st.columns(len(val_sel))
            for i, metrica in enumerate(val_sel):
                cols[i].metric(metrica, f"{totales[metrica]:,.0f}")
            
            st.markdown("---")
            t1, t2 = st.tabs(["📊 Gráfico", "📄 Tabla"])
            with t1:
                st.bar_chart(df_filtered.groupby(filas_sel[0])[val_sel].sum())
            with t2:
                tabla = pd.pivot_table(df_filtered, index=filas_sel, values=val_sel, aggfunc='sum', margins=True, margins_name='TOTAL')
                st.dataframe(tabla.style.format("{:,.0f}").background_gradient(cmap='Blues'), use_container_width=True)

        else: # Comparativa
            nombre_a = formato_fecha_linda(periodo_a)
            nombre_b = formato_fecha_linda(periodo_b)
            st.subheader(f"🆚 Comparativa ({filtro_tipo_atencion}): {nombre_a} vs {nombre_b}")
            
            df_a = df_filtered[df_filtered['PERIODO'] == periodo_a]
            df_b = df_filtered[df_filtered['PERIODO'] == periodo_b]
            
            cols = st.columns(len(val_sel))
            for i, metrica in enumerate(val_sel):
                va = df_a[metrica].sum()
                vb = df_b[metrica].sum()
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

    except Exception as e:
        st.error("Error técnico en Oferta de Turnos:")
        st.write(e)


# ==============================================================================
# APP 2: CALL CENTER
# ==============================================================================
elif app_mode == "🎧 Call Center (Llamados)":

    st.title("Call Center - CEMIC")
    st.markdown("---")

    # --- CARGA DE DATOS CALL CENTER ---
    @st.cache_data
    def cargar_datos_cc():
        url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTOxpr7RRNTLGO96pUK8HJ0iy2ZHeqNpiR7OelleljCVoWPuJCO26q5z66VisWB76khl7Tmsqh5CqNC/pub?gid=0&single=true&output=csv" 
        df = pd.read_csv(url_csv, dtype=str)
        
        cols_numericas = [
            'RECIBIDAS_FIN', 'ATENDIDAS_FIN', 'PERDIDAS_FIN', 
            'RECIBIDAS_PREPAGO', 'ATENDIDAS_PREPAGO', 'PERDIDAS_PREPAGO',
            'TURNOS_PRACT_TEL', 'TURNOS_CONS_TEL', 'TURNOS_TOTAL_TEL'
        ]
        
        for col in cols_numericas:
            if col in df.columns:
                df[col] = df[col].str.replace('.', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.fillna(0)
        return df

    def parsear_fecha_custom(texto_fecha):
        if pd.isna(texto_fecha): return None
        texto = str(texto_fecha).lower().strip().replace(".", "")
        
        meses = {
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12,
            'jan': 1, 'apr': 4, 'aug': 8, 'dec': 12 
        }
        
        partes = texto.replace("-", " ").split()
        if len(partes) < 2: return None
        
        mes_txt = partes[0][:3] 
        anio_txt = partes[1]
        
        if len(anio_txt) == 2: anio_txt = "20" + anio_txt
        
        num_mes = meses.get(mes_txt)
        if num_mes:
            return pd.Timestamp(year=int(anio_txt), month=num_mes, day=1)
        return None

    try:
        df = cargar_datos_cc()
        
        df['FECHA_REAL'] = df['MES'].apply(parsear_fecha_custom)
        df = df.dropna(subset=['FECHA_REAL']).sort_values('FECHA_REAL')
        
        df['TOTAL_LLAMADAS'] = df['RECIBIDAS_FIN'] + df['RECIBIDAS_PREPAGO']
        df['TOTAL_ATENDIDAS'] = df['ATENDIDAS_FIN'] + df['ATENDIDAS_PREPAGO']
        df['TOTAL_PERDIDAS'] = df['PERDIDAS_FIN'] + df['PERDIDAS_PREPAGO']
        
        df['SLA_GLOBAL'] = (df['TOTAL_ATENDIDAS'] / df['TOTAL_LLAMADAS']) * 100

        # --- BARRA LATERAL CC ---
        with st.sidebar:
            st.header("📞 Filtros Call Center")
            modo = st.radio("Modo de Análisis:", ["📅 Evolución Mensual", "🔄 Comparativa Interanual"])
            st.divider()
            segmento = st.selectbox("Filtrar por Tipo:", ["Todo Unificado", "Solo Financiadores", "Solo Prepago"])
            st.divider()
            st.info("💡 Tip: La 'Comparativa Interanual' busca automáticamente el mismo mes en años anteriores.")

        # --- VISUALIZACIÓN CC ---
        if modo == "📅 Evolución Mensual":
            fechas_dispo = sorted(df['FECHA_REAL'].unique(), reverse=True)
            fecha_sel = st.selectbox("Seleccionar Mes:", fechas_dispo, format_func=lambda x: x.strftime("%B-%Y").capitalize())
            
            datos_mes = df[df['FECHA_REAL'] == fecha_sel].iloc[0]
            
            if segmento == "Solo Financiadores":
                rec, aten, perd = datos_mes['RECIBIDAS_FIN'], datos_mes['ATENDIDAS_FIN'], datos_mes['PERDIDAS_FIN']
            elif segmento == "Solo Prepago":
                rec, aten, perd = datos_mes['RECIBIDAS_PREPAGO'], datos_mes['ATENDIDAS_PREPAGO'], datos_mes['PERDIDAS_PREPAGO']
            else:
                rec, aten, perd = datos_mes['TOTAL_LLAMADAS'], datos_mes['TOTAL_ATENDIDAS'], datos_mes['TOTAL_PERDIDAS']
            
            sla_mes = (aten / rec * 100) if rec > 0 else 0
            pct_perdidas = (perd / rec * 100) if rec > 0 else 0

            color_delta_perdidas = "normal" if pct_perdidas > 10 else "inverse"
            color_delta_sla = "normal" if sla_mes >= 90 else "inverse"

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("📞 Llamadas Recibidas", f"{rec:,.0f}")
            c2.metric("✅ Atendidas", f"{aten:,.0f}", delta=f"{(aten/rec*100):.1f}%")
            c3.metric("❌ Perdidas (Abandono)", f"{perd:,.0f}", delta=f"-{pct_perdidas:.1f}%", delta_color=color_delta_perdidas)
            c4.metric("📊 Nivel de Servicio", f"{sla_mes:.1f}%", delta="Meta: >90%", delta_color=color_delta_sla)

            st.markdown("---")

            col_graf1, col_graf2 = st.columns([1, 1])
            
            with col_graf1:
                st.subheader("Nivel de Atención")
                df_pie = pd.DataFrame({
                    'Estado': ['Atendidas', 'Perdidas'],
                    'Cantidad': [aten, perd]
                })
                colores_fijos = {'Atendidas': '#4CAF50', 'Perdidas': '#FF5252'}
                fig_pie = px.pie(
                    df_pie, values='Cantidad', names='Estado',
                    color='Estado', color_discrete_map=colores_fijos, hole=0.4
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with col_graf2:
                st.subheader("Cantidad de turnos (Ts y AS)")
                datos_canales = {
                    'Canal': ['Consultorios (Tel)', 'Prácticas (Tel)', 'Total (Tel)'],
                    'Turnos': [datos_mes['TURNOS_CONS_TEL'], datos_mes['TURNOS_PRACT_TEL'], datos_mes['TURNOS_TOTAL_TEL']]
                }
                fig_bar = px.bar(datos_canales, x='Canal', y='Turnos', color='Canal')
                st.plotly_chart(fig_bar, use_container_width=True)

        else: # Comparativa Interanual
            st.subheader("🔄 Análisis Interanual (Mismo mes, distintos años)")
            meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            mes_target_nombre = st.selectbox("¿Qué mes quieres comparar?", meses_nombres)
            mes_target_num = meses_nombres.index(mes_target_nombre) + 1
            
            df_interanual = df[df['FECHA_REAL'].dt.month == mes_target_num].copy()
            
            if df_interanual.empty:
                st.warning(f"No encontré datos para {mes_target_nombre}.")
                st.stop()
                
            df_interanual['AÑO'] = df_interanual['FECHA_REAL'].dt.year.astype(str)
            
            tab1, tab2 = st.tabs(["📈 Evolución Visual", "📄 Datos"])
            
            with tab1:
                fig_inter = go.Figure()
                fig_inter.add_trace(go.Bar(x=df_interanual['AÑO'], y=df_interanual['TOTAL_ATENDIDAS'], name='Atendidas', marker_color='#4CAF50'))
                fig_inter.add_trace(go.Bar(x=df_interanual['AÑO'], y=df_interanual['TOTAL_PERDIDAS'], name='Perdidas', marker_color='#FF5252'))
                fig_inter.update_layout(barmode='group', title=f"Desempeño en {mes_target_nombre}")
                st.plotly_chart(fig_inter, use_container_width=True)
                st.caption("Evolución de Turnos Telefónicos Totales:")
                st.line_chart(data=df_interanual, x='AÑO', y='TURNOS_TOTAL_TEL')

            with tab2:
                st.dataframe(df_interanual[['AÑO', 'TOTAL_LLAMADAS', 'TOTAL_ATENDIDAS', 'TOTAL_PERDIDAS', 'SLA_GLOBAL']].style.format({
                    'TOTAL_LLAMADAS': '{:,.0f}', 'TOTAL_ATENDIDAS': '{:,.0f}', 'TOTAL_PERDIDAS': '{:,.0f}', 'SLA_GLOBAL': '{:.1f}%'
                }))

    except Exception as e:
        st.error("Hubo un error cargando los datos del Call Center.")
        st.expander("Ver error técnico").write(e)
