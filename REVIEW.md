# Small-C 直譯器 — 程式碼審查報告

> 審查日期：2026-06-11
> 複查更新：2026-06-11（依 commit `0e762e1` 全面複測，逐項標記已解決／新發現）
> 審查範圍：`src/` 全部模組（lexer / preprocessor / parser / interpreter / memory / symtable / builtins / repl / semantic_checker）
> 審查方式：靜態閱讀 + 動態實測（建立臨時 `.sc` 範例執行，測完即刪，未改動任何既有檔案）

---

## 0. 總體評估

整體是一個品質相當高的 tree-walking 直譯器，管線清楚：

```
source → Preprocessor → Lexer → Parser → Interpreter
         (#define)      (tokens) (AST)    (tree-walking, Visitor)
```

以下項目**經實測全部正確**，可放心：

| 測試項目 | 結果 |
|---|---|
| 遞迴函式（`fib`，自呼叫 + 堆疊框架隔離） | ✅ `0 1 1 2 3 5 8 13 21 34` |
| 指標算術 `*(p+i)`、陣列退化成指標 | ✅ `0 1 4 9 16` |
| `switch` fall-through、字元 case `'b'`、負數 case `-5` | ✅ 正確穿透與匹配 |
| 字串函式 `strcpy`/`strcat`/`strlen` | ✅ `Hello, World len=12` |
| 負數整數除法／取模（朝 0 截斷） | ✅ `-7/2=-3`、`-7%2=-1`、`7/-2=-3`、`7%-2=1` |
| `char` 有號環繞（`char c=200`） | ✅ `c=-56` |
| `%x`（unsigned 32-bit）、移位、位元 `& | ^` | ✅ `ffffffff`、`16`、`8/14/6` |
| block scope 隔離（`if(1){int z;}` 後存取 `z`） | ✅ 正確報 `Undefined symbol 'z'` |

C 語意細節（整數除法截斷方向、char/int 環繞）都按 C 而非 Python 行為實作，符合 `CLAUDE.md` 的設計意圖。

**複查結論（2026-06-11）：** 原報告列出的 3 個確認 Bug 與 7 個次要疑慮（#4–#10）**全部已修復**，實測通過、既有範例零回歸。唯一**待修**的是修復 `CHECK` 時引入的兩個「`CHECK` 擋下、`RUN` 卻能跑」假陽性（見 [§2.5](#25-後續修復進度與新發現)），以及一處過時文件引用（見 [§3](#3-文件不一致)）。

下面的問題依嚴重度排序。

---

## 1. ✅ 原確認的 Bug（已全部修復）

### Bug #1 — `for(int i=...)` 迴圈變數作用域洩漏　✅ 已於 commit `6308ede`「修改迴圈變數bug」修復

> **更新（2026-06-11）：** 已修復，**修法與本報告下方建議幾乎完全一致**——把整個 `for`（含 `init`）包進 `self.memory.push_frame()` + `self.symtable.enter_block()` ... `finally: leave_block()/pop_frame()`，讓 for-init 變數限定在迴圈自己的作用域內、迴圈結束即釋放。
> 實測回歸全數通過：同函式內兩個 `for(int i=...)` → `0 1 2 | 0 2 4`；`continue`+`break` → `0 1 3 4`；巢狀 `for` → `(0,0) (0,1) (1,0) (1,1)`；累加 → `sum=15`。**無回歸。**

**重現程式：**
```c
int main(){
    for(int i=0;i<3;i=i+1){ printf("%d ", i); }    // 正常輸出 0 1 2
    for(int i=0;i<3;i=i+1){ printf("%d ", i*2); }   // ✗ 原本崩潰，現已修復
    return 0;
}
```

**根因（修復前）：** `interpreter.py` `visit_ForNode` 在 `_visit_control_body` *之外* 直接執行 `self.visit(node.init)`，使 for-init 宣告的 `i` 落入函式層 scope 且迴圈結束後不釋放，第二個 `for(int i...)` 重新宣告時 `define_var` 偵測同名 → 拋 `Redefinition`。修復後 for-init 變數限定在迴圈自身的 block scope。

---

### Bug #2 — `CHECK` 不做任何語意檢查，名不符實　✅ 已於 commit `3c3a487`「修改CHECK的bug」修復（新增 `src/semantic_checker.py`）

