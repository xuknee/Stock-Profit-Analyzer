import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.dates import DateFormatter
from datetime import datetime

# Constants
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Scraping function 
def scrape_stock_prices(url):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()AA
    soup = BeautifulSoup(response.content, "html.parser")
    
    print(f"Page Title: {soup.title.text.strip()}")
    
    table = soup.find("table", {"class": "table yf-1jecxey"})  
    if table is None:
        print("Table not found. Check the HTML structure or the URL.")
        return pd.DataFrame()
    
    rows = table.find_all("tr")
    
    data = []
    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < 7:
            continue
        date = cols[0].text.strip()
        price = cols[4].text.strip()
        data.append([date, price])
    
    return pd.DataFrame(data, columns=["Date", "Price"])

# Processing function
def process_data(df):
    df.fillna(0, inplace=True)
    df.drop_duplicates(inplace=True)

    if "Price" in df.columns:
        df["Price"] = df["Price"].replace({'\$': '', ',': '', '[+-]': ''}, regex=True).astype(float)

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(by="Date", ascending=True)

    return df

# Profit visualization Function
def plot_profit_analysis(full_df, period_df, buy_date, sell_date):
    plt.figure(figsize=(14, 7))
    
    # Convert back to datetime for plotting
    full_df['Date'] = pd.to_datetime(full_df['Date'])
    period_df['Date'] = pd.to_datetime(period_df['Date'])
    buy_date = pd.to_datetime(buy_date)
    sell_date = pd.to_datetime(sell_date)
    
    # Plot full price trend
    sns.lineplot(data=full_df, x='Date', y='Price', label='Price History', color='lightblue', alpha=0.7)
    
    # Highlight the selected period
    sns.lineplot(data=period_df, x='Date', y='Price', label='Selected Period', color='blue')
    
    # Mark buy/sell points
    buy_price = period_df[period_df['Date'] == buy_date]['Price'].values[0]
    sell_price = period_df[period_df['Date'] == sell_date]['Price'].values[0]
    
    plt.scatter([buy_date, sell_date], [buy_price, sell_price], 
                color=['green', 'red'], s=100, zorder=5)
    
    # Annotations
    plt.annotate(f'BUY\n{buy_date.date()}\n${buy_price:.2f}',
                (buy_date, buy_price), textcoords="offset points",
                xytext=(0,15), ha='center', color='green',
                bbox=dict(boxstyle='round,pad=0.5', fc='white', alpha=0.8))
    plt.annotate(f'SELL\n{sell_date.date()}\n${sell_price:.2f}',
                (sell_date, sell_price), textcoords="offset points",
                xytext=(0,-20), ha='center', color='red',
                bbox=dict(boxstyle='round,pad=0.5', fc='white', alpha=0.8))
    
    # Draw vertical lines for period boundaries
    period_start = period_df['Date'].min()
    period_end = period_df['Date'].max()
    plt.axvline(x=period_start, color='gray', linestyle='--', alpha=0.5)
    plt.axvline(x=period_end, color='gray', linestyle='--', alpha=0.5)
    
    # Formatting
    plt.title(f"Optimal Buy/Sell Points (Period: {period_start.date()} to {period_end.date()})")
    plt.xlabel("Date")
    plt.ylabel("Price ($)")
    plt.gca().xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

# Calculate_profit Function
def calculate_profit(df):
    if df.empty:
        print("No data available for calculation.")
        return
    
    # Keep original full_df for visualization
    full_df = df.copy()
    
    # Convert to datetime.date for easier comparison
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    # Show available date range
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    print(f"\nAvailable data from {min_date} to {max_date}")
    
    # Get date range from user
    while True:
        try:
            start_input = input("Enter start date (YYYY-MM-DD): ")
            end_input = input("Enter end date (YYYY-MM-DD): ")
            
            start_date = datetime.strptime(start_input, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_input, "%Y-%m-%d").date()
            
            if start_date > end_date:
                print("Start date must be before end date. Try again.")
                continue
                
            if start_date < min_date or end_date > max_date:
                print(f"Dates must be between {min_date} and {max_date}")
                continue
                
            break
                
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD format.")
    
    # Filter data for the selected period
    period_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    
    if len(period_df) < 2:
        print("Not enough data points in selected period.")
        return
    
    # Calculate maximum profit
    min_price = float('inf')
    max_profit = 0
    buy_date = None
    sell_date = None
    
    for date, price in zip(period_df['Date'], period_df['Price']):
        if price < min_price:
            min_price = price
            potential_buy_date = date
        
        current_profit = price - min_price
        
        if current_profit > max_profit:
            max_profit = current_profit
            buy_date = potential_buy_date
            sell_date = date
    
    if max_profit <= 0:
        print("\nNo profitable period found in the selected date range.")
    else:
        print(f"\nMaximum Profit Calculation ({start_date} to {end_date}):")
        print(f"Buy on: {buy_date} at ${period_df[period_df['Date'] == buy_date]['Price'].values[0]:.2f}")
        print(f"Sell on: {sell_date} at ${period_df[period_df['Date'] == sell_date]['Price'].values[0]:.2f}")
        print(f"Potential profit per share: ${max_profit:.2f}")
        
        # Visualization with full range
        plot_profit_analysis(full_df, period_df, buy_date, sell_date)

def main():
    ticker = input("Enter stock ticker (e.g., AAPL): ").strip().upper()
    print(f"Scraping {ticker} data from Yahoo Finance...")
    stock_url = f"https://finance.yahoo.com/quote/{ticker}/history/?period1=1590174921&period2=1747941317"

    print("Scraping stock data...")
    stock_df = scrape_stock_prices(stock_url)

    if not stock_df.empty:
        print("Processing stock data...")
        stock_df = process_data(stock_df)
        
        if not stock_df.empty:
            csv_path = f"{ticker}_stock_data.csv"
            stock_df.to_csv(csv_path, index=False)
            print(f"✅ Successfully saved {len(stock_df)} records to {csv_path}")
            print("Calculating profit...")
            calculate_profit(stock_df)
        else:
            print("Processed DataFrame is empty. Skipping further analysis.")
    else:
        print("Stock DataFrame is empty. Exiting...")

if __name__ == "__main__":
    main()
