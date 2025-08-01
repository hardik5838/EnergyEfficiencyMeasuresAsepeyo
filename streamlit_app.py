import streamlit as st
import pandas as pd
import altair as alt

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
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

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
    tab1, tab2 = st.tabs(["Executive Summary & Command Center", "Quick Wins & Immediate Actions"])

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
```
