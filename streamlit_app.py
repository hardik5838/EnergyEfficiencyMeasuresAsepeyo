import streamlit as st
import pandas as pd

# This is the URL to the raw CSV file on GitHub.
# You will need to replace 'YOUR_USERNAME', 'YOUR_REPO_NAME', and 'YOUR_BRANCH'
# with your actual GitHub details.
csv_url = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO_NAME/YOUR_BRANCH/data/2025 Energy Audit summary.xlsx - Sheet1.csv"

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

# --- Future Development Ideas ---
st.markdown("---")
st.markdown("### Future Functionality")
st.markdown("""
- **Comparison Tab**: A new tab or page to compare data from different years. This can be implemented by adding more Excel files for different years and creating new functions to load and compare them.
- **Interactive Charts**: Add visualizations like bar charts to compare `Energy Saved` or `Money Saved` by `Center` or `Measure`.
- **Filtering Options**: Allow users to filter the data by `Center` or `Measure` using Streamlit widgets like `st.selectbox`.
""")
