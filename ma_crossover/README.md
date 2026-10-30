# Moving Average Crossover (Golden Cross / Death Cross)

> **Category**: Trend-Following  
> **Typical Asset Class**: Equity indices, ETFs, large-cap stocks, crypto  
> **Suggested Timeframe**: Daily (1d)  

---

## 1. Overview
The Moving Average Crossover is one of the oldest and most widely followed trend-following systems. It compares a **fast** moving average, which tracks recent prices, with a **slow** moving average, which tracks the longer-term trend.

When the fast average rises above the slow one, recent prices are outpacing the longer-term trend and the strategy goes **long**. When the fast average falls back below, the trend is considered broken and the strategy moves to **cash**.

With the classic **50 / 200-day** settings, these events have well-known names: the **Golden Cross** (bullish) and the **Death Cross** (bearish). Financial media and institutional desks regularly report on them.

---

## 2. Theoretical Rationale
Trend-following relies on **momentum persistence**, the tendency of assets that have been rising to keep rising for a while. Several behavioural and structural effects drive this:
- **Under-reaction**: investors absorb new information slowly, so prices adjust gradually instead of all at once.
- **Herding**: rising prices draw in more buyers, which extends the move.
- **Risk management flows**: many funds cut exposure as prices fall and add exposure as they rise.

The strategy doesn't try to call tops or bottoms. It **gives up the first and last part of each move** in exchange for staying in during the middle of large trends and stepping aside during long bear markets.

---

## 3. Indicators & Calculations

| Indicator | Default Parameter | Formula / Description |
|-----------|-------------------|-----------------------|
| `Fast SMA` | `50` | Simple average of the last 50 closing prices |
| `Slow SMA` | `200` | Simple average of the last 200 closing prices |

```
SMA(n)_t = (close_t + close_{t-1} + ... + close_{t-n+1}) / n
```

Prices are split- and dividend-adjusted (`auto_adjust=True`). The first 200 bars are used only to warm up the indicators and are excluded from signals and the backtest.

---

## 4. Strategy Rules

### Entry Rules (Buy / Long)
1. **Golden Cross**: the 50-day SMA closes **above** the 200-day SMA after being at or below it on the previous bar.
2. The signal is confirmed at the bar's close. Place the trade at the **next session's open**. The backtest fills at that price.

### Exit Rules (Sell / Close)
1. **Death Cross**: the 50-day SMA closes **at or below** the 200-day SMA.
2. No fixed stop-loss or take-profit. The opposite crossover is the only exit.

> [!NOTE]
> The strategy is **state-based**: it is long whenever Fast SMA > Slow SMA. If the fast average is already above the slow one on the first valid bar of the data, the strategy starts in a long position without a fresh crossover.

---

## 5. Market Regime & Performance Profile

### When It Works Best
- Long, sustained bull or bear markets, such as multi-year equity rallies or extended sell-offs.
- Avoiding deep drawdowns. The Death Cross has historically moved traders to cash during major index bear markets.
- Assets with strong, persistent trends.

### When It Fails (Known Risks & Pitfalls)
- **Choppy or sideways markets**: the averages repeatedly cross back and forth, producing a run of small losing trades ("whipsaws").
- **Lag**: a 200-day average reacts slowly. Entries come well after a bottom and exits well after a top, so V-shaped recoveries are often partly missed.
- **Often lags buy-and-hold in steady bull markets**: time spent in cash after a Death Cross can mean missing sharp rebounds.
- **Few trades**: with 50 / 200 there may be only a handful of signals over 5 years, so backtest statistics such as win rate rest on a very small sample.
- Commissions, slippage, and taxes are **not** modelled.

### Backtest Results (Snapshot)
> **SPY, daily bars, default settings (50 / 200 SMA)**. Data ends at the close on **2026-10-26**. The test window starts on **2022-08-12**, after 200 bars of indicator warm-up out of the 5-year download. Re-running `strategy.py` uses the latest data, so numbers will change over time.

| Metric | Value |
|--------|-------|
| Period tested | 2022-08-12 → 2026-10-26 (1,055 bars) |
| Total trades | 2 (1 closed, 1 still open) |
| Win rate | 100.0% |
| Strategy total return | **+69.39%** |
| Buy & hold benchmark | **+89.52%** |
| Max drawdown | -18.76% |
| Time in market | 84.5% |
| $10,000 would have become | $16,939.26 |

**Trade log** (fills at the open of the session after each signal)

| # | Entry date | Entry price | Exit date | Exit price | Return | Status |
|---|------------|-------------|-----------|------------|--------|--------|
| 1 | 2023-01-27 | $385.02 | 2025-04-17 | $519.03 | +34.81% | Closed (Death Cross) |
| 2 | 2025-06-30 | $609.10 | 2026-10-26 | $765.37 | +25.66% | Open (valued at last close) |

**Takeaways**
- The strategy **trailed buy-and-hold by about 20 percentage points**. Most of the gap comes from the April 2025 sell-off. The worst drawdown (-18.76%, 2025-02-19 → 2025-04-08) happened while still long. The Death Cross then sold near the bottom ($519 on 2025-04-17), and the Golden Cross only bought back at $609, about 17% higher. This is the **lag** described above.
- It held the 2023–2024 bull run through a single trade and sat in cash for about 15% of the period.
- **Two trades are far too few to judge the strategy statistically.** The 100% win rate says almost nothing about future performance.

> [!NOTE]
> Prices are split- and dividend-adjusted. Signals are evaluated on each day's close and filled at the **next day's open**. No commissions, slippage, or taxes are included.

---

## 6. How to Run

### 1. Prerequisites
Ensure you have installed the repository dependencies:
```bash
pip install -r ../requirements.txt
```

### 2. Configure Parameters
Open `strategy.py` and adjust the configuration block at the top:
```python
TICKER = "SPY"             # Target symbol
PERIOD = "5y"              # Lookback (must contain more than SLOW_MA bars)
INTERVAL = "1d"            # Bar interval
FAST_MA = 50               # Fast SMA period
SLOW_MA = 200              # Slow SMA period
ENABLE_BACKTEST = True     # Toggle quick backtest metrics
```
Popular alternatives: `20 / 50` (faster, more signals, more whipsaws) or `10 / 30` for shorter-term swing trading.

### 3. Execute
Run the standalone script directly:
```bash
python strategy.py
```

### 4. Interpreting Output
The script prints:
- **Market Snapshot**: latest date, close price, both SMA values, and how far the fast SMA is above or below the slow one, in %. A small gap means a crossover may be close.
- **Current State**: `LONG` or `FLAT`, the position the rules say you should currently hold.
- **Actionable Signal**: `BUY` or `SELL` only on the bar where a crossover just happened, otherwise `HOLD`. Act on it at the next session's open.
- **Last Signal**: date and type of the most recent crossover.
- **Quick Backtest Summary (if enabled)**: strategy return vs. buy-and-hold, win rate, number of trades, maximum drawdown, and time in market.

> [!NOTE]
> If you run the script while the market is open, today's unfinished bar is ignored and a message says so. Signals only use completed days, so a signal can't appear and then disappear before the close.

---

## 7. Disclaimer
*This strategy and code are provided strictly for educational purposes and do not constitute financial advice. See [DISCLAIMER.md](../DISCLAIMER.md) for full terms.*
