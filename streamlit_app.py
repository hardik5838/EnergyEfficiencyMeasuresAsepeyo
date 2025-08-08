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
        measure_map = {
            'Regulación de la temperatura de consigna': 'Control térmico', 'Sustitución de equipos de climatización': 'Control térmico',
            'Instalación de cortina de aire': 'Control térmico', 'Instalación de temporizador digital': 'Control térmico',
            'Aislamiento de tuberías': 'Control térmico', 'Recuperadores de calor': 'Control térmico',
            'Optimización de la potencia contratada': 'Gestión energética', 'Implementación de un sistema de gestión': 'Gestión energética',
            'Compensación del consumo de energía reactiva': 'Gestión energética', 'Reducción del consumo remanente': 'Gestión energética',
            'Buenas prácticas': 'Gestión energética', 'Batería de condensadores': 'Gestión energética',
            'Instalación solar fotovoltaica': 'Gestión energética', 'Sustitución de luminarias a LED': 'Iluminación eficiente',
            'Instalación de regletas programables': 'Iluminación eficiente', 'Mejora en el control': 'Iluminación eficiente'
        }
        def get_type(measure):
            for key, value in measure_map.items():
                if key.lower() in measure.lower(): return value
            return 'Other'
        df_in['Category'] = df_in['Measure'].apply(get_type)
        return df_in

    def categorize_by_intervention(df_in):
        def get_type(measure):
            measure = measure.lower()
            if any(word in measure for word in ["instalación", "batería", "recuperadores", "solar"]): return 'New System Installation'
            elif any(word in measure for word in ["sustitución", "cambio", "mejora", "aislamiento"]): return 'Equipment Retrofit & Upgrade'
            elif any(word in measure for word in ["prácticas", "regulación", "optimización", "reducción"]): return 'Operational & Behavioral'
            return 'Other'
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
            if any(word in measure for word in ["hvac", "climatización", "temperatura", "ventilación", "aislamiento", "cortina", "calor"]): return 'Building Envelope & HVAC'
            if any(word in measure for word in ["led", "iluminación", "luminarias", "eléctrico", "potencia", "reactiva", "condensadores", "regletas"]): return 'Lighting & Electrical'
            if any(word in measure for word in ["gestión", "fotovoltaica", "solar", "prácticas", "remanente"]): return 'Energy Management & Strategy'
            return 'Other'
        df_in['Category'] = df_in['Measure'].apply(get_type)
        return df_in

    # --- Sidebar for All User Filters ---
    with st.sidebar:
        st.title('⚡ Asepeyo Filters')
        
        analysis_type = st.radio("Select Analysis Type", ('Tipo de Medida', 'Tipo de Intervención', 'Impacto Financiero', 'Función de Negocio'))
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
                if st.button("All Centers", use_container_width=True):
                    st.session_state.selected_centers = available_centers
                if st.button("Deselect Centers", use_container_width=True):
                    st.session_state.selected_centers = []

                selected_centers = st.multiselect('Select Centers', available_centers, default=st.session_state.selected_centers)
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
    }.get(analysis_type, categorize_by_tipo)(df_original.copy())

    if selected_communities:
        df_filtered = df_categorized[df_categorized['Comunidad Autónoma'].isin(selected_communities)]
        if detailed_view and selected_centers:
            df_filtered = df_filtered[df_filtered['Center'].isin(selected_centers)]
    else:
        df_filtered = pd.DataFrame(columns=df_categorized.columns)

    # --- Main Panel Rendering ---
    st.title("Energy Efficiency Analysis")

    # Header Logic
    if not selected_communities:
        st.warning("Please select at least one community to view data.")
    elif detailed_view and not selected_centers:
        st.warning(f"Please select at least one center for detailed comparison.")
    elif detailed_view:
        st.header(f"Comparing {len(selected_centers)} centers across {len(selected_communities)} communities")
    else:
        st.header(f"Summarized view for {len(selected_communities)} communities")

    # KPI and Chart Rendering
    if not df_filtered.empty:
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
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.subheader(f"Measure Counts by {analysis_type}")
            # Aggregate data to include measure details for hover
            agg_data = df_filtered.groupby([group_by_col, 'Category']).agg(
                Count=('Measure', 'size'),
                Measures=('Measure', lambda x: '<br>'.join(x.unique()))
            ).reset_index()

            if show_percentage:
                total_counts = agg_data.groupby(group_by_col)['Count'].transform('sum')
                agg_data['Percentage'] = (agg_data['Count'] / total_counts) * 100
                y_val, y_label = 'Percentage', 'Percentage of Measures (%)'
            else:
                y_val, y_label = 'Count', 'Number of Measures'

            fig1 = px.bar(agg_data, x=group_by_col, y=y_val, color='Category', hover_data=['Measures'], title=f'Measure Counts per {group_by_col}')
            fig1.update_layout(yaxis_title=y_label, xaxis_title=group_by_col, legend_title=analysis_type, template="plotly_white")
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
        
        # ... (Advanced Analysis Section remains the same) ...

    else:
        st.info("No data available for the current filter selection.")
        
