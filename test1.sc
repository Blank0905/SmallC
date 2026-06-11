/* test1.sc — 算術、位元、邏輯運算與運算子優先級
 * 展示：四則運算、截斷除法、位元操作、移位、邏輯運算 */

int main() {
    /* 四則運算與優先級 */
    printf("=== 四則運算與優先級 ===\n");
    printf("2 + 3 * 4        = %d  (expect 14)\n",  2 + 3 * 4);
    printf("(2 + 3) * 4      = %d  (expect 20)\n",  (2 + 3) * 4);
    printf("100 / 7          = %d  (expect 14)\n",  100 / 7);
    printf("100 %% 7          = %d  (expect 2)\n",   100 % 7);

    /* 負數除法：朝 0 截斷（C 語意，非 Python 的朝負無窮） */
    printf("=== 負數整除（朝 0 截斷）===\n");
    printf("-7 / 2           = %d  (expect -3)\n",  -7 / 2);
    printf("-7 %% 2           = %d  (expect -1)\n",  -7 % 2);
    printf("7 / -2           = %d  (expect -3)\n",  7 / -2);
    printf("7 %% -2           = %d  (expect 1)\n",   7 % -2);

    /* 位元運算 */
    printf("=== 位元運算 ===\n");
    printf("0xFF & 0x0F      = 0x%x  (expect 0xf)\n",  0xFF & 0x0F);
    printf("0xA0 | 0x05      = 0x%x  (expect 0xa5)\n", 0xA0 | 0x05);
    printf("0xFF ^ 0x0F      = 0x%x  (expect 0xf0)\n", 0xFF ^ 0x0F);
    printf("~0               = %d  (expect -1)\n",     ~0);
    printf("~0 as hex        = 0x%x  (expect ffffffff)\n", ~0);
    printf("1 << 8           = %d  (expect 256)\n",    1 << 8);
    printf("256 >> 4         = %d  (expect 16)\n",     256 >> 4);
    printf("(0xAB&0xF0)|0x0C = 0x%x  (expect 0xac)\n",
           (0xAB & 0xF0) | 0x0C);

    /* 關係與邏輯運算 */
    printf("=== 關係與邏輯運算 ===\n");
    printf("5 > 3            = %d  (expect 1)\n", 5 > 3);
    printf("5 < 3            = %d  (expect 0)\n", 5 < 3);
    printf("5 == 5           = %d  (expect 1)\n", 5 == 5);
    printf("5 != 5           = %d  (expect 0)\n", 5 != 5);
    printf("5 >= 5 && 3 < 4  = %d  (expect 1)\n", 5 >= 5 && 3 < 4);
    printf("5 > 10 || 3 < 4  = %d  (expect 1)\n", 5 > 10 || 3 < 4);
    printf("!(5 > 3)         = %d  (expect 0)\n", !(5 > 3));

    return 0;
}
