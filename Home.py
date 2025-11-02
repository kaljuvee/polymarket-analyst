import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, timezone
import json

# Set page config
st.set_page_config(page_title="Polymarket Analyst", layout="wide")

# Title and description
st.title("Polymarket Market Analysis")
st.markdown("Analyze and visualize Polymarket prediction markets data")

# Function to fetch data
def fetch_market_data(params):
    try:
        response = requests.get("https://gamma-api.polymarket.com/markets", params=params)
        data = response.json()
        # Debug: Print first market object structure
        if data and len(data) > 0:
            print("First market object keys:", data[0].keys())
        return data
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

# Function to format category name
def format_category(category):
    if not category:
        return "Uncategorized"
    # Replace hyphens with spaces and capitalize words
    return category.replace('-', ' ').title()

# Function to process data into DataFrame
def process_market_data(data):
    if not data:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Debug: Print first market object structure
    if len(data) > 0:
        print("First market object structure:")
        print(json.dumps(data[0], indent=2))
    
    # Print column names for debugging
    print("Available columns:", df.columns.tolist())
    
    # Convert string lists to actual lists if they are strings
    if 'outcomes' in df.columns and isinstance(df['outcomes'].iloc[0], str):
        df['outcomes'] = df['outcomes'].apply(eval)
    if 'outcomePrices' in df.columns and isinstance(df['outcomePrices'].iloc[0], str):
        df['outcomePrices'] = df['outcomePrices'].apply(eval)
    
    # Convert numeric columns
    if 'volume' in df.columns:
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    if 'liquidity' in df.columns:
        df['liquidity'] = pd.to_numeric(df['liquidity'], errors='coerce')
    if 'volumeNum' in df.columns:
        df['volumeNum'] = pd.to_numeric(df['volumeNum'], errors='coerce')
    if 'liquidityNum' in df.columns:
        df['liquidityNum'] = pd.to_numeric(df['liquidityNum'], errors='coerce')
    
    # Convert dates to UTC timezone
    date_columns = ['endDate', 'createdAt', 'updatedAt', 'closedTime', 'startDate']
    for col in date_columns:
        if col in df.columns:
            try:
                # First convert to datetime
                df[col] = pd.to_datetime(df[col])
                # Check if already timezone-aware
                if df[col].dt.tz is None:
                    # If not timezone-aware, localize to UTC
                    df[col] = df[col].dt.tz_localize('UTC')
                else:
                    # If already timezone-aware, convert to UTC
                    df[col] = df[col].dt.tz_convert('UTC')
            except Exception as e:
                print(f"Warning: Could not process {col} column: {str(e)}")
                continue
    
    return df

# Function to get date range based on selection
def get_date_range(date_filter):
    today = datetime.now(timezone.utc)
    if date_filter == "Today":
        return today, today + timedelta(days=1)
    elif date_filter == "This Week":
        return today, today + timedelta(days=7)
    elif date_filter == "Later than One Week":
        return today + timedelta(days=7), today + timedelta(days=365)
    else:  # All Time
        return None, None

# Sidebar for controls
st.sidebar.header("Controls")

# Fetch button
if st.sidebar.button("Fetch Latest Data"):
    # Build parameters based on sidebar filters
    params = {
        'limit': '100'
    }
    
    # Add filters from session state if they exist
    if 'active_filter' in st.session_state:
        params['active'] = str(st.session_state['active_filter']).lower()
    if 'closed_filter' in st.session_state:
        params['closed'] = str(st.session_state['closed_filter']).lower()
    if 'archived_filter' in st.session_state:
        params['archived'] = str(st.session_state['archived_filter']).lower()
    
    with st.spinner("Fetching data..."):
        data = fetch_market_data(params)
        if data:
            st.success(f"Data fetched successfully! Retrieved {len(data)} markets.")
            # Store raw data in session state for debugging
            st.session_state['raw_data'] = data
            df = process_market_data(data)
            # Store in session state
            st.session_state['df'] = df
        else:
            st.error("Failed to fetch data")

