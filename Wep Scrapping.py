import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Function to scrape stock prices
def scrape_stock_prices(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Example: Extracting stock data from a table (adjust selectors as per the website)
    table = soup.find("table", {"class": "stock-table"})
    rows = table.find_all("tr")

    data = []
    for row in rows[1:]:  # Skip header row
        cols = row.find_all("td")
        stock_name = cols[0].text.strip()
        price = cols[1].text.strip()
        change = cols[2].text.strip()
        data.append([stock_name, price, change])

    return pd.DataFrame(data, columns=["Stock Name", "Price", "Change"])

# Function to scrape cryptocurrency data
def scrape_crypto_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Example: Extracting crypto data from a table (adjust selectors as per the website)
    table = soup.find("table", {"class": "crypto-table"})
    rows = table.find_all("tr")

    data = []
    for row in rows[1:]:  # Skip header row
        cols = row.find_all("td")
        crypto_name = cols[0].text.strip()
        price = cols[1].text.strip()
        market_cap = cols[2].text.strip()
        data.append([crypto_name, price, market_cap])

    return pd.DataFrame(data, columns=["Crypto Name", "Price", "Market Cap"])

# Function to scrape market news
def scrape_market_news(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Example: Extracting news headlines (adjust selectors as per the website)
    news_items = soup.find_all("div", {"class": "news-item"})
    data = []
    for item in news_items:
        headline = item.find("h2").text.strip()
        timestamp = item.find("span", {"class": "timestamp"}).text.strip()
        data.append([headline, timestamp])

    return pd.DataFrame(data, columns=["Headline", "Timestamp"])

# Function to process raw financial data
def process_data(df):
    # Handle missing values
    df.fillna(0, inplace=True)

    # Remove duplicates
    df.drop_duplicates(inplace=True)

    # Convert price columns to numeric (remove symbols like $)
    if "Price" in df.columns:
        df["Price"] = df["Price"].replace({'\$': '', ',': ''}, regex=True).astype(float)

    return df

# Function to visualize stock trends
def visualize_stock_trends(df):
    plt.figure(figsize=(10, 6))
    sns.lineplot(x=df.index, y="Price", data=df, label="Stock Price")
    plt.title("Stock Price Trends Over Time")
    plt.xlabel("Date")
    plt.ylabel("Price ($)")
    plt.legend()
    plt.show()

# Function to visualize correlations
def visualize_correlations(df):
    plt.figure(figsize=(8, 6))
    sns.heatmap(df.corr(), annot=True, cmap="coolwarm")
    plt.title("Correlation Between Market Factors")
    plt.show()

# Main function to run the project
def main():
    # URLs for scraping (replace with actual URLs)
    stock_url = "https://example.com/stock-prices"
    crypto_url = "https://example.com/crypto-prices"
    news_url = "https://example.com/market-news"

    # Scrape data
    stock_df = scrape_stock_prices(stock_url)
    crypto_df = scrape_crypto_data(crypto_url)
    news_df = scrape_market_news(news_url)

    # Process data
    stock_df = process_data(stock_df)
    crypto_df = process_data(crypto_df)

    # Visualize data
    visualize_stock_trends(stock_df)
    visualize_correlations(crypto_df)

    # Display scraped data
    print("Stock Data:")
    print(stock_df.head())
    print("\nCryptocurrency Data:")
    print(crypto_df.head())
    print("\nMarket News:")
    print(news_df.head())

if __name__ == "__main__":
    main()