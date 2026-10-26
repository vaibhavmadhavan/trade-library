"""
===============================================================================
Strategy Template: [Strategy Name]
===============================================================================
Description:
    [Insert brief description of the strategy, indicators used, and the
     core logic for entering/exiting trades.]

DISCLAIMER:
    This code is for educational and illustrative purposes only. It is not
    financial, investment, or trading advice. Past performance is no guarantee
    of future results. All trades must be executed manually at your own risk.
===============================================================================
"""

import sys
import warnings
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
import yfinance as yf

# Suppress external library warnings (e.g., pandas 3+ deprecation notices in yfinance)
warnings.filterwarnings("ignore")


# =============================================================================
# 1. STRATEGY CONFIGURATION
# =============================================================================
# Asset and timeframe settings
TICKER: str = "SPY"             # Target symbol (e.g., SPY, AAPL, QQQ, BTC-USD)
PERIOD: str = "2y"              # Historical lookback (e.g., 6mo, 1y, 2y, 5y, max)
INTERVAL: str = "1d"            # Bar interval (e.g., 1d, 1h, 15m)

# Strategy specific parameters (example: moving average crossover)
PARAM_FAST: int = 20            # Fast indicator period (e.g., 20-period MA)
PARAM_SLOW: int = 50            # Slow indicator period (e.g., 50-period MA)

# Execution and backtesting settings
ENABLE_BACKTEST: bool = True    # Set True to compute and display backtest metrics
INITIAL_CAPITAL: float = 10000.0  # Starting capital for backtest simulation


# =============================================================================
# 2. DATA RETRIEVAL
# =============================================================================
def fetch_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """
    Downloads historical price data using yfinance and standardizes columns.

    Args:
        ticker: Asset ticker symbol.
        period: Time window of data to download.
        interval: Data sampling interval.

    Returns:
        pd.DataFrame containing standardized OHLCV data.
    """
    try:
        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
        )
    except Exception as e:
        print(f"[ERROR] Failed to fetch data for '{ticker}': {e}")
        sys.exit(1)

    if df.empty or len(df) < 5:
        print(f"[ERROR] No sufficient data returned for ticker '{ticker}'. Check symbol or interval.")
        sys.exit(1)

    # Flatten MultiIndex columns if returned by newer yfinance versions
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Standardize column names
    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    })

    # Ensure required columns are present
    required_cols = ["open", "high", "low", "close"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"[ERROR] Missing expected columns from data: {missing}")
        sys.exit(1)

    return df.copy()


# =============================================================================
# 3. INDICATOR CALCULATIONS
# =============================================================================
def calculate_indicators(df: pd.DataFrame, fast_period: int, slow_period: int) -> pd.DataFrame:
    """
    Computes technical indicators required by the strategy.
    
    [Customize this function for your specific strategy]
    """
    data = df.copy()

    # Example: Simple Moving Averages
    data["fast_ma"] = data["close"].rolling(window=fast_period).mean()
    data["slow_ma"] = data["close"].rolling(window=slow_period).mean()

    return data