# Main content area
if 'df' in st.session_state:
    df = st.session_state['df']
    
    # Filters
    st.sidebar.subheader("Filters")
    
    # Date filter - DEFAULT TO "All Time" (index=3)
    date_options = ["Today", "This Week", "Later than One Week", "All Time"]
    selected_date = st.sidebar.selectbox("Select Time Range", date_options, index=3)
    
    # Active/Closed/Archived filters
    st.sidebar.markdown("**Market Status**")
    active_filter = st.sidebar.checkbox("Active Markets", value=True, key='active_filter')
    closed_filter = st.sidebar.checkbox("Closed Markets", value=False, key='closed_filter')
    archived_filter = st.sidebar.checkbox("Archived Markets", value=False, key='archived_filter')
    
    # Volume range filter
    if 'volumeNum' in df.columns:
        min_volume = float(df['volumeNum'].min()) if df['volumeNum'].notna().any() else 0.0
        max_volume = float(df['volumeNum'].max()) if df['volumeNum'].notna().any() else 1000000.0
        volume_range = st.sidebar.slider(
            "Volume Range ($)",
            min_value=min_volume,
            max_value=max_volume,
            value=(min_volume, max_volume),
            format="$%.0f"
        )
    elif 'volume' in df.columns:
        min_volume = float(df['volume'].min()) if df['volume'].notna().any() else 0.0
        max_volume = float(df['volume'].max()) if df['volume'].notna().any() else 1000000.0
        volume_range = st.sidebar.slider(
            "Volume Range ($)",
            min_value=min_volume,
            max_value=max_volume,
            value=(min_volume, max_volume),
            format="$%.0f"
        )
    else:
        volume_range = None
    
    # Liquidity range filter
    if 'liquidityNum' in df.columns:
        min_liquidity = float(df['liquidityNum'].min()) if df['liquidityNum'].notna().any() else 0.0
        max_liquidity = float(df['liquidityNum'].max()) if df['liquidityNum'].notna().any() else 1000000.0
        liquidity_range = st.sidebar.slider(
            "Liquidity Range ($)",
            min_value=min_liquidity,
            max_value=max_liquidity,
            value=(min_liquidity, max_liquidity),
            format="$%.0f"
        )
    elif 'liquidity' in df.columns:
        min_liquidity = float(df['liquidity'].min()) if df['liquidity'].notna().any() else 0.0
        max_liquidity = float(df['liquidity'].max()) if df['liquidity'].notna().any() else 1000000.0
        liquidity_range = st.sidebar.slider(
            "Liquidity Range ($)",
            min_value=min_liquidity,
            max_value=max_liquidity,
            value=(min_liquidity, max_liquidity),
            format="$%.0f"
        )
    else:
        liquidity_range = None
    
    # Category filter
    if 'category' in df.columns:
        categories = ['All'] + sorted(df['category'].dropna().unique().tolist())
        selected_category = st.sidebar.selectbox("Category", categories)
    else:
        selected_category = None
    
    # Apply filters
    filtered_df = df.copy()
    
    # Apply date filter
    if 'endDate' in df.columns:
        start_date, end_date = get_date_range(selected_date)
        if start_date and end_date:
            filtered_df = filtered_df[
                (filtered_df['endDate'] >= start_date) &
                (filtered_df['endDate'] <= end_date)
            ]
    
    # Apply status filters
    if 'active' in filtered_df.columns:
        if active_filter and not closed_filter:
            filtered_df = filtered_df[filtered_df['active'] == True]
        elif closed_filter and not active_filter:
            filtered_df = filtered_df[filtered_df['active'] == False]
    
    if 'closed' in filtered_df.columns and closed_filter:
        filtered_df = filtered_df[filtered_df['closed'] == True]
    
    if 'archived' in filtered_df.columns and not archived_filter:
        filtered_df = filtered_df[filtered_df['archived'] == False]
    
    # Apply volume filter
    if volume_range:
        if 'volumeNum' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['volumeNum'] >= volume_range[0]) &
                (filtered_df['volumeNum'] <= volume_range[1])
            ]
        elif 'volume' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['volume'] >= volume_range[0]) &
                (filtered_df['volume'] <= volume_range[1])
            ]
    
    # Apply liquidity filter
    if liquidity_range:
        if 'liquidityNum' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['liquidityNum'] >= liquidity_range[0]) &
                (filtered_df['liquidityNum'] <= liquidity_range[1])
            ]
        elif 'liquidity' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['liquidity'] >= liquidity_range[0]) &
                (filtered_df['liquidity'] <= liquidity_range[1])
            ]
    
    # Apply category filter
    if selected_category and selected_category != 'All' and 'category' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Markets", len(filtered_df))
    with col2:
        if 'volumeNum' in filtered_df.columns:
            st.metric("Total Volume", f"${filtered_df['volumeNum'].sum():,.2f}")
        elif 'volume' in filtered_df.columns:
            st.metric("Total Volume", f"${filtered_df['volume'].sum():,.2f}")
    with col3:
        if 'liquidityNum' in filtered_df.columns:
            st.metric("Average Liquidity", f"${filtered_df['liquidityNum'].mean():,.2f}")
        elif 'liquidity' in filtered_df.columns:
            st.metric("Average Liquidity", f"${filtered_df['liquidity'].mean():,.2f}")
    with col4:
        if 'active' in filtered_df.columns:
            active_count = filtered_df['active'].sum()
            st.metric("Active Markets", int(active_count))
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Market Details", "🔍 Raw JSON Data", "📈 Debug Info"])
    
    with tab1:
        st.subheader("Market Details")
        
        # Select columns to display
        display_columns = ['question', 'volumeNum', 'liquidityNum', 'endDate', 'active', 'category']
        # Fallback to old column names if new ones don't exist
        if 'volumeNum' not in filtered_df.columns and 'volume' in filtered_df.columns:
            display_columns = ['question', 'volume', 'liquidity', 'endDate', 'active', 'category']
        
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        
        # Format the dataframe for display
        display_df = filtered_df[available_columns].copy()
        
        # Sort by volume
        sort_col = 'volumeNum' if 'volumeNum' in display_df.columns else 'volume' if 'volume' in display_df.columns else 'endDate'
        
        # Configure column display
        column_config = {
            "question": st.column_config.TextColumn("Question", width="large"),
            "endDate": st.column_config.DatetimeColumn("End Date", format="YYYY-MM-DD HH:mm"),
            "active": st.column_config.CheckboxColumn("Active"),
            "category": st.column_config.TextColumn("Category")
        }
        
        if 'volumeNum' in display_df.columns:
            column_config["volumeNum"] = st.column_config.NumberColumn("Volume", format="$%.2f")
        if 'liquidityNum' in display_df.columns:
            column_config["liquidityNum"] = st.column_config.NumberColumn("Liquidity", format="$%.2f")
        if 'volume' in display_df.columns:
            column_config["volume"] = st.column_config.NumberColumn("Volume", format="$%.2f")
        if 'liquidity' in display_df.columns:
            column_config["liquidity"] = st.column_config.NumberColumn("Liquidity", format="$%.2f")
        
        # Sort and display the dataframe
        st.dataframe(
            display_df.sort_values(sort_col, ascending=False),
            use_container_width=True,
            column_config=column_config
        )
    
    with tab2:
        st.subheader("Raw JSON Data as DataFrame")
        
        if 'raw_data' in st.session_state:
            # Convert raw JSON to DataFrame for better viewing
            raw_df = pd.json_normalize(st.session_state['raw_data'])
            
            st.write(f"**Total records:** {len(raw_df)}")
            
            # Allow column selection
            all_columns = raw_df.columns.tolist()
            selected_columns = st.multiselect(
                "Select columns to display",
                all_columns,
                default=all_columns[:10] if len(all_columns) > 10 else all_columns
            )
            
            if selected_columns:
                st.dataframe(raw_df[selected_columns], use_container_width=True)
            else:
                st.info("Please select at least one column to display")
            
            # Download button for raw JSON
            st.download_button(
                label="Download Raw JSON",
                data=json.dumps(st.session_state['raw_data'], indent=2),
                file_name="polymarket_data.json",
                mime="application/json"
            )
            
            # Download button for CSV
            csv = raw_df.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name="polymarket_data.csv",
                mime="text/csv"
            )
        else:
            st.info("No raw data available. Click 'Fetch Latest Data' to load data.")
    
    with tab3:
        st.subheader("Debug Information")
        
        with st.expander("DataFrame Info"):
            st.write("**DataFrame Shape:**", df.shape)
            st.write("**Available Columns:**")
            st.write(df.columns.tolist())
            
            # Display data types
            st.write("**Column Data Types:**")
            st.dataframe(pd.DataFrame({
                'Column': df.dtypes.index,
                'Type': df.dtypes.values.astype(str)
            }))
        
        with st.expander("Sample Raw Data"):
            if 'raw_data' in st.session_state:
                st.json(st.session_state['raw_data'][:2])  # Show first two items
        
        with st.expander("Filtered Data Statistics"):
            st.write("**Filtered DataFrame Shape:**", filtered_df.shape)
            st.write(filtered_df.describe())

else:
    st.info("👈 Click 'Fetch Latest Data' in the sidebar to load market data")
    
    st.markdown("""
    ### Features:
    - 📊 View market details with volume, liquidity, and end dates
    - 🔍 Explore raw JSON data as DataFrame
    - 🎯 Filter by time range, volume, liquidity, and category
    - 📈 Toggle between active, closed, and archived markets
    - 💾 Download data as JSON or CSV
    
    ### Getting Started:
    1. Click **"Fetch Latest Data"** in the sidebar
    2. Adjust filters to narrow down markets
    3. Explore different tabs for various data views
    """)
