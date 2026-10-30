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
from typing import Dict, Any
import numpy as np
import pandas as pd
import yfinance as yf

# Suppress external library warnings (e.g., pandas 3+ deprecation notices in yfinance)
warnings.filterwarnings("ignore")


# =============================================================================
# 1. STRATEGY CONFIGURATION
# =============================================================================
STRATEGY_NAME: str = "[Strategy Name]"

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
def _drop_incomplete_bar(df: pd.DataFrame, interval: str, metadata: Dict[str, Any]) -> pd.DataFrame:
    """
    Removes the most recent bar if it has not finished yet (e.g. the script is
    run while the market is open). A bar that is still forming can produce a
    signal that disappears by the close, so only completed bars are used.
    """
    last_start = df.index[-1]
    tz = last_start.tz
    now = pd.Timestamp.now(tz=tz) if tz is not None else pd.Timestamp.now()

    # End of the current regular trading session, as reported by Yahoo Finance
    session_end = None
    try:
        session_end = pd.Timestamp(metadata["currentTradingPeriod"]["regular"]["end"])
        if tz is not None:
            session_end = session_end.tz_convert(tz)
    except (KeyError, TypeError, ValueError):
        session_end = None

    try:
        if interval.endswith("mo"):
            bar_end = last_start + pd.DateOffset(months=int(interval[:-2]))
        elif interval.endswith("wk"):
            bar_end = last_start + pd.DateOffset(weeks=int(interval[:-2]))
        elif interval.endswith("d"):
            bar_end = last_start + pd.Timedelta(days=int(interval[:-1]))
        elif interval.endswith("h"):
            bar_end = last_start + pd.Timedelta(hours=int(interval[:-1]))
        elif interval.endswith("m"):
            bar_end = last_start + pd.Timedelta(minutes=int(interval[:-1]))
        else:
            return df
    except ValueError:
        return df

    # Daily and intraday bars finish when the session closes, not after a fixed duration
    is_intraday = interval.endswith(("m", "h")) and not interval.endswith("mo")
    if session_end is not None and (interval == "1d" or is_intraday):
        if session_end.date() == last_start.date():
            bar_end = min(bar_end, session_end)
        elif interval == "1d":
            bar_end = last_start  # bar belongs to an earlier, already finished session

    if now < bar_end:
        print(f"[INFO] Ignoring in-progress bar starting {last_start} (not yet closed). "
              "Signals use the last completed bar.")
        return df.iloc[:-1]
    return df


def fetch_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """
    Downloads historical price data using yfinance and standardizes columns.
    Prices are split- and dividend-adjusted. Any bar that is still in progress
    is dropped so signals are based on completed bars only.

    Args:
        ticker: Asset ticker symbol.
        period: Time window of data to download.
        interval: Data sampling interval.

    Returns:
        pd.DataFrame containing standardized OHLCV data.
    """
    try:
        yf_ticker = yf.Ticker(ticker)
        df = yf_ticker.history(period=period, interval=interval, auto_adjust=True)
    except Exception as e:
        print(f"[ERROR] Failed to fetch data for '{ticker}': {e}")
        sys.exit(1)

    if df is None or df.empty:
        print(f"[ERROR] No data returned for ticker '{ticker}'. Check symbol or interval.")
        sys.exit(1)

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

    df = df[[col for col in ["open", "high", "low", "close", "volume"] if col in df.columns]]

    # Drop the latest bar if it is still forming
    try:
        metadata = yf_ticker.history_metadata or {}
    except Exception:
        metadata = {}
    df = _drop_incomplete_bar(df, interval, metadata)

    if len(df) < 5:
        print(f"[ERROR] Not enough completed bars returned for ticker '{ticker}'.")
        sys.exit(1)

    return df.copy()