> **更新（2026-06-11）：** 已修復。新增 `semantic_checker.py`（`SemanticChecker` 類別），`repl.py` `_cmd_check`（約 421 行）改為先 `_parse_full_buffer()` 取得 AST，再以 `SemanticChecker(self.builtins_mgr.functions.keys())` 走一輪靜態語意分析。
> 實測原本漏報的案例現已抓到：
> ```
> sc> CHECK            // int main(){ int x; y = 5; return 0; }
> Semantic Error: Undefined symbol 'y' at line 1   ← 已正確擋下
> ```
> 檢查器涵蓋：未定義變數／函式、重定義、break/continue/return 位置、函式參數個數、非指標解參考、void 當值用、陣列初始化超量、非 void 函式漏 return 等。

> ⚠️ **但此修復引入兩個 `CHECK` 與 `RUN` 不一致的假陽性，尚未解決，詳見 [§2.5](#25-後續修復進度與新發現)。**

---

### Bug #3 — `QUIT` 等互動 `input()` 在 pipe/EOF 下崩潰　✅ 已於 commit `4eef4b3`/`c2ebb2c`/`414edde` 完整修復

> **更新（2026-06-11）：** 已**完整**修復（含原報告殘留項）。
> - 主要修復（`4eef4b3`/`c2ebb2c`）：新增共用函式 `_confirm_discard_changes(action)`（約 200 行），集中處理 `is_dirty` 確認**並捕捉 `EOFError`**（EOF 時換行後回傳 `False`），`_cmd_load`／`_cmd_new`／`_confirm_quit` 三處皆改用它。
> - 殘留項修復（`414edde`）：`_cmd_edit` 的 `input(f"{n:3d} > ")`（約 302 行）**現已包 `try/except EOFError`**；`_cmd_insert`／`_cmd_append`（約 354、370 行）本就已保護。
> 實測 dirty buffer + pipe + `QUIT` 場景：顯示確認提示後 EOF 被接住，回到 `sc>`，再由主迴圈 `start()` 乾淨結束，**Traceback 0 次**。原報告所列 `input()` 風險點現已全部覆蓋。

---

## 2. ✅ 次要疑慮與寬鬆語意（原 #4–#10，已全部處理）

| # | 位置 | 描述 | 狀態 |
|---|---|---|---|
| 4 | `interpreter.py` `visit_VarDeclNode` | 初始化列表超量靜默截斷：`int a[3]={1,2,3,4,5};` 不報錯。 | ✅ 已於 `a02c90f` 修復（interpreter 執行期 + `semantic_checker` CHECK 期雙重檢查，報 "excess elements in array initializer"）。 |
| 5 | `interpreter.py` `_resolve_lvalue` | 對非指標（如 `int x; *x = 1;`）解參考不報錯，可能踩任意記憶體。 | ✅ 已於 `9bbcd8a` 修復（抽出 `_dereference_type()` 統一收緊；checker 亦同步報 "cannot dereference non-pointer type"）。 |
| 6 | `interpreter.py` `visit_FuncCallNode` | non-void 函式漏 `return` 不警告；void 函式被當值用不檢查。 | ✅ 已於 `7bff9b2` 修復（checker 以 `_guarantees_return` 檢查全路徑 return、`_ensure_value_expr` 擋 void 當值用）。⚠️ **`_guarantees_return` 對無窮迴圈判定有新假陽性，見 [§2.5](#25-後續修復進度與新發現)。** |
| 7 | `sc_builtins.py` `builtin_scanf` | 原以 `input().split()` 解析：`%c` 讀不到空白、欄位不足靜默少賦值、`%s` 不防溢位。 | ✅ 已於 `6dc804b` 大幅改寫（逐字元解析，支援 `%d/%c/%s/%x`、跳空白、回傳實際賦值數 `assigned`）。殘留：仍只讀單行、`%s` 未做緩衝區上界檢查（屬低風險寬鬆語意）。 |
| 8 | `sc_builtins.py` `builtin_pow` | 負指數回傳 0。 | ✅ 已於 `1744006` 修復（負指數改為 `raise "pow() exponent must be non-negative"`，不再靜默回 0）。 |
| 9 | `lexer.py` `integer()` | 十六進位判斷用 `isdigit()`，對某些 Unicode 數字也為真。 | ✅ 已於 `6816052` 修復（改用 `_is_hex_digit`／`_is_ascii_digit` 限定 ASCII，並對空 hex literal 報錯）。 |
| 10 | `interpreter.py` 整體 | 深層遞迴撞 Python `RecursionError`，而非模擬 stack overflow。 | ✅ 已於 `77882a4` 修復（新增 `call_depth`／`max_call_depth = 128` 護欄，超限改報 "call stack overflow"，不再噴 Python traceback）。 |

---

## 2.5 後續修復進度與新發現（2026-06-11 逐 commit 複查）

複查了 `6308ede` 起至 `0e762e1` 的所有 commit。修復方向皆正確、既有範例零假陽性（除下述兩處 CHECK 假陽性外）、指標無回歸、真錯誤都能抓到。進度如下：

| Commit | 對應問題 | 狀態 |
|---|---|---|
| `6308ede` 修改迴圈變數bug | Bug #1（for-init 作用域） | ✅ 已修，無回歸 |
| `3c3a487` 修改CHECK的bug | Bug #2（CHECK 不做語意檢查） | ✅ 已修（新增 `src/semantic_checker.py`），但**引入兩個假陽性，見下** ⚠️ |
| `414edde` 修改QUIT的bug | Bug #3 殘留（`_cmd_edit` 的 `input()`） | ✅ 已補上 `EOFError` |
| `a02c90f` 陣列初始化超量 | 次要 #4 | ✅ interpreter + checker 雙重檢查 |
| `9bbcd8a` 非指標解參考 | 次要 #5 | ✅ 抽出 `_dereference_type()` 統一收緊 |
| `7bff9b2` 漏 return／void 當值用 | 次要 #6 | ✅ 已修，但 `_guarantees_return` 引入新假陽性，見下 ⚠️ |
| `6dc804b` 改寫 scanf | 次要 #7 | ✅ 逐字元解析、回傳賦值數 |
| `1744006` pow 負指數 | 次要 #8 | ✅ 改為報錯 |
| `6816052` 十六進位解析 | 次要 #9 | ✅ 限定 ASCII hex |
| `77882a4` 深層遞迴 | 次要 #10 | ✅ `max_call_depth=128` 護欄 |
| `0f9b301` 改檔案結構 | — | 📄 `examples.md`、`*.sc` 移至 `test_data/`（CLAUDE.md 路徑 line 18/26 已同步更新；但 line 59 仍引用 `bug.md`，見 §3） |

### 🔴 待修 N1：`CHECK` 對「前向全域變數」假陽性 —— CHECK 與 RUN 不一致（仍未解決）

`3c3a487` 用 `semantic_checker.py` 修好了 Bug #2，但檢查器對全域變數的處理，與 interpreter 的執行模型不一致，產生假陽性。**2026-06-11 於 `0e762e1` 再次實測，仍會誤報。**

```c
int f(){ return g; }                 // 第 1 行：函式 f 用到全域變數 g
int g;                               // 第 2 行：g 在這裡才宣告
int main(){ g = 42; return f(); }    // 第 3 行
```

| 指令 | 結果（實測 `0e762e1`） |
|---|---|
| `CHECK` | ❌ `Semantic Error: Undefined symbol 'g' at line 1` |
| `RUN` | ✅ `Program exited with return value 42.` |

**根因（`semantic_checker.py` `check_ProgramNode`，約 150 行）：** 檢查器對「函式」做了**兩階段**（第一輪 `for decl ... if isinstance(decl, FuncDefNode): self.functions[...] = decl` 先把所有函式名註冊，所以函式間前向呼叫沒問題），但對「全域變數」沒有——全域變數要等第二輪「逐行檢查、輪到那一行」才在 `check_VarDeclNode` 裡 `_define_var` 進 `scopes[0]`。因此排在某全域變數**之前**的函式，其 body 引用該變數時，變數尚未進入作用域 → 誤報 `Undefined symbol`。

而 interpreter（`visit_ProgramNode`）是「**先掃完所有頂層宣告**，**才呼叫 main()**」，全域變數整份檔案可見、順序無關 → RUN 能跑。落差就表現為這個假陽性。

**建議修法：** 在 `check_ProgramNode` 第一輪迴圈（約 153–159 行），除了登記函式，也把所有頂層 `VarDeclNode` 先 `_define_var` 進 `scopes[0]`（讓全域變數比照函式「整份檔案可見」），第二輪再做實際檢查。如此前向全域變數不再誤判，真正未宣告的變數仍會被抓到。**不建議**反向把 RUN 改成強制先宣告後使用（會破壞現有能跑的程式）。

### 🔴 待修 N2（本次新發現）：`_guarantees_return` 對「無窮迴圈一定 return」誤判 —— CHECK 與 RUN 不一致

`7bff9b2` 修 #6 時，`semantic_checker.py` 新增 `_guarantees_return`（約 123 行）判斷「非 void 函式是否所有路徑都 return」，但**只處理 `ReturnNode`／`BlockNode`／`IfNode`（且 if 需有 else）**，未考慮「無窮迴圈內 return」這種一定會 return 的情形。於是合法的 C 函式被 CHECK 擋下，RUN 卻能正常執行。**2026-06-11 於 `0e762e1` 實測：**

```c
int f(){ while(1){ return 1; } }     // 合法：無窮迴圈內必 return，無 fall-through
int main(){ return f(); }
```

| 指令 | 結果（實測 `0e762e1`） |
|---|---|
| `CHECK` | ❌ `Semantic Error: non-void function 'f' reached end without return at line 1` |
| `RUN` | ✅ `Program exited with return value 1.` |

`for(;;){ return 7; }` 同樣會被誤報。對照組 `int sign(int x){ if(x>0) return 1; return 0; }`（末尾有 return）則正確通過，所以問題**僅限**「函式靠無窮迴圈保證 return、末尾沒有顯式 return」這種寫法。

**根因：** `_guarantees_return` 缺少對 `WhileNode`／`ForNode`／`DoWhileNode`（無條件或常數真條件且無 `break`）與「窮舉所有 case 的 `switch`」的判定。

**影響：** 觸發條件較窄（多數人會在函式尾補 `return`），但一旦踩到就是「`CHECK` 擋下、`RUN` 卻能跑」的自相矛盾，與 N1 同類，削弱 `CHECK` 可信度。

**建議修法（擇一）：**
- (A) 在 `_guarantees_return` 補上：`while(C)`／`for(init;C;...)` 當 `C` 省略或為恆真常數（如 `1`）且迴圈體內沒有跳出該迴圈的 `break` 時，視為「保證 return」；`do{...}while` 同理。
- (B) 保守降級：把「非 void 函式漏 return」從 `CHECK` 的**硬性錯誤**改成**警告**（warning），避免擋下實際可執行的程式——這也能順帶緩解 N1 的體感（CHECK 不再「擋下能跑的程式」）。

### 其他邊角（低優先，記錄備查）
- **switch case 作用域不一致**：`check_SwitchNode`（約 327 行）對每個 `case` 開獨立 scope，但 interpreter 的 case 共享 function scope；在 case 內宣告變數時兩者行為會不同。switch 內宣告變數罕見。
- **解參考函式回傳指標 `*func()`**：`_get_node_type`／`_expr_type` 對 `FuncCallNode` 以 `return_type` 推導，但若回傳型別資訊丟失指標深度，`*func()` 即使回傳指標也可能被 `_dereference_type` 誤判。屬既有限制，罕見。

---

## 3. 📄 文件不一致（仍待處理）

- **`bug.md` 已不存在，但 `CLAUDE.md`「重要慣例與陷阱 → 已知 bug 與缺口」段落（line 59）仍引用它**，且該段所列 bug（指標複合賦值 `p += 1` 崩潰、`switch` 只接受 `INT_CONST`、指標算術未乘 `sizeof`、陣列元素 `++` 未實作）**實測皆已修復**。
  → 建議：更新 `CLAUDE.md` line 59，移除對 `bug.md` 的引用，或以本報告取代之。
  → 註：`CLAUDE.md` 的 `*.sc` 路徑（line 18、26）已隨 `0f9b301` 同步更新為 `test_data/`，僅 line 59 的 bug.md 引用尚未清。

---

## 4. 建議處理優先序（更新後）

1. ~~**Bug #1（for-init 作用域）**~~ — ✅ 已於 `6308ede` 修復。
2. ~~**Bug #2（CHECK 語意檢查）**~~ — ✅ 已於 `3c3a487` 修復（新增 `semantic_checker.py`）。
3. ~~**Bug #3（EOF 崩潰）**~~ — ✅ 已於 `4eef4b3`/`c2ebb2c`/`414edde` 完整修復。
4. ~~**次要疑慮 #4–#10**~~ — ✅ 已全部修復。
5. **🔴 N1（CHECK 前向全域變數假陽性）** — 唯一需碰程式的待修項之一；在 `check_ProgramNode` 第一輪預先登記頂層全域變數。
6. **🔴 N2（CHECK 無窮迴圈 return 誤判）** — 補 `_guarantees_return` 對無窮迴圈／窮舉 switch 的判定，或把漏 return 降為警告。
7. **📄 文件**：清掉 `CLAUDE.md` line 59 對已不存在的 `bug.md` 之引用。