# =============================================================================
# 4. SIGNAL GENERATION
# =============================================================================
def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates trading signals and active market positions based on indicators.
    
    Position coding:
         1: Long (In Market)
         0: Neutral / Flat (Cash)
        -1: Short (Optional, for bi-directional strategies)
    """
    data = df.copy()
    data["signal"] = 0

    # Example Rule:
    # Buy when fast MA is above slow MA, otherwise stay in cash
    condition_long = data["fast_ma"] > data["slow_ma"]
    
    # 1 for Long, 0 for Cash
    data["position"] = np.where(condition_long, 1, 0)

    # Signal represents position change: +1 = Enter Long, -1 = Exit to Cash
    data["signal"] = data["position"].diff().fillna(0)

    return data


# =============================================================================
# 5. BACKTEST ENGINE
# =============================================================================
def run_quick_backtest(df: pd.DataFrame, initial_capital: float = 10000.0) -> Dict[str, Any]:
    """
    Performs a simple, vectorized backtest of the strategy to estimate performance.
    Signals generated at bar t are executed on bar t+1 to eliminate lookahead bias.
    """
    data = df.copy().dropna(subset=["close", "position"])
    if len(data) < 2:
        return {}

    # Asset percentage returns
    data["market_return"] = data["close"].pct_change().fillna(0.0)

    # Strategy returns (shift position by 1 bar to simulate next-bar execution)
    data["strategy_return"] = data["position"].shift(1).fillna(0.0) * data["market_return"]

    # Equity curves
    data["cum_market"] = (1.0 + data["market_return"]).cumprod()
    data["cum_strategy"] = (1.0 + data["strategy_return"]).cumprod()

    # Total cumulative returns
    total_market_return = (data["cum_market"].iloc[-1] - 1.0) * 100.0
    total_strategy_return = (data["cum_strategy"].iloc[-1] - 1.0) * 100.0

    # Drawdown calculation
    rolling_max = data["cum_strategy"].cummax()
    drawdown = (data["cum_strategy"] - rolling_max) / rolling_max
    max_drawdown = drawdown.min() * 100.0

    # Trade extraction & Win Rate calculation
    # Detect trades when position changes
    trades = []
    current_trade_return = 0.0
    in_trade = False

    for i in range(1, len(data)):
        pos = data["position"].iloc[i - 1]  # Active position during bar i
        ret = data["strategy_return"].iloc[i]

        if pos != 0:
            if not in_trade:
                in_trade = True
                current_trade_return = 1.0
            current_trade_return *= (1.0 + ret)

        if in_trade and (pos == 0 or i == len(data) - 1):
            trades.append(current_trade_return - 1.0)
            in_trade = False

    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t > 0)
    win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0

    final_portfolio_value = initial_capital * data["cum_strategy"].iloc[-1]

    return {
        "start_date": data.index[0].strftime("%Y-%m-%d"),
        "end_date": data.index[-1].strftime("%Y-%m-%d"),
        "total_bars": len(data),
        "total_trades": total_trades,
        "win_rate": win_rate,
        "strategy_return_pct": total_strategy_return,
        "market_return_pct": total_market_return,
        "max_drawdown_pct": max_drawdown,
        "final_capital": final_portfolio_value,
    }


# =============================================================================
# 6. OUTPUT & REPORTING
# =============================================================================
def print_report(df: pd.DataFrame, backtest_results: Dict[str, Any]) -> None:
    """
    Prints a formatted terminal summary showing recent indicators, the current
    actionable signal, and optional backtest metrics.
    """
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2] if len(df) > 1 else last_row

    last_date = df.index[-1].strftime("%Y-%m-%d")
    close_price = last_row["close"]
    current_position = int(last_row.get("position", 0))
    current_signal = int(last_row.get("signal", 0))

    action_map = {
        1: "BUY / LONG (Enter position)",
        -1: "SELL / EXIT (Close position)",
        0: "HOLD / NEUTRAL (No action required)",
    }
    action_text = action_map.get(current_signal, "HOLD")

    position_map = {
        1: "LONG (In Market)",
        0: "FLAT (Cash)",
        -1: "SHORT",
    }
    position_text = position_map.get(current_position, "UNKNOWN")

    print("\n" + "=" * 65)
    print(f" STRATEGY REPORT: [Strategy Name] | Ticker: {TICKER}")
    print("=" * 65)
    print(f" As of Date:       {last_date}")
    print(f" Latest Close:     ${close_price:.2f}")
    
    # Custom indicator readings (adjust to match your indicators)
    if "fast_ma" in last_row and "slow_ma" in last_row:
        print(f" Fast MA ({PARAM_FAST}):     ${last_row['fast_ma']:.2f}")
        print(f" Slow MA ({PARAM_SLOW}):     ${last_row['slow_ma']:.2f}")

    print("-" * 65)
    print(f" Current State:    {position_text}")
    print(f" Actionable Signal: {action_text}")
    print("-" * 65)

    if ENABLE_BACKTEST and backtest_results:
        print("\n" + "-" * 65)
        print(f" HISTORICAL BACKTEST SUMMARY ({backtest_results['start_date']} to {backtest_results['end_date']})")
        print("-" * 65)
        print(f" Total Bars Analyzed:     {backtest_results['total_bars']}")
        print(f" Total Trades Executed:   {backtest_results['total_trades']}")
        print(f" Trade Win Rate:          {backtest_results['win_rate']:.1f}%")
        print(f" Strategy Total Return:   {backtest_results['strategy_return_pct']:+.2f}%")
        print(f" Buy & Hold Benchmark:    {backtest_results['market_return_pct']:+.2f}%")
        print(f" Max Drawdown:            {backtest_results['max_drawdown_pct']:.2f}%")
        print(f" Simulated Ending Value:  ${backtest_results['final_capital']:,.2f} (from ${INITIAL_CAPITAL:,.2f})")
        print("-" * 65)

    print("\n[NOTE] Review the README.md in this folder for strategy rules & risk factors.")
    print("=" * 65 + "\n")


# =============================================================================
# 7. MAIN EXECUTION
# =============================================================================
def main():
    print(f"\n[INFO] Running [Strategy Name] for {TICKER} (Interval: {INTERVAL}, Period: {PERIOD})...")
    
    # 1. Fetch data
    df = fetch_data(ticker=TICKER, period=PERIOD, interval=INTERVAL)

    # 2. Compute indicators
    df = calculate_indicators(df, fast_period=PARAM_FAST, slow_period=PARAM_SLOW)

    # 3. Generate signals
    df = generate_signals(df)

    # 4. Optional backtest
    backtest_results = {}
    if ENABLE_BACKTEST:
        backtest_results = run_quick_backtest(df, initial_capital=INITIAL_CAPITAL)

    # 5. Output report
    print_report(df, backtest_results)


if __name__ == "__main__":
    main()
