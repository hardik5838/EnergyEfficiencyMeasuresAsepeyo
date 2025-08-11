# Import libraries
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Asepeyo Energy Efficiency Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Data Loading and Caching ---
@st.cache_data
def load_data(file_path):
    """Loads, cleans, and processes the energy audit data."""
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        for col in ['Energy Saved', 'Money Saved', 'Investment', 'Pay back period']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.fillna(0, inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Error: The data file was not found. Please ensure '2025 Energy Audit summary - Sheet1 (1).csv' exists.")
        return pd.DataFrame()

# --- Main Application Logic ---
df_original = load_data('2025 Energy Audit summary - Sheet1 (1).csv')

if not df_original.empty:

    # --- Session State Initialization ---
    if 'selected_centers' not in st.session_state:
        st.session_state.selected_centers = []
    if 'selected_communities' not in st.session_state:
        st.session_state.selected_communities = sorted(df_original['Comunidad Autónoma'].unique().tolist())

    # --- Helper Functions for Categorization ---
    def categorize_by_tipo(df_in):
        """Categorizes using the user's direct matching table."""
        measure_mapping = {
            "Regulation of the set temperature": {"Category": "Thermal control measures", "Code": "A.1"},
            "Air curtain installation": {"Category": "Thermal control measures", "Code": "A.3"},
            "Installing a digital timer on an electric water heater": {"Category": "Thermal control measures", "Code": "A.4"},
            "Installing a digital timer in a paraffin bath": {"Category": "Thermal control measures", "Code": "A.4"},
            "Ventilation regulation using a CO2 probe": {"Category": "Thermal control measures", "Code": "A.5"},
            "Heat recovery units": {"Category": "Thermal control measures", "Code": "A.6"},
            "O2 adjustment in diesel boiler C": {"Category": "Thermal control measures", "Code": "A.X"},
            "Installation of variable frequency drives in pumps": {"Category": "Thermal control measures", "Code": "A.X"},
            "Solar thermal installation": {"Category": "Thermal control measures", "Code": "A.X"},
            "Optimization of contracted power": {"Category": "Energy management measures", "Code": "B.1"},
            "Energy Management System": {"Category": "Energy management measures", "Code": "B.2"},
            "Elimination of reactive energy": {"Category": "Energy management measures", "Code": "B.3"},
            "Reduction of remaining consumption": {"Category": "Energy management measures", "Code": "B.4"},
            "Promote energy culture": {"Category": "Energy management measures", "Code": "B.5"},
            "Photovoltaic Installation": {"Category": "Energy management measures", "Code": "B.6"},
            "LED Lighting Change": {"Category": "Lighting control measures", "Code": "C.1"},
            "Installing programmable power strips": {"Category": "Lighting control measures", "Code": "C.2"},
            "Improved lighting control": {"Category": "Lighting control measures", "Code": "C.3"}
        }
        def get_info(measure_text):
            for standard_name, info in measure_mapping.items():
                if standard_name.lower() in measure_text.lower():
                    return pd.Series([info['Category'], info['Code']])
            return pd.Series(['Uncategorized', 'Z.Z'])
        df_in[['Category', 'Measure Code Base']] = df_in['Measure'].apply(get_info)
        return df_in

    def categorize_by_intervention(df_in):
        def get_type(measure):
            measure = measure.lower()
            if any(word in measure for word in ["instalación", "batería", "recuperadores", "solar", "fotovoltaica"]): return 'New System Installation'
            if any(word in measure for word in ["sustitución", "cambio", "mejora", "aislamiento"]): return 'Equipment Retrofit & Upgrade'
            if any(word in measure for word in ["prácticas", "cultura", "regulación", "optimización", "reducción"]): return 'Operational & Behavioral'
            return 'Specific Interventions'
        df_in['Category'] = df_in['Measure'].apply(get_type)
        return df_in

    def categorize_by_financials(df_in):
        def get_type(payback):
            if payback <= 0: return 'No Cost / Immediate'
            if payback < 2: return 'Quick Wins (< 2 years)'
            if payback <= 5: return 'Standard Projects (2-5 years)'
            return 'Strategic Investments (> 5 years)'
        df_in['Category'] = df_in['Pay back period'].apply(get_type)
        return df_in

    def categorize_by_function(df_in):
        def get_type(measure):
            measure = measure.lower()
            if any(word in measure for word in ["hvac", "climatización", "temperatura", "ventilación", "aislamiento", "cortina", "calor", "termo"]): return 'Building Envelope & HVAC'
            if any(word in measure for word in ["led", "iluminación", "luminarias", "eléctrico", "potencia", "reactiva", "condensadores", "regletas"]): return 'Lighting & Electrical'
            if any(word in measure for word in ["gestión", "fotovoltaica", "solar", "prácticas", "remanente", "cultura"]): return 'Energy Management & Strategy'
            return 'Other Functions'
        df_in['Category'] = df_in['Measure'].apply(get_type)
        return df_in
        
    def categorize_by_energy_type(df_in):
        """Categorizes measures by the type of energy they affect."""
        def get_type(measure):
            measure = measure.lower()
            if any(word in measure for word in ["gasóleo", "diesel", "caldera"]):
                return 'Gas/Fuel'
            if any(word in measure for word in ["led", "iluminación", "fotovoltaica", "eléctrico", "potencia", "reactiva", "variadores", "bombas"]):
                return 'Electric'
            if any(word in measure for word in ["climatización", "temperatura", "hvac", "aislamiento", "cortina", "recuperadores"]):
                return 'Both/HVAC'
            return 'Operational/N/A'
        df_in['Category'] = df_in['Measure'].apply(get_type)
        return df_in

    # --- Sidebar for All User Filters ---
    with st.sidebar:
        st.title('⚡ Asepeyo Filters')
        analysis_type = st.radio(
            "Select Analysis Type",
            ('Tipo de Medida', 'Tipo de Intervención', 'Impacto Financiero', 'Función de Negocio', 'Tipo de Energía')
        )
        show_percentage = st.toggle('Show percentage values')
        st.markdown("---")
        detailed_view = st.toggle('Show Detailed Center View', key='detailed_view')
        
        community_list = sorted(df_original['Comunidad Autónoma'].unique().tolist())
        if st.button("All Communities", use_container_width=True):
            st.session_state.selected_communities = community_list
        
        selected_communities = st.multiselect('Select Communities', community_list, default=st.session_state.selected_communities)
        st.session_state.selected_communities = selected_communities

        if detailed_view:
            if selected_communities:
                available_centers = sorted(df_original[df_original['Comunidad Autónoma'].isin(selected_communities)]['Center'].unique().tolist())
                if not all(center in available_centers for center in st.session_state.selected_centers):
                    st.session_state.selected_centers = available_centers
                
                st.write("Manage Center Selection:")
                col1, col2 = st.columns([0.7, 0.3])
                with col1:
                    selected_centers = st.multiselect('Select Centers', available_centers, default=st.session_state.selected_centers, label_visibility="collapsed")
                with col2:
                    if st.button("All", help="Select all centers"):
                        st.session_state.selected_centers = available_centers
                        st.experimental_rerun()
                st.session_state.selected_centers = selected_centers
            else:
                selected_centers = []
        else:
            selected_centers = []

    # --- Data Processing based on Filters ---
    df_categorized = {
        'Tipo de Intervención': categorize_by_intervention,
        'Impacto Financiero': categorize_by_financials,
        'Función de Negocio': categorize_by_function,
        'Tipo de Energía': categorize_by_energy_type,
    }.get(analysis_type, categorize_by_tipo)(df_original.copy())

    if selected_communities:
        df_filtered = df_categorized[df_categorized['Comunidad Autónoma'].isin(selected_communities)]
        if detailed_view and selected_centers:
            df_filtered = df_filtered[df_filtered['Center'].isin(selected_centers)]
    else:
        df_filtered = pd.DataFrame(columns=df_categorized.columns)

    # --- Main Panel Rendering ---
    st.title("Energy Efficiency Analysis")

    if not df_filtered.empty:
        # Generate the full measure code including frequency
        if 'Measure Code Base' in df_filtered.columns:
            df_filtered['Frequency'] = df_filtered.groupby(['Comunidad Autónoma', 'Measure Code Base']).cumcount() + 1
            df_filtered['Measure Code'] = df_filtered.apply(
                lambda row: f"{row['Measure Code Base']}.{row['Frequency']}" if row['Measure Code Base'] != 'Z.Z' else 'Uncategorized',
                axis=1
            )
        
        # ... (Your existing KPI, Header, and Chart code can now be pasted here)
        # For completeness, the full rendering code is included below.
        
        # Header Logic
        if detailed_view and not selected_centers:
            st.warning("Please select at least one center for detailed comparison.")
        elif detailed_view:
            st.header(f"Comparing {len(selected_centers)} centers across {len(selected_communities)} communities")
        else:
            st.header(f"Summarized view for {len(selected_communities)} communities")

        # KPI Display
        total_investment = df_filtered['Investment'].sum()
        total_money_saved = df_filtered['Money Saved'].sum()
        total_energy_saved = df_filtered['Energy Saved'].sum()
        roi = (total_money_saved / total_investment) * 100 if total_investment > 0 else 0

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric(label="Total Investment", value=f"€ {total_investment:,.0f}")
        kpi2.metric(label="Total Money Saved", value=f"€ {total_money_saved:,.0f}")
        kpi3.metric(label="Total Energy Saved", value=f"{total_energy_saved:,.0f} kWh")
        kpi4.metric(label="Return on Investment (ROI)", value=f"{roi:.2f} %")
        st.markdown("---")

        group_by_col = 'Center' if detailed_view else 'Comunidad Autónoma'
        
        # Chart Rendering
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.subheader(f"Measure Counts by {analysis_type}")
            agg_data = df_filtered.groupby([group_by_col, 'Category']).agg(Count=('Measure', 'size'), Measures=('Measure', lambda x: '<br>'.join(x.unique()))).reset_index()
            y_val, y_label = ('Percentage', 'Percentage of Measures (%)') if show_percentage else ('Count', 'Number of Measures')
            if show_percentage:
                total_counts = agg_data.groupby(group_by_col)['Count'].transform('sum')
                agg_data['Percentage'] = (agg_data['Count'] / total_counts) * 100

            fig1 = px.bar(agg_data, x=group_by_col, y=y_val, color='Category', hover_data=['Measures'])
            fig1.update_layout(title=f'Measure Counts per {group_by_col}', yaxis_title=y_label, xaxis_title=group_by_col, legend_title=analysis_type, template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)

            st.subheader("Energy Savings Analysis")
            energy_agg = df_filtered.groupby(group_by_col).agg(
                Total_Energy_Saved=('Energy Saved', 'sum'),
                Measures=('Measure', lambda x: '<br>'.join(x.unique()))
            ).reset_index()

            if show_percentage:
                total_savings_overall = energy_agg['Total_Energy_Saved'].sum()
                energy_agg['Percentage'] = (energy_agg['Total_Energy_Saved'] / total_savings_overall) * 100 if total_savings_overall > 0 else 0
                y_val, y_label = 'Percentage', 'Contribution to Total Savings (%)'
            else:
                y_val, y_label = 'Total_Energy_Saved', 'Energy Saved (kWh)'

            fig5 = px.bar(energy_agg.sort_values('Total_Energy_Saved', ascending=False), x=group_by_col, y=y_val, hover_data=['Measures'], title=f'Energy Savings per {group_by_col}')
            fig5.update_layout(yaxis_title=y_label, xaxis_title=group_by_col, template="plotly_white")
            st.plotly_chart(fig5, use_container_width=True)

        with col2:
            st.subheader("Economic Savings Analysis")
            eco_agg = df_filtered.groupby(group_by_col).agg(
                Total_Money_Saved=('Money Saved', 'sum'),
                Measure_Count=('Measure', 'size')
            ).reset_index()
            fig6 = px.pie(eco_agg, names=group_by_col, values='Total_Money_Saved', title=f'Contribution to Economic Savings by {group_by_col}', hole=0.4, hover_data=['Measure_Count'])
            fig6.update_traces(hovertemplate='<b>%{label}</b><br>Money Saved: €%{value:,.0f}<br>Measure Count: %{customdata[0]}<extra></extra>')
            st.plotly_chart(fig6, use_container_width=True)
            
            st.subheader("Investment vs. Financial Savings")
            fin_summary = df_filtered.groupby(group_by_col).agg(Total_Investment=('Investment', 'sum'), Total_Money_Saved=('Money Saved', 'sum')).reset_index()
            fig7 = px.scatter(fin_summary, x='Total_Investment', y='Total_Money_Saved', text=group_by_col, size='Total_Investment', color=group_by_col, title=f'Investment vs. Money Saved per {group_by_col}')
            fig7.update_traces(textposition='top center')
            st.plotly_chart(fig7, use_container_width=True)
        
# Advanced Analysis Section
    # --- Advanced Analysis Section ---
    st.markdown("---")
    st.header("Advanced Analysis")
    
    # Create two columns for the new charts
    adv_col1, adv_col2 = st.columns(2, gap="large")
    
    with adv_col1:
        # --- Recommendation 1: Investment vs. Savings Bubble Chart ---
        st.subheader("Investment Efficacy")
        
        # Filter out measures with no investment or savings to clean up the plot
        plot_data = df_filtered[(df_filtered['Investment'] > 0) & (df_filtered['Money Saved'] > 0)]
        
        if not plot_data.empty:
            fig_bubble = px.scatter(
                plot_data,
                x='Investment',
                y='Money Saved',
                size='Energy Saved',  # Bubble size represents energy savings
                color='Category',     # Color by the selected analysis type
                hover_name='Measure', # Show measure name on hover
                size_max=60,          # Control the maximum bubble size for readability
                template="plotly_white",
                title="Investment vs. Annual Savings"
            )
            
            fig_bubble.update_layout(
                xaxis_title="Investment (€)",
                yaxis_title="Annual Money Saved (€)",
                legend_title=analysis_type
            )
            st.plotly_chart(fig_bubble, use_container_width=True)
        else:
            st.info("No data with both investment and savings to display in the bubble chart.")
    
    with adv_col2:
        # --- Recommendation 2: Payback Period Histogram ---
        st.subheader("Project Payback Distribution")
        
        # Filter out items with no payback period for a cleaner histogram
        payback_data = df_filtered[df_filtered['Pay back period'] > 0]
        
        if not payback_data.empty:
            fig_hist = px.histogram(
                payback_data,
                x='Pay back period',
                nbins=20, # Adjust the number of bins for more or less detail
                template="plotly_white",
                title="Distribution of Payback Periods"
            )
            
            fig_hist.update_layout(
                xaxis_title="Payback Period (Years)",
                yaxis_title="Number of Measures"
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No data with a payback period to display in the histogram.")
    
    
    # --- Recommendation 3: Sankey Diagram ---
    st.markdown("---")
    st.subheader("Investment & Savings Flow (Sankey Diagram)")
    
    # Sankey diagrams require specific data formatting (source, target, value)
    sankey_data = df_filtered.groupby(['Category', group_by_col]).agg(
        Total_Investment=('Investment', 'sum'),
        Total_Savings=('Money Saved', 'sum')
    ).reset_index()
    
    if not sankey_data.empty and sankey_data['Total_Investment'].sum() > 0:
        import plotly.graph_objects as go
    
        # Create lists of unique sources and targets
        all_nodes = list(pd.concat([sankey_data['Category'], sankey_data[group_by_col]]).unique())
        
        # Create the Sankey diagram
        fig_sankey = go.Figure(data=[go.Sankey(
            node=dict(
              pad=15,
              thickness=20,
              line=dict(color="black", width=0.5),
              label=all_nodes,
            ),
            link=dict(
              # Map text labels to integer indices
              source=[all_nodes.index(cat) for cat in sankey_data['Category']],
              target=[all_nodes.index(center) for center in sankey_data[group_by_col]],
              value=sankey_data['Total_Investment'],
              # Add hover info to show both investment and savings
              hovertemplate='Investment from %{source.label} to %{target.label}: €%{value:,.0f}<br>' +
                            'Resulting Savings: €' + sankey_data['Total_Savings'].map('{:,.0f}'.format) + 
                            '<extra></extra>' # Hides the default trace info
            ))])
    
        fig_sankey.update_layout(title_text="Flow from Measure Category to Center by Investment", font_size=12)
        st.plotly_chart(fig_sankey, use_container_width=True)
  
        # --- Data Tables Section ---
        st.markdown("---")
        st.header("Data Tables")

        # Table 1: Measure Coding and Frequency
        st.subheader("1. Measure Coding System")
        code_explanation_df = pd.DataFrame(measure_mapping.items(), columns=['Measure Description', 'Info'])
        code_explanation_df['Category'] = code_explanation_df['Info'].apply(lambda x: x['Category'])
        code_explanation_df['Code Prefix'] = code_explanation_df['Info'].apply(lambda x: x['Code'])
        st.dataframe(
            code_explanation_df[['Category', 'Measure Description', 'Code Prefix']].sort_values(by=['Code Prefix']),
            use_container_width=True,
            hide_index=True
        )

        # Table 2: Detailed Financials per Measure Code
        st.subheader("2. Detailed Data per Measure")
        financial_table_df = df_filtered[[
            group_by_col,
            'Measure Code',
            'Measure',
            'Investment',
            'Energy Saved',
            'Money Saved',
            'Pay back period'
        ]].sort_values(by=[group_by_col, 'Measure Code'])

        st.dataframe(
            financial_table_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Investment": st.column_config.NumberColumn("Investment (€)", format="€ %d"),
                "Energy Saved": st.column_config.NumberColumn("Energy Saved (kWh)", format="%d kWh"),
                "Money Saved": st.column_config.NumberColumn("Money Saved (€/year)", format="€ %d"),
                "Pay back period": st.column_config.NumberColumn("Payback (years)", format="%.1f years"),
            }
        )

    else:
        st.info("No data available for the current filter selection.")
else:
    st.warning("Data could not be loaded. Please check the file path and try again.")










