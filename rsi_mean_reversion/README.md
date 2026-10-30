# RSI Mean Reversion (Oversold Bounce)

> **Category**: Mean-Reversion  
> **Typical Asset Class**: Equity indices, ETFs, large-cap stocks  
> **Suggested Timeframe**: Daily (1d)  

---

## 1. Overview
The Relative Strength Index (RSI), introduced by J. Welles Wilder Jr. in 1978, is one of the most widely used technical indicators. It measures the speed and size of recent price changes on a scale from 0 to 100.

This strategy uses RSI to **buy after sharp sell-offs** and **sell into strength**. Once RSI has fallen into oversold territory (below 30) and then **crosses back above 30**, selling pressure appears to be fading and the strategy goes long. It holds until RSI becomes overbought by **crossing above 70**, then moves back to cash.

Unlike trend-following, this strategy **buys weakness and sells strength**. It expects stretched prices to move back toward their average.

---

## 2. Theoretical Rationale
Mean reversion assumes that short-term price moves often **overshoot** what fundamentals justify:
- **Behavioural overreaction**: fear-driven selling pushes prices below fair value in the short term.
- **Liquidity provision**: forced sellers (margin calls, fund redemptions) accept discounted prices, which rewards buyers who step in.
- **Index-level resilience**: broad equity indices have historically tended to recover from short-term oversold conditions, which makes them better candidates than individual stocks.

Waiting for RSI to **cross back above 30**, instead of buying the moment it drops below 30, adds a simple confirmation that the selling has at least paused. This reduces, but does not remove, the risk of catching a falling knife.

---

## 3. Indicators & Calculations

| Indicator | Default Parameter | Formula / Description |
|-----------|-------------------|-----------------------|
| `RSI` | `14` | Wilder's Relative Strength Index |
| `Oversold level` | `30` | Entry threshold |
| `Overbought level` | `70` | Exit threshold |

RSI is calculated with **Wilder's original smoothing**, which matches TradingView and most charting platforms:

```
change_t = close_t - close_{t-1}
gain_t   = max(change_t, 0)
loss_t   = max(-change_t, 0)

First average  = simple mean of the first 14 gains / losses
Then           avg_t = (avg_{t-1} * 13 + value_t) / 14

RS  = avg_gain / avg_loss
RSI = 100 - 100 / (1 + RS)
```

Prices are split- and dividend-adjusted (`auto_adjust=True`). The first 14 bars are used only to warm up the indicator.

---

## 4. Strategy Rules

### Entry Rules (Buy / Long)
1. RSI was **at or below 30** on the previous bar.
2. RSI closes **above 30** on the current bar (crosses back up out of oversold).
3. The signal is confirmed at the bar's close. Place the trade at the **next session's open**. The backtest fills at that price.

### Exit Rules (Sell / Close)
1. RSI was **at or below 70** on the previous bar and closes **above 70** on the current bar.
2. No fixed stop-loss or time-based exit. The overbought crossover is the only exit.

> [!NOTE]
> The position is **stateful**. After a buy, the strategy stays long until the exit trigger fires, even if RSI drops back below 30 in the meantime. Repeated entry triggers while already long are ignored.

---

## 5. Market Regime & Performance Profile

### When It Works Best
- **Range-bound or gently rising markets**, where sell-offs are short and prices recover quickly.
- **Broad, diversified indices** (e.g. SPY, QQQ), which historically recover from oversold conditions more reliably than single stocks.
- After **short, sharp pullbacks** inside a longer-term uptrend.

### When It Fails (Known Risks & Pitfalls)
- **Prolonged bear markets ("falling knives")**: price can keep falling after the entry. With no stop-loss, the position is held through the decline until RSI eventually reaches 70, which can take months.
- **Strong bull markets**: RSI rarely drops to 30, so the strategy sits in cash and misses most of the trend.
- **Long holding periods**: reaching RSI 70 after an entry can take a long time, which ties up capital.
- **Single stocks**: oversold readings can reflect real fundamental damage (e.g. after an earnings miss), not a temporary overreaction.
- **Few trades** on daily data, so backtest statistics rest on a small sample.
- Commissions, slippage, and taxes are **not** modelled.

