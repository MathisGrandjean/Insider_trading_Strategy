import statsmodels.api as sm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, norm

from config import DATA_DIR, RESULTS_DIR
 
df_signal = pd.read_parquet(DATA_DIR / 'signal_insider_wide.parquet')
prices = pd.read_parquet(DATA_DIR / 'prices_constituents_snp_500.parquet')
universe = pd.read_excel(DATA_DIR / 'constituents_snp_500_survivor_free.xlsx')
market_cap = pd.read_parquet(DATA_DIR / 'market_cap.parquet')

# cleaning of the universe
universe['date_in'] = pd.to_datetime(universe['date_in'])
universe['date_out'] = pd.to_datetime(universe['date_out'])
universe['ticker'] = universe['ticker'].str.upper().str.strip()
universe['sector'] = universe['sector'].fillna('Unknown')

# point in time universe
dates = pd.date_range('2016-01-31', '2026-03-31', freq='ME')
rows = []
for _, row in universe.iterrows():
    date_in = row['date_in']
    date_out = row['date_out'] if pd.notna(row['date_out']) else pd.Timestamp('2099-12-31')
    for d in dates:
        if date_in <= d <= date_out:
            rows.append({'filing_date': d, 'ticker': row['ticker'], 'sector': row['sector']})
df_universe = pd.DataFrame(rows)

# cleaning of the signal
df_signal['filing_date'] = pd.to_datetime(df_signal['month']).dt.to_period('M').dt.to_timestamp('M') \
    if 'month' in df_signal.columns else pd.to_datetime(df_signal['filing_date'])
df_signal['ticker'] = df_signal['ticker'].str.upper().str.strip()

signal_cols = ['ticker', 'filing_date', 'ind_opp_buy', 'ind_opp_sell',
               'ind_rou_buy', 'ind_rou_sell',
               'log_n_opp_buy', 'log_n_opp_sell',
               'opp_sell', 'opp_buy']

signal_cols = [c for c in signal_cols if c in df_signal.columns]
df_signal = df_signal[signal_cols]

# merge signal + universe
df_full = df_universe.merge(df_signal, on=['ticker', 'filing_date'], how='left')
for col in signal_cols[2:]:
    df_full[col] = df_full[col].fillna(0)

# forward return
prices.index = pd.to_datetime(prices.index).to_period('M').to_timestamp('M')
returns_raw = prices.pct_change()
returns_fwd = returns_raw.shift(-1)
returns_long = returns_fwd.stack().reset_index()
returns_long.columns = ['filing_date', 'ticker', 'fwd_return']
returns_long['ticker'] = returns_long['ticker'].str.upper().str.strip()
df_full = df_full.merge(returns_long, on=['ticker', 'filing_date'], how='left')

# market cap benchmark
market_cap.columns = market_cap.columns.str.strip()
market_cap['trans_date'] = pd.to_datetime(market_cap['trans_date']).dt.to_period('M').dt.to_timestamp('M')
market_cap['ticker'] = market_cap['ticker'].astype(str).str.upper().str.strip()
market_cap = market_cap[['trans_date', 'ticker', 'market_cap']].rename(columns={'trans_date': 'filing_date'})
market_cap = market_cap.drop_duplicates(subset=['filing_date', 'ticker'])
market_cap.loc[market_cap['market_cap'] < 100_000_000, 'market_cap'] = np.nan
market_cap = market_cap.sort_values(['ticker', 'filing_date'])
market_cap = market_cap[['filing_date', 'ticker', 'market_cap']]

df_full = df_full.merge(market_cap, on=['ticker', 'filing_date'], how='left')
df_full = df_full.loc[:, ~df_full.columns.duplicated()]

#returns of the market cap benchmark
def vw_benchmark(df):
    d = df.dropna(subset=['fwd_return', 'market_cap']).copy()
    d['w_ret'] = d['fwd_return'] * d['market_cap']
    return d.groupby('filing_date')['w_ret'].sum() / d.groupby('filing_date')['market_cap'].sum()

benchmark = vw_benchmark(df_full)

#a portfolio must contain at least 5 stocks
MIN_N = 5

#compute an ols with Y = portfolio strategy return , X = market return 
def ols_vs_benchmark(port_ret, bench_ret, label, hac_lags=3):
    common = port_ret.dropna().index.intersection(bench_ret.dropna().index)

    y = port_ret.loc[common].values
    X = sm.add_constant(bench_ret.loc[common].values)
    model = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': hac_lags})
    return model

