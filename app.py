import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestión de Turnos", layout="wide")

# Título y Estilo
st.title("🏥 Dashboard de Gestión - CEMIC")
st.markdown("---")

# --- CONEXIÓN CON GOOGLE SHEETS (Segura) ---
# Esta función usa "Secretos" para no escribir la contraseña en el código
@st.cache_data(ttl=600) # Esto hace que no recargue el excel a cada clic (memoria caché)
def cargar_datos():
    # Definimos el alcance (permisos)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # Leemos las credenciales desde los "Secretos" de Streamlit
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    
    # Autorizamos y abrimos
    client = gspread.authorize(creds)
    
    # REEMPLAZA AQUI CON EL NOMBRE EXACTO DE TU ARCHIVO
    sheet = client.open("DATASET_APP_TEST") 
    worksheet = sheet.worksheet("BD_HISTORICO")
    
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# --- CARGA Y LIMPIEZA ---
try:
    df = cargar_datos()
    
    # Limpieza de fechas
    df['PERIODO'] = pd.to_datetime(df['PERIODO'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['PERIODO'])
    
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🎛️ Panel de Control")
    
    # 1. Selector de Fechas
    fechas_disponibles = sorted(df['PERIODO'].dt.strftime('%Y-%m-%d').unique().tolist())
    meses_sel = st.sidebar.multiselect(
        "1. Seleccionar Periodo:",
        options=fechas_disponibles,
        default=fechas_disponibles[0] if fechas_disponibles else None
    )
    
    # 2. Selector de Filas (Agrupación)
    cols_agrupar = ['DEPARTAMENTO', 'SERVICIO', 'SEDE', 'PROFESIONAL/EQUIPO', 'DIA_SEMANA']
    filas_sel = st.sidebar.multiselect(
        "2. Agrupar por:",
        options=cols_agrupar,
        default=['SERVICIO']
    )
    
    # 3. Selector de Valores (Métricas)
    cols_valores = ['TURNOS_MENSUAL', 'HS_MENSUAL', 'HS_SEMANAL', 'TURNOS DIARIOS']
    valores_sel = st.sidebar.multiselect(
        "3. Métricas a sumar:",
        options=cols_valores,
        default=['TURNOS_MENSUAL']
    )
    
    # --- ÁREA PRINCIPAL ---
    if st.sidebar.button("GENERAR TABLA"):
        if not meses_sel or not filas_sel or not valores_sel:
            st.error("⚠️ Por favor selecciona al menos una opción en cada filtro.")
        else:
            # Filtro de fecha
            mask = df['PERIODO'].isin(pd.to_datetime(meses_sel))
            df_filtrado = df[mask]
            
            # Tabla Dinámica
            tabla = pd.pivot_table(
                df_filtrado,
                index=filas_sel,
                values=valores_sel,
                aggfunc='sum',
                margins=True,
                margins_name='TOTAL GENERAL'
            )
            
            # Mensaje de éxito
            st.success(f"Mostrando datos de {len(meses_sel)} periodos seleccionados.")
            
            # Mostrar tabla interactiva
            st.dataframe(
                tabla.style.format("{:,.0f}").background_gradient(cmap='Blues'), 
                use_container_width=True,
                height=600
            )
            
            # Botón de descarga CSV
            csv = tabla.to_csv().encode('utf-8')
            st.download_button(
                "📥 Descargar Reporte en CSV",
                csv,
                "reporte_cemic.csv",
                "text/csv",
                key='download-csv'
            )

except Exception as e:
    st.warning("⚠️ Esperando conexión con Google Sheets...")
    st.info("Nota: Si ves esto al principio, es porque falta configurar las credenciales en Streamlit Cloud.")
    st.expander("Ver detalle del error (para el desarrollador)").write(e)
