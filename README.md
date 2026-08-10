# Insider Trading Signal

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

Selection follows a strict walk-forward split to avoid overfitting. All configurations are evaluated in-sample (2016-2019), and for each signal the window with the highest absolute t-statistic on alpha is selected. Only these selected configurations are then re-evaluated, untouched, on the validation period (2020-2021) and the out-of-sample period (2022-2026). Finally, the Deflated Sharpe Ratio corrects the out-of-sample Sharpe ratio for the fact that eight configurations were tested before a final choice was made, checking whether the observed performance is distinguishable from what chance alone would produce.
## Results
---

### In-sample selection (2016-2019)

<img width="887" height="217" alt="image" src="https://github.com/user-attachments/assets/ebfffaf1-ca7f-4f4c-b2db-7835b8de5f25" />


Full table of all 8 configurations (2 signals × 4 windows: 1, 3, 6, 12 months), with IC-IR, alpha, beta, t-statistics, Sharpe ratio, and number of months.

### Validation (2020-2021)


<img width="847" height="73" alt="image" src="https://github.com/user-attachments/assets/ceee70f3-7515-4b1c-8232-bd17b7907219" />


The two selected configurations re-evaluated untouched on the validation window. We keep buying and selling strategies with the highest information coefficent.

### Out-of-sample (2022-2026)


<img width="847" height="73" alt="image" src="https://github.com/user-attachments/assets/a919ce5d-a2ce-4e64-9d2f-a9486d2103bb" />


The two selected configurations evaluated on data never used in selection.

<img width="1418" height="648" alt="image" src="https://github.com/user-attachments/assets/3584555c-f0cc-4b37-8beb-95be03ed9d9d" />

<img width="1417" height="649" alt="image" src="https://github.com/user-attachments/assets/26f6d03b-8fa8-4c05-9474-5e28af8b72eb" />


### Multiple-testing correction

Deflated Sharpe Ratio (n_trials = 8, accounting for sample length and return skew/kurtosis):
- Opportunistic buy: DSR = 0.31
- Opportunistic sell: DSR = 0.004

### Interpretation

Neither configuration survives the walk-forward test.

In-sample, both look promising: the buy leg (window = 3 months) shows t(alpha) = 2.03 with a low market beta of 0.24, and the short leg on the sell signal (window = 6 months) shows a significant t(alpha) = -2.12 — but with the wrong sign. A short position losing money significantly is the opposite of an informed-selling signal.

Both fade immediately in validation. The buy leg's alpha drops to insignificance (t = 0.09) while its beta rises to 0.64; the short leg is insignificant too (t = -0.27), with a Sharpe of -0.84. Neither retains the in-sample result.

Out-of-sample, the pattern is the same. The buy leg's alpha is negative and insignificant (t = -1.03) while its beta jumps to 1.11 (t = 13.2). The cumulative-return chart is misleading here: the portfolio beats the benchmark, but that gap comes from holding more market risk through a rising market, not from picking better stocks. The short leg's alpha flips marginally positive but stays insignificant (t = 1.12), with beta at -0.98 (t = -28.3) — essentially pure inverse-market exposure with no insider information left.

The IC-IR reversal reinforces this: positive in-sample for both legs (0.45 and 0.35), then negative in both validation and out-of-sample (-0.06 and -0.43, then -0.11 and -0.40). A weak but real effect would fade; an effect that changes direction points to noise. The Deflated Sharpe Ratio confirms it: 0.31 for the buy leg and 0.004 for the short leg, both far below the 0.95 threshold needed to distinguish real performance from what testing eight configurations produces by chance.

The result is a clean negative one: on S&P 500 constituents over 2016-2026, the routine/opportunistic classification does not produce a risk-adjusted edge that survives out-of-sample testing and multiple-testing correction.

## Limitations and extensions

**Limitations:**
- Universe entry/exit dates depend on snapshot frequency, not official index-committee dates.
- Sector labels for delisted tickers are backfilled from current data (yfinance), not their true historical classification.
- Market cap is only as fresh as quarterly shares-outstanding filings, forward-filled in between.
- Insider transaction data is collected from quarterly SEC bulk dumps, not a live feed.
- Restricting to the S&P 500 likely works against finding a signal, since information asymmetry should be weaker in heavily analyst-covered large caps.
- Short-side results ignore borrow costs and stock-lending availability, which would further reduce the short leg's realisable return.

**Extensions:**
- Extend to small/micro caps, where insider information advantage is plausibly stronger.
- Use dollar volume traded instead of a binary indicator, to capture transaction size.
- Use transaction size relative to the insider's total holdings, to capture conviction.
  
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
