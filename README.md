# SmallC 互動式解譯器

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)
![無第三方依賴](https://img.shields.io/badge/dependencies-none-green)

## 專案概述

本專案是一個以 **Python 3** 完整實作的 **Small-C** 互動式解譯器。

本專案為**系統程式**課程的期末專題，整合並延伸了系統軟體的核心技術——包含符號表管理、詞法分析、語法導向處理與執行期環境模擬——從組合語言處理器的概念延伸到高階語言直譯器的實作。

整個解譯器以 **Python 3 標準函式庫**實作、**無任何第三方套件依賴**。

## 主要特色

- **互動式 REPL** — 在 `sc>` 提示符後輸入 Small-C 程式碼，遇到區塊、迴圈、函式時會自動偵測並進入多行續行模式
- **程式緩衝區管理** — 完整的編輯指令集（`LOAD`、`SAVE`、`LIST`、`EDIT`、`DELETE`、`INSERT`、`APPEND`、`NEW`），可在環境內直接開發原始碼
- **遞迴下降剖析器** — 完整處理各層運算子優先級與結合性
- **樹狀走訪直譯器** — 直接走訪 AST 執行，支援函式呼叫與遞迴
- **模擬記憶體模型** — 以 64KB 線性 `bytearray` 模擬位元組定址記憶體，支援陣列、指標、指標算術與取址操作
- **23 個內建函式** — 涵蓋 I/O（`printf`、`scanf`、`putchar`、`getchar`、`puts`）、字串（`strlen`、`strcpy`、`strcmp`、`strcat`）、數學（`abs`、`max`、`min`、`pow`、`sqrt`、`mod`、`rand`、`srand`）與工具（`memset`、`atoi`、`itoa`、`sizeof_int`、`sizeof_char`、`exit`）
  > 註：`pow(base, exp)` 回傳 `base` 的 `exp` 次方；當 `exp` 為負數時回傳 `0`（整數除法的自然結果），`exp` 為 `0` 時回傳 `1`。
- **執行追蹤** — `TRACE ON/OFF` 模式可在執行時逐行顯示語句與行號，方便除錯
- **狀態檢視** — `VARS` 顯示所有全域變數的名稱、型別與值；`FUNCS` 列出使用者定義函式與內建函式
- **語法檢查** — `CHECK` 指令只做語法與語意檢查而不執行
- **錯誤處理** — 清楚的語法錯誤與執行期錯誤訊息（除以零、陣列越界、型別錯誤等）
- **前置處理器** — 支援 object-like `#define` 常數巨集展開
- **註解** — 同時支援 C 風格區塊註解（`/* */`）與 C++ 單行註解（`//`）

## 支援的語言特性

| 類別 | 支援內容 |
|------|----------|
| **資料型別** | `int`（32-bit 有號）、`char`（8-bit 有號）、`int*`、`char*` |
| **常數** | 十進位整數、字元常數（`'A'`）、字串常數（`"hello"`）與跳脫序列（`\n`、`\t`、`\0`、`\\`、`\'`、`\"`） |
| **運算子** | 算術（`+`、`-`、`*`、`/`、`%`）、關係（`<`、`<=`、`>`、`>=`、`==`、`!=`）、邏輯（`&&`、`\|\|`、`!`）、位元（`&`、`\|`、`^`、`~`、`<<`、`>>`）、指定（`=`、`+=`、`-=`、`*=`、`/=`、`%=`）、前置遞增/遞減（`++x`、`--x`）、**後置遞增/遞減（`x++`、`x--`）**、三元（`? :`） |
| **控制流程** | `if`/`else`（可串接）、`while`、`for`（含 `for(int i=...)` 迴圈變數宣告）、`do`/`while`、`break`、`continue`、`return`、**`switch`/`case`（含 fall-through、字元/負數 case）** |
| **函式** | 使用者自定函式，支援 `int`/`char`/`void` 回傳型別、傳值呼叫、指標參數與遞迴 |
| **陣列** | 一維陣列、編譯期決定大小、由 0 起算 |
| **指標** | 取址（`&`）、解參考（`*`）、指標算術 |
| **區塊作用域** | **`if`/`while`/`for`/`do-while` 區塊（`{}`）內可宣告區域變數，離開區塊後失效（block scope）** |

> 注意：Small-C **不支援** float／struct／多層指標。

## 環境需求

- Python 3.10 或更新版本
- 無需安裝任何第三方套件，僅使用 Python 標準函式庫

## 執行方式

### 啟動解譯器

模組採用扁平 import，**必須先進入 `src/` 目錄**再啟動：

```bash
cd src
python main.py
```

啟動後會進入互動模式，提示符為 `sc>`。輸入 `HELP` 可查看完整指令清單。

### 即時模式

直接在提示符後輸入語句即可即時執行：

```
sc> printf("%d\n", 2 + 3 * 4);
14
sc> int x = 42;
sc> printf("x = %d\n", x);
x = 42
```

多行結構（函式、迴圈、條件式）會被自動偵測，提示符會持續續行，直到所有括號與引號平衡為止：

```
sc> int factorial(int n) {
        if (n <= 1) return 1;
        return n * factorial(n - 1);
    }
sc> printf("5! = %d\n", factorial(5));
5! = 120
```

### 程式緩衝區模式

用 `LOAD` 載入 `.sc` 檔（或用 `APPEND` 手動輸入）後，以 `RUN` 執行整個緩衝區：

```
sc> LOAD test.sc
sc> RUN
```

`test_data/` 目錄附有多個範例程式：`primes.sc`（質數）、`edge1.sc`~`edge3.sc`、`edge_ptr.sc`、`test.sc` 等。

### 互動式 REPL 指令

**1. 程式管理指令**

| 指令 | 說明 |
|------|------|
| `LOAD <filename>` | 從檔案載入 Small-C 原始碼 |
| `SAVE <filename>` | 儲存目前程式緩衝區至檔案 |
| `LIST` / `LIST <n>` / `LIST <n1>-<n2>` | 列出程式碼（全部／單行／範圍） |
| `EDIT <n>` | 編輯特定行的程式碼 |
| `DELETE <n>` / `DELETE <n1>-<n2>` | 刪除特定行 |
| `INSERT <n>` | 在特定行之前插入程式碼 |
| `APPEND` | 在緩衝區末尾進入多行輸入模式，以單獨一行的 `.` 停止 |
| `NEW` | 清除緩衝區並重置執行狀態 |

**2. 執行與除錯指令**

| 指令 | 說明 |
|------|------|
| `RUN` | 執行目前緩衝區的程式（從 `main()` 開始） |
| `CHECK` | 進行語法與語意檢查但不執行 |
| `TRACE ON` / `TRACE OFF` | 開啟／關閉執行追蹤模式（顯示執行軌跡） |
| `VARS` | 顯示目前所有全域變數的名稱、型別與值 |
| `FUNCS` | 顯示已定義的所有函式清單，內建函式以 `[built-in]` 標示 |

**3. 系統指令**

| 指令 | 說明 |
|------|------|
| `HELP` / `HELP <command>` | 顯示輔助說明 |
| `ABOUT` | 顯示解譯器資訊 |
| `CLEAR` | 清除終端機畫面 |
| `QUIT` | 結束解譯器 |

## 專案結構

```
SmallC/
├── src/                    # 原始碼（扁平 import，須在此目錄執行）
│   ├── main.py             # 程式入口（啟動器）
│   ├── repl.py             # 互動式 REPL 環境（LiveREPL）
│   ├── preprocessor.py     # #define 常數巨集展開
│   ├── lexer.py            # 詞法分析器（產生 token 串）
│   ├── ast_node.py         # 抽象語法樹節點定義
│   ├── sc_parser.py        # 遞迴下降剖析器
│   ├── semantic_checker.py # 靜態語意檢查（供 CHECK 使用）
│   ├── memory.py           # 模擬位元組定址記憶體（64KB）
│   ├── symtable.py         # 符號表（全域／函式區域兩層作用域）
│   ├── interpreter.py      # 樹狀走訪直譯器（含 TRACE）
│   └── sc_builtins.py      # 23 個內建函式
├── test_data/              # 範例 Small-C 程式
│   ├── primes.sc           # 範例：質數
│   ├── edge1.sc ~ edge3.sc # 邊界測試範例
│   ├── edge_ptr.sc         # 指標邊界測試
│   ├── test.sc             # 綜合測試範例
│   └── examples.md         # 作業範例 1–18
├── LICENSE                 # MIT 授權條款
└── README.md
```

## 架構

解譯器採用經典的管線架構，原始碼依序流經各個處理階段：

```
原始碼 → 前置處理器 → 詞法分析器 → 剖析器 → AST → 直譯器 → 輸出
         (#define)     (tokens)      (語法)              ↕
                                                    記憶體模型
                                                    符號表
                                                    內建函式
```

| 模組 | 職責 |
|------|------|
| `preprocessor.py` | 展開 object-like `#define` 常數巨集（會跳過字串／字元／註解內容） |
| `lexer.py` | 將原始碼轉為具型別的 token 串（字元常數在此即轉為 `ord()` 整數值） |
| `sc_parser.py` | 以遞迴下降剖析建構 AST，每個運算子優先級一個方法 |
| `semantic_checker.py` | `CHECK` 指令使用的靜態語意檢查，不執行程式 |
| `memory.py` | 模擬 64KB 線性記憶體：全域變數由位址 0 往上長，區域變數由尾端往下長 |
| `symtable.py` | 管理變數符號，支援全域、函式區域、block scope 三層作用域查找 |
| `interpreter.py` | 以 Visitor 模式走訪 AST 執行語句，控制流程以 Python 例外實作，支援 TRACE |
| `sc_builtins.py` | 實作全部 23 個內建函式（內建函式優先於使用者函式分派） |

## 授權

本專案採用 MIT 授權條款，詳見 [LICENSE](LICENSE)。

作者：Blank0905、Boris642、JayTangu
