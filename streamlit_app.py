# Importar librerías
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Eficiencia Energética de Asepeyo",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Carga y Cacheo de Datos ---
@st.cache_data
def load_data(file_path):
    """Carga, limpia y procesa los datos de la auditoría energética."""
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        # Unifica el renombrado para manejar tanto CSVs en inglés como en español
        df.rename(columns={
            'Center': 'Centro', 'Measure': 'Medida',
            'Energy Saved': 'Ahorro energético', 'Money Saved': 'Ahorro económico',
            'Investment': 'Inversión', 'Pay back period': 'Periodo de retorno',
            'Energía Ahorrada (kWh/año)': 'Ahorro energético', 'Dinero Ahorrado (€/año)': 'Ahorro económico',
            'Inversión (€)': 'Inversión', 'Periodo de Amortización (años)': 'Periodo de retorno'
        }, inplace=True)
        for col in ['Ahorro energético', 'Ahorro económico', 'Inversión', 'Periodo de retorno']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.fillna(0, inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo de datos en la ruta: {file_path}")
        return pd.DataFrame()
    except KeyError as e:
        st.error(f"Error de columna: No se encontró la columna requerida. Revise el CSV (columna faltante: {e})")
        return pd.DataFrame()

# --- Barra Lateral y Lógica de Carga de Datos ---
with st.sidebar:
    st.title('⚡ Filtros de análisis')
   
    DATA_DIR = "Data/"
    try:
        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
        if not files:
            st.warning("No se encontraron archivos CSV en la carpeta 'Data/'.")
            st.stop()
       
        selected_file = st.selectbox(
            "Seleccionar Auditoría", files,
            index=files.index("2025 Energy Audit summary - Sheet1.csv") if "2025 Energy Audit summary - Sheet1.csv" in files else 0
        )
        file_path = os.path.join(DATA_DIR, selected_file)
        df_original = load_data(file_path)
    except FileNotFoundError:
        st.error(f"El directorio '{DATA_DIR}' no fue encontrado.")
        st.stop()

    if not df_original.empty:
        tipo_analisis = st.radio(
            "Seleccionar Tipo de Análisis",
            ('Tipo de Medida', 'Tipo de Intervención', 'Impacto Financiero', 'Función de Negocio', 'Tipo de Ahorro Energético')
        )
        mostrar_porcentaje = st.toggle('Mostrar valores en porcentaje')
        st.markdown("---")
        vista_detallada = st.toggle('Mostrar vista detallada por centro')

        if 'last_file' not in st.session_state or st.session_state.last_file != selected_file:
            st.session_state.last_file = selected_file
            st.session_state.comunidades_seleccionadas = sorted(df_original['Comunidad Autónoma'].unique().tolist())
            st.session_state.centros_seleccionados = []
       
        lista_comunidades = sorted(df_original['Comunidad Autónoma'].unique().tolist())
        if st.button("Todas las Comunidades", use_container_width=True):
            st.session_state.comunidades_seleccionadas = lista_comunidades
       
        comunidades_seleccionadas = st.multiselect('Seleccionar Comunidades', lista_comunidades, default=st.session_state.comunidades_seleccionadas)
        st.session_state.comunidades_seleccionadas = comunidades_seleccionadas

        if vista_detallada:
            if comunidades_seleccionadas:
                centros_disponibles = sorted(df_original[df_original['Comunidad Autónoma'].isin(comunidades_seleccionadas)]['Centro'].unique().tolist())
                if not all(centro in centros_disponibles for centro in st.session_state.centros_seleccionados):
                    st.session_state.centros_seleccionados = centros_disponibles
               
                st.write("Selección de Centros:")
                col1, col2 = st.columns([0.7, 0.3])
                with col1:
                    centros_seleccionados = st.multiselect('Seleccionar Centros', centros_disponibles, default=st.session_state.centros_seleccionados, label_visibility="collapsed")
                with col2:
                    if st.button("Todos", help="Seleccionar todos los centros"):
                        st.session_state.centros_seleccionados = centros_disponibles
                        st.rerun()
                st.session_state.centros_seleccionados = centros_seleccionados
            else:
                centros_seleccionados = []
        else:
            centros_seleccionados = []

# --- Lógica de la Aplicación Principal ---
if 'df_original' in locals() and not df_original.empty:
   
    mapeo_medidas = {
        "Regulación de la temperatura de consigna": {"Category": "Medidas de control térmico", "Code": "A.1"},
        "Sustitución de equipos de climatización": {"Category": "Medidas de control térmico", "Code": "A.2"},
        "Instalación cortina de aire": {"Category": "Medidas de control térmico", "Code": "A.3"},
        "Instalación de temporizador digital": {"Category": "Medidas de control térmico", "Code": "A.4"},
        "Regulación de ventilación mediante sonda de CO2": {"Category": "Medidas de control térmico", "Code": "A.5"},
        "Recuperadores de calor": {"Category": "Medidas de control térmico", "Code": "A.6"},
        "Ajuste O2 en caldera gasóleo C": {"Category": "Medidas de control térmico", "Code": "A.7"},
        "Instalación de Variadores de frecuencia en bombas hidráulicas": {"Category": "Medidas de control térmico", "Code": "A.8"},
        "Instalación Solar térmica": {"Category": "Medidas de control térmico", "Code": "A.9"},
        "Aislamiento Térmico de Tuberías y Redes": {"Category": "Medidas de control térmico", "Code": "A.10"},
        "Mejora de la Eficiencia en Calderas": {"Category": "Medidas de control térmico", "Code": "A.11"},
        "Optimización de la potencia contratada": {"Category": "Medidas de gestión energética", "Code": "B.1"},
        "Sistema de Gestión Energética": {"Category": "Medidas de gestión energética", "Code": "B.2"},
        "Eliminación de la energía reactiva": {"Category": "Medidas de gestión energética", "Code": "B.3"},
        "Reducción del consumo remanente": {"Category": "Medidas de gestión energética", "Code": "B.4"},
        "Promover la cultura energética": {"Category": "Medidas de gestión energética", "Code": "B.5"},
        "Instalación Fotovoltaica": {"Category": "Medidas de gestión energética", "Code": "B.6"},
        "Instalación de Paneles Solares (Fotovoltaicos o Híbridos)": {"Category": "Medidas de gestión energética", "Code": "B.6"},
        "Cambio Iluminacion LED": {"Category": "Medidas de control de iluminación", "Code": "C.1"},
        "Sustitución de luminarias a LED": {"Category": "Medidas de control de iluminación", "Code": "C.1"},
        "Instalación regletas programables": {"Category": "Medidas de control de iluminación", "Code": "C.2"},
        "Mejora en el control de la iluminación": {"Category": "Medidas de control de iluminación", "Code": "C.3"},
        "Mejora en el control actual de iluminación": {"Category": "Medidas de control de iluminación", "Code": "C.3"},
        "Mejora en el control actual": {"Category": "Medidas de control de iluminación", "Code": "C.3"},
        "Sustitución de luminarias a LED y mejora en su control": {"Category": "Medidas de control de iluminación", "Code": "C.4"},
        "Renovación de Equipamiento Específico": {"Category": "Medidas de equipamiento general", "Code": "D.1"}
    }
       
    def categorizar_por_tipo(df_in):
        def get_info(texto_medida):
            for nombre_estandar, info in mapeo_medidas.items():
                if nombre_estandar.lower() in texto_medida.lower():
                    return pd.Series([info['Category'], info['Code']])
            return pd.Series(['Sin categorizar', 'Z.Z'])
        df_in[['Categoría', 'Base Código Medida']] = df_in['Medida'].apply(get_info)
        return df_in

    def categorizar_por_intervencion(df_in):
        def get_type(medida):
            medida = medida.lower()
            if any(word in medida for word in ["instalación", "batería", "recuperadores", "solar", "fotovoltaica"]): return 'Instalación de Nuevos Sistemas'
            if any(word in medida for word in ["sustitución", "cambio", "mejora", "aislamiento"]): return 'Reforma y Actualización de Equipos'
            if any(word in medida for word in ["prácticas", "cultura", "regulación", "optimización", "reducción"]): return 'Operacional y Comportamental'
            return 'Intervenciones Específicas'
        df_in['Categoría'] = df_in['Medida'].apply(get_type)
        return df_in

    def categorizar_por_financiero(df_in):
        def get_type(retorno):
            if retorno <= 0: return 'Sin Coste / Inmediato'
            if retorno < 2: return 'Resultados Rápidos (< 2 años)'
            if retorno <= 5: return 'Proyectos Estándar (2-5 años)'
            return 'Inversiones Estratégicas (> 5 años)'
        df_in['Categoría'] = df_in['Periodo de retorno'].apply(get_type)
        return df_in

    def categorizar_por_funcion(df_in):
        def get_type(medida):
            medida = medida.lower()
            if any(word in medida for word in ["hvac", "climatización", "temperatura", "ventilación", "aislamiento", "cortina", "calor", "termo"]): return 'Envolvente y Climatización (HVAC)'
            if any(word in medida for word in ["led", "iluminación", "luminarias", "eléctrico", "potencia", "reactiva", "condensadores", "regletas"]): return 'Iluminación y Electricidad'
            if any(word in medida for word in ["gestión", "fotovoltaica", "solar", "prácticas", "remanente", "cultura"]): return 'Gestión y Estrategia Energética'
            return 'Otras Funciones'
        df_in['Categoría'] = df_in['Medida'].apply(get_type)
        return df_in
       
    def categorizar_por_ahorro_energetico(df_in):
        def get_type(medida):
            medida = medida.lower()
            if any(word in medida for word in ["gasóleo", "diesel", "caldera", "térmica"]): return 'Ahorros Térmicos (Gas/Combustible)'
            if any(word in medida for word in ["led", "iluminación", "fotovoltaica", "eléctrico", "potencia", "reactiva", "variadores", "bombas", "regletas"]): return 'Ahorros Eléctricos'
            return 'Mixto / Operacional'
        df_in['Categoría'] = df_in['Medida'].apply(get_type)
        return df_in

    # --- Procesamiento de Datos según los Filtros ---
    mapa_funciones_categorizacion = {
        'Tipo de Medida': categorizar_por_tipo,
        'Tipo de Intervención': categorizar_por_intervencion,
        'Impacto Financiero': categorizar_por_financiero,
        'Función de Negocio': categorizar_por_funcion,
        'Tipo de Ahorro Energético': categorizar_por_ahorro_energetico,
    }
    funcion_a_usar = mapa_funciones_categorizacion.get(tipo_analisis)
    df_categorizado = funcion_a_usar(df_original.copy())

    if comunidades_seleccionadas:
        df_filtrado = df_categorizado[df_categorizado['Comunidad Autónoma'].isin(comunidades_seleccionadas)]
        if vista_detallada and centros_seleccionados:
            df_filtrado = df_filtrado[df_filtrado['Centro'].isin(centros_seleccionados)]
    else:
        df_filtrado = pd.DataFrame(columns=df_categorizado.columns)

    # --- Renderizado del Panel Principal ---
    st.image("Logo_ASEPEYO.png", width=250)
    st.title(f"Análisis de Eficiencia Energética - {selected_file.replace('.csv', '')}") # Título dinámico
   
    # --- RENDERIZADO DE KPIs, GRÁFICOS Y TABLAS ---
    if not df_filtrado.empty:
        if tipo_analisis == 'Tipo de Medida':
            df_filtrado['Frecuencia'] = df_filtrado.groupby(['Comunidad Autónoma', 'Base Código Medida']).cumcount() + 1
            df_filtrado['Código Medida'] = df_filtrado.apply(
                lambda row: f"{row['Base Código Medida']}.{row['Frecuencia']}" if row['Base Código Medida'] != 'Z.Z' else 'Sin categorizar', axis=1)
       
        columna_agrupar = 'Centro' if vista_detallada else 'Comunidad Autónoma'

        if vista_detallada and not centros_seleccionados:
            st.warning("Seleccione al menos un centro para ver la comparación detallada.")
        elif vista_detallada:
            st.header(f"Comparando {len(centros_seleccionados)} centros en {len(comunidades_seleccionadas)} comunidades")
        else:
            st.header(f"Vista resumida para {len(comunidades_seleccionadas)} comunidades")

        inversion_total = df_filtrado['Inversión'].sum()
        ahorro_economico_total = df_filtrado['Ahorro económico'].sum()
        ahorro_energetico_total = df_filtrado['Ahorro energético'].sum()
        roi = (ahorro_economico_total / inversion_total) * 100 if inversion_total > 0 else 0

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric(label="Inversión Total", value=f"€ {inversion_total:,.0f}")
        kpi2.metric(label="Ahorro Económico Total", value=f"€ {ahorro_economico_total:,.0f}")
        kpi3.metric(label="Ahorro Energético Total", value=f"{ahorro_energetico_total:,.0f} kWh")
        kpi4.metric(label="Retorno de la Inversión (ROI)", value=f"{roi:.2f} %")
        st.markdown("---")

        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.subheader(f"Recuento de Medidas por {tipo_analisis}")
            datos_agregados = df_filtrado.groupby([columna_agrupar, 'Categoría']).agg(
                Recuento=('Medida', 'size'),
                Medidas=('Medida', lambda x: '<br>'.join(x.unique()))
            ).reset_index()

            if mostrar_porcentaje:
                recuentos_totales = datos_agregados.groupby(columna_agrupar)['Recuento'].transform('sum')
                datos_agregados['Porcentaje'] = (datos_agregados['Recuento'] / recuentos_totales) * 100
                y_val, y_label = 'Porcentaje', 'Porcentaje de Medidas (%)'
            else:
                y_val, y_label = 'Recuento', 'Número de Medidas'

            fig1 = px.bar(datos_agregados, x=columna_agrupar, y=y_val, color='Categoría', hover_data=['Medidas'], title=f'Recuento de Medidas por {columna_agrupar}')
            fig1.update_layout(yaxis_title=y_label, xaxis_title=columna_agrupar, legend_title=tipo_analisis, template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)

            st.subheader("Análisis del Ahorro Energético")
            agg_energia = df_filtrado.groupby(columna_agrupar).agg(
                Ahorro_Total_Energia=('Ahorro energético', 'sum'),
                Medidas=('Medida', lambda x: '<br>'.join(x.unique()))
            ).reset_index()None selected 

Skip to content
Using ASEPEYO MCcSS 151 Mail with screen readers

Conversations
me
29 sep tab gas code
 - # Importar librerías import streamlit as st import pandas as pd import plotly.express as px import plotly.graph_objects as go import os # Configuración de la pá
 
12:39
29 sep tab gas code
Inbox


HARDIK DERASHRI <hderashri@asepeyo.es>
12:39 (2 minutes ago)
to me

# Importar librerías
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Eficiencia Energética de Asepeyo",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Carga y Cacheo de Datos ---
@st.cache_data
def load_data(file_path):
    """Carga, limpia y procesa los datos de la auditoría energética."""
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        # Unifica el renombrado para manejar tanto CSVs en inglés como en español
        df.rename(columns={
            'Center': 'Centro', 'Measure': 'Medida',
            'Energy Saved': 'Ahorro energético', 'Money Saved': 'Ahorro económico',
            'Investment': 'Inversión', 'Pay back period': 'Periodo de retorno',
            'Energía Ahorrada (kWh/año)': 'Ahorro energético', 'Dinero Ahorrado (€/año)': 'Ahorro económico',
            'Inversión (€)': 'Inversión', 'Periodo de Amortización (años)': 'Periodo de retorno'
        }, inplace=True)
        for col in ['Ahorro energético', 'Ahorro económico', 'Inversión', 'Periodo de retorno']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.fillna(0, inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo de datos en la ruta: {file_path}")
        return pd.DataFrame()
    except KeyError as e:
        st.error(f"Error de columna: No se encontró la columna requerida. Revise el CSV (columna faltante: {e})")
        return pd.DataFrame()

# --- Barra Lateral y Lógica de Carga de Datos ---
with st.sidebar:
    st.title('⚡ Filtros de análisis')
   
    DATA_DIR = "Data/"
    try:
        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
        if not files:
            st.warning("No se encontraron archivos CSV en la carpeta 'Data/'.")
            st.stop()
       
        selected_file = st.selectbox(
            "Seleccionar Auditoría", files,
            index=files.index("2025 Energy Audit summary - Sheet1.csv") if "2025 Energy Audit summary - Sheet1.csv" in files else 0
        )
        file_path = os.path.join(DATA_DIR, selected_file)
        df_original = load_data(file_path)
    except FileNotFoundError:
        st.error(f"El directorio '{DATA_DIR}' no fue encontrado.")
        st.stop()

    if not df_original.empty:
        tipo_analisis = st.radio(
            "Seleccionar Tipo de Análisis",
            ('Tipo de Medida', 'Tipo de Intervención', 'Impacto Financiero', 'Función de Negocio', 'Tipo de Ahorro Energético')
        )
        mostrar_porcentaje = st.toggle('Mostrar valores en porcentaje')
        st.markdown("---")
        vista_detallada = st.toggle('Mostrar vista detallada por centro')

        if 'last_file' not in st.session_state or st.session_state.last_file != selected_file:
            st.session_state.last_file = selected_file
            st.session_state.comunidades_seleccionadas = sorted(df_original['Comunidad Autónoma'].unique().tolist())
            st.session_state.centros_seleccionados = []
       
        lista_comunidades = sorted(df_original['Comunidad Autónoma'].unique().tolist())
        if st.button("Todas las Comunidades", use_container_width=True):
            st.session_state.comunidades_seleccionadas = lista_comunidades
       
        comunidades_seleccionadas = st.multiselect('Seleccionar Comunidades', lista_comunidades, default=st.session_state.comunidades_seleccionadas)
        st.session_state.comunidades_seleccionadas = comunidades_seleccionadas

        if vista_detallada:
            if comunidades_seleccionadas:
                centros_disponibles = sorted(df_original[df_original['Comunidad Autónoma'].isin(comunidades_seleccionadas)]['Centro'].unique().tolist())
                if not all(centro in centros_disponibles for centro in st.session_state.centros_seleccionados):
                    st.session_state.centros_seleccionados = centros_disponibles
               
                st.write("Selección de Centros:")
                col1, col2 = st.columns([0.7, 0.3])
                with col1:
                    centros_seleccionados = st.multiselect('Seleccionar Centros', centros_disponibles, default=st.session_state.centros_seleccionados, label_visibility="collapsed")
                with col2:
                    if st.button("Todos", help="Seleccionar todos los centros"):
                        st.session_state.centros_seleccionados = centros_disponibles
                        st.rerun()
                st.session_state.centros_seleccionados = centros_seleccionados
            else:
                centros_seleccionados = []
        else:
            centros_seleccionados = []

# --- Lógica de la Aplicación Principal ---
if 'df_original' in locals() and not df_original.empty:
   
    mapeo_medidas = {
        "Regulación de la temperatura de consigna": {"Category": "Medidas de control térmico", "Code": "A.1"},
        "Sustitución de equipos de climatización": {"Category": "Medidas de control térmico", "Code": "A.2"},
        "Instalación cortina de aire": {"Category": "Medidas de control térmico", "Code": "A.3"},
        "Instalación de temporizador digital": {"Category": "Medidas de control térmico", "Code": "A.4"},
        "Regulación de ventilación mediante sonda de CO2": {"Category": "Medidas de control térmico", "Code": "A.5"},
        "Recuperadores de calor": {"Category": "Medidas de control térmico", "Code": "A.6"},
        "Ajuste O2 en caldera gasóleo C": {"Category": "Medidas de control térmico", "Code": "A.7"},
        "Instalación de Variadores de frecuencia en bombas hidráulicas": {"Category": "Medidas de control térmico", "Code": "A.8"},
        "Instalación Solar térmica": {"Category": "Medidas de control térmico", "Code": "A.9"},
        "Aislamiento Térmico de Tuberías y Redes": {"Category": "Medidas de control térmico", "Code": "A.10"},
        "Mejora de la Eficiencia en Calderas": {"Category": "Medidas de control térmico", "Code": "A.11"},
        "Optimización de la potencia contratada": {"Category": "Medidas de gestión energética", "Code": "B.1"},
        "Sistema de Gestión Energética": {"Category": "Medidas de gestión energética", "Code": "B.2"},
        "Eliminación de la energía reactiva": {"Category": "Medidas de gestión energética", "Code": "B.3"},
        "Reducción del consumo remanente": {"Category": "Medidas de gestión energética", "Code": "B.4"},
        "Promover la cultura energética": {"Category": "Medidas de gestión energética", "Code": "B.5"},
        "Instalación Fotovoltaica": {"Category": "Medidas de gestión energética", "Code": "B.6"},
        "Instalación de Paneles Solares (Fotovoltaicos o Híbridos)": {"Category": "Medidas de gestión energética", "Code": "B.6"},
        "Cambio Iluminacion LED": {"Category": "Medidas de control de iluminación", "Code": "C.1"},
        "Sustitución de luminarias a LED": {"Category": "Medidas de control de iluminación", "Code": "C.1"},
        "Instalación regletas programables": {"Category": "Medidas de control de iluminación", "Code": "C.2"},
        "Mejora en el control de la iluminación": {"Category": "Medidas de control de iluminación", "Code": "C.3"},
        "Mejora en el control actual de iluminación": {"Category": "Medidas de control de iluminación", "Code": "C.3"},
        "Mejora en el control actual": {"Category": "Medidas de control de iluminación", "Code": "C.3"},
        "Sustitución de luminarias a LED y mejora en su control": {"Category": "Medidas de control de iluminación", "Code": "C.4"},
        "Renovación de Equipamiento Específico": {"Category": "Medidas de equipamiento general", "Code": "D.1"}
    }
       
    def categorizar_por_tipo(df_in):
        def get_info(texto_medida):
            for nombre_estandar, info in mapeo_medidas.items():
                if nombre_estandar.lower() in texto_medida.lower():
                    return pd.Series([info['Category'], info['Code']])
            return pd.Series(['Sin categorizar', 'Z.Z'])
        df_in[['Categoría', 'Base Código Medida']] = df_in['Medida'].apply(get_info)
        return df_in

    def categorizar_por_intervencion(df_in):
        def get_type(medida):
            medida = medida.lower()
            if any(word in medida for word in ["instalación", "batería", "recuperadores", "solar", "fotovoltaica"]): return 'Instalación de Nuevos Sistemas'
            if any(word in medida for word in ["sustitución", "cambio", "mejora", "aislamiento"]): return 'Reforma y Actualización de Equipos'
            if any(word in medida for word in ["prácticas", "cultura", "regulación", "optimización", "reducción"]): return 'Operacional y Comportamental'
            return 'Intervenciones Específicas'
        df_in['Categoría'] = df_in['Medida'].apply(get_type)
        return df_in

    def categorizar_por_financiero(df_in):
        def get_type(retorno):
            if retorno <= 0: return 'Sin Coste / Inmediato'
            if retorno < 2: return 'Resultados Rápidos (< 2 años)'
            if retorno <= 5: return 'Proyectos Estándar (2-5 años)'
            return 'Inversiones Estratégicas (> 5 años)'
        df_in['Categoría'] = df_in['Periodo de retorno'].apply(get_type)
        return df_in

    def categorizar_por_funcion(df_in):
        def get_type(medida):
            medida = medida.lower()
            if any(word in medida for word in ["hvac", "climatización", "temperatura", "ventilación", "aislamiento", "cortina", "calor", "termo"]): return 'Envolvente y Climatización (HVAC)'
            if any(word in medida for word in ["led", "iluminación", "luminarias", "eléctrico", "potencia", "reactiva", "condensadores", "regletas"]): return 'Iluminación y Electricidad'
            if any(word in medida for word in ["gestión", "fotovoltaica", "solar", "prácticas", "remanente", "cultura"]): return 'Gestión y Estrategia Energética'
            return 'Otras Funciones'
        df_in['Categoría'] = df_in['Medida'].apply(get_type)
        return df_in
       
    def categorizar_por_ahorro_energetico(df_in):
        def get_type(medida):
            medida = medida.lower()
            if any(word in medida for word in ["gasóleo", "diesel", "caldera", "térmica"]): return 'Ahorros Térmicos (Gas/Combustible)'
            if any(word in medida for word in ["led", "iluminación", "fotovoltaica", "eléctrico", "potencia", "reactiva", "variadores", "bombas", "regletas"]): return 'Ahorros Eléctricos'
            return 'Mixto / Operacional'
        df_in['Categoría'] = df_in['Medida'].apply(get_type)
        return df_in

    # --- Procesamiento de Datos según los Filtros ---
    mapa_funciones_categorizacion = {
        'Tipo de Medida': categorizar_por_tipo,
        'Tipo de Intervención': categorizar_por_intervencion,
        'Impacto Financiero': categorizar_por_financiero,
        'Función de Negocio': categorizar_por_funcion,
        'Tipo de Ahorro Energético': categorizar_por_ahorro_energetico,
    }
    funcion_a_usar = mapa_funciones_categorizacion.get(tipo_analisis)
    df_categorizado = funcion_a_usar(df_original.copy())

    if comunidades_seleccionadas:
        df_filtrado = df_categorizado[df_categorizado['Comunidad Autónoma'].isin(comunidades_seleccionadas)]
        if vista_detallada and centros_seleccionados:
            df_filtrado = df_filtrado[df_filtrado['Centro'].isin(centros_seleccionados)]
    else:
        df_filtrado = pd.DataFrame(columns=df_categorizado.columns)

    # --- Renderizado del Panel Principal ---
    st.image("Logo_ASEPEYO.png", width=250)
    st.title(f"Análisis de Eficiencia Energética - {selected_file.replace('.csv', '')}") # Título dinámico
   
    # --- RENDERIZADO DE KPIs, GRÁFICOS Y TABLAS ---
    if not df_filtrado.empty:
        if tipo_analisis == 'Tipo de Medida':
            df_filtrado['Frecuencia'] = df_filtrado.groupby(['Comunidad Autónoma', 'Base Código Medida']).cumcount() + 1
            df_filtrado['Código Medida'] = df_filtrado.apply(
                lambda row: f"{row['Base Código Medida']}.{row['Frecuencia']}" if row['Base Código Medida'] != 'Z.Z' else 'Sin categorizar', axis=1)
       
        columna_agrupar = 'Centro' if vista_detallada else 'Comunidad Autónoma'

        if vista_detallada and not centros_seleccionados:
            st.warning("Seleccione al menos un centro para ver la comparación detallada.")
        elif vista_detallada:
            st.header(f"Comparando {len(centros_seleccionados)} centros en {len(comunidades_seleccionadas)} comunidades")
        else:
            st.header(f"Vista resumida para {len(comunidades_seleccionadas)} comunidades")

        inversion_total = df_filtrado['Inversión'].sum()
        ahorro_economico_total = df_filtrado['Ahorro económico'].sum()
        ahorro_energetico_total = df_filtrado['Ahorro energético'].sum()
        roi = (ahorro_economico_total / inversion_total) * 100 if inversion_total > 0 else 0

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric(label="Inversión Total", value=f"€ {inversion_total:,.0f}")
        kpi2.metric(label="Ahorro Económico Total", value=f"€ {ahorro_economico_total:,.0f}")
        kpi3.metric(label="Ahorro Energético Total", value=f"{ahorro_energetico_total:,.0f} kWh")
        kpi4.metric(label="Retorno de la Inversión (ROI)", value=f"{roi:.2f} %")
        st.markdown("---")

        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.subheader(f"Recuento de Medidas por {tipo_analisis}")
            datos_agregados = df_filtrado.groupby([columna_agrupar, 'Categoría']).agg(
                Recuento=('Medida', 'size'),
                Medidas=('Medida', lambda x: '<br>'.join(x.unique()))
            ).reset_index()

            if mostrar_porcentaje:
                recuentos_totales = datos_agregados.groupby(columna_agrupar)['Recuento'].transform('sum')
                datos_agregados['Porcentaje'] = (datos_agregados['Recuento'] / recuentos_totales) * 100
                y_val, y_label = 'Porcentaje', 'Porcentaje de Medidas (%)'
            else:
                y_val, y_label = 'Recuento', 'Número de Medidas'

            fig1 = px.bar(datos_agregados, x=columna_agrupar, y=y_val, color='Categoría', hover_data=['Medidas'], title=f'Recuento de Medidas por {columna_agrupar}')
            fig1.update_layout(yaxis_title=y_label, xaxis_title=columna_agrupar, legend_title=tipo_analisis, template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)

            st.subheader("Análisis del Ahorro Energético")
            agg_energia = df_filtrado.groupby(columna_agrupar).agg(
                Ahorro_Total_Energia=('Ahorro energético', 'sum'),
                Medidas=('Medida', lambda x: '<br>'.join(x.unique()))
            ).reset_index()

            if mostrar_porcentaje:
                ahorro_general_total = agg_energia['Ahorro_Total_Energia'].sum()
                agg_energia['Porcentaje'] = (agg_energia['Ahorro_Total_Energia'] / ahorro_general_total) * 100 if ahorro_general_total > 0 else 0
                y_val, y_label = 'Porcentaje', 'Contribución al Ahorro Total (%)'
            else:
                y_val, y_label = 'Ahorro_Total_Energia', 'Ahorro Energético (kWh)'

            fig5 = px.bar(agg_energia.sort_values('Ahorro_Total_Energia', ascending=False), x=columna_agrupar, y=y_val, hover_data=['Medidas'], title=f'Ahorro Energético por {columna_agrupar}')
            fig5.update_layout(yaxis_title=y_label, xaxis_title=columna_agrupar, template="plotly_white")
            st.plotly_chart(fig5, use_container_width=True)

        with col2:
            st.subheader("Análisis del Ahorro Económico")
            agg_eco = df_filtrado.groupby(columna_agrupar).agg(
                Ahorro_Total_Economico=('Ahorro económico', 'sum'),
                Recuento_Medidas=('Medida', 'size')
            ).reset_index()
            fig6 = px.pie(agg_eco, names=columna_agrupar, values='Ahorro_Total_Economico', title=f'Contribución al Ahorro Económico por {columna_agrupar}', hole=0.4, hover_data=['Recuento_Medidas'])
            fig6.update_traces(hovertemplate='<b>%{label}</b><br>Ahorro Económico: €%{value:,.0f}<br>Nº de Medidas: %{customdata[0]}<extra></extra>')
            st.plotly_chart(fig6, use_container_width=True)
           
            st.subheader("Inversión vs. Ahorro Económico")
            resumen_fin = df_filtrado.groupby(columna_agrupar).agg(
                Inversion_Total=('Inversión', 'sum'),
                Ahorro_Total_Economico=('Ahorro económico', 'sum')
            ).reset_index()
           
            if mostrar_porcentaje and not resumen_fin.empty:
                inversion_total_todo = resumen_fin['Inversion_Total'].sum()
                ahorro_total_todo = resumen_fin['Ahorro_Total_Economico'].sum()
                resumen_fin['Inversión %'] = (resumen_fin['Inversion_Total'] / inversion_total_todo) * 100 if inversion_total_todo > 0 else 0
                resumen_fin['Ahorro %'] = (resumen_fin['Ahorro_Total_Economico'] / ahorro_total_todo) * 100 if ahorro_total_todo > 0 else 0
                fig7 = px.scatter(
                    resumen_fin, x='Inversión %', y='Ahorro %', text=columna_agrupar, size='Inversion_Total',
                    color=columna_agrupar, title='% de Contribución a Inversión vs. Ahorro',
                    labels={'Inversión %': '% Inversión Total', 'Ahorro %': '% Ahorro Total'}
                )
            else:
                fig7 = px.scatter(
                    resumen_fin, x='Inversion_Total', y='Ahorro_Total_Economico', text=columna_agrupar,
                    size='Inversion_Total', color=columna_agrupar, title=f'Inversión vs. Ahorro Económico por {columna_agrupar}'
                )
            fig7.update_traces(textposition='top center')
            fig7.update_layout(xaxis_title="Inversión (€)", yaxis_title="Ahorro Anual (€)", template="plotly_white")
            st.plotly_chart(fig7, use_container_width=True)
       
        st.markdown("---")
        st.header("Análisis Avanzado")
        adv_col1, adv_col2 = st.columns(2, gap="large")

        with adv_col1:
            st.subheader("Eficacia de la Inversión")
            datos_grafico = df_filtrado[(df_filtrado['Inversión'] > 0) & (df_filtrado['Ahorro económico'] > 0)]
            if not datos_grafico.empty:
                if mostrar_porcentaje:
                    inversion_total_todo = datos_grafico['Inversión'].sum()
                    ahorro_total_todo = datos_grafico['Ahorro económico'].sum()
                    datos_grafico['Inversión %'] = (datos_grafico['Inversión'] / inversion_total_todo) * 100 if inversion_total_todo > 0 else 0
                    datos_grafico['Ahorro %'] = (datos_grafico['Ahorro económico'] / ahorro_total_todo) * 100 if ahorro_total_todo > 0 else 0
                    eje_x, eje_y = 'Inversión %', 'Ahorro %'
                    label_x, label_y = '% de Inversión Total', '% de Ahorro Total'
                    texto_titulo = "Contribución Relativa a Inversión vs. Ahorro"
                else:
                    eje_x, eje_y = 'Inversión', 'Ahorro económico'
                    label_x, label_y = 'Inversión (€)', 'Ahorro Anual (€)'
                    texto_titulo = "Inversión vs. Ahorro Anual"
                fig_burbuja = px.scatter(
                    datos_grafico, x=eje_x, y=eje_y, size='Ahorro energético', color='Categoría',
                    hover_name='Medida',
                    hover_data=['Centro'],
                    size_max=60, title=texto_titulo, template="plotly_white"
                )
                fig_burbuja.update_layout(xaxis_title=label_x, yaxis_title=label_y, legend_title=tipo_analisis)
                st.plotly_chart(fig_burbuja, use_container_width=True)
            else:
                st.info("No hay datos de inversión y ahorro para este filtro. ")

        with adv_col2:
            st.subheader("Distribución del Periodo de Retorno")
            payback_data = df_filtrado[df_filtrado['Periodo de retorno'] > 0]
            if not payback_data.empty:
                if mostrar_porcentaje:
                    histnorm_val = 'percent'
                    y_axis_title = '% del Total de Medidas'
                    title_text = "Distribución Porcentual de los Periodos de Retorno"
                else:
                    histnorm_val = None
                    y_axis_title = 'Número de Medidas'
                    title_text = "Distribución de los Periodos de Retorno"
               
                fig_hist = px.histogram(
                    payback_data,
                    x='Periodo de retorno',
                    nbins=20,
                    histnorm=histnorm_val,
                    hover_data=['Centro', 'Medida'],
                    template="plotly_white",
                    title=title_text
                )
               
                fig_hist.update_layout(
                    xaxis_title="Periodo de Retorno (Años)",
                    yaxis_title=y_axis_title
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("No hay datos del Periodo de retorno para este filtro.")
       
        # --- Sankey Diagram (Full Width) ---
        st.subheader("Flujo de Inversión y Ahorro (Diagrama de Sankey)")
        datos_sankey = df_filtrado.groupby(['Categoría', columna_agrupar]).agg(Inversion_Total=('Inversión', 'sum'), Ahorro_Total=('Ahorro económico', 'sum')).reset_index()
        if not datos_sankey.empty and datos_sankey['Inversion_Total'].sum() > 0:
            todos_nodos = list(pd.concat([datos_sankey['Categoría'], datos_sankey[columna_agrupar]]).unique())
            fig_sankey = go.Figure(data=[go.Sankey(
                node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=todos_nodos),
                link=dict(
                    source=[todos_nodos.index(cat) for cat in datos_sankey['Categoría']],
                    target=[todos_nodos.index(center) for center in datos_sankey[columna_agrupar]],
                    value=datos_sankey['Inversion_Total'],
                    hovertemplate='Inversión de %{source.label} a %{target.label}: €%{value:,.0f}<br>' + 'Ahorro resultante: €' + datos_sankey['Ahorro_Total'].map('{:,.0f}'.format) + '<extra></extra>'
                ))])
            fig_sankey.update_layout(title_text=f"Flujo de Categoría a {columna_agrupar} por Inversión", font_size=12)
            st.plotly_chart(fig_sankey, use_container_width=True)
       
        st.markdown("---")
        st.header("Tablas de Datos")

        st.subheader("1. Explicación de Categorías")
        if tipo_analisis == 'Tipo de Medida':
            df_explicacion = pd.DataFrame([
                (info['Category'], desc, info['Code']) for desc, info in mapeo_medidas.items()
            ], columns=['Categoría', 'Descripción Medida', 'Prefijo Código']).sort_values(by='Prefijo Código')
        else:
            df_explicacion = df_filtrado[['Categoría']].drop_duplicates().sort_values('Categoría')
            df_explicacion['Explicación'] = df_explicacion['Categoría']
        st.dataframe(df_explicacion, use_container_width=True, hide_index=True)

        st.subheader(f"2. Datos Detallados por {columna_agrupar}")
        columnas_a_mostrar = [columna_agrupar, 'Medida', 'Categoría', 'Inversión', 'Ahorro energético', 'Ahorro económico', 'Periodo de retorno']
        if tipo_analisis == 'Tipo de Medida' and 'Código Medida' in df_filtrado.columns:
            columnas_a_mostrar.insert(1, 'Código Medida')
        df_tabla_financiera = df_filtrado[columnas_a_mostrar].sort_values(by=[columna_agrupar])
        st.dataframe(
            df_tabla_financiera, use_container_width=True, hide_index=True,
            column_config={
                "Inversión": st.column_config.NumberColumn("Inversión (€)", format="€ %d"),
                "Ahorro energético": st.column_config.NumberColumn("Ahorro Energético (kWh)", format="%d kWh"),
                "Ahorro económico": st.column_config.NumberColumn("Ahorro Anual (€)", format="€ %d"),
                "Periodo de retorno": st.column_config.NumberColumn("Retorno (años)", format="%.1f años"),
            }
        )
    else:
        st.info("No hay datos disponibles para la selección de filtros actual.")

else:
    st.warning("No se pudieron cargar los datos. Por favor, revise la ruta del archivo e inténtelo de nuevo.")


            if mostrar_porcentaje:
                ahorro_general_total = agg_energia['Ahorro_Total_Energia'].sum()
                agg_energia['Porcentaje'] = (agg_energia['Ahorro_Total_Energia'] / ahorro_general_total) * 100 if ahorro_general_total > 0 else 0
                y_val, y_label = 'Porcentaje', 'Contribución al Ahorro Total (%)'
            else:
                y_val, y_label = 'Ahorro_Total_Energia', 'Ahorro Energético (kWh)'

            fig5 = px.bar(agg_energia.sort_values('Ahorro_Total_Energia', ascending=False), x=columna_agrupar, y=y_val, hover_data=['Medidas'], title=f'Ahorro Energético por {columna_agrupar}')
            fig5.update_layout(yaxis_title=y_label, xaxis_title=columna_agrupar, template="plotly_white")
            st.plotly_chart(fig5, use_container_width=True)

        with col2:
            st.subheader("Análisis del Ahorro Económico")
            agg_eco = df_filtrado.groupby(columna_agrupar).agg(
                Ahorro_Total_Economico=('Ahorro económico', 'sum'),
                Recuento_Medidas=('Medida', 'size')
            ).reset_index()
            fig6 = px.pie(agg_eco, names=columna_agrupar, values='Ahorro_Total_Economico', title=f'Contribución al Ahorro Económico por {columna_agrupar}', hole=0.4, hover_data=['Recuento_Medidas'])
            fig6.update_traces(hovertemplate='<b>%{label}</b><br>Ahorro Económico: €%{value:,.0f}<br>Nº de Medidas: %{customdata[0]}<extra></extra>')
            st.plotly_chart(fig6, use_container_width=True)
           
            st.subheader("Inversión vs. Ahorro Económico")
            resumen_fin = df_filtrado.groupby(columna_agrupar).agg(
                Inversion_Total=('Inversión', 'sum'),
                Ahorro_Total_Economico=('Ahorro económico', 'sum')
            ).reset_index()
           
            if mostrar_porcentaje and not resumen_fin.empty:
                inversion_total_todo = resumen_fin['Inversion_Total'].sum()
                ahorro_total_todo = resumen_fin['Ahorro_Total_Economico'].sum()
                resumen_fin['Inversión %'] = (resumen_fin['Inversion_Total'] / inversion_total_todo) * 100 if inversion_total_todo > 0 else 0
                resumen_fin['Ahorro %'] = (resumen_fin['Ahorro_Total_Economico'] / ahorro_total_todo) * 100 if ahorro_total_todo > 0 else 0
                fig7 = px.scatter(
                    resumen_fin, x='Inversión %', y='Ahorro %', text=columna_agrupar, size='Inversion_Total',
                    color=columna_agrupar, title='% de Contribución a Inversión vs. Ahorro',
                    labels={'Inversión %': '% Inversión Total', 'Ahorro %': '% Ahorro Total'}
                )
            else:
                fig7 = px.scatter(
                    resumen_fin, x='Inversion_Total', y='Ahorro_Total_Economico', text=columna_agrupar,
                    size='Inversion_Total', color=columna_agrupar, title=f'Inversión vs. Ahorro Económico por {columna_agrupar}'
                )
            fig7.update_traces(textposition='top center')
            fig7.update_layout(xaxis_title="Inversión (€)", yaxis_title="Ahorro Anual (€)", template="plotly_white")
            st.plotly_chart(fig7, use_container_width=True)
       
        st.markdown("---")
        st.header("Análisis Avanzado")
        adv_col1, adv_col2 = st.columns(2, gap="large")

        with adv_col1:
            st.subheader("Eficacia de la Inversión")
            datos_grafico = df_filtrado[(df_filtrado['Inversión'] > 0) & (df_filtrado['Ahorro económico'] > 0)]
            if not datos_grafico.empty:
                if mostrar_porcentaje:
                    inversion_total_todo = datos_grafico['Inversión'].sum()
                    ahorro_total_todo = datos_grafico['Ahorro económico'].sum()
                    datos_grafico['Inversión %'] = (datos_grafico['Inversión'] / inversion_total_todo) * 100 if inversion_total_todo > 0 else 0
                    datos_grafico['Ahorro %'] = (datos_grafico['Ahorro económico'] / ahorro_total_todo) * 100 if ahorro_total_todo > 0 else 0
                    eje_x, eje_y = 'Inversión %', 'Ahorro %'
                    label_x, label_y = '% de Inversión Total', '% de Ahorro Total'
                    texto_titulo = "Contribución Relativa a Inversión vs. Ahorro"
                else:
                    eje_x, eje_y = 'Inversión', 'Ahorro económico'
                    label_x, label_y = 'Inversión (€)', 'Ahorro Anual (€)'
                    texto_titulo = "Inversión vs. Ahorro Anual"
                fig_burbuja = px.scatter(
                    datos_grafico, x=eje_x, y=eje_y, size='Ahorro energético', color='Categoría',
                    hover_name='Medida',
                    hover_data=['Centro'],
                    size_max=60, title=texto_titulo, template="plotly_white"
                )
                fig_burbuja.update_layout(xaxis_title=label_x, yaxis_title=label_y, legend_title=tipo_analisis)
                st.plotly_chart(fig_burbuja, use_container_width=True)
            else:
                st.info("No hay datos de inversión y ahorro para este filtro. ")

        with adv_col2:
            st.subheader("Distribución del Periodo de Retorno")
            payback_data = df_filtrado[df_filtrado['Periodo de retorno'] > 0]
            if not payback_data.empty:
                if mostrar_porcentaje:
                    histnorm_val = 'percent'
                    y_axis_title = '% del Total de Medidas'
                    title_text = "Distribución Porcentual de los Periodos de Retorno"
                else:
                    histnorm_val = None
                    y_axis_title = 'Número de Medidas'
                    title_text = "Distribución de los Periodos de Retorno"
               
                fig_hist = px.histogram(
                    payback_data,
                    x='Periodo de retorno',
                    nbins=20,
                    histnorm=histnorm_val,
                    hover_data=['Centro', 'Medida'],
                    template="plotly_white",
                    title=title_text
                )
               
                fig_hist.update_layout(
                    xaxis_title="Periodo de Retorno (Años)",
                    yaxis_title=y_axis_title
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("No hay datos del Periodo de retorno para este filtro.")
       
        # --- Sankey Diagram (Full Width) ---
        st.subheader("Flujo de Inversión y Ahorro (Diagrama de Sankey)")
        datos_sankey = df_filtrado.groupby(['Categoría', columna_agrupar]).agg(Inversion_Total=('Inversión', 'sum'), Ahorro_Total=('Ahorro económico', 'sum')).reset_index()
        if not datos_sankey.empty and datos_sankey['Inversion_Total'].sum() > 0:
            todos_nodos = list(pd.concat([datos_sankey['Categoría'], datos_sankey[columna_agrupar]]).unique())
            fig_sankey = go.Figure(data=[go.Sankey(
                node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=todos_nodos),
                link=dict(
                    source=[todos_nodos.index(cat) for cat in datos_sankey['Categoría']],
                    target=[todos_nodos.index(center) for center in datos_sankey[columna_agrupar]],
                    value=datos_sankey['Inversion_Total'],
                    hovertemplate='Inversión de %{source.label} a %{target.label}: €%{value:,.0f}<br>' + 'Ahorro resultante: €' + datos_sankey['Ahorro_Total'].map('{:,.0f}'.format) + '<extra></extra>'
                ))])
            fig_sankey.update_layout(title_text=f"Flujo de Categoría a {columna_agrupar} por Inversión", font_size=12)
            st.plotly_chart(fig_sankey, use_container_width=True)
       
        st.markdown("---")
        st.header("Tablas de Datos")

        st.subheader("1. Explicación de Categorías")
        if tipo_analisis == 'Tipo de Medida':
            df_explicacion = pd.DataFrame([
                (info['Category'], desc, info['Code']) for desc, info in mapeo_medidas.items()
            ], columns=['Categoría', 'Descripción Medida', 'Prefijo Código']).sort_values(by='Prefijo Código')
        else:
            df_explicacion = df_filtrado[['Categoría']].drop_duplicates().sort_values('Categoría')
            df_explicacion['Explicación'] = df_explicacion['Categoría']
        st.dataframe(df_explicacion, use_container_width=True, hide_index=True)

        st.subheader(f"2. Datos Detallados por {columna_agrupar}")
        columnas_a_mostrar = [columna_agrupar, 'Medida', 'Categoría', 'Inversión', 'Ahorro energético', 'Ahorro económico', 'Periodo de retorno']
        if tipo_analisis == 'Tipo de Medida' and 'Código Medida' in df_filtrado.columns:
            columnas_a_mostrar.insert(1, 'Código Medida')
        df_tabla_financiera = df_filtrado[columnas_a_mostrar].sort_values(by=[columna_agrupar])
        st.dataframe(
            df_tabla_financiera, use_container_width=True, hide_index=True,
            column_config={
                "Inversión": st.column_config.NumberColumn("Inversión (€)", format="€ %d"),
                "Ahorro energético": st.column_config.NumberColumn("Ahorro Energético (kWh)", format="%d kWh"),
                "Ahorro económico": st.column_config.NumberColumn("Ahorro Anual (€)", format="€ %d"),
                "Periodo de retorno": st.column_config.NumberColumn("Retorno (años)", format="%.1f años"),
            }
        )
    else:
        st.info("No hay datos disponibles para la selección de filtros actual.")

else:
    st.warning("No se pudieron cargar los datos. Por favor, revise la ruta del archivo e inténtelo de nuevo.")
