from lexer import Lexer, Token
from parser import Parser
from ast_node import *

# ─── 輔助函式 ────────────────────────────────────────────────────────────────

def print_ast(node, indent=0):
    """遞迴印出 AST，方便肉眼確認結構"""
    prefix = "  " * indent
    if isinstance(node, IntLiteralNode):
        print(f"{prefix}IntLiteral({node.value})")
    elif isinstance(node, CharLiteralNode):
        print(f"{prefix}CharLiteral({repr(node.value)})")
    elif isinstance(node, StringLiteralNode):
        print(f"{prefix}StringLiteral({repr(node.value)})")
    elif isinstance(node, VarNode):
        print(f"{prefix}Var({node.name})")
    elif isinstance(node, TypeNode):
        print(f"{prefix}Type({node.base_type}{'*'*node.pointer_depth})")
    elif isinstance(node, BinOpNode):
        print(f"{prefix}BinOp({node.op})")
        print_ast(node.left,  indent + 1)
        print_ast(node.right, indent + 1)
    elif isinstance(node, UnaryOpNode):
        pos = "prefix" if node.prefix else "postfix"
        print(f"{prefix}UnaryOp({node.op}, {pos})")
        print_ast(node.operand, indent + 1)
    elif isinstance(node, AssignNode):
        print(f"{prefix}Assign({node.op})")
        print_ast(node.target, indent + 1)
        print_ast(node.value,  indent + 1)
    elif isinstance(node, VarDeclNode):
        arr = "[array]" if node.array_size else ""
        print(f"{prefix}VarDecl({node.name}{arr})")
        print_ast(node.type_node, indent + 1)
        if node.init_expr: print_ast(node.init_expr, indent + 1)
    elif isinstance(node, FuncDefNode):
        print(f"{prefix}FuncDef({node.name})")
        print_ast(node.return_type, indent + 1)
        for p in node.params: print_ast(p, indent + 1)
        print_ast(node.body, indent + 1)
    elif isinstance(node, BlockNode):
        print(f"{prefix}Block")
        for s in node.statements: print_ast(s, indent + 1)
    elif isinstance(node, ExprStmtNode):
        print(f"{prefix}ExprStmt")
        print_ast(node.expr, indent + 1)
    elif isinstance(node, IfNode):
        print(f"{prefix}If")
        print_ast(node.condition, indent + 1)
        print_ast(node.then_block, indent + 1)
        if node.else_block:
            print(f"{prefix}Else")
            print_ast(node.else_block, indent + 1)
    elif isinstance(node, WhileNode):
        print(f"{prefix}While")
        print_ast(node.condition, indent + 1)
        print_ast(node.body, indent + 1)
    elif isinstance(node, ForNode):
        print(f"{prefix}For")
        if node.init:      print_ast(node.init,      indent + 1)
        if node.condition: print_ast(node.condition, indent + 1)
        if node.update:    print_ast(node.update,    indent + 1)
        print_ast(node.body, indent + 1)
    elif isinstance(node, ReturnNode):
        print(f"{prefix}Return")
        if node.value: print_ast(node.value, indent + 1)
    elif isinstance(node, FuncCallNode):
        print(f"{prefix}FuncCall({node.name})")
        for a in node.args: print_ast(a, indent + 1)
    elif isinstance(node, ProgramNode):
        print(f"{prefix}Program")
        for d in node.declarations: print_ast(d, indent + 1)
    else:
        print(f"{prefix}{type(node).__name__}")

def run_parser_test(name, code, expect_error=False):
    """執行一個 Parser 測試，印出 AST 或錯誤"""
    print(f"\n{'='*60}")
    print(f"[Parser] {name}")
    try:
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()
        if expect_error:
            print("  [FAIL] Expected error, parsed successfully")
        else:
            print("  [OK] AST:")
            print_ast(ast, indent=2)
    except Exception as e:
        if expect_error:
            print(f"  [OK] Correctly raised: {e}")
        else:
            print(f"  [FAIL] Unexpected error: {e}")

def run_test(name, code, expect_error=False):
    """執行一個測試案例，印出結果"""
    print(f"\n{'='*60}")
    print(f"[測試] {name}")
    print(f"  輸入: {repr(code)}")
    try:
        tokens = Lexer(code).tokenize()
        if expect_error:
            print(f"  [FAIL] 預期拋出錯誤，但成功 tokenize 了")
        else:
            print(f"  [OK] 結果:")
            for tok in tokens:
                print(f"     {tok}")
    except Exception as e:
        if expect_error:
            print(f"  [OK] 正確拋出錯誤: {e}")
        else:
            print(f"  [FAIL] 意外錯誤: {e}")