# =============================================================================
# 3. INDICATOR CALCULATIONS
# =============================================================================
def calculate_indicators(df: pd.DataFrame, fast_period: int, slow_period: int) -> pd.DataFrame:
    """
    Computes technical indicators required by the strategy.
    
    [Customize this function for your specific strategy]

    Warm-up rows (where indicators are not yet defined) are dropped so the
    signal history and backtest start only once all indicators are valid.
    """
    data = df.copy()

    # Example: Simple Moving Averages
    data["fast_ma"] = data["close"].rolling(window=fast_period).mean()
    data["slow_ma"] = data["close"].rolling(window=slow_period).mean()

    # Drop indicator warm-up period (list every indicator column here)
    return data.dropna(subset=["fast_ma", "slow_ma"])


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

    Execution model (no lookahead):
      - Signals are evaluated on the CLOSE of bar t.
      - Trades are filled at the OPEN of bar t+1, as a manual trader would.
    Commissions, slippage, and taxes are NOT modelled.
    """
    data = df.copy().dropna(subset=["open", "close", "position"])
    if len(data) < 3:
        return {}

    # Position held during bar i (decided at close of bar i-1, filled at open of bar i)
    held = data["position"].shift(1).fillna(0.0)
    # Position held overnight from close of bar i-1 to open of bar i
    held_overnight = held.shift(1).fillna(0.0)

    gap_return = (data["open"] / data["close"].shift(1) - 1.0).fillna(0.0)
    session_return = data["close"] / data["open"] - 1.0

    data["strategy_return"] = (
        (1.0 + held_overnight * gap_return) * (1.0 + held * session_return) - 1.0
    )
    data["market_return"] = data["close"].pct_change().fillna(0.0)

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

    # Trade log: a trade opens/closes at the open of the bar where `held` changes
    trades = []
    open_trade = None
    held_values = held.to_numpy()
    opens = data["open"].to_numpy()
    closes = data["close"].to_numpy()

    for i in range(len(data)):
        prev_held = held_values[i - 1] if i > 0 else 0.0
        if held_values[i] != prev_held:
            if open_trade is not None:
                open_trade.update(exit_date=data.index[i], exit_price=opens[i], status="Closed")
                trades.append(open_trade)
                open_trade = None
            if held_values[i] != 0:
                open_trade = {
                    "direction": int(held_values[i]),
                    "entry_date": data.index[i],
                    "entry_price": opens[i],
                }

    if open_trade is not None:
        # Still in a position: value it at the latest close
        open_trade.update(exit_date=data.index[-1], exit_price=closes[-1], status="Open")
        trades.append(open_trade)

    for t in trades:
        t["return_pct"] = t["direction"] * (t["exit_price"] / t["entry_price"] - 1.0) * 100.0

    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t["return_pct"] > 0)
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
        "time_in_market_pct": (held != 0).mean() * 100.0,
        "final_capital": final_portfolio_value,
        "trades": trades,
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

    last_date = df.index[-1].strftime("%Y-%m-%d")
    close_price = last_row["close"]
    current_position = int(last_row.get("position", 0))
    current_signal = int(last_row.get("signal", 0))

    action_map = {
        1: "BUY / LONG (Enter at next open)",
        -1: "SELL / EXIT (Close at next open)",
        0: "HOLD / NEUTRAL (No action required)",
    }
    action_text = action_map.get(current_signal, "HOLD")

    position_map = {
        1: "LONG (In Market)",
        0: "FLAT (Cash)",
        -1: "SHORT",
    }
    position_text = position_map.get(current_position, "UNKNOWN")

    # Most recent signal event (for context on how long the current state has lasted)
    signal_events = df[df["signal"] != 0]
    if not signal_events.empty:
        last_event_date = signal_events.index[-1].strftime("%Y-%m-%d")
        last_event_type = "BUY" if signal_events["signal"].iloc[-1] > 0 else "SELL"
        last_event_text = f"{last_event_type} on {last_event_date}"
    else:
        last_event_text = "None within analysed period"

    print("\n" + "=" * 65)
    print(f" STRATEGY REPORT: {STRATEGY_NAME} | Ticker: {TICKER}")
    print("=" * 65)
    print(f" As of Date:        {last_date}")
    print(f" Latest Close:      ${close_price:.2f}")

    # Custom indicator readings (adjust to match your indicators)
    print(f" Fast MA ({PARAM_FAST}):      ${last_row['fast_ma']:.2f}")
    print(f" Slow MA ({PARAM_SLOW}):      ${last_row['slow_ma']:.2f}")

    print("-" * 65)
    print(f" Current State:     {position_text}")
    print(f" Actionable Signal: {action_text}")
    print(f" Last Signal:       {last_event_text}")
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
        print(f" Time in Market:          {backtest_results['time_in_market_pct']:.1f}%")
        print(f" Simulated Ending Value:  ${backtest_results['final_capital']:,.2f} (from ${INITIAL_CAPITAL:,.2f})")
        print("-" * 65)

    print("\n[NOTE] Review the README.md in this folder for strategy rules & risk factors.")
    print("=" * 65 + "\n")


# =============================================================================
# 7. MAIN EXECUTION
# =============================================================================
def main():
    print(f"\n[INFO] Running {STRATEGY_NAME} for {TICKER} (Interval: {INTERVAL}, Period: {PERIOD})...")

    # 1. Fetch data
    df = fetch_data(ticker=TICKER, period=PERIOD, interval=INTERVAL)

    # 2. Compute indicators
    df = calculate_indicators(df, fast_period=PARAM_FAST, slow_period=PARAM_SLOW)
    if len(df) < 2:
        print("[ERROR] Not enough data after indicator warm-up. Increase PERIOD.")
        sys.exit(1)

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
