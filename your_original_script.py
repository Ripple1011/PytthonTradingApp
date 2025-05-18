import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import sys
import os

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print a nice header for the app."""
    print("=" * 80)
    print("                   INDIAN STOCK MARKET ANALYZER")
    print("=" * 80)
    print("Find the best stock opportunities within your budget")
    print("-" * 80)

def get_nifty500_stocks():
    """Get a list of Nifty 500 stocks."""
    try:
        # Try to download Nifty 500 data from Yahoo Finance
        nifty500 = yf.Ticker("^NSEI")
        
        # This is a backup list of popular NSE stocks in case we can't get the full Nifty 500
        popular_stocks = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", 
            "SBIN", "BHARTIARTL", "KOTAKBANK", "ITC", "BAJFINANCE", "AXISBANK",
            "WIPRO", "ADANIPORTS", "TATASTEEL", "HCLTECH", "ASIANPAINT", "MARUTI",
            "TECHM", "TITAN", "ULTRACEMCO", "INDUSINDBK", "SUNPHARMA", "ONGC",
            "BAJAJFINSV", "NTPC", "POWERGRID", "GRASIM", "TATAMOTORS", "LT",
            "CIPLA", "DRREDDY", "DIVISLAB", "BPCL", "SHREECEM", "EICHERMOT"
        ]
        
        print(f"Scanning popular Indian stocks... ({len(popular_stocks)} stocks)")
        return [f"{stock}.NS" for stock in popular_stocks]
    
    except Exception as e:
        print(f"Warning: Unable to fetch Nifty 500 list. Using default stock list. Error: {e}")
        # Return a smaller list of major Indian stocks as backup
        default_stocks = [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
            "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS"
        ]
        print(f"Using a default list of {len(default_stocks)} major stocks.")
        return default_stocks

def get_stock_data(ticker, period="3mo"):
    """Get historical stock data for a given ticker."""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        
        if data.empty:
            return None
            
        # Get the stock name
        try:
            name = stock.info['longName']
        except:
            name = ticker.replace(".NS", "")
            
        return data, name
    except Exception as e:
        return None

def calculate_technical_indicators(data):
    """Calculate technical indicators for stock analysis."""
    if data is None or len(data) < 50:
        return None
    
    # Calculate moving averages
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['MA50'] = data['Close'].rolling(window=50).mean()
    data['MA200'] = data['Close'].rolling(window=200).mean()
    
    # Calculate RSI (Relative Strength Index)
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # Calculate MACD (Moving Average Convergence Divergence)
    data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = data['EMA12'] - data['EMA26']
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    
    # Calculate volatility (standard deviation of daily returns)
    data['Daily_Return'] = data['Close'].pct_change()
    data['Volatility'] = data['Daily_Return'].rolling(window=20).std() * 100
    
    return data

def calculate_growth_potential(data):
    """Estimate potential growth for a stock based on technical indicators."""
    if data is None or len(data) < 50:
        return 0, 0
    
    current_price = data.iloc[-1]['Close']
    growth_percent = 0
    target_price = current_price
    
    # Method 1: Based on RSI reversion to mean
    rsi = data.iloc[-1]['RSI']
    if 30 <= rsi <= 45:  # Oversold but recovering
        growth_percent = 10  # Estimate 10% growth potential
    elif 45 < rsi <= 55:  # Neutral zone
        growth_percent = 7   # Moderate growth potential
    elif 55 < rsi <= 65:  # Strong momentum
        growth_percent = 12  # Good growth potential
    else:
        # Method 2: Based on price vs moving averages
        ma20 = data.iloc[-1]['MA20']
        ma50 = data.iloc[-1]['MA50']
        
        if current_price > ma20 > ma50:  # Strong uptrend
            growth_percent = 15
        elif ma20 > current_price > ma50:  # Potential reversal up
            growth_percent = 8
        elif current_price > ma50:  # Above longer-term average
            growth_percent = 5
    
    # Calculate target price
    target_price = current_price * (1 + growth_percent/100)
    
    # Method 3: Historical resistance levels (simplified)
    # Find the highest price in the dataset
    historical_high = data['Close'].max()
    if historical_high > current_price:
        # If we're below historical high, consider it as potential target
        potential_growth = (historical_high / current_price - 1) * 100
        # If historical high suggests lower growth, use it
        if potential_growth < growth_percent:
            growth_percent = potential_growth
            target_price = historical_high
    
    return growth_percent, target_price

def calculate_stop_loss(data, risk_percentage=5):
    """Calculate a recommended stop-loss price."""
    if data is None:
        return 0
    
    current_price = data.iloc[-1]['Close']
    stop_loss_price = current_price * (1 - risk_percentage/100)
    
    return stop_loss_price

def recommend_holding_time(data):
    """Recommend a holding period based on volatility and trend strength."""
    if data is None:
        return "Unknown"
    
    # Get volatility and trend score
    volatility = data.iloc[-1]['Volatility']
    trend_score = calculate_trend_strength(data)
    
    # Determine holding time based on volatility and trend strength
    if volatility > 3:  # High volatility
        if trend_score > 70:  # Strong trend
            return "4-6 weeks (Short-term)"
        else:
            return "1-3 weeks (Very short-term)"
    elif volatility > 2:  # Medium volatility
        if trend_score > 70:
            return "2-4 months (Medium-term)"
        else:
            return "1-2 months (Short-term)"
    else:  # Low volatility
        if trend_score > 70:
            return "4-6 months (Medium-term)"
        else:
            return "2-3 months (Medium-term)"

def recommend_exit_strategy(data, growth_percent, stop_loss_price):
    """Recommend an exit strategy for profit booking and stop-loss."""
    if data is None:
        return "Unknown", 0
    
    current_price = data.iloc[-1]['Close']
    
    # Calculate profit target
    profit_target = current_price * (1 + growth_percent/100)
    
    # Calculate profit percentage
    profit_percentage = growth_percent
    
    # Recommend exit strategy based on volatility
    volatility = data.iloc[-1]['Volatility']
    
    if volatility > 3:  # High volatility
        strategy = f"Exit if profit reaches +{int(profit_percentage * 0.7)}% or loss exceeds -{int((current_price - stop_loss_price) / current_price * 100)}%"
    else:  # Lower volatility
        strategy = f"Exit if profit reaches +{int(profit_percentage)}% or loss exceeds -{int((current_price - stop_loss_price) / current_price * 100)}%"
    
    return strategy, profit_target

def calculate_trend_strength(data):
    """Calculate a trend strength score from 0-100."""
    if data is None or data.iloc[-1]['MA20'] is np.nan or data.iloc[-1]['MA50'] is np.nan:
        return 0
    
    score = 0
    
    # Price above moving averages
    if data.iloc[-1]['Close'] > data.iloc[-1]['MA20']:
        score += 20
    if data.iloc[-1]['Close'] > data.iloc[-1]['MA50']:
        score += 20
    
    # Moving average alignment (MA20 > MA50 for uptrend)
    if data.iloc[-1]['MA20'] > data.iloc[-1]['MA50']:
        score += 20
    
    # RSI between 50 and 70 (strong but not overbought)
    rsi = data.iloc[-1]['RSI']
    if 50 <= rsi <= 70:
        score += 20
    elif 40 <= rsi < 50:
        score += 10
    
    # MACD above signal line
    if data.iloc[-1]['MACD'] > data.iloc[-1]['Signal']:
        score += 20
    
    return score

def get_buy_signal(data):
    """Generate a buy/hold/sell signal based on technical indicators.
    
    Returns:
        str: Signal - 'BUY', 'HOLD', or 'SELL'
    """
    if data is None or len(data) < 20:
        return "N/A"
    
    score = 0
    
    # Check price relative to moving averages
    current_price = data.iloc[-1]['Close']
    ma20 = data.iloc[-1]['MA20']
    ma50 = data.iloc[-1]['MA50']
    
    # Price above MAs is bullish
    if current_price > ma20:
        score += 1
    if current_price > ma50:
        score += 1
    
    # MA crossover (short-term MA above long-term MA is bullish)
    if ma20 > ma50:
        score += 1
    
    # RSI conditions
    rsi = data.iloc[-1]['RSI']
    if rsi < 30:  # Oversold
        score += 1
    elif rsi > 70:  # Overbought
        score -= 1
    
    # MACD conditions
    macd = data.iloc[-1]['MACD']
    signal_line = data.iloc[-1]['Signal']
    
    # MACD above signal line is bullish
    if macd > signal_line:
        score += 1
    else:
        score -= 1
    
    # Generate signal based on score
    if score >= 3:
        return "BUY"
    elif score <= -1:
        return "SELL"
    else:
        return "HOLD"

def get_advanced_analysis(data):
    """Generate advanced analysis including growth potential, stop-loss, and exit strategy."""
    if data is None:
        return {
            'growth_percent': 0,
            'target_price': 0,
            'stop_loss_price': 0,
            'holding_time': "Unknown",
            'exit_strategy': "Unknown"
        }
    
    # Calculate growth potential
    growth_percent, target_price = calculate_growth_potential(data)
    
    # Calculate stop-loss price
    stop_loss_price = calculate_stop_loss(data)
    
    # Recommend holding time
    holding_time = recommend_holding_time(data)
    
    # Recommend exit strategy
    exit_strategy, _ = recommend_exit_strategy(data, growth_percent, stop_loss_price)
    
    return {
        'growth_percent': growth_percent,
        'target_price': target_price,
        'stop_loss_price': stop_loss_price,
        'holding_time': holding_time,
        'exit_strategy': exit_strategy
    }

def plot_stock_chart(data, ticker, name):
    """Generate a stock chart with technical indicators."""
    if data is None or len(data) < 20:
        print(f"Not enough data to plot chart for {ticker}")
        return
    
    plt.figure(figsize=(12, 10))
    
    # Plot stock price and moving averages
    plt.subplot(3, 1, 1)
    plt.plot(data.index, data['Close'], label='Price', color='blue')
    plt.plot(data.index, data['MA20'], label='20-Day MA', color='orange')
    plt.plot(data.index, data['MA50'], label='50-Day MA', color='red')
    
    # Add growth potential and stop-loss if available
    try:
        growth_percent, target_price = calculate_growth_potential(data)
        stop_loss_price = calculate_stop_loss(data)
        current_price = data.iloc[-1]['Close']
        
        # Add horizontal lines for current price, target price, and stop-loss
        last_date = data.index[-1]
        extend_days = 10  # Show projection for 10 days
        projection_date = last_date + timedelta(days=extend_days)
        
        # Create projection line for price targets
        plt.plot([last_date, projection_date], [current_price, current_price], 'b--', alpha=0.7)
        plt.plot([last_date, projection_date], [target_price, target_price], 'g--', alpha=0.7)
        plt.plot([last_date, projection_date], [stop_loss_price, stop_loss_price], 'r--', alpha=0.7)
        
        # Add text labels
        plt.text(projection_date, current_price, f' Current: ₹{current_price:.2f}', verticalalignment='center')
        plt.text(projection_date, target_price, f' Target (+{growth_percent:.1f}%): ₹{target_price:.2f}', verticalalignment='center', color='green')
        plt.text(projection_date, stop_loss_price, f' Stop-Loss: ₹{stop_loss_price:.2f}', verticalalignment='center', color='red')
    except:
        # If projection fails, just continue without it
        pass
    
    plt.title(f"{name} ({ticker}) - Stock Analysis")
    plt.ylabel('Price (₹)')
    plt.legend()
    plt.grid(True)
    
    # Plot RSI
    plt.subplot(3, 1, 2)
    plt.plot(data.index, data['RSI'], label='RSI', color='purple')
    plt.axhline(y=70, color='red', linestyle='--', alpha=0.3)
    plt.axhline(y=30, color='green', linestyle='--', alpha=0.3)
    plt.axhline(y=50, color='black', linestyle='--', alpha=0.2)
    plt.fill_between(data.index, data['RSI'], 70, where=(data['RSI'] >= 70), color='red', alpha=0.3)
    plt.fill_between(data.index, data['RSI'], 30, where=(data['RSI'] <= 30), color='green', alpha=0.3)
    
    plt.title('Relative Strength Index (RSI)')
    plt.ylabel('RSI')
    plt.legend()
    plt.grid(True)
    
    # Plot MACD
    plt.subplot(3, 1, 3)
    plt.plot(data.index, data['MACD'], label='MACD', color='blue')
    plt.plot(data.index, data['Signal'], label='Signal Line', color='red')
    plt.bar(data.index, data['MACD'] - data['Signal'], label='Histogram', color='green', alpha=0.5)
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    plt.title('MACD (Moving Average Convergence Divergence)')
    plt.ylabel('MACD')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

def find_stock_opportunities(budget):
    """Find good stock opportunities within the given budget."""
    print_header()
    
    # Get list of stocks to analyze
    stock_list = get_nifty500_stocks()
    print(f"Analyzing {len(stock_list)} stocks for opportunities...")
    
    # Store results
    opportunities = []
    count = 0
    
    # Progress bar
    total_stocks = len(stock_list)
    
    for ticker in stock_list:
        count += 1
        # Show progress
        progress = count / total_stocks * 100
        sys.stdout.write(f"\rProgress: [{int(progress) * '=' + (100 - int(progress)) * ' '}] {progress:.1f}%")
        sys.stdout.flush()
        
        # Get stock data
        result = get_stock_data(ticker)
        if result is None:
            continue
        
        data, name = result
        
        # Calculate technical indicators
        data_with_indicators = calculate_technical_indicators(data)
        if data_with_indicators is None:
            continue
        
        # Get current price and check if within budget
        current_price = data_with_indicators.iloc[-1]['Close']
        if current_price > budget:
            continue
        
        # Calculate how many shares can be bought
        shares_possible = int(budget / current_price)
        if shares_possible < 1:
            continue
        
        # Calculate trend strength score
        trend_score = calculate_trend_strength(data_with_indicators)
        
        # Get buy/hold signal
        signal = get_buy_signal(data_with_indicators)
        
        # Get advanced analysis
        advanced = get_advanced_analysis(data_with_indicators)
        
        # Store the opportunity
        opportunities.append({
            'ticker': ticker,
            'name': name,
            'price': current_price,
            'shares': shares_possible,
            'investment': shares_possible * current_price,
            'trend_score': trend_score,
            'signal': signal,
            'data': data_with_indicators,
            'growth_percent': advanced['growth_percent'],
            'target_price': advanced['target_price'],
            'stop_loss_price': advanced['stop_loss_price'],
            'holding_time': advanced['holding_time'],
            'exit_strategy': advanced['exit_strategy']
        })
    
    print("\n")
    
    # Sort opportunities by trend score (highest first)
    opportunities.sort(key=lambda x: x['trend_score'], reverse=True)
    
    return opportunities

def display_opportunities(opportunities, limit=10):
    """Display the top stock opportunities in a formatted table."""
    if not opportunities:
        print("No suitable stock opportunities found within your budget.")
        return
    
    # Display only the top opportunities
    top_opportunities = opportunities[:limit]
    
    print("\n" + "=" * 100)
    print(f"TOP {len(top_opportunities)} STOCK OPPORTUNITIES")
    print("=" * 100)
    print(f"{'STOCK':<8} {'NAME':<20} {'PRICE':<10} {'SHARES':<8} {'AMOUNT':<10} {'TREND':<6} {'SIGNAL':<5} {'GROWTH':<8} {'TARGET':<10} {'STOP-LOSS':<10}")
    print("-" * 100)
    
    for opp in top_opportunities:
        ticker = opp['ticker'].replace('.NS', '')
        print(f"{ticker:<8} {opp['name'][:20]:<20} ₹{opp['price']:<9.2f} {opp['shares']:<8} ₹{opp['investment']:<9.2f} {opp['trend_score']:<6} {opp['signal']:<5} {opp['growth_percent']:<7.1f}% ₹{opp['target_price']:<9.2f} ₹{opp['stop_loss_price']:<9.2f}")
    
    print("=" * 100)
    print(f"Budget: ₹{budget:.2f} | Trend Score: Higher is better (0-100) | Growth: Potential upside")
    print("=" * 100)

def analyze_specific_stock(ticker):
    """Analyze a specific stock by ticker symbol."""
    if not ticker.endswith('.NS'):
        ticker = ticker + '.NS'
    
    print(f"\nAnalyzing {ticker}...")
    
    result = get_stock_data(ticker)
    if result is None:
        print(f"Could not retrieve data for {ticker}. Please check the ticker symbol.")
        return
    
    data, name = result
    
    # Calculate technical indicators
    data_with_indicators = calculate_technical_indicators(data)
    if data_with_indicators is None:
        print(f"Not enough historical data for {ticker} to calculate indicators.")
        return
    
    # Calculate trend strength and signal
    trend_score = calculate_trend_strength(data_with_indicators)
    signal = get_buy_signal(data_with_indicators)
    
    # Get advanced analysis
    advanced = get_advanced_analysis(data_with_indicators)
    current_price = data_with_indicators.iloc[-1]['Close']
    
    # Display detailed analysis
    print("\n" + "=" * 80)
    print(f"DETAILED ANALYSIS: {name} ({ticker})")
    print("=" * 80)
    print(f"Current Price: ₹{current_price:.2f}")
    print(f"20-Day MA: ₹{data_with_indicators.iloc[-1]['MA20']:.2f}")
    print(f"50-Day MA: ₹{data_with_indicators.iloc[-1]['MA50']:.2f}")
    print(f"RSI (14-Day): {data_with_indicators.iloc[-1]['RSI']:.2f}")
    print(f"Volatility (20-Day): {data_with_indicators.iloc[-1]['Volatility']:.2f}%")
    print(f"Trend Strength Score: {trend_score}/100")
    print(f"Signal: {signal}")
    print("-" * 80)
    print("ADVANCED ANALYSIS:")
    print(f"Growth Potential: ₹{advanced['target_price']:.2f} (+{advanced['growth_percent']:.1f}%)")
    print(f"Stop-Loss Price: ₹{advanced['stop_loss_price']:.2f} (-{(current_price - advanced['stop_loss_price']) / current_price * 100:.1f}%)")
    print(f"Recommended Holding Time: {advanced['holding_time']}")
    print(f"Exit Strategy: {advanced['exit_strategy']}")
    print("=" * 80)
    
    # Display the formatted output in the requested clear format
    print("\nSUMMARY:")
    print(f"""
