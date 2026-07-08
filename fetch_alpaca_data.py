# -*- coding: utf-8 -*-
"""
Created on Sun May 24 09:11:46 2026

@author: Mathis
"""

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data import TimeFrame
import pandas as pd
import os
from dotenv import load_dotenv
from config import BASE_DIR, DATA_DIR

load_dotenv(dotenv_path=BASE_DIR / ".env.txt")

API_KEY = os.getenv('ALPACA_API_KEY')
API_SECRET = os.getenv('ALPACA_API_SECRET')

def load_sp500_universe(path):
    df = pd.read_csv(path,sep=',')
    
    df = df[['ticker','name','sector','cik']]
    return df


def fetch_sp500_data(tickers, api_key, api_secret, start, end):
    
    client = StockHistoricalDataClient(api_key, api_secret)
    
    request = StockBarsRequest(
        symbol_or_symbols=tickers,
        timeframe=TimeFrame.Month,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        adjustment='all' 
    )
    
    bars = client.get_stock_bars(request).df
    prices = bars['close'].unstack(level=0)
    prices.index = pd.to_datetime(prices.index).to_period('M').to_timestamp('M')
    prices.index.name = 'date'
    return prices


data = load_sp500_universe(DATA_DIR / "constituents_snp_500_survivor_free.csv")
tickers = data['ticker'].tolist()
prices = fetch_sp500_data(tickers,api_key= API_KEY,
                          api_secret=API_SECRET,
                          start="2016-01-01", 
                          end="2026-04-30")

prices.to_parquet(DATA_DIR / 'prices_constituents_snp_500.parquet')

# %%

import pandas as pd 
import requests 
import time

snp = pd.read_csv(DATA_DIR / "constituents_snp_500_survivor_free.csv", sep=',')

cik = snp['cik'].to_list()

headers = {'User-Agent': 'your_name grmathis21@gmail.com'}  # obligatoire SEC

def get_shares_outstanding(cik):
    cik_str = str(cik).zfill(10)
    url = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_str}.json'
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        
        facts = data.get('facts', {}).get('dei', {})  # <- dei pas us-gaap
        shares = facts.get('EntityCommonStockSharesOutstanding', {}).get('units', {}).get('shares', [])
        
        if not shares:
            return None
        
        df = pd.DataFrame(shares)  # chaque dict devient une ligne
        df = df[df['form'].isin(['10-K', '10-Q'])]
        df['end'] = pd.to_datetime(df['end'])
        df = df.sort_values('end')[['end', 'val', 'form']]
        df['cik'] = cik
        return df

    except Exception as e:
        return None
all_shares = []
for c in cik:
    df = get_shares_outstanding(c)
    if df is not None:
        all_shares.append(df)
    time.sleep(0.12)

# Concatener tous les résultats
shares_df = pd.concat(all_shares, ignore_index=True)

# Pivot table
pivot = shares_df.pivot_table(index='end', columns='cik', values='val', aggfunc='last')
pivot.columns = pivot.columns.astype(str)
pivot_monthly = (
    pivot
    .resample('ME')
    .apply(lambda x: x.dropna().iloc[-1] if x.dropna().shape[0] > 0 else float('nan'))
)

pivot_monthly.to_parquet(DATA_DIR / 'outstanding_share_snp_500.parquet')

# %%

prices = pd.read_parquet(DATA_DIR / 'prices_constituents_snp_500.parquet')
shares = pd.read_parquet(DATA_DIR / 'outstanding_share_snp_500.parquet')
universe = pd.read_excel(DATA_DIR / 'constituents_snp_500_survivor_free.xlsx')

# CIK → ticker mapping
universe['cik'] = universe['cik'].astype(str).str.zfill(10)
cik_to_ticker = universe.set_index('cik')['ticker'].to_dict()

shares = shares.ffill()
shares.columns = shares.columns.astype(str).str.zfill(10)
shares = shares.rename(columns=cik_to_ticker)

# Aligner les index sur fin de mois
prices.index = pd.to_datetime(prices.index).to_period('M').to_timestamp('M')
shares.index = pd.to_datetime(shares.index).to_period('M').to_timestamp('M')

# Market cap = price × shares outstanding
common_tickers = prices.columns.intersection(shares.columns)
market_cap = prices[common_tickers] * shares[common_tickers]

market_cap_long = (
    market_cap
    .stack()
    .reset_index()
)
market_cap_long.columns = ['trans_date', 'ticker', 'market_cap']
market_cap_long = market_cap_long[
    (market_cap_long['trans_date'] >= '2000-01-01') &
    (market_cap_long['market_cap'] > 0)
]

market_cap_long.to_parquet(DATA_DIR / 'market_cap.parquet')

shares = shares.ffill()

# 2. Stack vers long (garde maintenant les valeurs propagées)
shares_long = shares.stack().reset_index()
shares_long.columns = ['month', 'ticker', 'shares_outstanding']

# 3. S'assurer que month est bien en datetime (probablement déjà le cas vu ton index)
shares_long['month'] = pd.to_datetime(shares_long['month'])
shares_long.to_parquet(DATA_DIR / 'outstanding_shares_clean.parquet')