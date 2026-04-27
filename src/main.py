from lexer import Lexer, Token

# ─── 輔助函式 ────────────────────────────────────────────────────────────────

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
    print("所有測試完成")

if __name__ == "__main__":
    main()