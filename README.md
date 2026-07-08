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

## Methodology

Insiders are classified as routine or opportunistic based on their trading history: for each insider and each year, the set of calendar months in which they filed a transaction is compared against the same set for each of the three preceding years. If that pattern repeats (the insider tends to trade in the same month every year), they are classified as routine for that year; otherwise, opportunistic. Insiders with fewer than three years of history are excluded rather than classified, and only past years are used, so there is no look-ahead in the labeling itself.

Each classification is turned into a monthly ticker-level signal: for a given lookback window (1, 3, 6, or 12 months), a ticker's signal is active if at least one opportunistic buy (or sell) transaction occurred within that window. Because the underlying panel is a complete monthly grid for every ticker in the universe, these windows correspond directly to calendar months.

Each month, all tickers with an active signal are grouped into an equal-weighted long portfolio, with a minimum of five constituents required to avoid degenerate portfolios. This portfolio is compared against a value-weighted benchmark built from the same universe. Four metrics are computed for every signal and window combination: the information coefficient (cross-sectional Spearman correlation between the signal and the next month's return), its stability over time (IC information ratio), the portfolio's alpha and beta versus the benchmark (via an OLS regression with Newey-West standard errors), and the annualized Sharpe ratio.

Selection follows a strict walk-forward split to avoid overfitting. All configurations are evaluated in-sample (2016-2019), and for each signal the window with the highest IC information ratio is selected. Only these selected configurations are then re-evaluated, untouched, on the validation period (2020-2021) and the out-of-sample period (2022-2026). Finally, the Deflated Sharpe Ratio corrects the out-of-sample Sharpe ratio for the fact that eight configurations were tested before a final choice was made, checking whether the observed performance is distinguishable from what chance alone would produce.
## Results
---

### In-sample selection (2016-2019)

<img width="1056" height="219" alt="image" src="https://github.com/user-attachments/assets/ecf1055c-a749-42ae-98e2-f8c342420e06" />


Full table of all 8 configurations (2 signals × 4 windows: 1, 3, 6, 12 months), with IC, IC-IR, alpha, beta, t-statistics, Sharpe ratio, and number of months.

### Validation (2020-2021)

<img width="1064" height="75" alt="image" src="https://github.com/user-attachments/assets/7be3b447-06a6-433b-8c4f-b645ddd719fc" />


The two selected configurations re-evaluated untouched on the validation window. We keep buying and selling strategies with the highest information coefficent.

### Out-of-sample (2022-2026)

<img width="784" height="75" alt="image" src="https://github.com/user-attachments/assets/318e8100-f432-4610-aec7-38aef83ef1bf" />


The two selected configurations evaluated on data never used in selection.


<img width="1855" height="849" alt="image" src="https://github.com/user-attachments/assets/116967ea-724b-41e5-aada-3ccb03dc3304" />

### Multiple-testing correction

Deflated Sharpe Ratio (n_trials = 8, accounting for sample length and return skew/kurtosis):
- Opportunistic sell: DSR = 0.38

### Interpretation

Both selected configurations fail the walk-forward test. In-sample, opportunistic sell (window = 6 months) looks attractive: IC = 0.35, t(alpha) = 2.12, Sharpe = 1.24. In validation the IC flips sign to -0.43 and stays negative out-of-sample (IC-IR = -0.40). Opportunistic buy shows the same pattern (IC = 0.45 in-sample, then -0.36 and -0.45). An immediate sign reversal like this is a stronger warning than a simple decline — it points to an in-sample fit driven by noise rather than a real, if weak, effect.

Out-of-sample, neither alpha is significant (t-alpha of -1.17 and -1.12), while beta is close to 1 for both portfolios (1.00 and 0.98, highly significant) — the strategies mostly replicate market exposure, with no distinguishable insider-specific excess return left over.

The sell signal's in-sample result is also economically backwards: being long stocks with an active opportunistic sell signal produced a positive in-sample return, when informed insider selling should predict underperformance, not outperformance. Read this way, the reversal to negative in validation is closer to the economically expected sign — a further indication that the in-sample fit was not capturing genuine insider information.
## Limitations and extensions

**Limitations:**
- Universe entry/exit dates depend on snapshot frequency, not official index-committee dates.
- Sector labels for delisted tickers are backfilled from current data (yfinance), not their true historical classification.
- Market cap is only as fresh as quarterly shares-outstanding filings, forward-filled in between.
- Insider transaction data is collected from quarterly SEC bulk dumps, not a live feed.
- Restricting to the S&P 500 likely works against finding a signal, since information asymmetry should be weaker in heavily analyst-covered large caps.

**Extensions:**
- Extend to small/micro caps, where insider information advantage is plausibly stronger.
- Use dollar volume traded instead of a binary indicator, to capture transaction size.
- Use transaction size relative to the insider's total holdings, to capture conviction.
- Combine classification, intensity, dollar size, and conviction into a single composite score.
  
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
