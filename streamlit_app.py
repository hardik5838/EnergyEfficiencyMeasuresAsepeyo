import streamlit as st
import pandas as pd
import altair as alt

# This is the URL to the raw CSV file on GitHub.
# You will need to replace 'YOUR_USERNAME', 'YOUR_REPO_NAME', and 'YOUR_BRANCH'
# with your actual GitHub details.
csv_url = "https://raw.githubusercontent.com/hardik5838/EnergyEfficiencyMeasuresAsepeyo/refs/heads/main/Data/2025%20Energy%20Audit%20summary%20-%20Sheet1.csv"

# Function to load and clean the data
def load_data(url):
    """
    Loads the CSV data from a URL and cleans the column names.
    """
    try:
        # Read the CSV from the GitHub URL. The 'header=1' parameter is used
        # because the first row seems to be an empty row, with the headers
        # starting from the second row (index 1).
        df = pd.read_csv(url, header=1)
        
        # Drop the unnamed columns that appear in the raw data
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Clean up column names by stripping leading/trailing whitespace
        df.columns = [col.strip() for col in df.columns]
        
        # Fill the 'Center' and 'Measure' columns' NaN values by using the previous valid value
        df['Center'] = df['Center'].ffill()
        df['Measure'] = df['Measure'].ffill()
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame() # Return an empty DataFrame on error

# Set up the Streamlit app layout
st.set_page_config(
    page_title="2025 Energy Audit Summary",
    layout="wide"
)

st.title("Energy Audit Summary for 2025")

# Load the data
df_audit = load_data(csv_url)

# Check if the data was loaded successfully and display it
if not df_audit.empty:
    st.markdown("### Raw Data from the 2025 Energy Audit")
    st.dataframe(df_audit, use_container_width=True)
else:
    st.warning("Could not load the energy audit data. Please check the GitHub URL and file path.")



# Check if the data was loaded successfully and display a warning if not.
if df_audit.empty:
    st.warning("Could not load the energy audit data. Please check the GitHub URL and file path.")
else:
    # --- Tab 1: Executive Summary & Command Center ---
    st.header("Executive Summary & Command Center")
    st.markdown("### National Impact KPIs")

    # Chart 1.1: National Impact KPIs
    # Map the user's requested names to the actual column names
    col_money_saved = 'Money Saved'
    col_investment = 'Investment'
    col_energy_saved = 'Energy Saved'
    col_center = 'Center'
    
    # Calculate the KPIs
    total_savings = df_audit[col_money_saved].sum()
    total_investment = df_audit[col_investment].sum()
    
    # Handle the case of zero total savings to avoid division by zero
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

    # Chart 1.2: The "Cost of Inaction" Counter
    st.markdown("### The 'Cost of Inaction' Counter")
    
    # Filter for measures with zero investment
    zero_cost_measures = df_audit[df_audit[col_investment] == 0]
    
    # Calculate daily cost of delay
    daily_cost_of_delay = zero_cost_measures[col_money_saved].sum() / 365
    
    st.markdown(
        f"""
        <div style="background-color: #F8D7DA; padding: 20px; border-radius: 5px; text-align: center;">
            <h5 style="color: #DC3545; font-size: 20px;">Daily Cost of Delay</h5>
            <h1 style="color: #DC3545; font-size: 48px; margin-top: -10px;">€{daily_cost_of_delay:,.2f}</h1>
            <p style="color: #DC3545;">Economic savings lost each day by not implementing zero-cost measures.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("---")

    # Chart 1.3: Regional Efficiency Scorecard
    st.markdown("### Regional Efficiency Scorecard")

    # Group the data by region (using the 'Center' column as requested)
    regional_data = df_audit.groupby(col_center).agg(
        total_investment=(col_investment, 'sum'),
        total_savings=(col_money_saved, 'sum')
    ).reset_index()

    # Calculate the weighted average payback
    regional_data['avg_payback'] = regional_data['total_investment'] / regional_data['total_savings']
    
    # Sort the table by payback period
    regional_data = regional_data.sort_values('avg_payback').reset_index(drop=True)
    
    # Define the styling function for the payback column
    def color_payback_cells(val):
        color = ''
        if val < 2.0:
            color = '#D4EDDA'
        elif 2.0 <= val < 4.0:
            color = '#FFF3CD'
        else:
            color = '#F8D7DA'
        return f'background-color: {color}'
        
    # Apply the styling to the DataFrame and rename columns for display
    styled_df = regional_data.style.applymap(
        color_payback_cells, subset=['avg_payback']
    ).set_properties(
        **{'background-color': '#F8F9FA'}, 
        subset=pd.IndexSlice[regional_data.index, :]
    ).format(
        {'total_investment': "€{:,.0f}", 'total_savings': "€{:,.0f}", 'avg_payback': "{:.1f}"}
    ).hide(axis="index") # Hide the default index

    # Display the styled table with renamed columns
    st.dataframe(
        styled_df,
        column_order=('Comunidad Autónoma', 'Total Investment (€)', 'Annual Savings (€)', 'Average Payback (Years)'),
        column_config={
            'Comunidad Autónoma': st.column_config.TextColumn("Comunidad Autónoma", help="Region Name"),
            'Total Investment (€)': st.column_config.NumberColumn("Total Investment (€)", help="Total Investment in Euros"),
            'Annual Savings (€)': st.column_config.NumberColumn("Annual Savings (€)", help="Total Annual Savings in Euros"),
            'Average Payback (Years)': st.column_config.NumberColumn("Average Payback (Years)", help="Average Payback Period in Years")
        },
        use_container_width=True
    )

    st.markdown("---")

    # Chart 1.4: Economic & Energy Savings by Region
    st.markdown("### Economic & Energy Savings by Region")

    # Create two columns for the side-by-side charts
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Chart A: Economic Savings by Region
        economic_chart_data = regional_data[[col_center, 'total_savings']].rename(
            columns={col_center: 'Comunidad', 'total_savings': 'Total Savings'}
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
        # Chart B: Energy Savings by Region
        energy_data = df_audit.groupby(col_center)[col_energy_saved].sum().reset_index()
        energy_chart_data = energy_data.rename(
            columns={col_center: 'Comunidad', col_energy_saved: 'Total Savings'}
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




# --- Future Development Ideas ---
st.markdown("---")
st.markdown("### Future Functionality")
st.markdown("""
- **Comparison Tab**: A new tab or page to compare data from different years. This can be implemented by adding more Excel files for different years and creating new functions to load and compare them.
- **Interactive Charts**: Add visualizations like bar charts to compare `Energy Saved` or `Money Saved` by `Center` or `Measure`.
- **Filtering Options**: Allow users to filter the data by `Center` or `Measure` using Streamlit widgets like `st.selectbox`.
""")
