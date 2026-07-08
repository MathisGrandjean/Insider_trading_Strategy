# Insider Trading Signal — Replication & Robustness Study (Cohen, Malloy & Pomorski, 2012)

The strategy classifies corporate insiders (Officers and Directors) as "routine" or "opportunistic" based on whether they trade in the same calendar month every year, following Cohen, Malloy and Pomorski (2012): routine insiders trade on a predictable schedule and are assumed to carry little information, while opportunistic insiders trade at irregular times and are assumed more likely to act on private information. For each month, tickers with at least one opportunistic buy (or sell) filing within a given lookback window are grouped into an equal-weighted long portfolio, tested against a value-weighted S&P 500 benchmark. The idea is simple: if opportunistic insider buying (selling) carries information, the resulting portfolio should show a positive (negative) forward return beyond what the benchmark already captures.

## Data

### Universe overview

The point-in-time universe contains 613 unique tickers over 2016-2026, of which 503 are currently active constituents. 190 tickers entered the S&P 500 and 110 exited (delisted or removed) since 2016, giving a realistic sense of the churn a survivorship-bias-free study needs to capture. The universe spans 12 GICS sectors, led by Industrials (93 tickers), Financials (91), and Information Technology (83), with Communication Services (25) and a single unclassified ticker at the low end.

<img width="1210" height="495" alt="fig_universe_size" src="https://github.com/user-attachments/assets/72efc983-914b-4299-b35d-bd8c0427b946" />
Universe size grows steadily from about 405 tickers in early 2016 to close to 500 by 2026, consistent with the gradual index additions net of removals.

<img width="990" height="550" alt="fig_sector_breakdown" src="https://github.com/user-attachments/assets/9e1668bc-08d9-41d5-8a3d-d7c03bd009c7" />

Sector composition, unique tickers per GICS sector over the full period.

### Raw insider transaction activity

After restricting the SEC Form 4 database to tickers that were ever part of the survivor-free universe, the sample contains 362,675 raw transactions from 15,069 unique insiders across 606 tickers, spanning January 2013 to March 2026. Sell transactions dominate heavily (330,544, or roughly 91% of the sample) relative to buy transactions (32,131) — an expected asymmetry, since insiders sell routinely for diversification and liquidity reasons far more often than they buy, which is precisely the motivation behind isolating the *opportunistic* subset rather than treating all transactions as informative.

<img width="1210" height="495" alt="fig_transactions_per_year" src="https://github.com/user-attachments/assets/e8b1405a-7bf2-437f-b333-10792b229ee6" />
Annual transaction counts, split buy/sell. Both series broadly track market activity, with visible peaks in 2021 and 2024-2025.

### Signal coverage

After classification into routine and opportunistic insiders and aggregation to the ticker-month level, the signal panel covers 20,277 ticker-month observations across 593 tickers. The opportunistic sell signal is active in 70.6% of the panel, opportunistic buy in only 6.6% — again reflecting the underlying asymmetry in raw transactions. Routine sell covers 42.2% of the panel, routine buy just 2.0%.

<img width="1210" height="495" alt="fig_signal_activity_over_time" src="https://github.com/user-attachments/assets/7dbdc570-d019-4f4e-b9ae-3cae5074874d" />
Number of tickers with an active opportunistic signal each month; the sell signal (red) fluctuates between roughly 50 and 200 tickers, while the buy signal (green) stays consistently below 30, confirming that opportunistic buying is a comparatively rare, high-conviction event relative to opportunistic selling.

*(Note: the two panels above are described only for the opportunistic signal, since that is the one this study evaluates — see next sections. Routine signals were computed but not carried into the selection protocol.)*

## Results
---

### In-sample selection (2016-2019)

<img width="1056" height="219" alt="image" src="https://github.com/user-attachments/assets/8ca4a999-bd21-4192-80ed-668b03030271" />

Full table of all 8 configurations (2 signals × 4 windows: 1, 3, 6, 12 months), with IC, IC-IR, alpha, beta, t-statistics, Sharpe ratio, and number of months.

### Validation (2020-2021)

<img width="1064" height="75" alt="image" src="https://github.com/user-attachments/assets/6f1e093b-9443-45ae-a87e-7d61929322a0" />

The two selected configurations re-evaluated untouched on the validation window. We keep buying and selling strategies with the highest information coefficent.