#compute information coefficient : correlation between signal and return
def compute_ic(df, signal_col, return_col='fwd_return', min_obs=20):
    ic_rows = []
    for date, g in df.groupby('filing_date'):
        g = g.dropna(subset=[signal_col, return_col])
        ic, _ = spearmanr(g[signal_col], g[return_col])
        ic_rows.append({'filing_date': date, 'ic': ic})
    return pd.DataFrame(ic_rows).set_index('filing_date')

#caculation of the deflated sharpe ratio of each lockback window
def deflated_sharpe_ratio(observed_sharpe_ann, n_trials, n_obs, skew=0, kurt=3):
    sr_m = observed_sharpe_ann / np.sqrt(12)
    sr_std = np.sqrt((1 - skew*sr_m + (kurt-1)/4*sr_m**2) / (n_obs - 1))
    expected_max_sr = sr_std * ((1-np.euler_gamma)*norm.ppf(1-1/n_trials)
                                  + np.euler_gamma*norm.ppf(1-1/(n_trials*np.e)))
    return norm.cdf((sr_m - expected_max_sr) / sr_std)

#calculate the return of portfolio EW with buying signal
def build_port_return(df, indicator_col, period_mask=None, min_n=MIN_N):
    sub = df if period_mask is None else df[period_mask]
    sub = sub.dropna(subset=[indicator_col, 'fwd_return'])
    n_series = sub[sub[indicator_col] == 1].groupby('filing_date').size()
    valid = n_series[n_series >= min_n].index
    return sub[sub[indicator_col] == 1].groupby('filing_date')['fwd_return'].mean().reindex(valid).dropna()

#evaluate each window of the lookback period and calculate IC and ols compare to return and shapre ratio
def evaluate_window(df, indicator_col, period_mask, min_n=MIN_N):
    #for each strategy with a different windown we compte the IC
    sub = df[period_mask].dropna(subset=[indicator_col, 'fwd_return'])
    ic_df = compute_ic(sub, indicator_col)
    ic_ir_val = ic_df['ic'].mean()/ic_df['ic'].std()*np.sqrt(12) 

    n_series = sub[sub[indicator_col]==1].groupby('filing_date').size()
    valid = n_series[n_series >= min_n].index
    
    #we calcule the return of the strategy, of the benchmark and the sharpe ratio
    ret = sub[sub[indicator_col]==1].groupby('filing_date')['fwd_return'].mean().reindex(valid).dropna()
    sharpe = ret.mean()/ret.std()*np.sqrt(12)
    bench_sub = benchmark.reindex(ret.index).dropna()
    common_idx = ret.index.intersection(bench_sub.index)
    
    #we perform our ols between the strategy portfolio and the market porfolio
    t_alpha = np.nan
    alpha, beta, t_beta = np.nan, np.nan, np.nan 

    m = ols_vs_benchmark(ret.loc[common_idx], bench_sub.loc[common_idx], '')
    if m is not None:
        t_alpha = m.tvalues[0]
        alpha, beta = m.params       
        t_beta = m.tvalues[1]         
    return {'ic_ir': ic_ir_val, 't_alpha': t_alpha, 'sharpe': sharpe, 'n_months': len(ret),
            'alpha': alpha, 'beta': beta, 't_beta': t_beta}

#building a moving indiactor based on the windwow
def build_rolling_indicator(df, base_col, window):
    d = df.sort_values(['ticker', 'filing_date']).copy()
    d[f'{base_col}_w{window}'] = d.groupby('ticker')[base_col].transform(
        lambda x: x.rolling(window, min_periods=1).max())
    return d

def compute_weight_turnover(df, indicator_col):
    membership = (df[df[indicator_col] == 1]
                  .groupby('filing_date')['ticker'].apply(set).sort_index())
    dates_list = membership.index.tolist()
    rows = []
    for i in range(1, len(dates_list)):
        prev_set, curr_set = membership.iloc[i-1], membership.iloc[i]
        n_prev, n_curr = len(prev_set), len(curr_set)
        if n_prev == 0 or n_curr == 0:
            continue
        w_prev, w_curr = 1/n_prev, 1/n_curr
        delta = sum(abs((w_curr if t in curr_set else 0) - (w_prev if t in prev_set else 0))
                    for t in prev_set | curr_set)
        rows.append({'filing_date': dates_list[i], 'turnover': 0.5 * delta})
    return pd.DataFrame(rows).set_index('filing_date')

