# -*- coding: utf-8 -*-
import pandas as pd
import requests
import yfinance as yf
import time
from config import DATA_DIR
 

# 1. Chargement
df = pd.read_csv(DATA_DIR / "historical_constituents_snp_500.csv")
current = pd.read_csv(DATA_DIR / "constituents_snp_500.csv")
df['date'] = pd.to_datetime(df['date'])
df = df[df['date'] >= '2013-01-01']

# 2. Dates d'entrée / sortie par ticker
rows = []
for _, row in df.iterrows():
    for t in row['tickers'].split(','):
        rows.append({'ticker': t.strip().upper(), 'date': row['date']})

df_long = pd.DataFrame(rows)
dates = df_long.groupby('ticker')['date'].agg(date_in='min', date_out='max').reset_index()

current_tickers = set(current['Symbol'].str.upper())
historical_tickers = set(dates['ticker'])
missing_tickers = historical_tickers - current_tickers

headers = {
    "User-Agent": "mathis.grandjean@edhec.com",
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov"
}
edgar = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers).json()
edgar_df = pd.DataFrame.from_dict(edgar, orient='index')
edgar_df['ticker'] = edgar_df['ticker'].str.upper()

name_map = {}
cik_map = {}
for ticker in missing_tickers:
    match = edgar_df[edgar_df['ticker'] == ticker]
    if not match.empty:
        cik_map[ticker] = str(match['cik_str'].values[0]).zfill(10)
        name_map[ticker] = match['title'].values[0]

# 5. Sector via yfinance
sector_map = {}
for i, ticker in enumerate(list(missing_tickers)):
    try:
        info = yf.Ticker(ticker).info
        sector_map[ticker] = info.get('sector', None)
    except:
        sector_map[ticker] = None
    if i % 50 == 0:
        time.sleep(1)

# 6. Construire ref pour les manquants
df_missing = pd.DataFrame({
    'ticker': list(missing_tickers),
    'name': [name_map.get(t) for t in missing_tickers],
    'cik': [cik_map.get(t) for t in missing_tickers],
    'sector': [sector_map.get(t) for t in missing_tickers]
})

# 7. Construire ref pour current
df_current_ref = pd.DataFrame({
    'ticker': current['Symbol'].str.upper(),
    'name': current['Security'],
    'cik': current['CIK'].astype(str).str.zfill(10),
    'sector': current['GICS Sector']
})
# 8. Concatener
df_ref = pd.concat([df_current_ref, df_missing], ignore_index=True)

# 9. Merger avec dates entrée/sortie
df_final = df_ref.merge(dates, on='ticker', how='left')

# date_out = NaT si encore dans le current (toujours présent)
df_final.loc[df_final['ticker'].isin(current_tickers), 'date_out'] = pd.NaT
sector_mapping = {
    'Financial Services': 'Financials',
    'Consumer Defensive': 'Consumer Staples',
    'Technology': 'Information Technology',
    'Basic Materials': 'Materials',
    'Healthcare': 'Health Care',
    'Consumer Cyclical': 'Consumer Discretionary'
}

df_final['sector'] = df_final['sector'].replace(sector_mapping)
df_final = df_final.dropna(subset='cik')

df_final.to_csv(DATA_DIR / "constituents_snp_500_survivor_free.csv", index=False)