### Out-of-sample (2022-2026)

<img width="784" height="75" alt="image" src="https://github.com/user-attachments/assets/fdecbb12-ea81-40a0-98f9-9e3a54d4e69d" />



The two selected configurations evaluated on data never used in selection.


<img width="1855" height="849" alt="image" src="https://github.com/user-attachments/assets/116967ea-724b-41e5-aada-3ccb03dc3304" />

### Multiple-testing correction

Deflated Sharpe Ratio (n_trials = 8, accounting for sample length and return skew/kurtosis):
- Opportunistic sell: DSR = 0.38

## Interpretation

Both selected configurations fail the walk-forward test. In-sample, opportunistic sell (window = 6 months) looks attractive: IC = 0.35, t(alpha) = 2.12, Sharpe = 1.24. In validation the IC flips sign to -0.43 and stays negative out-of-sample (IC-IR = -0.40). Opportunistic buy shows the same pattern (IC = 0.45 in-sample, then -0.36 and -0.45). An immediate sign reversal like this is a stronger warning than a simple decline — it points to an in-sample fit driven by noise rather than a real, if weak, effect.

Out-of-sample, neither alpha is significant (t-alpha of -1.17 and -1.12), while beta is close to 1 for both portfolios (1.00 and 0.98, highly significant) — the strategies mostly replicate market exposure, with no distinguishable insider-specific excess return left over.

The sell signal's in-sample result is also economically backwards: being long stocks with an active opportunistic sell signal produced a positive in-sample return, when informed insider selling should predict underperformance, not outperformance. Read this way, the reversal to negative in validation is closer to the economically expected sign — a further indication that the in-sample fit was not capturing genuine insider information.

## Pipeline :

1. transaction_data_cleaning.py
2. snp500_survivor_free.py
3. fetch_alpaca_data.py
4. signal_builder_insider.py
5. build_portfolio.py

## 1. `transaction_data_cleaning.py` — SEC Form 4 database

This script loads the quarterly SEC insider transaction dumps (`SUBMISSION.tsv`, `REPORTINGOWNER.tsv`, `NONDERIV_TRANS.tsv`) and merges them on the accession number that links a filing to its submitter, its reporting owner, and its individual transaction lines. Only open-market purchases and sales are kept (`trans_code` in {P, S}), and only original Form 4 filings (`document_type == '4'`) are retained, excluding 4/A amendments so that a corrected filing does not create a duplicate transaction. Column names are standardized, all relevant dates are parsed, net shares are computed with the correct sign depending on whether the transaction was an acquisition or a disposition, and exact duplicate rows are dropped.

## 2. `snp500_survivor_free.py` — point-in-time universe

To avoid survivorship bias, the S&P 500 universe is reconstructed dynamically rather than taken from the current constituent list. Historical constituent snapshots going back to 2013 are used to infer, for each ticker, an entry date (its first observed appearance) and an exit date (its last observed appearance, left open-ended if the ticker is still a current member). For tickers that have since been delisted or removed and are therefore missing from the current reference file, identifiers (CIK, company name) are recovered from SEC EDGAR and sector classifications from yfinance; sector labels are then harmonized to standard GICS naming so that both current and historical constituents share a consistent taxonomy. The resulting table, one row per ticker with its entry and exit dates, sector, and CIK, is the basis for building the monthly point-in-time universe used everywhere downstream.

## 3. `fetch_alpaca_data.py` — prices and market capitalization

Monthly close prices for every ticker ever present in the universe are downloaded through the Alpaca API, fully adjusted for splits and dividends. Shares outstanding are retrieved separately from SEC XBRL company facts, specifically the `EntityCommonStockSharesOutstanding` tag reported in 10-K and 10-Q filings, then resampled to month-end and forward-filled between reporting dates since shares outstanding are only disclosed periodically. Market capitalization is obtained as adjusted price times shares outstanding, with the CIK-to-ticker mapping applied so the final table can be merged with the rest of the pipeline on ticker and month.

## 4. `signal_builder_insider.py` — routine vs opportunistic classification

