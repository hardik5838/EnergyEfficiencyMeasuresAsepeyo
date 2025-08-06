import streamlit as st
import pandas as pd
import altair as alt
import requests
import json
import io # Import the io module

# URL raw de GitHub para el archivo GeoJSON
geojson_url = "https://raw.githubusercontent.com/hardik5838/EnergyEfficiencyMeasuresAsepeyo/refs/heads/main/Data/georef-spain-comunidad-autonoma.geojson"

# URL raw de GitHub para los datos CSV
csv_url = "https://raw.githubusercontent.com/hardik5838/EnergyEfficiencyMeasuresAsepeyo/refs/heads/main/Data/2025%20Energy%20Audit%20summary%20-%20Sheet1.csv"


# Función para cargar y limpiar los datos
@st.cache_data
def load_data(url):
    """
    Carga los datos CSV desde una URL y limpia los nombres de las columnas.
    """
    try:
        # Read the CSV with header=1 as per user's instruction
        # This means the second row of the CSV will be used as headers
        df = pd.read_csv(url, header=0)

        # Define a mapping for standardizing column names
        column_renames = {
            'comunidad autónoma': 'comunidad_autonoma', # Standardize 'Comunidad Autónoma'
            'center': 'comunidad_autonoma',          # Map 'Center' to 'comunidad_autonoma'
            'measure': 'medida_mejora',
            'energy saved': 'ahorro_energetico_kwh',
            'money saved': 'ahorro_economico_eur',
            'investment': 'inversion_eur',
            'pay back period': 'periodo_retorno_simple_anos'
        }

        # Apply renaming. Only rename columns that actually exist in the DataFrame.
        df.rename(columns={k: v for k, v in column_renames.items() if k in df.columns}, inplace=True)

        # Remove any columns that are still 'unnamed' (e.g., 'unnamed: 0')
        # These often result from leading blank cells in the header row.
        df = df.loc[:, ~df.columns.astype(str).str.contains('^unnamed')]


        
        # Ensure 'comunidad_autonoma' is a simple Series (string type) and fill NaNs
        # ffill() propagates the last valid observation forward to next valid observation
        df['comunidad_autonoma'] = df['comunidad_autonoma'].astype(str).ffill()

        # Clean and convert numeric columns
        numeric_cols = ['ahorro_energetico_kwh', 'ahorro_economico_eur', 'inversion_eur', 'periodo_retorno_simple_anos']
        for col in numeric_cols:
            if col in df.columns:
                # Replace thousands separators (dots) and decimal separators (commas)
                # Then convert to numeric, coercing errors to NaN
                df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce') 
        
        # Add a category column for measure types. Handle potential NaN values in 'medida_mejora'
        df['categoria_medida'] = df['medida_mejora'].apply(lambda x: 
            'Medidas de Control de la iluminación' if 'luminarias' in str(x).lower() or 'iluminación' in str(x).lower() else
            'Medidas de gestión energética' if 'gestión energética' in str(x).lower() or 'fotovoltaica' in str(x).lower() or 'potencia' in str(x).lower() else
            'Medidas de control térmico' if 'temperatura' in str(x).lower() or 'gasóleo' in str(x).lower() or 'calor' in str(x).lower() or 'cortina de aire' in str(x).lower() else
            'Otros'
        )
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()        

