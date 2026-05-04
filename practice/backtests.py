# backtests.py
# バックテスト関連の関数を定義

import pandas as pd
import numpy as np
import talib as ta


def run_golden_cross_backtest(df, close, signal=None, **kwargs):
    """
    ゴールデンクロスで買い、5%下落で売るバックテスト
    """
    if signal is None:
        raise ValueError("signal が必要です。")

    df["Buy"] = signal
    position = 0
    positions = []
    buy_price = None

    for i in range(len(df)):
        if df["Buy"].iloc[i]:
            position = 1
            buy_price = close.iloc[i]
        elif position == 1 and close.iloc[i] <= buy_price * 0.95:
            position = 0
        positions.append(position)
    df["Position"] = positions

    return _finalize_backtest(df)


def run_ma_cross_backtest(df, close, ma_short=None, ma_long=None, signal=None, death_signal=None, **kwargs):
    """
    デッドクロスで売り、ゴールデンクロスで買う典型的なMAクロス戦略
    """
    if signal is None or death_signal is None:
        if ma_short is None or ma_long is None:
            raise ValueError("signal または ma_short/ma_long が必要です。")
        signal = (ma_short > ma_long) & (ma_short.shift(1) <= ma_long.shift(1))
        death_signal = (ma_short < ma_long) & (ma_short.shift(1) >= ma_long.shift(1))

    df["Buy"] = signal
    df["Sell"] = death_signal
    position = 0
    positions = []

    for i in range(len(df)):
        if df["Buy"].iloc[i]:
            position = 1
        elif df["Sell"].iloc[i]:
            position = 0
        positions.append(position)
    df["Position"] = positions

    return _finalize_backtest(df)


def run_buy_and_hold_backtest(df, **kwargs):
    """
    ずっと保有するシンプルな戦略
    """
    df["Position"] = 1
    return _finalize_backtest(df)


def run_rsi_backtest(df, close, **kwargs):
    """
    RSIベースの戦略: RSI < 30 で買い、RSI > 70 で売る
    """
    rsi = ta.RSI(close.values, timeperiod=14)
    df["RSI"] = pd.Series(rsi, index=df.index)

    df["Buy"] = df["RSI"] < 30
    df["Sell"] = df["RSI"] > 70
    position = 0
    positions = []

    for i in range(len(df)):
        if df["Buy"].iloc[i]:
            position = 1
        elif df["Sell"].iloc[i]:
            position = 0
        positions.append(position)
    df["Position"] = positions

    return _finalize_backtest(df)



def _finalize_backtest(df):
    df["Return"] = df["Close"].pct_change()
    df["Strategy"] = df["Return"] * df["Position"].shift(1)
    initial = 100
    df["Cumulative Market"] = initial * (1 + df["Return"]).cumprod()
    df["Cumulative Strategy"] = initial * (1 + df["Strategy"]).cumprod()
    df["Market Peak"] = df["Cumulative Market"].cummax()
    df["Market Drawdown"] = df["Cumulative Market"] / df["Market Peak"] - 1
    df["Strategy Peak"] = df["Cumulative Strategy"].cummax()
    df["Strategy Drawdown"] = df["Cumulative Strategy"] / df["Strategy Peak"] - 1
    df["Max Market Drawdown"] = df["Market Drawdown"].cummin()
    df["Max Strategy Drawdown"] = df["Strategy Drawdown"].cummin()
    return df


BACKTESTS = {
    "1": {
        "name": "Golden Cross + 5% Stop",
        "func": run_golden_cross_backtest,
        "description": "ゴールデンクロスで買い、5%下落で売る",
    },
    "2": {
        "name": "MAクロス売買",
        "func": run_ma_cross_backtest,
        "description": "ゴールデンクロスで買い、デッドクロスで売る",
    },
    "3": {
        "name": "Buy & Hold",
        "func": run_buy_and_hold_backtest,
        "description": "常に保有する単純戦略",
    },
    "4": {
        "name": "RSI戦略",
        "func": run_rsi_backtest,
        "description": "RSI < 30 で買い、RSI > 70 で売る",
    },
    
}


def list_backtests():
    return [(key, info["name"], info["description"]) for key, info in BACKTESTS.items()]


def get_backtest_choice(key):
    return BACKTESTS.get(key)
