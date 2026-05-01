# SmallC — 互動式 C 語言解譯器

A Small-C interactive interpreter implemented in Python 3, developed as a final project for the Programming Languages course.

## 功能概覽

### 支援的語言特性

| 類別 | 支援內容 |
|------|---------|
| **資料型別** | `int`、`char`、`int*`、`char*`、`void`（不支援浮點數、`struct`、多層指標等） |
| **字面量** | 十進位整數、十六進位整數（`0x`）、字元（含跳脫序列 `\n`、`\t`、`\0` 等）、字串 |
| **算術運算子** | `+` `-` `*` `/` `%`、`++` `--`（前綴必備，後綴為自選加分項） |
| **位元運算子** | `&` `|` `^` `~` `<<` `>>` |
| **邏輯運算子** | `&&`（支援短路求值）、`||`（支援短路求值）、`!` |
| **比較運算子** | `==` `!=` `<` `>` `<=` `>=` |
| **賦值運算子** | `=` `+=` `-=` `*=` `/=` `%=` |
| **控制結構** | `if-else`（含 `else if` 鏈式）、`while`、`for`、`do-while`、`break`、`continue`、`return` |
| **加分項** | `switch/case/default`、三元運算子 `? :`、後綴 `++`/`--` 等 |
| **內建 I/O** | `putchar`、`getchar`、`printf`（`%d` `%c` `%s` `%x` `%%`）、`puts`、`scanf`（`%d` `%c`） |
| **字串與數學**| `strlen`、`strcpy`、`strcmp`、`strcat`、`abs`、`max`、`min`、`pow`、`sqrt`、`mod`、`rand`、`srand` |
| **記憶體與其他**| `memset`、`sizeof_int`、`sizeof_char`、`atoi`、`itoa`、`exit` |

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

## 環境需求

- Python 3.10+
- 無第三方套件依賴

## 執行方式

```bash
cd src
python main.py
```

進入 REPL 後，使用 `LOAD` 載入 `.sc` 檔案，或直接在提示符後輸入 SmallC 程式碼。

## SmallC 程式範例

```c
int add(int a, int b) {
    return a + b;
}

int main() {
    int result = add(3, 4);
    printf("%d\n", result);
    return 0;
}
```