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
        st.error(f"Error: The data file was not found. Please ensure 'Data/2025 Energy Audit summary - Sheet1.csv' exists.")
        return pd.DataFrame()

# --- Main Application Logic ---
df_original = load_data('2025 Energy Audit summary - Sheet1 (1).csv')

if not df_original.empty:

    # --- Session State Initialization ---
    if 'selected_centers' not in st.session_state:
        st.session_state.selected_centers = []

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
        
        analysis_type = st.radio(
            "Select Analysis Type",
            ('Tipo de Medida', 'Tipo de Intervención', 'Impacto Financiero', 'Función de Negocio')
        )
        
        show_percentage = st.toggle('Show percentage values')

        st.markdown("---")
        
        community_list = sorted(df_original['Comunidad Autónoma'].unique().tolist())
        selected_communities = st.multiselect(
            'Select Communities',
            community_list,
            default=community_list
        )

        if selected_communities:
            available_centers = sorted(df_original[df_original['Comunidad Autónoma'].isin(selected_communities)]['Center'].unique().tolist())
            
            st.write("Manage Center Selection:")
            col1, col2 = st.columns(2)
            if col1.button("Select All", use_container_width=True):
                st.session_state.selected_centers = available_centers
            if col2.button("Deselect All", use_container_width=True):
                st.session_state.selected_centers = []
            
            # This check resets center selection if the available centers change
            if not all(center in available_centers for center in st.session_state.selected_centers):
                st.session_state.selected_centers = available_centers

            selected_centers = st.multiselect('Select Centers', available_centers, default=st.session_state.selected_centers)
            st.session_state.selected_centers = selected_centers
        else:
            selected_centers = []

    # --- Data Processing based on Filters ---
    if analysis_type == 'Tipo de Intervención':
        df_categorized = categorize_by_intervention(df_original.copy())
    elif analysis_type == 'Impacto Financiero':
        df_categorized = categorize_by_financials(df_original.copy())
    elif analysis_type == 'Función de Negocio':
        df_categorized = categorize_by_function(df_original.copy())
    else:
        df_categorized = categorize_by_tipo(df_original.copy())

    if selected_communities:
        df_filtered = df_categorized[df_categorized['Comunidad Autónoma'].isin(selected_communities)]
        if selected_centers:
            df_filtered = df_filtered[df_filtered['Center'].isin(selected_centers)]
    else:
        df_filtered = pd.DataFrame(columns=df_categorized.columns)

    # --- Main Panel Rendering ---
    st.title("Energy Efficiency Analysis")

    # Header Logic
    if not selected_communities:
        st.warning("Please select at least one community from the sidebar to view data.")
    elif len(selected_communities) == 1 and len(selected_centers) == 1:
        st.header(f"Data for: {selected_centers[0]}")
    elif len(selected_communities) > 0 and not selected_centers:
        st.warning(f"Please select at least one center in the chosen community/communities.")
    else:
        st.header(f"Comparing {len(selected_centers)} centers in {len(selected_communities)} communities")

    # KPI Calculation
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

    # Chart Rendering
    if not df_filtered.empty:
        # Determine grouping level based on selections
        if len(selected_communities) > 1:
            group_by_col = 'Comunidad Autónoma'
        else:
            group_by_col = 'Center'
        
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.subheader(f"Measure Counts by {analysis_type}")
            if 'Category' in df_filtered.columns:
                if show_percentage:
                    measures_by_type = df_filtered.groupby([group_by_col, 'Category']).size().unstack(fill_value=0)
                    measures_pct = measures_by_type.apply(lambda x: x * 100 / x.sum(), axis=1).stack().reset_index(name='Percentage')
                    fig1 = px.bar(measures_pct, x=group_by_col, y='Percentage', color='Category', title=f'% of Measure Types per {group_by_col.replace("_", " ")}')
                    fig1.update_yaxes(title_text="Percentage of Measures (%)")
                else:
                    measures_by_type = df_filtered.groupby([group_by_col, 'Category']).size().reset_index(name='Count')
                    fig1 = px.bar(measures_by_type, x=group_by_col, y='Count', color='Category', title=f'Measure Counts per {group_by_col.replace("_", " ")}')
                    fig1.update_yaxes(title_text="Number of Measures")
                fig1.update_layout(xaxis_title=group_by_col.replace("_", " ").title(), legend_title=analysis_type, template="plotly_white")
                st.plotly_chart(fig1, use_container_width=True)

            st.subheader("Energy Savings Analysis")
            if show_percentage:
                total_savings = df_filtered['Energy Saved'].sum()
                energy_savings = df_filtered.groupby(group_by_col)['Energy Saved'].sum().reset_index()
                energy_savings['Percentage'] = (energy_savings['Energy Saved'] / total_savings) * 100 if total_savings > 0 else 0
                fig5 = px.bar(energy_savings.sort_values('Energy Saved', ascending=False), x=group_by_col, y='Percentage', title=f'% Contribution to Energy Savings')
                fig5.update_yaxes(title_text="Contribution to Total Savings (%)")
            else:
                energy_savings = df_filtered.groupby(group_by_col)['Energy Saved'].sum().reset_index()
                fig5 = px.bar(energy_savings.sort_values('Energy Saved', ascending=False), x=group_by_col, y='Energy Saved', title=f'Energy Savings (kWh) per {group_by_col.replace("_", " ")}')
                fig5.update_yaxes(title_text="Energy Saved (kWh)")
            fig5.update_layout(xaxis_title=group_by_col.replace("_", " ").title(), template="plotly_white")
            st.plotly_chart(fig5, use_container_width=True)

        with col2:
            st.subheader("Economic Savings Analysis")
            economic_savings = df_filtered.groupby(group_by_col)['Money Saved'].sum().reset_index()
            fig6 = px.pie(economic_savings, names=group_by_col, values='Money Saved', title=f'Contribution to Economic Savings by {group_by_col.replace("_", " ")}', hole=0.4)
            fig6.update_layout(template="plotly_white")
            st.plotly_chart(fig6, use_container_width=True)
            
            st.subheader("Investment vs. Financial Savings")
            financial_summary = df_filtered.groupby(group_by_col).agg(Total_Investment=('Investment', 'sum'), Total_Money_Saved=('Money Saved', 'sum')).reset_index()
            fig7 = px.scatter(financial_summary, x='Total_Investment', y='Total_Money_Saved', text=group_by_col, size='Total_Investment', color=group_by_col, title=f'Investment vs. Money Saved per {group_by_col.replace("_", " ")}')
            fig7.update_traces(textposition='top center')
            fig7.update_layout(template="plotly_white")
            st.plotly_chart(fig7, use_container_width=True)

        # Advanced Analysis Section
        st.markdown("---")
        st.header("Advanced Analysis")
        adv_col1, adv_col2 = st.columns(2, gap="large")

        with adv_col1:
            st.subheader("Investment Efficacy")
            plot_data = df_filtered[(df_filtered['Investment'] > 0) & (df_filtered['Money Saved'] > 0)]
            if not plot_data.empty:
                fig_bubble = px.scatter(plot_data, x='Investment', y='Money Saved', size='Energy Saved', color='Category', hover_name='Measure', size_max=60, title="Investment vs. Annual Savings")
                fig_bubble.update_layout(xaxis_title="Investment (€)", yaxis_title="Annual Money Saved (€)", legend_title=analysis_type, template="plotly_white")
                st.plotly_chart(fig_bubble, use_container_width=True)

        with adv_col2:
            st.subheader("Project Payback Distribution")
            payback_data = df_filtered[df_filtered['Pay back period'] > 0]
            if not payback_data.empty:
                fig_hist = px.histogram(payback_data, x='Pay back period', nbins=20, title="Distribution of Payback Periods")
                fig_hist.update_layout(xaxis_title="Payback Period (Years)", yaxis_title="Number of Measures", template="plotly_white")
                st.plotly_chart(fig_hist, use_container_width=True)

        st.markdown("---")
        st.subheader("Investment & Savings Flow (Sankey Diagram)")
        sankey_data = df_filtered.groupby(['Category', group_by_col]).agg(Total_Investment=('Investment', 'sum'), Total_Savings=('Money Saved', 'sum')).reset_index()
        if not sankey_data.empty and sankey_data['Total_Investment'].sum() > 0:
            all_nodes = list(pd.concat([sankey_data['Category'], sankey_data[group_by_col]]).unique())
            fig_sankey = go.Figure(data=[go.Sankey(
                node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=all_nodes),
                link=dict(
                  source=[all_nodes.index(cat) for cat in sankey_data['Category']],
                  target=[all_nodes.index(center) for center in sankey_data[group_by_col]],
                  value=sankey_data['Total_Investment'],
                  hovertemplate='Investment from %{source.label} to %{target.label}: €%{value:,.0f}<br>' + 'Resulting Savings: €' + sankey_data['Total_Savings'].map('{:,.0f}'.format) + '<extra></extra>'
                ))])
            fig_sankey.update_layout(title_text="Flow from Measure Category to Location by Investment", font_size=12)
            st.plotly_chart(fig_sankey, use_container_width=True)

else:
    st.warning("Data could not be loaded. Please check the file path and try again.")
