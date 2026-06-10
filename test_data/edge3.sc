int main() {
    int a = 5;
    int b = 5;
    int res_a;
    int res_b;

    printf("=== 測試 1: Prefix (++a) ===\n");
    res_a = ++a; 
    printf("a 的值: %d (預期: 6)\n", a);
    printf("res_a 的值: %d (預期: 6)\n", res_a);

    printf("\n=== 測試 2: Postfix (b++) ===\n");
    res_b = b++; 
    printf("b 的值: %d (預期: 6)\n", b);
    printf("res_b 的值: %d (預期: 5)\n", res_b);

    printf("\n=== 測試 3: 遞減運算 (--x 與 y--) ===\n");
    int x = 10;
    int y = 10;
    printf("--x 在表達式中回傳: %d (預期: 9)\n", --x);
    printf("x 執行後的值: %d (預期: 9)\n", x);
    
    printf("y-- 在表達式中回傳: %d (預期: 10)\n", y--);
    printf("y 執行後的值: %d (預期: 9)\n", y);

    return 0;
}