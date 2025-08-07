#######################
# Import libraries
import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt

#######################
# Page configuration
st.set_page_config(
    page_title="Asepeyo Energy Efficiency Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set Altair theme to light for better contrast
alt.themes.enable("default")

#######################
# Load and process data
@st.cache_data
def load_data(file_path):
    """Loads and processes the energy audit data."""
    try:
        df = pd.read_csv(file_path)
        # Clean column names
        df.columns = df.columns.str.strip()
        # Convert numeric columns, filling errors with 0
        for col in ['Energy Saved', 'Money Saved', 'Investment', 'Pay back period']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.fillna(0, inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Error: The file '{file_path}' was not found. Please make sure the file is in the correct directory.")
        return pd.DataFrame() # Return empty DataFrame on error

# Provide the correct path to your CSV file
df = load_data('2025 Energy Audit summary - Sheet1 (1).csv')

if not df.empty:

    #######################
    # Sidebar Filters with Dependent Dropdowns
    with st.sidebar:
        st.title('⚡ Asepeyo Energy Dashboard')
        
        # 1. Filter by Autonomous Community
        community_list = ['All'] + sorted(df['Comunidad Autónoma'].unique().tolist())
        selected_community = st.selectbox('Select a Community', community_list)

        # Initialize df_filtered with community selection
        if selected_community == 'All':
            df_filtered = df
            selected_center = 'All' # No center selection if all communities are shown
        else:
            df_filtered = df[df['Comunidad Autónoma'] == selected_community]
            
            # 2. Dependent Filter for Center
            center_list = ['All'] + sorted(df_filtered['Center'].unique().tolist())
            selected_center = st.selectbox('Select a Center', center_list)

            # Further filter by center if a specific one is chosen
            if selected_center != 'All':
                df_filtered = df_filtered[df_filtered['Center'] == selected_center]


    #######################
    # Main Panel with Dynamic Title
    st.title("Energy Efficiency Analysis")
    # Create a dynamic subheader
    if selected_community == 'All':
        st.header("Showing data for All Communities")
    elif selected_center == 'All':
        st.header(f"Showing all centers in: {selected_community}")
    else:
        st.header(f"Showing data for: {selected_center}")


    # --- Key Performance Indicators (KPIs) ---
    total_investment = df_filtered['Investment'].sum()
    total_money_saved = df_filtered['Money Saved'].sum()
    total_energy_saved = df_filtered['Energy Saved'].sum()
    
    # Avoid division by zero for ROI calculation
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
    col1, col2 = st.columns(2, gap="large")

    with col1:
        # --- Chart 1: Measures required per community/center ---
        st.subheader("Measure Counts")
        if selected_community == 'All':
            # Group by community if 'All' is selected
            measures_count = df.groupby('Comunidad Autónoma')['Measure'].count().reset_index().rename(columns={'Measure': 'Count'})
            fig1 = px.bar(
                measures_count.sort_values('Count', ascending=False),
                x='Comunidad Autónoma', y='Count', title='Measures per Community',
                labels={'Count': 'Number of Measures', 'Comunidad Autónoma': 'Community'},
                template="plotly_white"
            )
        else:
            # Group by center if a community is selected
            measures_count = df_filtered.groupby('Center')['Measure'].count().reset_index().rename(columns={'Measure': 'Count'})
            fig1 = px.bar(
                measures_count.sort_values('Count', ascending=False),
                x='Center', y='Count', title=f'Measures per Center in {selected_community}',
                labels={'Count': 'Number of Measures'},
                template="plotly_white"
            )
        st.plotly_chart(fig1, use_container_width=True)

        
        # --- Chart 5: Energy Savings per community/center ---
        st.subheader("Energy Savings Analysis")
        # Adapt grouping based on selection
        group_by_col = 'Center' if selected_community != 'All' else 'Comunidad Autónoma'
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
        group_by_col = 'Center' if selected_community != 'All' else 'Comunidad Autónoma'
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
        group_by_col = 'Center' if selected_community != 'All' else 'Comunidad Autónoma'
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
    group_by_col = 'Center' if selected_community != 'All' else 'Comunidad Autónoma'
    regional_investment_summary = df_filtered.groupby(group_by_col).agg(
        Total_Investment=('Investment', 'sum'),
        Measure_Count=('Measure', 'count')
    ).reset_index()
    regional_investment_summary['Average_Investment_per_Measure'] = regional_investment_summary.apply(
        lambda row: row['Total_Investment'] / row['Measure_Count'] if row['Measure_Count'] > 0 else 0, axis=1
    )
    st.dataframe(
        regional_investment_summary,
        use_container_width=True,
        column_config={
            "Total_Investment": st.column_config.NumberColumn("Total Investment (€)", format="€ %.2f"),
            "Measure_Count": "Number of Measures",
            "Average_Investment_per_Measure": st.column_config.NumberColumn("Avg. Investment/Measure (€)", format="€ %.2f")
        },
        hide_index=True
    )


else:
    st.warning("Data could not be loaded. Please check the file path and try again.")

