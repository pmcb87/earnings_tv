"""tradingview watchlist creator

1. All stocks with earnings this week and the following week.
2. Export in a format suitable for TradingView import.
"""

import requests
import json
import os
from datetime import datetime, timedelta
import yfinance as yf

# Create a session once for reuse
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
})

# Constants
FOLDER_NAME = "earnings_watchlists"
EXCHANGE_CONVERSION = {
    "NYQ": "NYSE",
    "NMS": "NASDAQ",
    "NGM": "NASDAQ",
    "OTC": "OTC",
    "AMEX": "ASE",
}

def get_earnings(week):
    """Fetch earnings data for the given week."""
    day_1, day_2 = week
    url = f"https://api.savvytrader.com/pricing/assets/earnings/calendar?start={day_1}&end={day_2}"
    headers = {
        "accept": "*/*",
        "referer": "https://earningshub.com/",
        "user-agent": session.headers["User-Agent"]
    }
    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching earnings data for {week}: {e}")
        return []

def get_weeks():
    """Calculate the start and end dates for the current and next week."""
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=4)

    # Next week
    start_of_next_week = start_of_week + timedelta(days=7)
    end_of_next_week = start_of_next_week + timedelta(days=4)

    # Create tuples for both weeks
    weeks = [
        (start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d")),
        (start_of_next_week.strftime("%Y-%m-%d"), end_of_next_week.strftime("%Y-%m-%d"))
    ]

    print(f"Weeks: {weeks}")
    return weeks

def process_json(earnings_data):
    """Filter and format earnings data based on market cap."""
    return [
        {"symbol": ticker["symbol"], "earningsDate": ticker["earningsDate"]}
        for ticker in earnings_data if ticker.get("marketCap", 0) > 10000000000
    ]

def get_exchange(list_of_tickers):
    """Fetch exchange information for a list of tickers."""
    formatted_tickers = []
    for ticker in list_of_tickers:
        try:
            stock = yf.Ticker(ticker["symbol"], session=session)
            info = stock.info
            exchange = EXCHANGE_CONVERSION.get(info.get('exchange', 'Unknown'), 'Unknown')
            ticker["exchange"] = exchange
            formatted_tickers.append(ticker)
        except (IndexError, KeyError, ValueError) as e:
            print(f"Failed to fetch info for {ticker['symbol']}: {e}")
        except Exception as e:
            print(f"Unexpected error for {ticker['symbol']}: {e}")
    return formatted_tickers

def process_list(formatted_tickers):
    """Organize tickers by earnings date."""
    earnings_dict = {}
    for entry in formatted_tickers:
        date = entry['earningsDate']
        symbol_exchange = {'symbol': entry['symbol'], 'exchange': entry['exchange']}
        earnings_dict.setdefault(date, []).append(symbol_exchange)
    return earnings_dict

def format_watchlist(earnings_dict):
    """Format the earnings data for TradingView import."""
    formatted_strings = []
    for date, entries in earnings_dict.items():
        date_string = f"###{date}"
        symbols_string = ", ".join(f"{entry['exchange']}:{entry['symbol']}" for entry in entries)
        formatted_strings.append(f"{date_string}, {symbols_string}")
    return ", ".join(formatted_strings)

def save_watchlist(watchlist_formatted, week):
    """Save the formatted watchlist to a text file."""
    folder_path = os.path.join(os.getcwd(), FOLDER_NAME)
    os.makedirs(folder_path, exist_ok=True)
    
    start_date, end_date = week
    file_name = f"Earnings {start_date} to {end_date}.txt"
    file_path = os.path.join(folder_path, file_name)
    
    try:
        with open(file_path, "w") as file:
            file.write(watchlist_formatted)
        print(f"Saved file: {file_path}")
    except IOError as e:
        print(f"Error saving file: {e}")

def main():
    weeks = get_weeks()  # Get current and next week
    for week in weeks:
        earnings = get_earnings(week)
        if not earnings:
            print(f"No earnings data available for {week}.")
            continue

        formatted_tickers = get_exchange(process_json(earnings))
        earnings_dict = process_list(formatted_tickers)
        watchlist_formatted = format_watchlist(earnings_dict)
        save_watchlist(watchlist_formatted, week)

if __name__ == "__main__":
    main()