@st.cache_data
def load_geojson(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error loading GeoJSON file from URL: {e}")
        return None
    except Exception as e:
        st.error(f"Error parsing GeoJSON: {e}")
        return None


# Configuración del diseño de la aplicación Streamlit
st.set_page_config(
    page_title="Resumen de Auditoría Energética 2025",
    layout="wide"
    page_icon="🏂",

)

st.title("Resumen de Auditoría Energética para 2025")

df_audit = load_data(csv_url)

if df_audit.empty: 
    st.warning("No se pudieron cargar los datos de la auditoría energética. Por favor, verifica la URL de GitHub y la ruta del archivo.")
else:
    # --- Interfaz con pestañas ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "Resumen Ejecutivo y Centro de Mando", 
        "Ganancias Rápidas y Acciones Inmediatas", 
        "Implementaciones Estratégicas y Proyectos Escalables",
        "Inversiones de Alto Impacto y Visión Futura"
    ])

    # Pre-calcula los datos regionales para evitar cálculos redundantes
    regional_data = df_audit.groupby('comunidad_autonoma').agg(
        total_investment=('inversion_eur', 'sum'),
        total_savings_eur=('ahorro_economico_eur', 'sum'),
        total_savings_kwh=('ahorro_energetico_kwh', 'sum'),
        count_measures=('medida_mejora', 'count') # Añadido para el gráfico de medidas por comunidad
    ).reset_index()

    # Calcula el período medio de recuperación después de la agrupación
    regional_data['avg_payback'] = regional_data['total_investment'] / regional_data['total_savings_eur']
    
    with tab1:
        st.header("KPIs de Impacto Nacional")
        
        # Gráfico 1.1: KPIs de Impacto Nacional
        total_savings = regional_data['total_savings_eur'].sum()
        total_investment = regional_data['total_investment'].sum()
        
        if total_savings > 0:
            avg_payback = total_investment / total_savings
        else:
            avg_payback = 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Ahorro Económico Anual Total", value=f"€{total_savings:,.0f}")
        with col2:
            st.metric(label="Inversión Requerida Total", value=f"€{total_investment:,.0f}")
        with col3:
            st.metric(label="Período Medio de Recuperación", value=f"{avg_payback:.1f} Años")
    
        st.markdown("### El 'Contador del Costo de la Inacción'")
        
        # Gráfico 1.2: El "Contador del Costo de la Inacción"
        zero_cost_measures = df_audit[df_audit['inversion_eur'] == 0]
        daily_cost_of_delay = zero_cost_measures['ahorro_economico_eur'].sum() / 365
        
        st.markdown(
            f"""
            <div style="background-color: #ffdbdb; padding: 20px; border-radius: 5px; text-align: center;">
                <h3 style="color: #000000; font-size: 20px;">Costo Diario del Retraso</h3>
                <h1 style="color: #000000; font-size: 48px; margin-top: -10px;">€{daily_cost_of_delay:,.2f}</h1>
                <p style="color: #DC3545;">Ahorros económicos perdidos cada día por no implementar medidas de costo cero.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
    
        # Gráfico 1.3: Cuadro de Mando de Eficiencia Regional
        st.markdown("### Cuadro de Mando de Eficiencia Regional")

        regional_data_sorted = regional_data.sort_values('avg_payback').reset_index(drop=True)
        
        def color_payback_cells(val):
            color = ''
            if pd.isna(val) or val < 2.0:
                color = '#D4EDDA'
            elif 2.0 <= val < 4.0:
                color = '#FFF3CD'
            else:
                color = '#F8D7DA'
            return f'background-color: {color}'
            
        styled_df = regional_data_sorted.style.applymap(
            color_payback_cells, subset=['avg_payback']
        ).set_properties(
            **{'background-color': '#F8F9FA'}, 
            subset=pd.IndexSlice[regional_data_sorted.index, :]
        ).format(
            {'total_investment': "€{:,.0f}", 'total_savings_eur': "€{:,.0f}", 'avg_payback': "{:.1f}"}
        ).hide(axis="index")
    
        st.dataframe(
            styled_df,
            column_order=('comunidad_autonoma', 'total_investment', 'total_savings_eur', 'avg_payback'),
            column_config={
                'comunidad_autonoma': st.column_config.TextColumn("Comunidad Autónoma", help="Nombre de la Región"),
                'total_investment': st.column_config.NumberColumn("Inversión Total (€)", help="Inversión Total en Euros"),
                'total_savings_eur': st.column_config.NumberColumn("Ahorro Anual (€)", help="Ahorro Anual Total en Euros"),
                'avg_payback': st.column_config.NumberColumn("Recuperación Media (Años)", help="Período Medio de Recuperación en Años")
            },
            use_container_width=True
        )
    
        st.markdown("---")
    
        # Gráfico 1.4: Ahorros Económicos y Energéticos por Región
        st.markdown("### Ahorros Económicos y Energéticos por Región")
    
        chart_col1, chart_col2 = st.columns(2)
    
        # Gráfico 1.4.1 Ahorros Económicos por Región
        with chart_col1:
            economic_chart_data = regional_data[['comunidad_autonoma', 'total_savings_eur']].rename(
                columns={'comunidad_autonoma': 'Comunidad', 'total_savings_eur': 'Total Savings'}
            )
            chart_a = alt.Chart(economic_chart_data).mark_bar(
                color='#007BFF'
            ).encode(
                x=alt.X('Comunidad', axis=alt.Axis(title='Comunidad Autónoma')),
                y=alt.Y('Total Savings', axis=alt.Axis(title='Ahorro Económico Anual Total (€)')),
                tooltip=[
                    alt.Tooltip('Comunidad', title='Comunidad'),
                    alt.Tooltip('Total Savings', title='Ahorro Total', format='€,.0f')
                ]
            ).properties(
                title="Ahorro Económico Anual Total por Región"
            )
            st.altair_chart(chart_a, use_container_width=True)
    
        # Gráfico 1.4.2 Ahorros Energéticos por Región
        with chart_col2:
            energy_chart_data = regional_data[['comunidad_autonoma', 'total_savings_kwh']].rename(
                columns={'comunidad_autonoma': 'Comunidad', 'total_savings_kwh': 'Total Savings'}
            )
            chart_b = alt.Chart(energy_chart_data).mark_bar(
                color='#007BFF'
            ).encode(
                x=alt.X('Comunidad', axis=alt.Axis(title='Comunidad Autónoma')),
                y=alt.Y('Total Savings', axis=alt.Axis(title='Ahorro Energético Anual Total (kWh)')),
                tooltip=[
                    alt.Tooltip('Comunidad', title='Comunidad'),
                    alt.Tooltip('Total Savings', title='Ahorro Total', format=',.0f')
                ]
            ).properties(
                title="Ahorro Energético Anual Total por Región"
            )
            st.altair_chart(chart_b, use_container_width=True)
        
        st.markdown("---")

    with tab2:
        st.header("Ganancias Rápidas y Acciones Inmediatas")
        
        # Gráfico 2.1: Gráfico de Impacto de "Victorias de Costo Cero"
        st.markdown("### Gráfico de Impacto de 'Victorias de Costo Cero'")
        
        zero_cost_data = df_audit[df_audit['inversion_eur'] == 0]
        zero_cost_summary = zero_cost_data.groupby('medida_mejora')['ahorro_economico_eur'].sum().reset_index()
        zero_cost_summary = zero_cost_summary.sort_values('ahorro_economico_eur', ascending=False)
        
        chart_2_1 = alt.Chart(zero_cost_summary).mark_bar(color='#28A745').encode(
            x=alt.X('ahorro_economico_eur', axis=alt.Axis(title='Ahorro Anual (€)')),
            y=alt.Y('medida_mejora', sort='-x', axis=alt.Axis(title='Medida')),
            tooltip=[
                alt.Tooltip('medida_mejora', title='Medida'),
                alt.Tooltip('ahorro_economico_eur', title='Ahorro Anual', format='€,.0f')
            ]
        ).properties(
            title="Ahorro Anual de Medidas de Inversión Cero"
        )
        st.altair_chart(chart_2_1, use_container_width=True)
        
        st.markdown("---")
        
        # Gráfico 2.2: Matriz de "Frutos al Alcance de la Mano"
        st.markdown("### Matriz de 'Frutos al Alcance de la Mano'")

        base_chart = alt.Chart(df_audit).mark_point(
            color='#007BFF'
        ).encode(
            x=alt.X('periodo_retorno_simple_anos', axis=alt.Axis(title='Período de Recuperación (Años)')),
            y=alt.Y('ahorro_economico_eur', axis=alt.Axis(title='Ahorro Económico Anual (€)')),
            tooltip=[
                alt.Tooltip('medida_mejora', title='Medida'),
                alt.Tooltip('comunidad_autonoma', title='Centro'),
                alt.Tooltip('ahorro_economico_eur', title='Ahorro', format='€,.0f'),
                alt.Tooltip('periodo_retorno_simple_anos', title='Recuperación', format='.1f')
            ]
        ).properties(
            title="Matriz de Priorización de Proyectos"
        )
        
        vline = alt.Chart(pd.DataFrame({'x': [1.5]})).mark_rule(
            color='#6C757D', strokeDash=[4, 4]
        ).encode(
            x='x'
        )
        
        hline = alt.Chart(pd.DataFrame({'y': [1000]})).mark_rule(
            color='#6C757D', strokeDash=[4, 4]
        ).encode(
            y='y'
        )
        
        combined_chart = base_chart + vline + hline
        
        st.altair_chart(combined_chart, use_container_width=True)

        st.markdown(
            f"""
            <div style="text-align: right; color: #6C757D; margin-top: -20px;">
                Proyectos de Alta Prioridad
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("---")
        
        # Gráfico 2.3: Retorno de la Inversión en el Primer Año
        st.markdown("### Retorno de la Inversión en el Primer Año")
        
        roi_data = regional_data.copy()
        
        roi_data['remaining_investment'] = roi_data['total_investment'] - roi_data['total_savings_eur']
        roi_data['remaining_investment'] = roi_data['remaining_investment'].apply(lambda x: max(x, 0))

        roi_melted = roi_data.melt(
            id_vars='comunidad_autonoma', 
            value_vars=['total_savings_eur', 'remaining_investment'],
            var_name='roi_type',
            value_name='value'
        )
        
        chart_2_3 = alt.Chart(roi_melted).mark_bar().encode(
            x=alt.X('comunidad_autonoma', axis=alt.Axis(title='Comunidad Autónoma')),
            y=alt.Y('value', stack="normalize", axis=alt.Axis(title='Proporción de la Inversión')),
            color=alt.Color(
                'roi_type',
                scale=alt.Scale(domain=['total_savings_eur', 'remaining_investment'], range=['#28A745', '#CED4DA']),
                legend=alt.Legend(title="Desglose de la Inversión", labelExpr="datum.label == 'total_savings_eur' ? 'Ahorro Anual' : 'Inversión Restante'")
            ),
            tooltip=[
                alt.Tooltip('comunidad_autonoma', title='Comunidad'),
                alt.Tooltip('roi_type', title='Tipo'),
                alt.Tooltip('value', title='Valor', format='€,.0f')
            ]
        ).properties(
            title="Retorno Económico en el Primer Año por Región"
        )
        st.altair_chart(chart_2_3, use_container_width=True)

    with tab3:
        st.header("Implementaciones Estratégicas y Proyectos Escalables")

        # Gráfico 3.1: Treemap "Ubicación y Urgencia" (usando un gráfico de barras apiladas como alternativa)
        st.markdown("### Medidas Más Comunes por Frecuencia y Urgencia")
        st.markdown("*(Alternativa a Treemap: Gráfico de Barras Apiladas)*")

        # Obtiene los datos para el gráfico
        treemap_data = df_audit.groupby('medida_mejora').agg(
            num_centers=('comunidad_autonoma', 'count'),
            avg_payback=('periodo_retorno_simple_anos', 'mean')
        ).reset_index().sort_values('num_centers', ascending=False)
        
        # Define la escala de color para la urgencia (período de recuperación)
        treemap_data['payback_urgency'] = pd.cut(
            treemap_data['avg_payback'],
            bins=[-1, 2, 4, treemap_data['avg_payback'].max() + 1],
            labels=['< 2 años', '2-4 años', '> 4 años']
        )
        
        chart_3_1 = alt.Chart(treemap_data).mark_bar(
            size=30
        ).encode(
            x=alt.X('num_centers', axis=alt.Axis(title='Número de Centros')),
            y=alt.Y('medida_mejora', sort='-x', axis=alt.Axis(title='Medida')),
            color=alt.Color(
                'payback_urgency',
                scale=alt.Scale(domain=['< 2 años', '2-4 años', '> 4 años'], range=['#28A745', '#FFC107', '#DC3545']),
                legend=alt.Legend(title="Recuperación Media")
            ),
            tooltip=[
                alt.Tooltip('medida_mejora', title='Medida'),
                alt.Tooltip('num_centers', title='Encontrado en', format='.0f'),
                alt.Tooltip('avg_payback', title='Recuperación Media', format='.1f')
            ]
        ).properties(
            title="Medidas Más Comunes por Frecuencia y Urgencia"
        )
        st.altair_chart(chart_3_1, use_container_width=True)

        st.markdown("---")
        
        # Gráfico 3.2: Perfil de Inversión por Medida
        st.markdown("### Desglose de Inversión para las 5 Medidas Más Frecuentes")
        
        # Obtiene las 5 medidas más frecuentes
        top_5_measures = treemap_data['medida_mejora'].head(5).tolist()
        
        # Filtra el DataFrame original solo para estas medidas
        top_5_data = df_audit[df_audit['medida_mejora'].isin(top_5_measures)].copy()
        
        # Define las categorías del período de recuperación
        top_5_data['payback_category'] = pd.cut(
            top_5_data['periodo_retorno_simple_anos'],
            bins=[-1, 1, 3, top_5_data['periodo_retorno_simple_anos'].max() + 1],
            labels=['< 1 año', '1-3 años', '> 3 años']
        )

        # Crea el gráfico de barras apiladas
        chart_3_2 = alt.Chart(top_5_data).mark_bar().encode(
            x=alt.X('medida_mejora', axis=alt.Axis(title='Medida')),
            y=alt.Y('sum(inversion_eur)', axis=alt.Axis(title='Inversión Total (€)')),
            color=alt.Color(
                'payback_category',
                scale=alt.Scale(domain=['< 1 año', '1-3 años', '> 3 años'], range=['#28A745', '#FFC107', '#DC3545']),
                legend=alt.Legend(title="Período de Recuperación")
            ),
            tooltip=[
                alt.Tooltip('medida_mejora', title='Medida'),
                alt.Tooltip('payback_category', title='Categoría de Recuperación'),
                alt.Tooltip('sum(inversion_eur)', title='Inversión', format='€,.0f')
            ]
        ).properties(
            title="Desglose de Inversión para las 5 Medidas Más Frecuentes"
        )
        st.altair_chart(chart_3_2, use_container_width=True)
        
        st.markdown("---")

    # Gráfico 3.3: Perfil de Necesidades Regionales
        st.markdown("### Proporción de Tipos de Medida por Región")

        # Define un mapeo de colores para las categorías conocidas
        color_map = {
            'Medidas de gestión energética': '#007BFF',  # Azul
            'Medidas de Control de la iluminación': '#FFC107',  # Amarillo
            'Medidas de control térmico': '#6C757D',      # Gris
            'Otros': '#CED4DA'                          # Neutro para categorías desconocidas
        }

        # Obtiene todas las categorías únicas de los datos y sus colores correspondientes
        unique_categories = df_audit['categoria_medida'].unique().tolist()
        domain = [cat for cat in unique_categories if cat in color_map]
        range_colors = [color_map[cat] for cat in domain]

        # Crea el gráfico de columnas apiladas
        chart_3_3 = alt.Chart(df_audit).mark_bar().encode(
            x=alt.X('comunidad_autonoma', axis=alt.Axis(title='Comunidad Autónoma')),
            y=alt.Y('count()', stack="normalize", axis=alt.Axis(title='Proporción de Medidas', format='%')),
            color=alt.Color(
                'categoria_medida',
                scale=alt.Scale(domain=domain, range=range_colors),
                legend=alt.Legend(title="Tipo de Medida")
            ),
            tooltip=[
                alt.Tooltip('comunidad_autonoma', title='Comunidad Autónoma'),
                alt.Tooltip('categoria_medida', title='Tipo de Medida'),
                alt.Tooltip('count()', title='Número de Medidas')
            ]
        ).properties(
            title="Proporción de Tipos de Medida por Región"
        )
        st.altair_chart(chart_3_3, use_container_width=True)
        
        # Gráfico adicional: Medidas requeridas por comunidad
        st.markdown("### Medidas Requeridas por Comunidad Autónoma")
        selected_comunidad_medidas = st.selectbox(
            "Selecciona una Comunidad Autónoma para ver sus medidas:",
            options=df_audit['comunidad_autonoma'].unique().tolist(),
            key='select_comunidad_medidas'
        )
        measures_by_comunidad = df_audit[df_audit['comunidad_autonoma'] == selected_comunidad_medidas].groupby('medida_mejora').agg(
            total_investment=('inversion_eur', 'sum'),
            total_savings_eur=('ahorro_economico_eur', 'sum'),
            count=('medida_mejora', 'count')
        ).reset_index().sort_values('count', ascending=False)

        chart_measures_comunidad = alt.Chart(measures_by_comunidad).mark_bar().encode(
            x=alt.X('count', axis=alt.Axis(title='Número de Veces Requerida')),
            y=alt.Y('medida_mejora', sort='-x', axis=alt.Axis(title='Medida')),
            tooltip=[
                alt.Tooltip('medida_mejora', title='Medida'),
                alt.Tooltip('count', title='Veces Requerida'),
                alt.Tooltip('total_investment', title='Inversión Total', format='€,.0f'),
                alt.Tooltip('total_savings_eur', title='Ahorro Total', format='€,.0f')
            ]
        ).properties(
            title=f"Medidas Requeridas en {selected_comunidad_medidas}"
        )
        st.altair_chart(chart_measures_comunidad, use_container_width=True)

        # Gráfico adicional: Tipos requeridos por Centro en Cataluña
        st.markdown("### Tipos de Medida Requeridos por Centro en Cataluña")
        cataluna_data = df_audit[df_audit['comunidad_autonoma'] == 'Cataluña']
        if not cataluna_data.empty:
            chart_types_cataluna = alt.Chart(cataluna_data).mark_bar().encode(
                x=alt.X('Center', axis=alt.Axis(title='Centro')),
                y=alt.Y('count()', stack="normalize", axis=alt.Axis(title='Proporción de Medidas', format='%')),
                color=alt.Color(
                    'categoria_medida',
                    scale=alt.Scale(domain=domain, range=range_colors),
                    legend=alt.Legend(title="Tipo de Medida")
                ),
                tooltip=[
                    alt.Tooltip('Center', title='Centro'),
                    alt.Tooltip('categoria_medida', title='Tipo de Medida'),
                    alt.Tooltip('count()', title='Número de Medidas')
                ]
            ).properties(
                title="Proporción de Tipos de Medida por Centro en Cataluña"
            )
            st.altair_chart(chart_types_cataluna, use_container_width=True)
        else:
            st.info("No hay datos para Cataluña.")
        
    with tab4:
        st.header("Inversiones de Alto Impacto y Visión Futura")
        # Gráfico 4.1: Mapa de "Potencial Fotovoltaico"
        st.markdown("### Ahorro Energético Potencial (kWh) de Instalaciones Solares")
        
        # Carga los datos GeoJSON
        source_geojson = load_geojson(geojson_url)

        if source_geojson is not None:
            # Filtra por proyectos solares y agrupa por región
            solar_data = df_audit[df_audit['medida_mejora'] == 'Instalación Fotovoltaica']
            solar_savings_by_region = solar_data.groupby('comunidad_autonoma')['ahorro_energetico_kwh'].sum().reset_index()

            # Crea una lista de todas las regiones para asegurar que todas estén en el mapa
            all_regions = df_audit['comunidad_autonoma'].unique().tolist()
            full_solar_data = pd.DataFrame({'comunidad_autonoma': all_regions})
            full_solar_data = pd.merge(full_solar_data, solar_savings_by_region, on='comunidad_autonoma', how='left').fillna(0)

            # Mapea manualmente los nombres para que coincidan con las propiedades de GeoJSON
            name_mapping = {
                'Andalucía': 'Andalucía',
                'Aragón': 'Aragón',
                'Castilla la Mancha': 'Castilla-La Mancha',
                'Castilla y León': 'Castilla y León',
                'Cataluña': 'Cataluña',
                'Comunidad Valenciana': 'Valenciana',
                'Euskadi (País Vasco)': 'País Vasco',
                'Madrid': 'Madrid',
                'Murcia': 'Murcia',
                'Extremadura': 'Extremadura',
                'La Rioja': 'La Rioja',
                'Cantabria': 'Cantabria',
                'Asturias': 'Asturias',
                # Asegúrate de que todos los nombres de tu CSV estén mapeados a los de GeoJSON
                # Si hay más regiones en tu CSV que no están aquí, añádelas.
            }
            full_solar_data['comunidad_autonoma_geojson'] = full_solar_data['comunidad_autonoma'].map(name_mapping).fillna(full_solar_data['comunidad_autonoma'])


            # Crea el mapa coroplético de Altair
            chart_4_1 = alt.Chart(alt.Data(values=source_geojson['features'])).mark_geoshape( # Usa alt.Data(values=...) para GeoJSON cargado
                stroke='black', 
                strokeWidth=0.5
            ).encode(
                color=alt.Color(
                    'properties.ahorro_energetico_kwh:Q', # Accede a la propiedad del GeoJSON
                    scale=alt.Scale(scheme='blues', domain=(0, full_solar_data['ahorro_energetico_kwh'].max())),
                    title="Ahorro Energético (kWh)"
                ),
                tooltip=[
                    alt.Tooltip('properties.name', title='Comunidad Autónoma'), # Muestra el nombre de la propiedad GeoJSON
                    alt.Tooltip('properties.ahorro_energetico_kwh:Q', title='Ahorro Potencial', format=',.0f')
                ]
            ).transform_lookup(
                lookup='properties.region', # Haz el lookup por la propiedad 'region' del GeoJSON
                from_=alt.LookupData(full_solar_data, 'comunidad_autonoma_geojson', ['ahorro_energetico_kwh'])
            ).project(
                type="mercator"
            ).properties(
                title="Ahorro Energético Potencial (kWh) de Instalaciones Solares"
            )
            st.altair_chart(chart_4_1, use_container_width=True)
            st.markdown("---")

            # Gráfico 4.2: Análisis del "Costo Total de Propiedad"
            st.markdown("### Análisis del Impacto Financiero a Largo Plazo")
            
            # Crea un menú desplegable
            high_cost_measures = [
                "Sustitución luminarias a LED", 
                "Instalación Fotovoltaica",
                "Instalación cortina de aire en puerta de entrada",
                "Sistema de Gestión Energética"
            ]
            
            selected_measure = st.selectbox(
                "Selecciona una medida de alto costo:",
                options=high_cost_measures
            )

            # Filtra los datos para la medida seleccionada
            measure_data = df_audit[df_audit['medida_mejora'] == selected_measure]
            
            if not measure_data.empty:
                total_investment = measure_data['inversion_eur'].sum()
                total_annual_savings = measure_data['ahorro_economico_eur'].sum()
                
                # Crea los datos del gráfico de cascada
                waterfall_data = pd.DataFrame({
                    'category': ['Inversión'] + [f'Año {i+1}' for i in range(10)] + ['Total'],
                    'amount': [-total_investment] + [total_annual_savings] * 10 + [total_annual_savings * 10 - total_investment]
                })
                
                # Crea una columna de color para el gráfico
                waterfall_data['color'] = ['#DC3545'] + ['#28A745'] * 10 + ['#007BFF']

                # Crea el gráfico de cascada de Altair
                chart_4_2 = alt.Chart(waterfall_data).mark_bar().encode(
                    x=alt.X('category', sort=None, axis=alt.Axis(title='Año')),
                    y=alt.Y('amount', axis=alt.Axis(title='Impacto Financiero Acumulado (€)')),
                    color=alt.Color('color', scale=None),
                    tooltip=[
                        alt.Tooltip('category', title='Categoría'),
                        alt.Tooltip('amount', title='Cantidad', format='€,.0f')
                    ]
                ).properties(
                    title=f"Impacto Financiero a Largo Plazo para {selected_measure}"
                )
                st.altair_chart(chart_4_2, use_container_width=True)
            else:
                st.info("No se encontraron datos para la medida seleccionada.")
            
            st.markdown("---")

            # Gráfico 4.3: Matriz de Inversión Estratégica
            st.markdown("### Perfil de Ahorro vs. Inversión Regional")
            
            # Calcula la inversión total y el ahorro total por región
            regional_summary_4_3 = df_audit.groupby('comunidad_autonoma').agg(
                total_investment=('inversion_eur', 'sum'),
                total_savings_kwh=('ahorro_energetico_kwh', 'sum')
            ).reset_index()

            # Calcula el porcentaje de ahorro energético (requiere un total de energía base, usaremos el total nacional como proxy si no está disponible)
            total_national_energy_kwh = regional_summary_4_3['total_savings_kwh'].sum()
            if total_national_energy_kwh > 0:
                regional_summary_4_3['percentage_savings'] = (regional_summary_4_3['total_savings_kwh'] / total_national_energy_kwh) * 100
            else:
                regional_summary_4_3['percentage_savings'] = 0

            chart_4_3 = alt.Chart(regional_summary_4_3).mark_point(
                size=100,
                color='#007BFF'
            ).encode(
                x=alt.X('percentage_savings', axis=alt.Axis(title='Ahorro Energético Porcentual (%)')),
                y=alt.Y('total_investment', axis=alt.Axis(title='Inversión Requerida Total (€)')),
                tooltip=[
                    alt.Tooltip('comunidad_autonoma', title='Comunidad Autónoma'),
                    alt.Tooltip('percentage_savings', title='Ahorro Porcentual', format='.1f'),
                    alt.Tooltip('total_investment', title='Inversión Total', format='€,.0f')
                ]
            )
            
            # Añade etiquetas de texto a los puntos
            text = chart_4_3.mark_text(
                align='left',
                baseline='middle',
                dx=7
            ).encode(
                text='comunidad_autonoma'
            )

            st.altair_chart(chart_4_3 + text, use_container_width=True)

            # Gráfico adicional: Inversión vs Ahorro Porcentual de Energía en Madrid
            st.markdown("### Inversión vs. Ahorro Energético Porcentual en Madrid")
            madrid_data = regional_summary_4_3[regional_summary_4_3['comunidad_autonoma'] == 'Madrid']
            if not madrid_data.empty:
                chart_madrid_investment_savings = alt.Chart(madrid_data).mark_point(
                    size=150,
                    color='#DC3545' # Rojo para destacar Madrid
                ).encode(
                    x=alt.X('percentage_savings', axis=alt.Axis(title='Ahorro Energético Porcentual (%)')),
                    y=alt.Y('total_investment', axis=alt.Axis(title='Inversión Requerida Total (€)')),
                    tooltip=[
                        alt.Tooltip('comunidad_autonoma', title='Comunidad Autónoma'),
                        alt.Tooltip('percentage_savings', title='Ahorro Porcentual', format='.1f'),
                        alt.Tooltip('total_investment', title='Inversión Total', format='€,.0f')
                    ]
                ).properties(
                    title="Inversión vs. Ahorro Energético Porcentual en Madrid"
                )
                st.altair_chart(chart_madrid_investment_savings, use_container_width=True)
            else:
                st.info("No hay datos para Madrid.")

            # Gráfico adicional: Relación Ahorro e Inversión en Términos Financieros por Comunidad
            st.markdown("### Relación Ahorro e Inversión en Términos Financieros por Comunidad")
            chart_financial_relation = alt.Chart(regional_data).mark_point(
                size=100,
                color='#28A745' # Verde para destacar el ahorro financiero
            ).encode(
                x=alt.X('total_investment', axis=alt.Axis(title='Inversión Total (€)')),
                y=alt.Y('total_savings_eur', axis=alt.Axis(title='Ahorro Económico Anual Total (€)')),
                tooltip=[
                    alt.Tooltip('comunidad_autonoma', title='Comunidad Autónoma'),
                    alt.Tooltip('total_investment', title='Inversión Total', format='€,.0f'),
                    alt.Tooltip('total_savings_eur', title='Ahorro Económico', format='€,.0f')
                ]
            ).properties(
                title="Relación Ahorro e Inversión Financiera por Comunidad"
            )
            st.altair_chart(chart_financial_relation, use_container_width=True)
        
    st.markdown("---")
    st.subheader("Datos Brutos de la Auditoría Energética 2025")
    st.dataframe(df_audit, use_container_width=True)


    # --- Ideas para Futuras Implementaciones ---
    st.markdown("---")
    st.markdown("### Funcionalidad Futura")
    st.markdown("""
- **Pestaña de Comparación**: Una nueva pestaña o página para comparar datos de diferentes años. Esto se puede implementar añadiendo más archivos Excel para diferentes años y creando nuevas funciones para cargarlos y compararlos.
- **Gráficos Interactivos**: Añadir visualizaciones como gráficos de barras para comparar `Energy Saved` o `Money Saved` por `Center` o `Measure`.
- **Opciones de Filtrado**: Permitir a los usuarios filtrar los datos por `Center` o `Measure` utilizando widgets de Streamlit como `st.selectbox`.
""")
