import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.dates import DateFormatter
from datetime import datetime, timedelta
import os
import time
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

class StockAnalyzer:
    def __init__(self, output_dir='./data/'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def validate_ticker(self, ticker):
        """Validate ticker symbol format"""
        if not ticker or len(ticker.strip()) == 0:
            return False, "Ticker cannot be empty"
        if len(ticker) > 10:  # Most tickers are 1-5 chars, some ETFs longer
            return False, "Ticker too long"
        return True, "Valid ticker"
    
    def get_stock_data(self, ticker, period="max", use_cache=True, cache_hours=24):
        """
        Fetch stock data using yfinance with caching
        
        Args:
            ticker (str): Stock ticker symbol
            period (str): Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            use_cache (bool): Whether to use cached data
            cache_hours (int): Cache validity in hours
        """
        ticker = ticker.upper().strip()
        
        # Validate ticker
        is_valid, msg = self.validate_ticker(ticker)
        if not is_valid:
            print(f"❌ Invalid ticker: {msg}")
            return pd.DataFrame()
        
        cache_file = os.path.join(self.output_dir, f"{ticker}_cache.csv")
        
        # Check cache first
        if use_cache and os.path.exists(cache_file):
            try:
                mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
                if datetime.now() - mod_time < timedelta(hours=cache_hours):
                    print(f"📁 Using cached data for {ticker} (updated {mod_time.strftime('%Y-%m-%d %H:%M')})")
                    df = pd.read_csv(cache_file)
                    df['Date'] = pd.to_datetime(df['Date'])
                    return df
            except Exception as e:
                print(f"⚠️ Cache read error: {e}")
        
        # Fetch fresh data
        try:
            print(f"📡 Fetching {ticker} data from Yahoo Finance...")
            stock = yf.Ticker(ticker)
            
            # Get stock info to verify ticker exists
            info = stock.info
            if not info or 'regularMarketPrice' not in info:
                print(f"❌ Invalid ticker symbol: {ticker}")
                return pd.DataFrame()
            
            # Get historical data
            hist = stock.history(period=period)
            
            if hist.empty:
                print(f"❌ No data found for {ticker}")
                return pd.DataFrame()
            
            # Clean and prepare data
            df = hist.reset_index()
            df = df[['Date', 'Close']].copy()
            df.columns = ['Date', 'Price']
            
            # Remove any invalid data
            df = df.dropna()
            df = df[df['Price'] > 0]
            
            if df.empty:
                print(f"❌ No valid price data found for {ticker}")
                return pd.DataFrame()
            
            # Sort by date
            df = df.sort_values('Date').reset_index(drop=True)
            
            # Cache the data
            try:
                df.to_csv(cache_file, index=False)
                print(f"💾 Cached data saved for {ticker}")
            except Exception as e:
                print(f"⚠️ Cache save error: {e}")
            
            print(f"✅ Successfully loaded {len(df)} records for {ticker}")
            print(f"📅 Data range: {df['Date'].min().date()} to {df['Date'].max().date()}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching data for {ticker}: {str(e)}")
            return pd.DataFrame()
    
    def get_date_input(self, prompt, min_date, max_date):
        """Get and validate date input from user"""
        while True:
            try:
                date_input = input(f"{prompt} (YYYY-MM-DD): ").strip()
                if not date_input:
                    print("Date cannot be empty. Please try again.")
                    continue
                    
                date_obj = datetime.strptime(date_input, "%Y-%m-%d").date()
                
                if date_obj < min_date:
                    print(f"Date must be on or after {min_date}")
                    continue
                if date_obj > max_date:
                    print(f"Date must be on or before {max_date}")
                    continue
                    
                return date_obj
                
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD format (e.g., 2024-01-15)")
    
    def find_optimal_trade(self, df, start_date, end_date):
        """
        Find optimal buy/sell dates for maximum profit using dynamic programming
        
        Args:
            df (DataFrame): Stock data with Date and Price columns
            start_date (date): Start date for analysis
            end_date (date): End date for analysis
            
        Returns:
            dict: Trade information including buy/sell dates, prices, and profit
        """
        # Filter data for the selected period
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        period_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)].copy()
        
        if len(period_df) < 2:
            return None
        
        # Find maximum profit using single pass algorithm
        min_price = float('inf')
        max_profit = 0
        buy_date = None
        sell_date = None
        buy_price = 0
        sell_price = 0
        
        for _, row in period_df.iterrows():
            current_price = row['Price']
            current_date = row['Date']
            
            # Update minimum price and potential buy date
            if current_price < min_price:
                min_price = current_price
                potential_buy_date = current_date
            
            # Calculate profit if we sell today
            current_profit = current_price - min_price
            
            # Update maximum profit and trade dates
            if current_profit > max_profit:
                max_profit = current_profit
                buy_date = potential_buy_date
                sell_date = current_date
                buy_price = min_price
                sell_price = current_price
        
        if max_profit <= 0:
            return None
        
        return {
            'buy_date': buy_date,
            'sell_date': sell_date,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'profit': max_profit,
            'profit_percent': (max_profit / buy_price) * 100,
            'period_df': period_df
        }
    
    def plot_analysis(self, full_df, trade_info, ticker):
        """Create comprehensive visualization of the trading analysis"""
        if not trade_info:
            print("No profitable trades found to visualize.")
            return
        
        # Setup the plot
        plt.style.use('seaborn-v0_8' if hasattr(plt.style, 'seaborn-v0_8') else 'default')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # Convert dates for plotting
        full_df['Date'] = pd.to_datetime(full_df['Date'])
        period_df = trade_info['period_df'].copy()
        period_df['Date'] = pd.to_datetime(period_df['Date'])
        
        # Plot 1: Full price history with highlighted period
        ax1.plot(full_df['Date'], full_df['Price'], label='Full Price History', 
                color='lightblue', alpha=0.7, linewidth=1)
        ax1.plot(period_df['Date'], period_df['Price'], label='Analysis Period', 
                color='blue', linewidth=2)
        
        # Mark buy/sell points
        buy_date_dt = pd.to_datetime(trade_info['buy_date'])
        sell_date_dt = pd.to_datetime(trade_info['sell_date'])
        
        ax1.scatter([buy_date_dt], [trade_info['buy_price']], 
                   color='green', s=150, zorder=5, marker='^', label='BUY')
        ax1.scatter([sell_date_dt], [trade_info['sell_price']], 
                   color='red', s=150, zorder=5, marker='v', label='SELL')
        
        # Annotations
        ax1.annotate(f'BUY\n{trade_info["buy_date"]}\n${trade_info["buy_price"]:.2f}',
                    (buy_date_dt, trade_info['buy_price']), 
                    textcoords="offset points", xytext=(10, 20), ha='left',
                    bbox=dict(boxstyle='round,pad=0.5', fc='lightgreen', alpha=0.8),
                    arrowprops=dict(arrowstyle='->', color='green'))
        
        ax1.annotate(f'SELL\n{trade_info["sell_date"]}\n${trade_info["sell_price"]:.2f}',
                    (sell_date_dt, trade_info['sell_price']), 
                    textcoords="offset points", xytext=(-10, 20), ha='right',
                    bbox=dict(boxstyle='round,pad=0.5', fc='lightcoral', alpha=0.8),
                    arrowprops=dict(arrowstyle='->', color='red'))
        
        ax1.set_title(f'{ticker} Stock Price Analysis - Full History', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Detailed view of analysis period
        ax2.plot(period_df['Date'], period_df['Price'], color='blue', linewidth=2, marker='o', markersize=3)
        ax2.scatter([buy_date_dt], [trade_info['buy_price']], 
                   color='green', s=150, zorder=5, marker='^')
        ax2.scatter([sell_date_dt], [trade_info['sell_price']], 
                   color='red', s=150, zorder=5, marker='v')
        
        # Fill area between buy and sell prices
        ax2.axhline(y=trade_info['buy_price'], color='green', linestyle='--', alpha=0.5)
        ax2.axhline(y=trade_info['sell_price'], color='red', linestyle='--', alpha=0.5)
        ax2.fill_between(period_df['Date'], trade_info['buy_price'], trade_info['sell_price'], 
                        alpha=0.2, color='gold')
        
        ax2.set_title(f'Analysis Period Detail - Profit: ${trade_info["profit"]:.2f} ({trade_info["profit_percent"]:.1f}%)', 
                     fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Price ($)', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Format dates
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # Save plot
        plot_file = os.path.join(self.output_dir, f"{ticker}_analysis.png")
        try:
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            print(f"📊 Chart saved as {plot_file}")
        except Exception as e:
            print(f"⚠️ Could not save chart: {e}")
        
        plt.show()
    
    def calculate_profit(self, df, ticker):
        """Main profit calculation workflow"""
        if df.empty:
            print("❌ No data available for calculation.")
            return
        
        # Show available date range
        df['Date'] = pd.to_datetime(df['Date'])
        min_date = df['Date'].min().date()
        max_date = df['Date'].max().date()
        
        print(f"\n📅 Available data from {min_date} to {max_date}")
        print(f"📊 Total records: {len(df)}")
        
        # Get date range from user
        print(f"\n🎯 Select date range for profit analysis:")
        start_date = self.get_date_input("Enter start date", min_date, max_date)
        end_date = self.get_date_input("Enter end date", start_date, max_date)
        
        print(f"\n🔍 Analyzing period: {start_date} to {end_date}")
        
        # Find optimal trade
        trade_info = self.find_optimal_trade(df, start_date, end_date)
        
        if not trade_info:
            print("\n❌ No profitable trading opportunity found in the selected period.")
            print("💡 Try a different date range or check if the stock was generally declining.")
            return
        
        # Display results
        print(f"\n🎉 OPTIMAL TRADING STRATEGY FOUND!")
        print(f"{'='*50}")
        print(f"📈 Stock: {ticker}")
        print(f"🗓️  Analysis Period: {start_date} to {end_date}")
        print(f"🟢 BUY:  {trade_info['buy_date']} at ${trade_info['buy_price']:.2f}")
        print(f"🔴 SELL: {trade_info['sell_date']} at ${trade_info['sell_price']:.2f}")
        print(f"💰 Profit per share: ${trade_info['profit']:.2f}")
        print(f"📊 Return: {trade_info['profit_percent']:.2f}%")
        print(f"⏱️  Holding period: {(pd.to_datetime(trade_info['sell_date']) - pd.to_datetime(trade_info['buy_date'])).days} days")
        print(f"{'='*50}")
        
        # Save results
        csv_file = os.path.join(self.output_dir, f"{ticker}_analysis_results.csv")
        results_df = pd.DataFrame([{
            'Ticker': ticker,
            'Analysis_Start': start_date,
            'Analysis_End': end_date,
            'Buy_Date': trade_info['buy_date'],
            'Buy_Price': trade_info['buy_price'],
            'Sell_Date': trade_info['sell_date'],
            'Sell_Price': trade_info['sell_price'],
            'Profit_Per_Share': trade_info['profit'],
            'Return_Percent': trade_info['profit_percent'],
            'Holding_Days': (pd.to_datetime(trade_info['sell_date']) - pd.to_datetime(trade_info['buy_date'])).days
        }])
        
        try:
            results_df.to_csv(csv_file, index=False)
            print(f"💾 Results saved to {csv_file}")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")
        
        # Create visualization
        print(f"\n📊 Generating visualization...")
        self.plot_analysis(df, trade_info, ticker)
    
    def run_analysis(self):
        """Main application workflow"""
        print("🚀 Stock Profit Analyzer")
        print("=" * 40)
        
        while True:
            try:
                ticker = input("\n📈 Enter stock ticker (e.g., AAPL, TSLA) or 'quit' to exit: ").strip()
                
                if ticker.lower() in ['quit', 'exit', 'q']:
                    print("👋 Thanks for using Stock Profit Analyzer!")
                    break
                
                if not ticker:
                    print("❌ Please enter a valid ticker symbol.")
                    continue
                
                # Fetch stock data
                stock_df = self.get_stock_data(ticker)
                
                if stock_df.empty:
                    continue
                
                # Save raw data
                csv_path = os.path.join(self.output_dir, f"{ticker}_stock_data.csv")
                try:
                    stock_df.to_csv(csv_path, index=False)
                    print(f"💾 Raw data saved to {csv_path}")
                except Exception as e:
                    print(f"⚠️ Could not save raw data: {e}")
                
                # Run profit analysis
                self.calculate_profit(stock_df, ticker)
                
                # Ask for another analysis
                while True:
                    continue_choice = input("\n🔄 Analyze another stock? (y/n): ").strip().lower()
                    if continue_choice in ['y', 'yes']:
                        break
                    elif continue_choice in ['n', 'no']:
                        print("👋 Thanks for using Stock Profit Analyzer!")
                        return
                    else:
                        print("Please enter 'y' for yes or 'n' for no.")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                print("Please try again with a different ticker.")

def main():
    """Entry point of the application"""
    analyzer = StockAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()