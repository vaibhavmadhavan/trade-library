# Trade Library 📈

A curated collection of self-contained, copy-pasteable manual trading strategies in Python.

Each strategy lives in its own dedicated folder with a clear, educational `README.md` explaining the market logic, entry/exit rules, indicator formulas, and when it works or fails. Every strategy script is completely self-contained—meaning you can copy just the single `strategy.py` file, tweak parameters, and run it directly.

---

> ⚠️ **Disclaimer:** All content in this repository is strictly for **educational and informational purposes only**. None of the materials constitute investment or financial advice. See [DISCLAIMER.md](DISCLAIMER.md) for full terms.

---

## 🚀 Quick Start

### 1. Clone & Install Dependencies
All strategies share the same minimal dependencies (`pandas`, `numpy`, `yfinance`):
```bash
git clone https://github.com/vaibhavmadhavan/trade-library.git
cd trade-library
pip install -r requirements.txt
```

### 2. Pick a Strategy
Browse the [Strategy Catalog](#-strategy-catalog) below or explore any strategy folder directly.

### 3. Configure & Run
Open the chosen strategy's `strategy.py`, inspect the configuration block at the top, and run it:
```bash
cd <strategy-folder>
python strategy.py
```
The script will fetch the latest market data, calculate indicators, output the current actionable signal (`BUY`, `SELL`, `HOLD`), and display a historical backtest summary.

---

## 📚 Strategy Catalog

| Folder | Strategy | Type / Category | Indicators | Asset Class |
|--------|----------|-----------------|------------|-------------|
| [`ma_crossover/`](ma_crossover/) | Moving Average Crossover (Golden / Death Cross) | Trend-Following | SMA 50 / SMA 200 | Indices, ETFs, stocks, crypto |
| [`rsi_mean_reversion/`](rsi_mean_reversion/) | RSI Mean Reversion (Oversold Bounce) | Mean-Reversion | RSI 14 (Wilder), 30 / 70 | Indices, ETFs, large-caps |

*To create or propose a new strategy, refer to the [`_template/`](_template/) directory.*

---

## 🧩 Architectural Design Principles

1. **One Folder = One Strategy**: Every strategy is entirely self-sufficient in its own directory.
2. **Self-Contained Code**: Each `strategy.py` can be copied outside this repository and run standalone with zero custom internal imports.
3. **Signal Only (Manual Execution)**: Scripts generate transparent trading signals. No broker API keys, automated order placement, or external execution hooks.
4. **Uniform Standard**: Every strategy adheres to the exact same sections in its `README.md` and the exact same 7-part architecture in `strategy.py`.
5. **No Lookahead Bias**: Signals are evaluated on a bar's close, and backtests fill trades at the **next bar's open**, just as a manual trader would. Bars that are still forming (e.g. running the script while the market is open) are ignored, so signals never change after you see them.

---

## 🛠️ Adding a New Strategy

To add a new strategy to the library:
1. Duplicate the [`_template/`](_template/) folder and rename it with snake_case (e.g., `rsi_oversold_bounce/`).
2. Update `README.md` inside that folder following the provided prompts.
3. Update `strategy.py`:
   - Adjust the configuration variables (Section 1).
   - Define custom indicator logic in `calculate_indicators()` (Section 3).
   - Define entry/exit rules in `generate_signals()` (Section 4).
   - Customize report printouts in `print_report()` (Section 6).
4. Add the strategy to the [Strategy Catalog](#-strategy-catalog) above.

---

## 📄 License & Disclaimer

Distributed under educational use guidelines. Please review [DISCLAIMER.md](DISCLAIMER.md) before using this codebase.