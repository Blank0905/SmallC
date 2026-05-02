# VARS / FUNCS 修改說明

## 問題原因

`FUNCS` 原本會讀取 `func_node.line`，但 `FuncDefNode` 沒有保存函式起始行號，所以執行時會發生屬性錯誤。另一個問題是參數型別只印 `base_type`，例如 `int *arr` 會被顯示成 `int arr`，指標資訊不見。

`FUNCS` 也依賴 `RUN` 後的符號表，所以 `LOAD -> CHECK -> FUNCS` 這種流程無法列出目前 buffer 已定義的函式。

`VARS` 原本把全域變數顯示邏輯直接寫在指令裡，對指標與陣列的輸出不夠集中，也沒有明確標示指標目前存放的位址值。

## 修改方式

- `FuncDefNode` 新增 `line` 欄位，parser 在讀到函式名稱 token 時把行號傳進去。
- `FUNCS` 改為直接解析目前 `code_buffer`，列出目前已定義的使用者函式；內建函式仍以 `[built-in]` 標示。
- 型別顯示改用 `base_type + "*" * pointer_depth`，所以 `int *arr` 會顯示為 `int* arr`。
- `VARS` 只列出全域變數，符合指令規格。
- `VARS` 對陣列顯示長度與前十個元素，超過十個以 `...` 省略。
- `VARS` 對指標明確顯示其存放的位址值，例如 `int* p = address: 5`，並額外嘗試顯示該位址指向的值。

## 為什麼這樣改

行號是 parser 最清楚的資訊，所以在建立 AST 節點時保存，比在 `FUNCS` 裡事後猜測可靠。

`FUNCS` 是查詢「目前已定義函式」的指令，不應該要求程式先執行；直接解析 buffer 可以支援 `LOAD -> CHECK -> FUNCS`。

`VARS` 根據規格顯示全域變數即可；函式區域變數在函式結束時會離開作用域並釋放 stack frame，不應混入全域變數列表。
