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
def fetch_market_data():
    try:
        params = {
            'active': 'true',
            'closed': 'false',
            'archived': 'false',
            'limit': '100'
        }
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
    
    # Convert dates to UTC timezone
    date_columns = ['endDate', 'createdAt', 'updatedAt', 'closedTime']
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
    with st.spinner("Fetching data..."):
        data = fetch_market_data()
        if data:
            st.success("Data fetched successfully!")
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
    
    # Debug expander
    with st.expander("Debug: Raw Data Sample"):
        if 'raw_data' in st.session_state:
            st.json(st.session_state['raw_data'][:2])  # Show first two items
        st.write("DataFrame Info:")
        st.write(df.info())
        st.write("\nDataFrame Columns:")
        st.write(df.columns.tolist())
    
    # Filters
    st.sidebar.subheader("Filters")
    
    # Date filter
    date_options = ["Today", "This Week", "Later than One Week", "All Time"]
    selected_date = st.sidebar.selectbox("Select Time Range", date_options, index=0)
    
    # Volume range filter
    if 'volume' in df.columns:
        min_volume = float(df['volume'].min())
        max_volume = float(df['volume'].max())
        volume_range = st.sidebar.slider(
            "Volume Range",
            min_value=min_volume,
            max_value=max_volume,
            value=(min_volume, max_volume)
        )
    
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
    
    # Apply volume filter
    if 'volume' in df.columns:
        filtered_df = filtered_df[
            (filtered_df['volume'] >= volume_range[0]) &
            (filtered_df['volume'] <= volume_range[1])
        ]
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Markets", len(filtered_df))
    with col2:
        if 'volume' in filtered_df.columns:
            st.metric("Total Volume", f"${filtered_df['volume'].sum():,.2f}")
    with col3:
        if 'liquidity' in filtered_df.columns:
            st.metric("Average Liquidity", f"${filtered_df['liquidity'].mean():,.2f}")
    
    # Data Table
    st.subheader("Market Details")
    display_columns = ['question', 'volume', 'liquidity', 'endDate', 'active']
    available_columns = [col for col in display_columns if col in filtered_df.columns]
    
    # Format the dataframe for display
    display_df = filtered_df[available_columns].copy()
    
    # Sort and display the dataframe
    st.dataframe(
        display_df[available_columns].sort_values('volume' if 'volume' in display_df.columns else 'endDate', ascending=False),
        use_container_width=True,
        column_config={
            "question": st.column_config.TextColumn("Question", width="large"),
            "volume": st.column_config.NumberColumn("Volume", format="$%.2f"),
            "liquidity": st.column_config.NumberColumn("Liquidity", format="$%.2f"),
            "endDate": st.column_config.DatetimeColumn("End Date", format="YYYY-MM-DD HH:mm"),
            "active": st.column_config.CheckboxColumn("Active")
        }
    )
else:
    st.info("Click 'Fetch Latest Data' to load market data")