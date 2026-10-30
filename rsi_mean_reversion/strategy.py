"""
===============================================================================
Strategy: RSI Mean Reversion (Oversold Bounce)
===============================================================================
Description:
    A long-only mean-reversion strategy using the 14-period Relative Strength
    Index (RSI) with J. Welles Wilder's original smoothing method.

    - BUY:  RSI crosses back ABOVE the oversold level (30), signalling that
            selling pressure is fading after an oversold reading.
    - SELL: RSI crosses ABOVE the overbought level (70), taking profit once the
            bounce has become overextended.

    Between a BUY and the next SELL the strategy remains LONG; otherwise it
    stays FLAT (in cash).

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
STRATEGY_NAME: str = "RSI Mean Reversion"

# Asset and timeframe settings
TICKER: str = "SPY"             # Target symbol (e.g., SPY, AAPL, QQQ, BTC-USD)
PERIOD: str = "5y"              # Historical lookback (e.g., 2y, 5y, 10y, max)
INTERVAL: str = "1d"            # Bar interval (e.g., 1d, 1h, 15m)

# Strategy specific parameters
RSI_PERIOD: int = 14            # RSI lookback (Wilder's original: 14)
RSI_OVERSOLD: float = 30.0      # BUY when RSI crosses back above this level
RSI_OVERBOUGHT: float = 70.0    # SELL when RSI crosses above this level

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
def wilder_rsi(close: pd.Series, period: int) -> pd.Series:
    """
    Relative Strength Index using Wilder's smoothing (matches TradingView and
    most charting platforms).

        change_t   = close_t - close_{t-1}
        gain_t     = max(change_t, 0)
        loss_t     = max(-change_t, 0)

        Seed (first value): simple average of the first `period` gains / losses
        Thereafter:         avg_t = (avg_{t-1} * (period - 1) + value_t) / period

        RS  = avg_gain / avg_loss
        RSI = 100 - 100 / (1 + RS)
    """
    change = close.diff().to_numpy()
    gains = np.where(change > 0, change, 0.0)
    losses = np.where(change < 0, -change, 0.0)

    rsi = np.full(len(close), np.nan)
    if len(close) <= period:
        return pd.Series(rsi, index=close.index)

    # Seed with simple average of the first `period` changes (index 1..period)
    avg_gain = gains[1:period + 1].mean()
    avg_loss = losses[1:period + 1].mean()

    for i in range(period, len(close)):
        if i > period:
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi[i] = 100.0 if avg_gain > 0 else 50.0
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100.0 - 100.0 / (1.0 + rs)

    return pd.Series(rsi, index=close.index)


def calculate_indicators(df: pd.DataFrame, rsi_period: int) -> pd.DataFrame:
    """
    Computes the Wilder RSI of the close price.

    Warm-up rows (where RSI is not yet defined) are dropped so the signal
    history and backtest start only once the indicator is valid.
    """
    data = df.copy()
    data["rsi"] = wilder_rsi(data["close"], rsi_period)

    # Drop indicator warm-up period
    return data.dropna(subset=["rsi"])


# =============================================================================
# 4. SIGNAL GENERATION
# =============================================================================
def generate_signals(df: pd.DataFrame, oversold: float, overbought: float) -> pd.DataFrame:
    """
    Generates trading signals and active market positions based on indicators.

    Entry trigger: RSI crosses back above `oversold`  (prev <= oversold, now > oversold)
    Exit trigger:  RSI crosses above `overbought`     (prev <= overbought, now > overbought)

    Because entry and exit are separate events, the position is stateful:
    once LONG it is held until an exit trigger, and vice versa.

    Position coding:
         1: Long (In Market)
         0: Flat (Cash)

    Signal coding (change in position):
         1: Enter long
        -1: Exit to cash
         0: No change
    """
    if oversold >= overbought:
        print(f"[ERROR] RSI_OVERSOLD ({oversold}) must be below RSI_OVERBOUGHT ({overbought}).")
        sys.exit(1)

    data = df.copy()
    prev_rsi = data["rsi"].shift(1)

    entry_trigger = ((prev_rsi <= oversold) & (data["rsi"] > oversold)).to_numpy()
    exit_trigger = ((prev_rsi <= overbought) & (data["rsi"] > overbought)).to_numpy()

    position = np.zeros(len(data), dtype=int)
    state = 0
    for i in range(len(data)):
        if state == 0 and entry_trigger[i]:
            state = 1
        elif state == 1 and exit_trigger[i]:
            state = 0
        position[i] = state

    data["position"] = position
    data["signal"] = data["position"].diff().fillna(0).astype(int)

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
        1: f"BUY / LONG (RSI crossed back above {RSI_OVERSOLD:g} - enter at next open)",
        -1: f"SELL / EXIT (RSI crossed above {RSI_OVERBOUGHT:g} - close at next open)",
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

    rsi_value = last_row["rsi"]
    if rsi_value < RSI_OVERSOLD:
        rsi_zone = "OVERSOLD (watch for cross back above to BUY)"
    elif rsi_value > RSI_OVERBOUGHT:
        rsi_zone = "OVERBOUGHT"
    else:
        rsi_zone = "NEUTRAL"

    print("\n" + "=" * 65)
    print(f" STRATEGY REPORT: {STRATEGY_NAME} | Ticker: {TICKER}")
    print("=" * 65)
    print(f" As of Date:        {last_date}")
    print(f" Latest Close:      ${close_price:.2f}")
    print(f" RSI ({RSI_PERIOD}):          {rsi_value:.2f}")
    print(f" RSI Zone:          {rsi_zone}")
    print(f" Levels:            Oversold {RSI_OVERSOLD:g} / Overbought {RSI_OVERBOUGHT:g}")
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
    df = calculate_indicators(df, rsi_period=RSI_PERIOD)
    if len(df) < 2:
        print(f"[ERROR] Not enough data after indicator warm-up. Increase PERIOD (needs > {RSI_PERIOD} bars).")
        sys.exit(1)

    # 3. Generate signals
    df = generate_signals(df, oversold=RSI_OVERSOLD, overbought=RSI_OVERBOUGHT)

    # 4. Optional backtest
    backtest_results = {}
    if ENABLE_BACKTEST:
        backtest_results = run_quick_backtest(df, initial_capital=INITIAL_CAPITAL)

    # 5. Output report
    print_report(df, backtest_results)


if __name__ == "__main__":
    main()
