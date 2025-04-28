import json
import yahoo_fin.stock_info as si

# Load target allocation
with open('target_alloc.json', 'r') as f:
    target_alloc = json.load(f)

re_tickers = []
re_ratio = 0.0

for ticker, alloc in target_alloc.items():
    try:
        info = si.get_quote_table(ticker)
        # Combine all string values for easier searching
        info_str = ' '.join(str(v).lower() for v in info.values())
        if 'reit' in info_str or 'real estate' in info_str:
            re_tickers.append(ticker)
            re_ratio += alloc
    except Exception as e:
        print(f"Warning: Could not fetch info for {ticker}: {e}")

print(f"RE/REIT tickers: {re_tickers}")
print(f"RE ratio: {re_ratio:.2%}")