IS_END, VAL_END = pd.Timestamp('2019-12-31'), pd.Timestamp('2021-12-31')
WINDOWS = [1, 3, 6, 12]

#for each window we adapte our signal
for w in WINDOWS:
    df_full = build_rolling_indicator(df_full, 'ind_opp_buy', w)
    df_full = build_rolling_indicator(df_full, 'ind_opp_sell', w)

#create masks between In sample, Validation and Out of sample period
is_mask  = df_full['filing_date'] <= IS_END
val_mask = (df_full['filing_date'] > IS_END) & (df_full['filing_date'] <= VAL_END)
oos_mask = df_full['filing_date'] > VAL_END

# for each trial in our strategy we evaluate the window
is_results = []
for sig in ['ind_opp_buy', 'ind_opp_sell']:
    for w in WINDOWS:
        r = evaluate_window(df_full, f'{sig}_w{w}', is_mask)
        r.update({'signal': sig, 'window': w})
        is_results.append(r)

df_is_results = pd.DataFrame(is_results)
df_is_results.to_excel(RESULTS_DIR / "results_IS.xlsx")

#we consider the best window if it has the best information coefficient for buying and selling strategy so we keep two strategies
best_per_signal = df_is_results.loc[df_is_results.groupby('signal')['ic_ir'].idxmax()]

#we evaluate our strategy in the validation period for the best buying and sellin strategy
val_results = []
for _, row in best_per_signal.iterrows():
    col = f"{row['signal']}_w{int(row['window'])}"
    r = evaluate_window(df_full, col, val_mask)
    r.update({'signal': row['signal'], 'window': row['window']})
    val_results.append(r)

df_val_results = pd.DataFrame(val_results)
df_val_results.to_excel(RESULTS_DIR / "results_validation.xlsx")

#same for the oos period
oos_results = []
for _, row in best_per_signal.iterrows():
    col = f"{row['signal']}_w{int(row['window'])}"
    r = evaluate_window(df_full, col, oos_mask)
    r.update({'signal': row['signal'], 'window': row['window']})
    oos_results.append(r)

df_oos_results = pd.DataFrame(oos_results)
df_oos_results.to_excel(RESULTS_DIR / "results_OOS.xlsx")

#we compte our deflated share ratio for the best strategy tested out of sample
dsr_results = {}
for _, row in df_oos_results.iterrows():
    if pd.notna(row['sharpe']) and row['n_months'] > 10:
        dsr = deflated_sharpe_ratio(row['sharpe'], n_trials=len(WINDOWS)*2, n_obs=row['n_months'])
        dsr_results[row['signal']] = dsr

best_signal_row = df_oos_results.loc[df_oos_results['sharpe'].idxmax()]
best_col = f"{best_signal_row['signal']}_w{int(best_signal_row['window'])}"
best_dsr = dsr_results.get(best_signal_row['signal'], np.nan)

#we compute the turnover cost and portfolio return of our best strategy
turnover_best = compute_weight_turnover(df_full[oos_mask], best_col)
port_ret_best_oos = build_port_return(df_full, best_col, period_mask=oos_mask)

print(f"Turnover moyen (OOS) : {turnover_best['turnover'].mean():.1%}/mois")

#print a graphique that compare the return of the best strategy and the benchmark
for _, row in best_per_signal.iterrows():
    col = f"{row['signal']}_w{int(row['window'])}"
    port_ret_full = build_port_return(df_full, col)
    common_full = port_ret_full.index.intersection(benchmark.dropna().index)

    oos_row = df_oos_results[(df_oos_results['signal']==row['signal']) &
                               (df_oos_results['window']==row['window'])].iloc[0]
    t_oos = oos_row['t_alpha']

    cum_port  = (1 + port_ret_full.loc[common_full]).cumprod()
    cum_bench = (1 + benchmark.loc[common_full]).cumprod()

    fig, ax = plt.subplots(figsize=(13, 6))
    cum_port.plot(ax=ax, label=f"{row['signal']} w={int(row['window'])}m", color='blue', linewidth=1.8)
    cum_bench.plot(ax=ax, label='Benchmark VW', color='grey', linewidth=1.8)
    ax.axvspan(cum_port.index.min(), IS_END, alpha=0.08, color='red', label='IS (sélection)')
    ax.axhline(1, color='black', linestyle='--', linewidth=0.5)
    ax.set_title(f"{row['signal']} (w={int(row['window'])}m) return vs market porfolio return")
    ax.legend()
    plt.tight_layout()
    plt.show()
    
