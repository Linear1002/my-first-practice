import sys
import os
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from backtests import get_backtest_choice, list_backtests


# 銘柄選択
ticker = input("銘柄コードを入力してください。")

# データ取得（過去1年）
stock = yf.Ticker(ticker)
df = stock.history(period="1y")

# 通過情報取得
currency = stock.info.get("currency")

# 終値だけ取り出す
close = df["Close"]

# 移動平均線
ma_short = close.rolling(window=5).mean()
ma_long = close.rolling(window=20).mean()

# ゴールデンクロスの自動追加
signal = (ma_short > ma_long) & (ma_short.shift(1) <= ma_long.shift(1))
golden_cross = close[signal]

# デッドクロスの自動追加
death_signal = (ma_short < ma_long) & (ma_short.shift(1) >= ma_long.shift(1))
death_cross = close[death_signal]

# すべてのバックテストを実行
results = {}
for key, name, description in list_backtests():
    backtest_info = get_backtest_choice(key)
    print(f"実行中: {name}")
    
    # データフレームをコピーして各戦略で独立して実行
    df_copy = df.copy()
    df_result = backtest_info["func"](
        df_copy,
        close=close,
        ma_short=ma_short,
        ma_long=ma_long,
        signal=signal,
        death_signal=death_signal,
    )
    
    # 最終リターンとドローダウンを保存
    final_return = (df_result["Cumulative Strategy"].iloc[-1] / 100 - 1) * 100
    cum = df_result["Cumulative Strategy"]
    drawdown = (cum / cum.cummax()) - 1
    max_dd = drawdown.min()
    df_result["Strategy Drawdown"] = drawdown
    results[name] = {
        "final_return": final_return,
        "df": df_result,
        "final": df_result["Cumulative Strategy"].iloc[-1],
        "max_drawdown": max_dd,
    }

# 結果を表示
print("\n=== バックテスト結果 ===")
for name, data in results.items():
    print(f"{name}: Return={data['final_return']:.2f}%, MaxDD={data['max_drawdown']:.2%}")

# グラフで比較
plt.figure(figsize=(12, 8))

# 市場リターンをプロット
plt.plot(df.index, results[list(results.keys())[0]]["df"]["Cumulative Market"], 
         label="Market (Buy & Hold)", color="black", linewidth=2, linestyle="--")

# 各戦略のリターンをプロット
colors = ['blue', 'green', 'red', 'orange', 'purple']
for i, (name, data) in enumerate(results.items()):
    color = colors[i % len(colors)]
    plt.plot(df.index, data["df"]["Cumulative Strategy"], 
             label=f"{name} ({data['final_return']:.1f}%)", color=color, linewidth=2)

plt.title(f"{ticker} - All Strategy Comparison")
plt.xlabel("Date")
plt.ylabel(f"Cumulative Return ({currency})")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
last_name, last_data = list(results.items())[-1]
print(f"{last_name}: Final={last_data['final']:.2f}, MaxDD={last_data['max_drawdown']:.2%}")

# 任意でドローダウンをプロットする場合
plt.figure(figsize=(12, 6))
for i, (name, data) in enumerate(results.items()):
    plt.plot(data["df"].index, data["df"]["Strategy Drawdown"], 
             label=f"{name} Drawdown", linewidth=1.5)
plt.title(f"{ticker} - Strategy Drawdown")
plt.xlabel("Date")
plt.ylabel("Drawdown")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()