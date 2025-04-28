# Investment Portfolio Rebalancer

本專案可協助你在新增現金後，根據目標配置自動計算美股/台股的加碼數量，並產生詳細報告。

## 功能特色
- 支援多市場（美股/台股）
- 自動取得即時匯率與股價
- 以美元為主結算
- 產生加碼建議（to_buy.json）與完整報告（report.json）

## 安裝方式
1. 安裝 Python 3.8 以上
2. 安裝必要套件：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法
1. 準備兩個檔案於專案根目錄：
   - `holdings.json`：現有持股數量，例如：
     ```json
     { "AAPL": 10, "TSLA": 5, "2330.TW": 20 }
     ```
   - `target_alloc.json`：目標配置比例（加總需為 1），例如：
     ```json
     { "AAPL": 0.3, "TSLA": 0.3, "2330.TW": 0.4 }
     ```
2. 編輯 `rebalancing.py` 內的 `NEW_CASH_TWD` 參數，設定你要投入的新台幣金額。
3. 執行：
   ```bash
   python rebalancing.py
   ```

## 輸出說明
- `to_buy.json`：建議加碼數量（每個標的應買幾股）
- `report.json`：詳細報告，包含每個標的原始與新持股、價格、總價（皆以美元計價），以及總結資產價值。

---
如有問題歡迎提 issue！ 