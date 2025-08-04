import streamlit as st
import pandas as pd
import altair as alt
import requests
import json

# GitHub raw URL for the GeoJSON file
geojson_url = "https://raw.githubusercontent.com/hardik5838/EnergyEfficiencyMeasuresAsepeyo/refs/heads/main/Data/georef-spain-comunidad-autonoma.geojson"

# GitHub raw URL for the CSV data
csv_url = "https://raw.githubusercontent.com/hardik5838/EnergyEfficiencyMeasuresAsepeyo/refs/heads/main/Data/2025%20Energy%20Audit%20summary%20-%20Sheet1.csv"


# Function to load and clean the data
@st.cache_data
def load_data(url):
    """
    Loads the CSV data from a URL and cleans the column names.
    """
    try:
        df = pd.read_csv(url, header=1)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df.columns = [col.strip() for col in df.columns]
        df['Center'] = df['Center'].ffill()

        # Map the original column names to the new, user-friendly names
        col_map = {
            'Money Saved': 'ahorro_economico_eur',
            'Investment': 'inversion_eur',
            'Energy Saved': 'ahorro_energetico_kwh',
            'Center': 'comunidad_autonoma',
            'Measure': 'medida_mejora',
            'Pay back period': 'periodo_retorno_simple_anos'
        }
        
        df.rename(columns=col_map, inplace=True)

        # Clean and convert numeric columns
        numeric_cols = ['ahorro_energetico_kwh', 'ahorro_economico_eur', 'inversion_eur', 'periodo_retorno_simple_anos']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Add a category column for measure types. Make sure to handle potential NaN values in 'medida_mejora'
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


# Set up the Streamlit app layout
st.set_page_config(
    page_title="2025 Energy Audit Summary",
    layout="wide"
)

st.title("Energy Audit Summary for 2025")

df_audit = load_data(csv_url)

if df_audit.empty:
    st.warning("Could not load the energy audit data. Please check the GitHub URL and file path.")