The signal construction is restricted to insiders classified as Officers or Directors, with transactions filtered to valid prices, positive share counts, and correctly cleaned tickers. The core of this script is the routine versus opportunistic classification, built following the Cohen, Malloy and Pomorski methodology: for each insider and each calendar year, the set of calendar months in which that insider filed a transaction is computed for each of the three preceding years. If the intersection of these three monthly sets is non-empty, meaning the insider tends to trade in the same month every year, they are classified as routine for the current year; otherwise they are classified as opportunistic. Insiders with fewer than three years of trading history are excluded rather than classified, since there is not enough information to establish a pattern. Critically, the current year is never used in its own classification, so there is no look-ahead in the labeling itself. Once classified, transactions are aggregated by ticker, month, and signal type (opportunistic buy, opportunistic sell, routine buy, routine sell), producing both a binary indicator (whether at least one transaction of that type occurred in the month) and a log-count intensity for each combination.

## 5. `build_portfolio.py` — portfolio construction and validation protocol

The monthly point-in-time universe is first merged with the signal table, with missing values filled as zero to represent the absence of insider activity, and then merged with forward returns and market capitalization. Forward returns are computed by shifting the return series back by one month, so that the signal observed at month M is evaluated against the return realized over month M+1, not the return that produced the signal itself. The signal itself is built strictly from the filing date at which the transaction became public, rather than the transaction date, so that no information is used before it could actually have been observed by an investor. Market capitalization values below 100 million dollars are treated as missing to exclude illiquid micro-caps from the benchmark.

Each binary indicator is then extended into rolling lookback variants over 1, 3, 6, and 12 months per ticker, where the signal is considered active if at least one relevant insider transaction occurred at any point within that lookback window. Because the merged panel forms a complete monthly grid for every ticker present in the universe, these lookback windows correspond directly to calendar months rather than to a fixed number of irregularly spaced observations.

Portfolios are built as equal-weighted long positions across all tickers with an active signal at a given date, subject to a minimum of five constituents per date to avoid degenerate portfolios built on too few names. The benchmark is a value-weighted portfolio of the full universe, weighted by market capitalization. For every signal and window combination, four metrics are computed. The information coefficient is the cross-sectional Spearman rank correlation between the signal and the forward return at each date, and its stability over time is summarized by the IC information ratio, the mean IC divided by its standard deviation, annualized by the square root of twelve. Alpha and beta are estimated by regressing portfolio returns on benchmark returns with Newey-West standard errors to account for potential autocorrelation in the residuals, with both coefficients and their t-statistics reported. The Sharpe ratio is computed from monthly portfolio returns and annualized. Turnover is computed using the exact two-sided formula, half the sum of absolute weight changes, based on how equal-weight portfolio membership evolves between consecutive rebalancing dates.

The selection protocol follows a strict walk-forward structure. In the in-sample period, from 2016 to 2019, all eight configurations, two signals crossed with four windows, are evaluated, and for each signal the window with the highest IC information ratio is selected. These selected configurations, and only these, are then re-evaluated untouched on the validation period, from 2020 to 2021, and finally on the out-of-sample period, from 2022 to 2026, which was never used in any selection decision. To account for the fact that eight configurations were tested before making a selection, the out-of-sample Sharpe ratio of each selected configuration is assessed using the Deflated Sharpe Ratio of Bailey and López de Prado, which compares the observed Sharpe ratio to the Sharpe ratio that would be expected purely by chance given the number of trials, the sample length, and the skewness and kurtosis of the realized returns. A Deflated Sharpe Ratio below conventional confidence thresholds indicates that the observed performance cannot be distinguished from the noise generated by testing multiple configurations and keeping the best one.

## How to run

Scripts must be run in order (each produces a file consumed by the next):

1. `transaction_data_cleaning.py`
2. `snp500_survivor_free.py`
3. `fetch_alpaca_data.py`
4. `signal_builder_insider.py`
5. `build_portfolio.py`
   
## Environment

- Python 3.11
- Key dependencies: `pandas`, `numpy`, `statsmodels`, `scipy`, `matplotlib`, `alpaca-py`, `python-dotenv`

Install with:
```bash
pip install -r requirements.txt
```
## References

Cohen, L., Malloy, C., & Pomorski, L. (2012). "Decoding Inside Information." *The Journal of Finance*, 67(3), 1009-1043.

Bailey, D. H., & López de Prado, M. (2014). "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality." *Journal of Portfolio Management*, 40(5), 94-107.

## Author

Mathis Grandjean — MSc in Financial Engineering, EDHEC Business School

## License

This project is for educational and portfolio purposes.
