import time
import requests
import streamlit as st
import pandas as pd
import plotly.express as px

# Function to fetch data from CoinGecko API with caching for performance
@st.cache_data(ttl=600)  # Cache data for 10 minutes (600 seconds)
def fetch_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 50,  # Limit to top 50 coins for better performance
        "page": 1,
        "sparkline": "true"  # Requesting price trends over the last 7 days
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        elif response.status_code == 429:
            st.warning("Rate limit exceeded. Retrying in 10 seconds...")
            time.sleep(10)  # Wait before retrying
            return fetch_crypto_data()  # Retry fetching the data
        elif response.status_code == 401:
            st.error("Unauthorized request: Please check API key (if applicable).")
        else:
            st.error(f"Failed to fetch data. Status code: {response.status_code}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Function to fetch price data for different time periods with proper error handling
def fetch_historical_data(coin_id, days):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "minute" if days == "1" else "daily"  # Minute interval for 1 day, daily for longer periods
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            st.warning("Rate limit exceeded. Retrying in 10 seconds...")
            time.sleep(10)  # Wait before retrying
            return fetch_historical_data(coin_id, days)  # Retry fetching the data
        elif response.status_code == 401:
            st.error("Unauthorized request: Please check API key (if applicable).")
        else:
            st.error(f"Failed to fetch historical data. Status code: {response.status_code}")
        return {}
    except Exception as e:
        st.error(f"Error fetching historical data: {e}")
        return {}

# Streamlit app title
st.title("📊 Cryptocurrency Dashboard")
st.write("Track real-time prices and price trends over different time periods.")

# Sidebar for filtering options
st.sidebar.header("🔍 Filter Options")
coin_name = st.sidebar.text_input("Enter Coin Name (e.g., Bitcoin, Ethereum)").strip()
st.sidebar.write("Data updates every **10 minutes**. Select a coin to explore.")

# Fetch data (cached for 10 minutes)
df = fetch_crypto_data()

# Filter data based on user input
if coin_name:
    filtered_df = df[df["name"].str.contains(coin_name, case=False)]
else:
    filtered_df = df

# Check if multiple coins with the same name exist
if len(filtered_df) > 1:
    st.write(f"Multiple coins found with the name '{coin_name}':")
    # Show a selection of coins with more details (coin ID, symbol)
    coin_options = filtered_df[['id', 'name', 'symbol']].reset_index(drop=True)
    selected_coin = st.selectbox("Select a Coin", options=coin_options.to_dict(orient='records'), format_func=lambda x: f"{x['name']} ({x['symbol']})")

    # Get the selected coin from the options
    selected_coin_id = selected_coin['id']
    filtered_df = df[df['id'] == selected_coin_id]
elif len(filtered_df) == 1:
    selected_coin = filtered_df.iloc[0]
else:
    st.write("No coins found with the name. Please try again.")

# Display real-time price for the selected coin
if not filtered_df.empty:
    st.subheader("Real-Time Price")
    st.write(f"**{filtered_df.iloc[0]['name']}**: ${filtered_df.iloc[0]['current_price']:,}")

# Display data table without market cap (check if required columns exist)
if 'name' in filtered_df.columns and 'current_price' in filtered_df.columns and 'total_volume' in filtered_df.columns:
    st.subheader("Top Cryptocurrencies")
    st.dataframe(filtered_df[["name", "current_price", "total_volume"]])
else:
    st.warning("Some columns are missing. Data may not be fully loaded.")

# Display price trend for each time period directly on the page
if len(filtered_df) == 1:
    coin_id = filtered_df.iloc[0]['id']
    
    # Current Trend
    st.subheader(f"📊 {filtered_df.iloc[0]['name']} Current Price Trend")
    st.write(f"**{filtered_df.iloc[0]['name']}**: ${filtered_df.iloc[0]['current_price']:,}")
    
    # 1 Hour Trend
    st.subheader("📊 1 Hour Price Trend")
    sparkline_data = filtered_df.iloc[0]["sparkline_in_7d"]["price"]
    fig = px.line(x=list(range(len(sparkline_data))), y=sparkline_data, labels={"x": "Minutes", "y": "Price ($)"}, title="Price Trend Over the Last Hour")
    st.plotly_chart(fig)
    
    # 24 Hours Trend
    st.subheader("📊 24 Hours Price Trend")
    historical_data_24h = fetch_historical_data(coin_id, "1")
    if historical_data_24h:
        price_data = historical_data_24h["prices"]
        x_values = [x[0] for x in price_data]
        y_values = [x[1] for x in price_data]
        fig = px.line(x=x_values, y=y_values, labels={"x": "Date", "y": "Price ($)"}, title="Price Trend Over the Last 24 Hours")
        st.plotly_chart(fig)
    
    # 1 Week Trend
    st.subheader("📊 1 Week Price Trend")
    historical_data_1w = fetch_historical_data(coin_id, "7")
    if historical_data_1w:
        price_data = historical_data_1w["prices"]
        x_values = [x[0] for x in price_data]
        y_values = [x[1] for x in price_data]
        fig = px.line(x=x_values, y=y_values, labels={"x": "Date", "y": "Price ($)"}, title="Price Trend Over the Last 1 Week")
        st.plotly_chart(fig)

    # 1 Month Trend
    st.subheader("📊 1 Month Price Trend")
    historical_data_1m = fetch_historical_data(coin_id, "30")
    if historical_data_1m:
        price_data = historical_data_1m["prices"]
        x_values = [x[0] for x in price_data]
        y_values = [x[1] for x in price_data]
        fig = px.line(x=x_values, y=y_values, labels={"x": "Date", "y": "Price ($)"}, title="Price Trend Over the Last 1 Month")
        st.plotly_chart(fig)

    # 6 Months Trend
    st.subheader("📊 6 Months Price Trend")
    historical_data_6m = fetch_historical_data(coin_id, "180")
    if historical_data_6m:
        price_data = historical_data_6m["prices"]
        x_values = [x[0] for x in price_data]
        y_values = [x[1] for x in price_data]
        fig = px.line(x=x_values, y=y_values, labels={"x": "Date", "y": "Price ($)"}, title="Price Trend Over the Last 6 Months")
        st.plotly_chart(fig)

    # 1 Year Trend
    st.subheader("📊 1 Year Price Trend")
    historical_data_1y = fetch_historical_data(coin_id, "365")
    if historical_data_1y:
        price_data = historical_data_1y["prices"]
        x_values = [x[0] for x in price_data]
        y_values = [x[1] for x in price_data]
        fig = px.line(x=x_values, y=y_values, labels={"x": "Date", "y": "Price ($)"}, title="Price Trend Over the Last 1 Year")
        st.plotly_chart(fig)

st.success("🔄 Data updates every 10 minutes.")