else:
    # --- Tabbed interface ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "Executive Summary & Command Center", 
        "Quick Wins & Immediate Actions", 
        "Strategic Rollouts & Scalable Projects",
        "High-Impact Investments & Future Vision"
    ])


    with tab1:
        st.header("National Impact KPIs")
        
        # Chart 1.1: National Impact KPIs
        total_savings = df_audit['ahorro_economico_eur'].sum()
        total_investment = df_audit['inversion_eur'].sum()
        
        if total_savings > 0:
            avg_payback = total_investment / total_savings
        else:
            avg_payback = 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Total Annual Economic Savings", value=f"€{total_savings:,.0f}")
        with col2:
            st.metric(label="Total Required Investment", value=f"€{total_investment:,.0f}")
        with col3:
            st.metric(label="Average Payback Period", value=f"{avg_payback:.1f} Years")
    
        st.markdown("### The 'Cost of Inaction' Counter")
        
        # Chart 1.2: The "Cost of Inaction" Counter
        zero_cost_measures = df_audit[df_audit['inversion_eur'] == 0]
        daily_cost_of_delay = zero_cost_measures['ahorro_economico_eur'].sum() / 365
        
        st.markdown(
            f"""
            <div style="background-color: #ffdbdb; padding: 20px; border-radius: 5px; text-align: center;">
                <h3 style="color: #000000; font-size: 20px;">Daily Cost of Delay</h3>
                <h1 style="color: #000000; font-size: 48px; margin-top: -10px;">€{daily_cost_of_delay:,.2f}</h1>
                <p style="color: #DC3545;">Economic savings lost each day by not implementing zero-cost measures.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
    
        # Chart 1.3: Regional Efficiency Scorecard
        st.markdown("### Regional Efficiency Scorecard")

        regional_data = df_audit.groupby('comunidad_autonoma').agg(
            total_investment=('inversion_eur', 'sum'),
            total_savings=('ahorro_economico_eur', 'sum')
        ).reset_index()
        
        regional_data['avg_payback'] = regional_data['total_investment'] / regional_data['total_savings']
        
        regional_data = regional_data.sort_values('avg_payback').reset_index(drop=True)
        
        def color_payback_cells(val):
            color = ''
            if val < 2.0:
                color = '#D4EDDA'
            elif 2.0 <= val < 4.0:
                color = '#FFF3CD'
            else:
                color = '#F8D7DA'
            return f'background-color: {color}'
            
        styled_df = regional_data.style.applymap(
            color_payback_cells, subset=['avg_payback']
        ).set_properties(
            **{'background-color': '#F8F9FA'}, 
            subset=pd.IndexSlice[regional_data.index, :]
        ).format(
            {'total_investment': "€{:,.0f}", 'total_savings': "€{:,.0f}", 'avg_payback': "{:.1f}"}
        ).hide(axis="index")
    
        st.dataframe(
            styled_df,
            column_order=('comunidad_autonoma', 'total_investment', 'total_savings', 'avg_payback'),
            column_config={
                'comunidad_autonoma': st.column_config.TextColumn("Comunidad Autónoma", help="Region Name"),
                'total_investment': st.column_config.NumberColumn("Total Investment (€)", help="Total Investment in Euros"),
                'total_savings': st.column_config.NumberColumn("Annual Savings (€)", help="Total Annual Savings in Euros"),
                'avg_payback': st.column_config.NumberColumn("Average Payback (Years)", help="Average Payback Period in Years")
            },
            use_container_width=True
        )
    
        st.markdown("---")
    
        # Chart 1.4: Economic & Energy Savings by Region
        st.markdown("### Economic & Energy Savings by Region")
    
        chart_col1, chart_col2 = st.columns(2)
    
        # Refactor Chart 1.4.1 Economic & Energy Savings by Region (Economic)
        with chart_col1:
            economic_chart_data = regional_data[['comunidad_autonoma', 'total_savings']].rename(
                columns={'comunidad_autonoma': 'Comunidad', 'total_savings': 'Total Savings'}
            )
            chart_a = alt.Chart(economic_chart_data).mark_bar(
                color='#007BFF'
            ).encode(
                x=alt.X('Comunidad', axis=alt.Axis(title='Comunidad Autónoma')),
                y=alt.Y('Total Savings', axis=alt.Axis(title='Total Annual Economic Savings (€)')),
                tooltip=[
                    alt.Tooltip('Comunidad', title='Comunidad'),
                    alt.Tooltip('Total Savings', title='Total Savings', format='€,.0f')
                ]
            ).properties(
                title="Total Annual Economic Savings by Region"
            )
            st.altair_chart(chart_a, use_container_width=True)
    
        # Refactor Chart 1.4.2 Economic & Energy Savings by Region (Energy)
        with chart_col2:
            energy_data = df_audit.groupby('comunidad_autonoma')['ahorro_energetico_kwh'].sum().reset_index()
            energy_chart_data = energy_data.rename(
                columns={'comunidad_autonoma': 'Comunidad', 'ahorro_energetico_kwh': 'Total Savings'}
            )
            chart_b = alt.Chart(energy_chart_data).mark_bar(
                color='#007BFF'
            ).encode(
                x=alt.X('Comunidad', axis=alt.Axis(title='Comunidad Autónoma')),
                y=alt.Y('Total Savings', axis=alt.Axis(title='Total Annual Energy Savings (kWh)')),
                tooltip=[
                    alt.Tooltip('Comunidad', title='Comunidad'),
                    alt.Tooltip('Total Savings', title='Total Savings', format=',.0f')
                ]
            ).properties(
                title="Total Annual Energy Savings by Region"
            )
            st.altair_chart(chart_b, use_container_width=True)
        
        st.markdown("---")

    with tab2:
        st.header("Quick Wins & Immediate Actions")
        
        # Chart 2.1: "Zero-Cost Victories" Impact Chart
        st.markdown("### Zero-Cost Victories Impact Chart")
        
        zero_cost_data = df_audit[df_audit['inversion_eur'] == 0]
        zero_cost_summary = zero_cost_data.groupby('medida_mejora')['ahorro_economico_eur'].sum().reset_index()
        zero_cost_summary = zero_cost_summary.sort_values('ahorro_economico_eur', ascending=False)
        
        chart_2_1 = alt.Chart(zero_cost_summary).mark_bar(color='#28A745').encode(
            x=alt.X('ahorro_economico_eur', axis=alt.Axis(title='Annual Savings (€)')),
            y=alt.Y('medida_mejora', sort='-x', axis=alt.Axis(title='Measure')),
            tooltip=[
                alt.Tooltip('medida_mejora', title='Measure'),
                alt.Tooltip('ahorro_economico_eur', title='Annual Savings', format='€,.0f')
            ]
        ).properties(
            title="Annual Savings from Zero-Investment Measures"
        )
        st.altair_chart(chart_2_1, use_container_width=True)
        
        st.markdown("---")
        
        # Chart 2.2: "Low-Hanging Fruit" Matrix
        st.markdown("### Low-Hanging Fruit Matrix")

        base_chart = alt.Chart(df_audit).mark_point(
            color='#007BFF'
        ).encode(
            x=alt.X('periodo_retorno_simple_anos', axis=alt.Axis(title='Payback Period (Years)')),
            y=alt.Y('ahorro_economico_eur', axis=alt.Axis(title='Annual Economic Savings (€)')),
            tooltip=[
                alt.Tooltip('medida_mejora', title='Measure'),
                alt.Tooltip('comunidad_autonoma', title='Center'),
                alt.Tooltip('ahorro_economico_eur', title='Savings', format='€,.0f'),
                alt.Tooltip('periodo_retorno_simple_anos', title='Payback', format='.1f')
            ]
        ).properties(
            title="Project Prioritization Matrix"
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
                High Priority Projects
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("---")
        
        # Chart 2.3: First-Year Return on Investment
        st.markdown("### First-Year Return on Investment")
        
        roi_data = df_audit.groupby('comunidad_autonoma').agg(
            total_investment=('inversion_eur', 'sum'),
            total_savings=('ahorro_economico_eur', 'sum')
        ).reset_index()
        
        roi_data['remaining_investment'] = roi_data['total_investment'] - roi_data['total_savings']
        roi_data['remaining_investment'] = roi_data['remaining_investment'].apply(lambda x: max(x, 0))

        roi_melted = roi_data.melt(
            id_vars='comunidad_autonoma', 
            value_vars=['total_savings', 'remaining_investment'],
            var_name='roi_type',
            value_name='value'
        )
        
        chart_2_3 = alt.Chart(roi_melted).mark_bar().encode(
            x=alt.X('comunidad_autonoma', axis=alt.Axis(title='Comunidad Autónoma')),
            y=alt.Y('value', stack="normalize", axis=alt.Axis(title='Proportion of Investment')),
            color=alt.Color(
                'roi_type',
                scale=alt.Scale(domain=['total_savings', 'remaining_investment'], range=['#28A745', '#CED4DA']),
                legend=alt.Legend(title="Investment Breakdown", labelExpr="datum.label == 'total_savings' ? 'Annual Savings' : 'Remaining Investment'")
            ),
            tooltip=[
                alt.Tooltip('comunidad_autonoma', title='Comunidad'),
                alt.Tooltip('roi_type', title='Type'),
                alt.Tooltip('value', title='Value', format='€,.0f')
            ]
        ).properties(
            title="First-Year Economic Return by Region"
        )
        st.altair_chart(chart_2_3, use_container_width=True)

    with tab3:
        st.header("Strategic Rollouts & Scalable Projects")

        # Chart 3.1: "Ubiquity & Urgency" Treemap (using a stacked bar chart as an alternative)
        st.markdown("### Most Common Measures by Frequency and Urgency")
        st.markdown("*(Alternative to Treemap: Stacked Bar Chart)*")

        # Get data for the chart
        treemap_data = df_audit.groupby('medida_mejora').agg(
            num_centers=('comunidad_autonoma', 'count'),
            avg_payback=('periodo_retorno_simple_anos', 'mean')
        ).reset_index().sort_values('num_centers', ascending=False)
        
        # Define color scale for urgency (payback period)
        treemap_data['payback_urgency'] = pd.cut(
            treemap_data['avg_payback'],
            bins=[-1, 2, 4, treemap_data['avg_payback'].max() + 1],
            labels=['< 2 years', '2-4 years', '> 4 years']
        )
        
        chart_3_1 = alt.Chart(treemap_data).mark_bar(
            size=30
        ).encode(
            x=alt.X('num_centers', axis=alt.Axis(title='Number of Centers')),
            y=alt.Y('medida_mejora', sort='-x', axis=alt.Axis(title='Measure')),
            color=alt.Color(
                'payback_urgency',
                scale=alt.Scale(domain=['< 2 years', '2-4 years', '> 4 years'], range=['#28A745', '#FFC107', '#DC3545']),
                legend=alt.Legend(title="Average Payback")
            ),
            tooltip=[
                alt.Tooltip('medida_mejora', title='Measure'),
                alt.Tooltip('num_centers', title='Found in', format='.0f'),
                alt.Tooltip('avg_payback', title='Avg Payback', format='.1f')
            ]
        ).properties(
            title="Most Common Measures by Frequency and Urgency"
        )
        st.altair_chart(chart_3_1, use_container_width=True)

        st.markdown("---")
        
        # Chart 3.2: Investment Profile by Measure
        st.markdown("### Investment Breakdown for Top 5 Most Frequent Measures")
        
        # Get the top 5 most frequent measures
        top_5_measures = treemap_data['medida_mejora'].head(5).tolist()
        
        # Filter the original DataFrame for only these measures
        top_5_data = df_audit[df_audit['medida_mejora'].isin(top_5_measures)].copy()
        
        # Define payback period categories
        top_5_data['payback_category'] = pd.cut(
            top_5_data['periodo_retorno_simple_anos'],
            bins=[-1, 1, 3, top_5_data['periodo_retorno_simple_anos'].max() + 1],
            labels=['< 1 year', '1-3 years', '> 3 years']
        )

        # Create stacked bar chart
        chart_3_2 = alt.Chart(top_5_data).mark_bar().encode(
            x=alt.X('medida_mejora', axis=alt.Axis(title='Measure')),
            y=alt.Y('sum(inversion_eur)', axis=alt.Axis(title='Total Investment (€)')),
            color=alt.Color(
                'payback_category',
                scale=alt.Scale(domain=['< 1 year', '1-3 years', '> 3 years'], range=['#28A745', '#FFC107', '#DC3545']),
                legend=alt.Legend(title="Payback Period")
            ),
            tooltip=[
                alt.Tooltip('medida_mejora', title='Measure'),
                alt.Tooltip('payback_category', title='Payback Category'),
                alt.Tooltip('sum(inversion_eur)', title='Investment', format='€,.0f')
            ]
        ).properties(
            title="Investment Breakdown for Top 5 Most Frequent Measures"
        )
        st.altair_chart(chart_3_2, use_container_width=True)
        
        st.markdown("---")

    # Chart 3.3: Regional Needs Profile
        st.markdown("### Proportion of Measure Types by Region")

        # Define a color mapping for the known categories
        color_map = {
            'Medidas de gestión energética': '#007BFF',  # Blue
            'Medidas de Control de la iluminación': '#FFC107',  # Yellow
            'Medidas de control térmico': '#6C757D',      # Grey
            'Otros': '#CED4DA'                          # Neutral for unknown categories
        }

        # Get all unique categories from the data and their corresponding colors
        unique_categories = df_audit['categoria_medida'].unique().tolist()
        domain = [cat for cat in unique_categories if cat in color_map]
        range_colors = [color_map[cat] for cat in domain]

        # Create stacked column chart
        chart_3_3 = alt.Chart(df_audit).mark_bar().encode(
            x=alt.X('comunidad_autonoma', axis=alt.Axis(title='Comunidad Autónoma')),
            y=alt.Y('count()', stack="normalize", axis=alt.Axis(title='Proportion of Measures', format='%')),
            color=alt.Color(
                'categoria_medida',
                scale=alt.Scale(domain=domain, range=range_colors),
                legend=alt.Legend(title="Measure Type")
            ),
            tooltip=[
                alt.Tooltip('comunidad_autonoma', title='Comunidad Autónoma'),
                alt.Tooltip('categoria_medida', title='Measure Type'),
                alt.Tooltip('count()', title='Number of Measures')
            ]
        ).properties(
            title="Proportion of Measure Types by Region"
        )
        st.altair_chart(chart_3_3, use_container_width=True)
        
        
        
    with tab4:
        st.header("High-Impact Investments & Future Vision")
        # Chart 4.1: "Photovoltaic Potential" Map
        st.markdown("### Potential Energy Savings (kWh) from Solar Installations")
        
        # Load the GeoJSON data
        source = load_geojson(geojson_url)

        if source is not None:
            # Filter for solar projects and group by region
            solar_data = df_audit[df_audit['medida_mejora'] == 'Instalación Fotovoltaica']
            solar_savings_by_region = solar_data.groupby('comunidad_autonoma')['ahorro_energetico_kwh'].sum().reset_index()

            # Create a list of all regions to ensure all are on the map
            all_regions = df_audit['comunidad_autonoma'].unique().tolist()
            full_solar_data = pd.DataFrame({'comunidad_autonoma': all_regions})
            full_solar_data = pd.merge(full_solar_data, solar_savings_by_region, on='comunidad_autonoma', how='left').fillna(0)

            # Manually map the names to match the GeoJSON properties
            # The GeoJSON names are in Spanish, but without the accents
            name_mapping = {
                'Aragón': 'Aragon',
                'Comunidad Valenciana': 'Valencia',
                'Murcia': 'Murcia',
                'País Vasco': 'País Vasco',
                'Castilla-La Mancha': 'Castilla-La Mancha',
                'Extremadura': 'Extremadura',
                'Andalucía': 'Andalucía',
                'Canarias': 'Canary Is.',
                'Ceuta': 'Ceuta',
                'Cataluña': 'Cataluña',
                'Castilla y León': 'Castilla y León',
                'La Rioja': 'La Rioja'
            }
            full_solar_data['comunidad_autonoma_geojson'] = full_solar_data['comunidad_autonoma'].map(name_mapping).fillna(full_solar_data['comunidad_autonoma'])


            # Create the Altair choropleth map
            chart_4_1 = alt.Chart(source).mark_geoshape(
                stroke='black', 
                strokeWidth=0.5
            ).encode(
                color=alt.Color(
                    'ahorro_energetico_kwh:Q', 
                    scale=alt.Scale(scheme='blues', domain=(0, full_solar_data['ahorro_energetico_kwh'].max())),
                    title="Energy Savings (kWh)"
                ),
                tooltip=[
                    alt.Tooltip('properties.name', title='Comunidad Autónoma'),
                    alt.Tooltip('ahorro_energetico_kwh:Q', title='Potential Savings', format=',.0f')
                ]
            ).transform_lookup(
                lookup='properties.name',
                from_=alt.LookupData(full_solar_data, 'comunidad_autonoma_geojson', ['ahorro_energetico_kwh'])
            ).project(
                type="mercator"
            ).properties(
                title="Potential Energy Savings (kWh) from Solar Installations"
            )
            st.altair_chart(chart_4_1, use_container_width=True)
            st.markdown("---")

            # Chart 4.2: "Total Cost of Ownership" Analysis
            st.markdown("### Long-Term Financial Impact Analysis")
            
            # Create a dropdown menu
            high_cost_measures = [
                "Sustitución luminarias a LED", 
                "Instalación Fotovoltaica",
                "Instalación cortina de aire en puerta de entrada",
                "Sistema de Gestión Energética"
            ]
            
            selected_measure = st.selectbox(
                "Select a high-cost measure:",
                options=high_cost_measures
            )

            # Filter the data for the selected measure
            measure_data = df_audit[df_audit['medida_mejora'] == selected_measure]
            
            if not measure_data.empty:
                total_investment = measure_data['inversion_eur'].sum()
                total_annual_savings = measure_data['ahorro_economico_eur'].sum()
                
                # Create the waterfall chart data
                waterfall_data = pd.DataFrame({
                    'category': ['Investment'] + [f'Year {i+1}' for i in range(10)] + ['Total'],
                    'amount': [-total_investment] + [total_annual_savings] * 10 + [total_annual_savings * 10 - total_investment]
                })
                
                # Create a color column for the chart
                waterfall_data['color'] = ['#DC3545'] + ['#28A745'] * 10 + ['#007BFF']

                # Create the Altair waterfall chart
                chart_4_2 = alt.Chart(waterfall_data).mark_bar().encode(
                    x=alt.X('category', sort=None, axis=alt.Axis(title='Year')),
                    y=alt.Y('amount', axis=alt.Axis(title='Cumulative Financial Impact (€)')),
                    color=alt.Color('color', scale=None),
                    tooltip=[
                        alt.Tooltip('category', title='Category'),
                        alt.Tooltip('amount', title='Amount', format='€,.0f')
                    ]
                ).properties(
                    title=f"Long-Term Financial Impact for {selected_measure}"
                )
                st.altair_chart(chart_4_2, use_container_width=True)
            else:
                st.info("No data found for the selected measure.")
            
            st.markdown("---")

            # Chart 4.3: Strategic Investment Matrix
            st.markdown("### Regional Savings vs. Investment Profile")
            
            # Calculate total investment and total savings by region
            regional_summary = df_audit.groupby('comunidad_autonoma').agg(
                total_investment=('inversion_eur', 'sum'),
                total_savings=('ahorro_energetico_kwh', 'sum')
            ).reset_index()

            chart_4_3 = alt.Chart(regional_summary).mark_point(
                size=100,
                color='#007BFF'
            ).encode(
                x=alt.X('total_savings', axis=alt.Axis(title='Total Energy Savings (kWh)')),
                y=alt.Y('total_investment', axis=alt.Axis(title='Total Required Investment (€)')),
                tooltip=[
                    alt.Tooltip('comunidad_autonoma', title='Comunidad Autónoma'),
                    alt.Tooltip('total_savings', title='Total Savings', format=',.0f'),
                    alt.Tooltip('total_investment', title='Total Investment', format='€,.0f')
                ]
            )
            
            # Add text labels to the points
            text = chart_4_3.mark_text(
                align='left',
                baseline='middle',
                dx=7
            ).encode(
                text='comunidad_autonoma'
            )

            st.altair_chart(chart_4_3 + text, use_container_width=True)
        
    st.markdown("---")
    st.subheader("Raw Data from the 2025 Energy Audit")
    st.dataframe(df_audit, use_container_width=True)


    # --- Future Development Ideas ---
    st.markdown("---")
    st.markdown("### Future Functionality")
    st.markdown("""
- **Comparison Tab**: A new tab or page to compare data from different years. This can be implemented by adding more Excel files for different years and creating new functions to load and compare them.
- **Interactive Charts**: Add visualizations like bar charts to compare `Energy Saved` or `Money Saved` by `Center` or `Measure`.
- **Filtering Options**: Allow users to filter the data by `Center` or `Measure` using Streamlit widgets like `st.selectbox`.
""")

