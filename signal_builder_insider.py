# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import re

from config import DATA_DIR
 
df_insider = pd.read_parquet(DATA_DIR / 'insider_trading_database.parquet')

#only keeping member of the company
df_insider = df_insider[df_insider["relationship"].isin(['Officer','Director'])]

df_insider['year']         = df_insider['filing_date'].dt.year
df_insider['month_of_year'] = df_insider['filing_date'].dt.month


df_insider = df_insider[
    (df_insider['filing_date'] >= '2000-01-01') &
    (df_insider['filing_date'] <= pd.Timestamp.today()) &
    (df_insider['price'] > 0) &
    (df_insider['price'] < 100_000) &
    (df_insider['shares'] > 0) &
    (df_insider['trans_code'].isin(['P', 'S']))
].copy()


# cleaning of tickers
def clean_ticker(ticker):
    ticker = str(ticker).strip()
    match_paren = re.match(r'^\(([A-Z]+)\)$', ticker)
    if match_paren:
        return match_paren.group(1)
    match_exchange = re.match(r'^\(?(?:NYSE|NASDAQ|AMEX):([A-Z]+)\)?$', ticker)
    if match_exchange:
        return match_exchange.group(1)
    if ticker.isdigit():
        return None
    if re.match(r'^[A-Z]{1,5}(\.[A-Z])?$', ticker):
        return ticker
    return None

df_insider['ticker'] = df_insider['ticker'].apply(clean_ticker)

df_insider = df_insider[
    df_insider['ticker'].notna() &
    (df_insider['ticker'] != 'NONE') &
    (df_insider['ticker'] != '')
].copy()

df_classify = df_insider.drop_duplicates(subset=['owner_cik','accession_number'])

owner_months = (
    df_classify
    .groupby(['owner_cik', 'year'])['month_of_year']
    .apply(frozenset)
    .reset_index()
    .rename(columns={'month_of_year': 'months_filed'})
    .sort_values(['owner_cik', 'year'])
    .reset_index(drop=True)
)
def classify_owners(owner_months: pd.DataFrame) -> pd.DataFrame:

    results = []
 
    for owner_cik, group in owner_months.groupby('owner_cik'):
        group          = group.sort_values('year')
        years          = group['year'].values
        months_by_year = dict(zip(group['year'], group['months_filed']))
 
        for year in years:
            prev_years = [y for y in years if y < year]
 
            # if less than 3 years history, insufficient_history
            if len(prev_years) < 3:
                results.append({
                    'owner_cik'      : owner_cik,
                    'year'           : year,
                    'classification' : 'insufficient_history',
                    'recurring_months': [],
                })
                continue
 
            prev_3 = prev_years[-3:]
 
            recurring = months_by_year[prev_3[0]]
            for y in prev_3[1:]:
                recurring = recurring & months_by_year[y]
 
            results.append({
                'owner_cik'       : owner_cik,
                'year'            : year,
                'classification'  : 'routine' if recurring else 'opportunistic',
                'recurring_months': sorted(recurring),
            })
 
    return pd.DataFrame(results)
 
df_classif = classify_owners(owner_months)
df_insider = df_insider.merge(
    df_classif[['owner_cik', 'year', 'classification']],
    on=['owner_cik', 'year'],
    how='left'
)
 
df_insider['classification'] = df_insider['classification'].fillna('insufficient_history')
df_insider = df_insider[df_insider['classification']!='insufficient_history']

df_insider['month'] = pd.to_datetime(df_insider['filing_date']).dt.to_period('M').dt.to_timestamp('M')

df_insider['signal_key'] = (
    df_insider['classification'].str[:3] + '_' +
    df_insider['trans_code'].map({'P': 'buy', 'S': 'sell'})
)

universe = pd.read_excel(DATA_DIR / 'constituents_snp_500_survivor_free.xlsx')

ticker_universe = universe['ticker'].tolist()

df_insider = df_insider[df_insider['ticker'].isin(ticker_universe)]

agg = (
    df_insider
    .groupby(['ticker', 'month', 'signal_key'])
    .agg(n_transactions=('accession_number', 'count'))
    .reset_index()
)

wide = agg.pivot_table(
    index=['ticker', 'month'],
    columns='signal_key',
    values='n_transactions',
    aggfunc='sum',
    fill_value=0
).reset_index()
wide.columns.name = None

for col in ['opp_buy', 'opp_sell', 'rou_buy', 'rou_sell']:
    if col not in wide.columns:
        wide[col] = 0

# Signaux
wide['ind_opp_buy']    = (wide['opp_buy']  > 0).astype(int)
wide['ind_opp_sell']   = (wide['opp_sell'] > 0).astype(int)
wide['ind_rou_buy']    = (wide['rou_buy']  > 0).astype(int)
wide['ind_rou_sell']   = (wide['rou_sell'] > 0).astype(int)

wide.to_parquet(DATA_DIR / 'signal_insider_wide.parquet')