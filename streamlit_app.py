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
    # --- Sidebar and Data Processing ---

# 1. Define all sidebar widgets to get user input
with st.sidebar:
    st.title('⚡ Asepeyo Filters')
    
    analysis_type = st.radio(
        "Select Analysis Type",
        ('Tipo de Medida', 'Tipo de Intervención', 'Impacto Financiero', 'Función de Negocio'),
        key='analysis_type'
    )

    st.markdown("---")
    
    # The community and center filters will be dependent on the categorized data
    # We will define them after processing
    
# 2. Define the categorization functions
def categorize_by_tipo(df_in):
    """Categorizes by the original measure types."""
    measure_map = {
        'Regulación de la temperatura de consigna': 'Control térmico',
        'Sustitución de equipos de climatización': 'Control térmico',
        'Instalación de cortina de aire': 'Control térmico',
        'Instalación de temporizador digital': 'Control térmico',
        'Aislamiento de tuberías': 'Control térmico',
        'Recuperadores de calor': 'Control térmico',
        'Optimización de la potencia contratada': 'Gestión energética',
        'Implementación de un sistema de gestión': 'Gestión energética',
        'Compensación del consumo de energía reactiva': 'Gestión energética',
        'Reducción del consumo remanente': 'Gestión energética',
        'Buenas prácticas': 'Gestión energética',
        'Batería de condensadores': 'Gestión energética',
        'Instalación solar fotovoltaica': 'Gestión energética',
        'Sustitución de luminarias a LED': 'Iluminación eficiente',
        'Instalación de regletas programables': 'Iluminación eficiente',
        'Mejora en el control': 'Iluminación eficiente'
    }
    def get_type(measure):
        for key, value in measure_map.items():
            if key.lower() in measure.lower(): return value
        return 'Other'
    df_in['Category'] = df_in['Measure'].apply(get_type)
    return df_in

def categorize_by_intervention(df_in):
    """Categorizes by the type of work required."""
    def get_type(measure):
        measure = measure.lower()
        if any(word in measure for word in ["instalación", "batería", "recuperadores", "solar"]):
            return 'New System Installation'
        elif any(word in measure for word in ["sustitución", "cambio", "mejora", "aislamiento"]):
            return 'Equipment Retrofit & Upgrade'
        elif any(word in measure for word in ["prácticas", "regulación", "optimización", "reducción"]):
            return 'Operational & Behavioral'
        return 'Other'
    df_in['Category'] = df_in['Measure'].apply(get_type)
    return df_in

def categorize_by_financials(df_in):
    """Categorizes by the payback period."""
    def get_type(payback):
        if payback <= 0: return 'No Cost / Immediate'
        if payback < 2: return 'Quick Wins (< 2 years)'
        if payback <= 5: return 'Standard Projects (2-5 years)'
        return 'Strategic Investments (> 5 years)'
    df_in['Category'] = df_in['Pay back period'].apply(get_type)
    return df_in

def categorize_by_function(df_in):
    """Categorizes by the relevant business function."""
    def get_type(measure):
        measure = measure.lower()
        if any(word in measure for word in ["hvac", "climatización", "temperatura", "ventilación", "aislamiento", "cortina", "calor"]):
            return 'Building Envelope & HVAC'
        if any(word in measure for word in ["led", "iluminación", "luminarias", "eléctrico", "potencia", "reactiva", "condensadores", "regletas"]):
            return 'Lighting & Electrical'
        if any(word in measure for word in ["gestión", "fotovoltaica", "solar", "prácticas", "remanente"]):
            return 'Energy Management & Strategy'
        return 'Other'
    df_in['Category'] = df_in['Measure'].apply(get_type)
    return df_in

# 3. Apply the selected categorization based on the radio button input
if analysis_type == 'Tipo de Intervención':
    df_categorized = categorize_by_intervention(df.copy())
elif analysis_type == 'Impacto Financiero':
    df_categorized = categorize_by_financials(df.copy())
elif analysis_type == 'Función de Negocio':
    df_categorized = categorize_by_function(df.copy())
else:  # Default to 'Tipo de Medida'
    df_categorized = categorize_by_tipo(df.copy())

# 4. NOW, define the rest of the sidebar filters using the categorized data
with st.sidebar:
    community_list = ['All'] + sorted(df_categorized['Comunidad Autónoma'].unique().tolist())
    selected_community = st.selectbox('Select a Community', community_list)

    if selected_community == 'All':
        df_filtered = df_categorized
        selected_centers = [] # No centers to select if 'All' communities
    else:
        df_community_filtered = df_categorized[df_categorized['Comunidad Autónoma'] == selected_community]
        center_list = sorted(df_community_filtered['Center'].unique().tolist())
        selected_centers = st.multiselect(
            'Select Centers to Compare',
            center_list,
            default=center_list
        )
        if selected_centers:
            df_filtered = df_community_filtered[df_community_filtered['Center'].isin(selected_centers)]
        else:
            df_filtered = pd.DataFrame(columns=df_categorized.columns)
    
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
            # --- Chart 1: Dynamic Measure Counts (Stacked by Selected Type) ---
            st.subheader(f"Measure Counts by {analysis_type}")
            group_by_col = 'Center' if selected_community != 'All' else 'Comunidad Autónoma'

            # Group by the primary column AND the new dynamic 'Category' column
            if 'Category' in df_filtered.columns:
                measures_by_type = df_filtered.groupby([group_by_col, 'Category']).size().reset_index(
                    name='Count')

                fig1 = px.bar(
                    measures_by_type,
                    x=group_by_col,
                    y='Count',
                    color='Category',  # This now correctly uses the dynamic category
                    title=f'Measure Types per {group_by_col.replace("_", " ")}',
                    template="plotly_white"
                )

                # Improve layout for better readability
                fig1.update_layout(
                    xaxis_title=group_by_col.replace("_", " ").title(),
                    yaxis_title="Number of Measures",
                    legend_title=analysis_type  # The legend title is also dynamic
                )
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.warning("Could not generate chart. 'Category' column not found.")
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
                "Average_Investment_per_Measure": st.column_config.NumberColumn("Avg. Investment/Measure (€)",
                                                                                format="€ %.2f")
            },
            hide_index=True
        )

else:
    st.warning("Data could not be loaded. Please check the file path and try again.")


