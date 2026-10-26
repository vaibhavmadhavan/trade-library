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
- **Market Snapshot**: Latest bar date, close price, and indicator values.
- **Actionable Signal**: Current state (`BUY`, `SELL`, or `HOLD/NEUTRAL`).
- **Quick Backtest Summary (if enabled)**: Total strategy return vs. buy-and-hold benchmark, win rate, total trades, and maximum drawdown.

---

## 7. Disclaimer
*This strategy and code are provided strictly for educational purposes and do not constitute financial advice. See [DISCLAIMER.md](../DISCLAIMER.md) for full terms.*
