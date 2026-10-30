# [Strategy Name]

> **Category**: [e.g. Trend-Following / Mean-Reversion / Breakout / Momentum]  
> **Typical Asset Class**: [e.g. Equities, ETFs, Crypto, FX]  
> **Suggested Timeframe**: [e.g. Daily (1d), Hourly (1h), 15m]  

---

## 1. Overview
[Provide a 2-3 paragraph summary explaining the strategy, the market inefficiency it seeks to exploit, and its high-level mechanics.]

---

## 2. Theoretical Rationale
[Explain the core thesis behind the strategy. Why should this edge exist? Is it behavioral (overreaction/panic), structural (index rebalancing/liquidity flows), or trend persistence?]

---

## 3. Indicators & Calculations
[Detail the technical indicators used and their mathematical definitions.]

| Indicator | Default Parameter | Formula / Description |
|-----------|-------------------|-----------------------|
| `Indicator 1` | `Parameter (e.g. 20)` | `Description / Formula` |
| `Indicator 2` | `Parameter (e.g. 50)` | `Description / Formula` |

---

## 4. Strategy Rules

### Entry Rules (Buy / Long)
1. Condition 1 (e.g. `Fast MA` crosses above `Slow MA`).
2. Condition 2 (e.g. `RSI < 70`).
3. Confirmation (e.g. volume exceeds 20-day average).

### Exit Rules (Sell / Close / Short)
1. Signal Exit (e.g. `Fast MA` crosses below `Slow MA`).
2. Stop-Loss (e.g. 2x Average True Range below entry price, or fixed -3%).
3. Take-Profit (e.g. predefined risk-reward ratio or opposite signal).

---

## 5. Market Regime & Performance Profile

### When It Works Best
- [e.g. Strong directional bull or bear markets]
- [e.g. High-momentum assets with persistent trends]

### When It Fails (Known Risks & Pitfalls)
- [e.g. Choppy, sideways, low-volatility consolidation]
- [e.g. Frequent whipsaw losses from false breakouts]
- [e.g. High transaction costs/slippage if traded on low timeframes]

### Backtest Results (Snapshot)
> **[Ticker], [interval] bars, default settings**. Data ends at the close on **[YYYY-MM-DD]**. The test window starts on **[YYYY-MM-DD]**, after indicator warm-up. Re-running `strategy.py` uses the latest data, so numbers will change over time.

| Metric | Value |
|--------|-------|
| Period tested | [start] → [end] ([N] bars) |
| Total trades | [N] |
| Win rate | [x]% |
| Strategy total return | [+x]% |
| Buy & hold benchmark | [+x]% |
| Max drawdown | [-x]% |
| Time in market | [x]% |
| $10,000 would have become | $[x] |

**Trade log**

| # | Entry date | Entry price | Exit date | Exit price | Return | Status |
|---|------------|-------------|-----------|------------|--------|--------|
| 1 | [date] | $[x] | [date] | $[x] | [+x]% | [Closed / Open] |

**Takeaways**
- [How it compared with buy-and-hold and why]
- [Notable trades that illustrate the strategy's strengths or failure modes]
- [Sample-size caveat]

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
PERIOD = "2y"              # Historical data lookback period
INTERVAL = "1d"            # Bar interval (1d, 1h, 15m, etc.)
ENABLE_BACKTEST = True     # Toggle quick backtest metrics
```

### 3. Execute
Run the standalone script directly:
```bash
python strategy.py
```

### 4. Interpreting Output
The script prints:
- **Market Snapshot**: latest completed bar date, close price, and indicator values.
- **Current State**: `LONG` or `FLAT`, the position the rules say you should currently hold.
- **Actionable Signal**: `BUY` or `SELL` only on the bar where a trigger just fired, otherwise `HOLD`. Act on it at the next session's open.
- **Last Signal**: date and type of the most recent trigger.
- **Quick Backtest Summary (if enabled)**: strategy return vs. buy-and-hold, win rate, number of trades, maximum drawdown, and time in market.

> [!NOTE]
> If you run the script while the market is open, today's unfinished bar is ignored and a message says so. Signals only use completed days, so a signal can't appear and then disappear before the close.

---

## 7. Disclaimer
*This strategy and code are provided strictly for educational purposes and do not constitute financial advice. See [DISCLAIMER.md](../DISCLAIMER.md) for full terms.*
