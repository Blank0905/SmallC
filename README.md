# [專案名稱] - A Small C Implementation in Python 3

## 環境需求

- Python 3.10+
- 無第三方套件依賴


## 執行方式

```bash
cd src
python main.py
```
使用 `LOAD` 載入 `.sc` 檔案，或直接在提示符`sc>`後輸入 SmallC 程式碼。

### 互動式 REPL 指令

**1. 程式管理指令**
- `LOAD <filename>`：從檔案載入 Small-C 原始碼
- `SAVE <filename>`：儲存目前程式緩衝區至檔案
- `LIST` / `LIST <n>` / `LIST <n1>-<n2>`：列出程式碼
- `EDIT <n>`：編輯特定行的程式碼
- `DELETE <n>` / `DELETE <n1>-<n2>`：刪除特定行
- `INSERT <n>`：在特定行之前插入程式碼
- `APPEND`：在緩衝區末尾進入多行輸入模式
- `NEW`：清除緩衝區並重置執行狀態

**2. 執行與除錯指令**
- `RUN`：執行目前緩衝區的程式
- `CHECK`：進行語法與語意檢查但不執行
- `TRACE ON` / `TRACE OFF`：開啟/關閉執行追蹤模式（顯示執行軌跡）
- `VARS`：顯示目前所有全域變數名稱、型別與值
- `FUNCS`：顯示目前已定義的所有函式清單

**3. 系統指令**
- `HELP` / `HELP <command>`：顯示輔助說明
- `ABOUT`：顯示解譯器資訊
- `CLEAR`：清除終端機畫面
- `QUIT` / `EXIT`：結束解譯器