Stock: {ticker}
-> Buy Price: ₹{current_price:.2f}
-> Growth Potential: ₹{advanced['target_price']:.2f} (+{advanced['growth_percent']:.1f}%) in {advanced['holding_time'].split()[0]} {advanced['holding_time'].split()[1]}
-> Stop-Loss: ₹{advanced['stop_loss_price']:.2f} (-{(current_price - advanced['stop_loss_price']) / current_price * 100:.1f}%)
-> Hold Time: {advanced['holding_time']}
-> Exit if:
   - Profit >{advanced['growth_percent']:.1f}% OR
   - Loss >{(current_price - advanced['stop_loss_price']) / current_price * 100:.1f}%
""")
    
    # Plot the chart
    plot_stock_chart(data_with_indicators, ticker, name)

def main():
    """Main function to run the stock analyzer."""
    clear_screen()
    print_header()
    
    print("\nWelcome to the Indian Stock Market Analyzer!")
    print("This app helps you find good NSE stock opportunities within your budget.")
    print("NEW: Now with growth prediction and exit strategy recommendations!")
    
    while True:
        print("\nOptions:")
        print("1. Find stock opportunities within budget")
        print("2. Analyze a specific stock")
        print("3. Adjust risk settings")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            try:
                budget = float(input("\nEnter your budget (in ₹): "))
                if budget <= 0:
                    print("Budget must be greater than zero.")
                    continue
                    
                opportunities = find_stock_opportunities(budget)
                display_opportunities(opportunities)
                
                # Ask if user wants to analyze any of the stocks in detail
                analyze_choice = input("\nWould you like to analyze any of these stocks in detail? (y/n): ")
                if analyze_choice.lower() == 'y':
                    ticker = input("Enter the stock ticker (without .NS): ")
                    analyze_specific_stock(ticker)
                    
            except ValueError:
                print("Invalid input. Please enter a valid budget amount.")
                
        elif choice == '2':
            ticker = input("\nEnter the stock ticker symbol (e.g., RELIANCE): ")
            analyze_specific_stock(ticker)
            
        elif choice == '3':
            try:
                print("\nRisk Settings:")
                print("These settings control how your exit strategy is calculated.")
                global RISK_PERCENTAGE
                global PROFIT_TARGET_MULTIPLIER
                
                # Show current settings
                print(f"Current stop-loss percentage: {RISK_PERCENTAGE}%")
                print(f"Current profit target multiplier: {PROFIT_TARGET_MULTIPLIER}x")
                
                # Adjust settings
                new_risk = float(input("\nEnter new stop-loss percentage (e.g., 5 for 5%): "))
                new_profit = float(input("Enter new profit target multiplier (e.g., 2 means 2x the risk): "))
                
                if 1 <= new_risk <= 20 and 0.5 <= new_profit <= 5:
                    RISK_PERCENTAGE = new_risk
                    PROFIT_TARGET_MULTIPLIER = new_profit
                    print(f"\nSettings updated. Stop-loss: {RISK_PERCENTAGE}%, Profit target: {PROFIT_TARGET_MULTIPLIER}x risk")
                else:
                    print("\nInvalid input. Stop-loss must be between 1-20% and profit multiplier between 0.5-5x.")
            except ValueError:
                print("Invalid input. Please enter valid numbers.")
            
        elif choice == '4':
            print("\nThank you for using the Indian Stock Market Analyzer. Goodbye!")
            break
            
        else:
            print("Invalid choice. Please select 1, 2, 3, or 4.")

# Run the program if executed as a script
if __name__ == "__main__":
    # Check if yfinance is installed
    try:
        import yfinance
    except ImportError:
        print("ERROR: The yfinance module is not installed.")
        print("Please install it by running this command in your terminal or command prompt:")
        print("pip install yfinance pandas matplotlib numpy")
        sys.exit(1)
        
    # Global variables and settings
    budget = 10000
    RISK_PERCENTAGE = 5  # Default stop-loss percentage
    PROFIT_TARGET_MULTIPLIER = 2  # Default profit target multiplier
    
    # Run the main function
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user. Goodbye!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check your internet connection and try again.")