# ─── 測試案例 ─────────────────────────────────────────────────────────────────

def main():

    # 1. 關鍵字
    run_test("關鍵字",
             "int char void if else while for do break continue return")

    # 2. 識別字
    run_test("識別字",
             "foo _bar x123 myVar _")

    # 3. 十進位整數
    run_test("十進位整數",
             "0 42 1000")

    # 4. 十六進位整數
    run_test("十六進位整數",
             "0xff 0X1A 0x0")

    # 5. 十六進位無數字 → 錯誤
    run_test("十六進位無數字（應報錯）",
             "0x", expect_error=True)

    # 6. 字元常數（普通）
    run_test("字元常數（普通字元）",
             "'a' 'Z' '5'")

    # 7. 字元常數（跳脫序列）
    run_test("字元常數（跳脫序列）",
             r"'\n' '\t' '\0' '\\' '\'' '\"'")

    # 8. 空字元常數 → 錯誤
    run_test("空字元常數（應報錯）",
             "''", expect_error=True)

    # 9. 字串常數（普通）
    run_test("字串常數（普通）",
             '"hello" "SmallC"')

    # 10. 字串常數（含跳脫序列）
    run_test("字串常數（含跳脫序列）",
             r'"line1\nline2" "tab\there" "quote\""')

    # 11. 字串含真實換行 → 錯誤
    run_test("字串含真實換行（應報錯）",
             '"abc\ndef"', expect_error=True)

    # 12. 字串未閉合 → 錯誤
    run_test("字串未閉合（應報錯）",
             '"unclosed', expect_error=True)

    # 13. 字串結尾反斜線 → 錯誤
    run_test("字串結尾反斜線 EOF（應報錯）",
             '"abc\\', expect_error=True)

    # 14. 算術與複合賦值運算子
    run_test("算術與複合賦值",
             "a + b - c * d / e % f")
    run_test("複合賦值",
             "a += 1; b -= 2; c *= 3; d /= 4; e %= 5")

    # 15. 遞增遞減
    run_test("遞增遞減",
             "++i --j")

    # 16. 比較運算子
    run_test("比較運算子",
             "a == b != c < d > e <= f >= g")

    # 17. 邏輯運算子
    run_test("邏輯運算子",
             "a && b || c !d")

    # 18. 位元運算子
    run_test("位元運算子",
             "a & b | c ^ d ~e a << 2 b >> 1")

    # 19. 括號、大括號、方括號
    run_test("括號類",
             "( ) [ ] { }")

    # 20. 標點符號
    run_test("標點符號",
             "; , : ? .")

    # 21. 單行註解
    run_test("單行註解",
             "int x // this is a comment\n x = 1;")

    # 22. 多行註解
    run_test("多行註解",
             "int /* block\ncomment */ x;")

    # 23. 未閉合多行註解 → 錯誤
    run_test("未閉合多行註解（應報錯）",
             "int x /* unclosed", expect_error=True)

    # 24. 綜合：C 風格函式
    run_test("綜合：C 函式宣告",
             'int add(int a, int b) { return a + b; }')

    # 25. 未知字元 → 錯誤
    run_test("未知字元（應報錯）",
             "int x = 1 @ 2;", expect_error=True)

    # 26. 空字串輸入
    run_test("空輸入",
             "")

    print(f"\n{'='*60}")
    print("Lexer Tests Done")

    # ─── Parser 測試 ──────────────────────────────────────────────────────────
    run_parser_test("simple function",
        "int main() { return 0; }")
    run_parser_test("var decl + add",
        "int add(int a, int b) { int x = a + b; return x; }")
    run_parser_test("if-else",
        "int f(int x) { if (x > 0) { return 1; } else if (x==0){ return 0; } else {return -1;} }")
    run_parser_test("while loop",
        "void loop() { int i = 0; while (i < 10) { i = i + 1; } }")
    run_parser_test("for loop",
        "void f() { for (int i = 0; i < 5; i++) { } }")
    run_parser_test("expr priority 1+2*3",
        "int f() { return 1 + 2 * 3; }")
    run_parser_test("function call",
        "int f() { return add(1, 2); }")
    run_parser_test("syntax error (missing semicolon)",
        "int f() { int x = 1 }", expect_error=True)

    print(f"\n{'='*60}")
    print("Parser Tests Done")

if __name__ == "__main__":
    main()