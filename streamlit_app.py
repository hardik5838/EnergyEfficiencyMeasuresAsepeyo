# Import libraries
import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt

# Page configuration
st.set_page_config(
    page_title="Asepeyo Energy Efficiency Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load and process data
@st.cache_data
def load_data(file_path):
    """Loads and processes the energy audit data."""
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        for col in ['Energy Saved', 'Money Saved', 'Investment', 'Pay back period']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.fillna(0, inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Error: The file '{file_path}' was not found. Please make sure the file is in the correct directory.")
        return pd.DataFrame()

# Provide the correct path to your CSV file
df = load_data('Data/2025 Energy Audit summary - Sheet1.csv')

if not df.empty:

# --- Categorize Measures ---
# This block adds a 'Measure Type' column to the DataFrame based on the measure names.

# Mapping of specific measures to their general category
    measure_map = {
    # Control térmico
    'Regulación de la temperatura de consigna': 'Control térmico',
    'Sustitución de equipos de climatización': 'Control térmico',
    'Instalación de cortina de aire': 'Control térmico',
    'Instalación cortina de aire en puerta de entrada': 'Control térmico',
    'Instalación de temporizador digital': 'Control térmico',
    'Aislamiento de tuberías de climatización': 'Control térmico',
    'Regulación de ventilación mediante sonda CO2': 'Control térmico',
    'Recuperadores de calor': 'Control térmico',
    
    # Gestión energética
    'Optimización de la potencia contratada': 'Gestión energética',
    'Implementación de un sistema de gestión energética': 'Gestión energética',
    'Sistema de Gestión Energética': 'Gestión energética',
    'Compensación del consumo de energía reactiva': 'Gestión energética',
    'Reducción del consumo remanente': 'Gestión energética',
    'Reducción de consumo remanente': 'Gestión energética',
    'Buenas prácticas': 'Gestión energética',
    'Promover la cultura energética': 'Gestión energética',
    'Batería de condensadores': 'Gestión energética',
    'Instalación solar fotovoltaica': 'Gestión energética',
    'Instalación Solar térmica': 'Gestión energética',
    
    # Iluminación eficiente
    'Sustitución de luminarias a LED': 'Iluminación eficiente',
    'Cambio Iluminacion LED': 'Iluminación eficiente',
    'Instalación de regletas programables': 'Iluminación eficiente',
    'Instalación regletas programables': 'Iluminación eficiente',
    'Control de renovación de aire mediante sonda CO2': 'Iluminación eficiente',
    'Mejora en el control actual de la iluminación': 'Iluminación eficiente',
    'Mejora en el control de la iluminación': 'Iluminación eficiente'
}

# Function to find the category for a given measure text
def get_measure_type(measure_text):
    for key, value in measure_map.items():
        if key.lower() in measure_text.lower():
            return value
    return 'Other' # Default category if no match is found

# Apply the function to create the new column
if not df.empty:
    df['Measure Type'] = df['Measure'].apply(get_measure_type)   
    
    
    
    # Sidebar Filters with Multi-Select
    with st.sidebar:
        st.title('⚡ Asepeyo Energy Dashboard')
        
        # 1. Filter by Autonomous Community
        community_list = ['All'] + sorted(df['Comunidad Autónoma'].unique().tolist())
        selected_community = st.selectbox('Select a Community', community_list)

        # Initialize df_filtered and selected_centers
        selected_centers = []
        if selected_community == 'All':
            df_filtered = df
        else:
            df_community_filtered = df[df['Comunidad Autónoma'] == selected_community]
            
            # 2. Dependent MULTI-SELECT for Center
            center_list = sorted(df_community_filtered['Center'].unique().tolist())
            selected_centers = st.multiselect(
                'Select one or more Centers to compare', 
                center_list, 
                default=center_list  # By default, all centers in the community are selected
            )

            # Further filter by the list of selected centers
            if selected_centers:
                df_filtered = df_community_filtered[df_community_filtered['Center'].isin(selected_centers)]
            else:
                # If no center is selected, show an empty dataframe
                df_filtered = pd.DataFrame(columns=df.columns)



    
    # Main Panel with Dynamic Title
    st.title("Energy Efficiency Analysis")
    
    
    # Create a dynamic subheader
    if selected_community == 'All':
        st.header("Showing data for All Communities")
    elif not selected_centers:
        st.warning(f"Please select at least one center in {selected_community} to view data.")
    elif len(selected_centers) == 1:
        st.header(f"Showing data for: {selected_centers[0]}")
    else:
        st.header(f"Comparing {len(selected_centers)} centers in {selected_community}")

    
    # --- Key Performance Indicators (KPIs) ---
    total_investment = df_filtered['Investment'].sum()
    total_money_saved = df_filtered['Money Saved'].sum()
    total_energy_saved = df_filtered['Energy Saved'].sum()
    
    if total_investment > 0:
        roi = (total_money_saved / total_investment) * 100
    else:
        roi = 0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(label="Total Investment", value=f"€ {total_investment:,.0f}")
    kpi2.metric(label="Total Money Saved", value=f"€ {total_money_saved:,.0f}")
    kpi3.metric(label="Total Energy Saved", value=f"{total_energy_saved:,.0f} kWh")
    kpi4.metric(label="Return on Investment (ROI)", value=f"{roi:.2f} %")
    
    st.markdown("---")


    # --- Chart Layout ---
    # Only display charts if there is data to show
    if not df_filtered.empty:
        col1, col2 = st.columns(2, gap="large")

        with col1:
            # --- Chart 1: Measures required per community/center (Stacked by Type) ---
            st.subheader("Measure Counts by Type")
            group_by_col = 'Center' if selected_community != 'All' else 'Comunidad Autónoma'
            
            # Group by the primary column AND the new Measure Type to get counts for each segment
            measures_by_type = df_filtered.groupby([group_by_col, 'Measure Type']).size().reset_index(name='Count')
            
            fig1 = px.bar(
                measures_by_type,
                x=group_by_col,
                y='Count',
                color='Measure Type', # This creates the stacked segments
                title=f'Measure Types per {group_by_col.replace("_", " ")}',
                template="plotly_white",
                # Define custom colors for consistency and clarity
                color_discrete_map={
                    'Control térmico': '#0072B2',       # Blue
                    'Gestión energética': '#009E73',  # Green
                    'Iluminación eficiente': '#F0E442', # Yellow
                    'Other': '#D55E00'                  # Orange
                }
            )
            
            # Improve layout for better readability
            fig1.update_layout(
                xaxis_title=group_by_col.replace("_", " ").title(),
                yaxis_title="Number of Measures",
                legend_title="Measure Type"
            )
            st.plotly_chart(fig1, use_container_width=True)

            
            # --- Chart 5: Energy Savings per community/center ---
            st.subheader("Energy Savings Analysis")
            energy_savings = df_filtered.groupby(group_by_col)['Energy Saved'].sum().reset_index()
            fig5 = px.bar(
                energy_savings.sort_values('Energy Saved', ascending=False),
                x=group_by_col, y='Energy Saved', title=f'Energy Savings (kWh) per {group_by_col.replace("_", " ")}',
                labels={'Energy Saved': 'Total Energy Saved (kWh)'},
                template="plotly_white"
            )
            st.plotly_chart(fig5, use_container_width=True)


        with col2:
            # --- Chart 6: Economic Savings Donut Chart ---
            st.subheader("Economic Savings Analysis")
            economic_savings = df_filtered.groupby(group_by_col)['Money Saved'].sum().reset_index()
            fig6_donut = px.pie(
                economic_savings,
                names=group_by_col, values='Money Saved',
                title=f'Contribution to Economic Savings by {group_by_col.replace("_", " ")}',
                hole=0.4,
                template="plotly_white"
            )
            st.plotly_chart(fig6_donut, use_container_width=True)

            
            # --- Chart 7: Investment vs. Savings Scatter Plot ---
            st.subheader("Investment vs. Financial Savings")
            financial_summary = df_filtered.groupby(group_by_col).agg(
                Total_Investment=('Investment', 'sum'),
                Total_Money_Saved=('Money Saved', 'sum')
            ).reset_index()
            fig7 = px.scatter(
                financial_summary,
                x='Total_Investment', y='Total_Money_Saved',
                text=group_by_col,
                size='Total_Investment',
                color=group_by_col,
                title=f'Investment vs. Money Saved per {group_by_col.replace("_", " ")}',
                labels={'Total_Investment': 'Total Investment (€)', 'Total_Money_Saved': 'Total Money Saved (€)'},
                template="plotly_white"
            )
            fig7.update_traces(textposition='top center')
            st.plotly_chart(fig7, use_container_width=True)
            
        # --- Chart 4: Investment Summary Table (at the bottom for more space) ---
        st.markdown("---")
        st.subheader("Investment Summary")
        summary_df = df_filtered.groupby(group_by_col).agg(
            Total_Investment=('Investment', 'sum'),
            Measure_Count=('Measure', 'count'),
            Total_Money_Saved=('Money Saved', 'sum')
        ).reset_index()
        summary_df['Average_Investment_per_Measure'] = summary_df.apply(
            lambda row: row['Total_Investment'] / row['Measure_Count'] if row['Measure_Count'] > 0 else 0, axis=1
        )
        st.dataframe(
            summary_df,
            use_container_width=True,
            column_config={
                "Total_Investment": st.column_config.NumberColumn("Total Investment (€)", format="€ %.2f"),
                "Measure_Count": "Number of Measures",
                "Total_Money_Saved": st.column_config.NumberColumn("Total Money Saved (€)", format="€ %.2f"),
                "Average_Investment_per_Measure": st.column_config.NumberColumn("Avg. Investment/Measure (€)", format="€ %.2f")
            },
            hide_index=True
        )

else:
    st.warning("Data could not be loaded. Please check the file path and try again.")
