#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Re-balance your portfolio after adding new cash (TWD base).
含自動匯率與多市場（US / TW）處理。
"""

import json, sys, math
from pathlib import Path
import pandas as pd
import yfinance as yf
from tabulate import tabulate

# ======== 使用者設定 ========
HOLDINGS_FILE = Path("holdings.json")
TARGET_FILE   = Path("target_alloc.json")
NEW_CASH_TWD  = 4_000_000            # 新增現金（台幣）
SHOW_ZERO     = False                # 是否列出「不用加碼」的股票
# ============================


def jload(p: Path):
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def fetch_prices(symbols: list[str]) -> dict[str, float]:
    """回傳 {symbol: (price, currency)}，currency: 'USD' or 'TWD'"""
    all_symbols = symbols + ["USDTWD=X"]
    raw = yf.download(
        " ".join(all_symbols),
        period="1d",
        interval="1d",
        progress=False,
        threads=True,
        group_by="ticker",
    )

    missing = []
    # Check if USDTWD=X exists and has data
    if "USDTWD=X" not in raw or raw["USDTWD=X"]["Close"].dropna().empty:
        missing.append("USDTWD=X (forex rate)")
    # Check each symbol
    for s in symbols:
        if s not in raw or raw[s]["Close"].dropna().empty:
            missing.append(s)
    if missing:
        print(f"❌ 無法取得以下標的價格: {', '.join(missing)}")
        print("請檢查網路連線、ticker 是否正確，或稍後再試。")
        sys.exit(1)

    fx = raw["USDTWD=X"]["Close"].dropna()[-1]   # 美元兌台幣
    prices = {}
    for s in symbols:
        last = raw[s]["Close"].dropna()[-1]
        if s.endswith(".TW"):
            prices[s] = (float(last), "TWD")
        else:
            prices[s] = (float(last), "USD")
    return prices, fx


def main():
    hold   = jload(HOLDINGS_FILE)
    target = jload(TARGET_FILE)

    if abs(sum(target.values()) - 1) > 1e-6:
        sys.exit("❌  target_alloc.json 權重加總必須等於 1")

    symbols = sorted(set(hold) | set(target))
    prices, usd_twd = fetch_prices(symbols)

    # 計算目前持有價值（統一換成 TWD）
    cur_val = 0
    for s, qty in hold.items():
        px, ccy = prices[s]
        cur_val += qty * (px * (usd_twd if ccy == "USD" else 1))

    total_capital = cur_val + NEW_CASH_TWD

    plan = []
    for s in symbols:
        px, ccy   = prices[s]
        px_twd    = px * (usd_twd if ccy == "USD" else 1)
        tgt_val   = target.get(s, 0) * total_capital
        held_val  = hold.get(s, 0) * px_twd
        diff_val  = tgt_val - held_val
        buy_shrs  = 0 if diff_val <= 0 else math.floor(diff_val / px_twd)

        plan.append(
            dict(
                Symbol=s,
                Price=f"{px:.2f} {ccy}",
                Price_TWD=round(px_twd, 2),
                Own=hold.get(s, 0),
                Buy=buy_shrs,
                Cost_TWD=round(buy_shrs * px_twd, 2),
            )
        )

    df = pd.DataFrame(plan).set_index("Symbol")
    if not SHOW_ZERO:
        df = df[df["Buy"] > 0]

    print("\n⚖️  Re-balancing proposal")
    print(tabulate(df, headers="keys", tablefmt="github"))

    out = df["Buy"].astype(int).to_dict()
    Path("to_buy.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print("\n✅  已輸出 to_buy.json")

    # ===== 新增 report.json 輸出（以美元為主） =====
    report = {}
    orig_total = 0.0
    new_total = 0.0
    for s in symbols:
        px, ccy = prices[s]
        px_usd = px if ccy == "USD" else px / usd_twd
        own_qty = hold.get(s, 0)
        own_val_usd = own_qty * px_usd
        buy_qty = df.loc[s, "Buy"] if s in df.index else 0
        new_qty = own_qty + buy_qty
        new_val_usd = new_qty * px_usd
        report[s] = {
            "orig_qty": int(own_qty),
            "orig_price_usd": float(round(px_usd, 2)),
            "orig_value_usd": float(round(own_val_usd, 2)),
            "new_qty": int(new_qty),
            "new_price_usd": float(round(px_usd, 2)),
            "new_value_usd": float(round(new_val_usd, 2)),
            "currency": ccy,
        }
        orig_total += own_val_usd
        new_total += new_val_usd
    report_out = {
        "summary": {
            "orig_total_usd": float(round(orig_total, 2)),
            "new_total_usd": float(round(new_total, 2)),
        },
        "positions": report
    }
    Path("report.json").write_text(json.dumps(report_out, indent=2, ensure_ascii=False))
    print("✅  已輸出 report.json")


if __name__ == "__main__":
    main()