### Backtest Results (Snapshot)
> **SPY, daily bars, default settings (RSI 14, levels 30 / 70)**. Data ends at the close on **2026-10-26**. The test window starts on **2021-11-16**, after 14 bars of indicator warm-up out of the 5-year download. Re-running `strategy.py` uses the latest data, so numbers will change over time.

| Metric | Value |
|--------|-------|
| Period tested | 2021-11-16 → 2026-10-26 (1,240 bars) |
| Total trades | 5 (all closed) |
| Win rate | 80.0% |
| Strategy total return | **+48.85%** |
| Buy & hold benchmark | **+74.38%** |
| Max drawdown | -20.56% |
| Time in market | 34.6% |
| $10,000 would have become | $14,885.00 |

**Trade log** (fills at the open of the session after each signal)

| # | Entry date | Entry price | Exit date | Exit price | Return | Status |
|---|------------|-------------|-----------|------------|--------|--------|
| 1 | 2022-01-31 | $414.14 | 2022-08-15 | $401.65 | -3.02% | Closed |
| 2 | 2022-09-29 | $348.27 | 2023-06-13 | $416.80 | +19.68% | Closed |
| 3 | 2023-10-05 | $409.25 | 2023-11-21 | $437.05 | +6.79% | Closed |
| 4 | 2025-03-13 | $547.73 | 2025-06-30 | $609.10 | +11.20% | Closed |
| 5 | 2026-04-01 | $650.60 | 2026-04-17 | $702.58 | +7.99% | Closed |

**Takeaways**
- The strategy **trailed buy-and-hold by about 26 percentage points**, mainly because it was in the market only about 35% of the time during a strong bull market. Long stretches with no oversold reading (e.g. Nov 2023 → Mar 2025) were spent in cash.
- **Trade 1 shows the falling-knife risk.** The strategy bought in January 2022 and held through the first half of the 2022 bear market, because RSI peaked at 67.9 and never crossed 70 to trigger an exit. The full -20.56% max drawdown happened during this trade, from 2022-03-29 to 2022-06-16, even though the trade eventually closed at only -3.02%.
- Return per unit of time invested was high: +48.9% while exposed to the market only about a third of the time. Capital in cash could earn interest, which this backtest does not include.
- **Five trades are still a small sample.** The 80% win rate should not be relied on.

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
PERIOD = "5y"              # Historical data lookback period
INTERVAL = "1d"            # Bar interval
RSI_PERIOD = 14            # RSI lookback
RSI_OVERSOLD = 30.0        # Buy on cross back above this level
RSI_OVERBOUGHT = 70.0      # Sell on cross above this level
ENABLE_BACKTEST = True     # Toggle quick backtest metrics
```
Popular alternatives: `RSI_OVERBOUGHT = 50–60` to take profits sooner, or `RSI_PERIOD = 2` with levels `10 / 90` for very short-term trading (Larry Connors style).

### 3. Execute
Run the standalone script directly:
```bash
python strategy.py
```

### 4. Interpreting Output
The script prints:
- **Market Snapshot**: latest date, close price, current RSI value, and RSI zone (`OVERSOLD`, `NEUTRAL`, or `OVERBOUGHT`).
- **Current State**: `LONG` or `FLAT`, the position the rules say you should currently hold.
- **Actionable Signal**: `BUY` or `SELL` only on the bar where a trigger just fired, otherwise `HOLD`. Act on it at the next session's open.
- **Last Signal**: date and type of the most recent trigger.
- **Quick Backtest Summary (if enabled)**: strategy return vs. buy-and-hold, win rate, number of trades, maximum drawdown, and time in market.

> [!NOTE]
> If you run the script while the market is open, today's unfinished bar is ignored and a message says so. Signals only use completed days, so a signal can't appear and then disappear before the close.

---

## 7. Disclaimer
*This strategy and code are provided strictly for educational purposes and do not constitute financial advice. See [DISCLAIMER.md](../DISCLAIMER.md) for full terms.*
