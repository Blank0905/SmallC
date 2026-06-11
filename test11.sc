/* test11.sc — 執行期錯誤示範
 *
 * 修改 ERROR_TYPE 的值後重新 RUN，觀察對應的錯誤訊息：
 *   1 = 除以零          (Division by zero)
 *   2 = 取模零          (Modulo by zero)
 *   3 = 陣列越界        (array index out of bounds)
 *   4 = 堆疊溢位        (call stack overflow, max depth 128)
 *   5 = sqrt 負數引數   (sqrt() argument must be non-negative)
 *   6 = 空指標解參考    (null pointer dereference)
 *
 * 每次執行只觸發一種錯誤，「不會印到這行」後面的 printf 不會出現。
 */

#define ERROR_TYPE 2

/* ─────────────────── 各錯誤示範函式 ─────────────────── */

void demo_div_zero() {
    int a;
    int b;
    int result;
    a = 10;
    b = 3;
    printf("安全：10 / 3 = %d\n", a / b);
    printf("安全：10 %% 3 = %d\n", a % b);
    b = 0;
    printf("即將：%d / 0 ...\n", a);
    result = a / b;                /* RuntimeError: Division by zero */
    printf("(不會印到這行)\n");
}

void demo_mod_zero() {
    int a;
    int b;
    a = 7;
    b = 0;
    printf("即將：%d %% 0 ...\n", a);
    a = a % b;                     /* RuntimeError: Modulo by zero */
    printf("(不會印到這行)\n");
}

void demo_array_oob() {
    int arr[5];
    int i;
    for (i = 0; i < 5; i = i + 1) {
        arr[i] = i * 10;
    }
    printf("安全：arr[4] = %d  (最後合法元素)\n", arr[4]);
    printf("即將：arr[5]（大小為 5，越界）...\n");
    printf("arr[5] = %d\n", arr[5]);  /* RuntimeError: array index out of bounds */
    printf("(不會印到這行)\n");
}

void inf_recurse(int depth) {
    /* 不印出每層，直接遞迴到溢位，避免輸出 128 行 */
    inf_recurse(depth + 1);
}

void demo_stack_overflow() {
    printf("安全：遞迴深度上限 = 128\n");
    printf("即將：無限遞迴 ...\n");
    inf_recurse(1);                /* RuntimeError: call stack overflow */
    printf("(不會印到這行)\n");
}

void demo_sqrt_neg() {
    printf("安全：sqrt(144) = %d\n", sqrt(144));
    printf("安全：sqrt(0)   = %d\n", sqrt(0));
    printf("即將：sqrt(-1) ...\n");
    printf("sqrt(-1) = %d\n", sqrt(-1));  /* RuntimeError: sqrt() argument must be non-negative */
    printf("(不會印到這行)\n");
}

void demo_null_deref() {
    int x;
    int *p;
    x = 42;
    p = &x;
    printf("安全：*p = %d  (合法指標)\n", *p);
    p = 0;                         /* 設為 NULL（位址 0 保留給 NULL）*/
    printf("即將：解參考 NULL 指標 ...\n");
    printf("*p = %d\n", *p);       /* RuntimeError: null pointer dereference */
    printf("(不會印到這行)\n");
}

/* ─────────────────── main ─────────────────── */

int main() {
    printf("=== 執行期錯誤測試（ERROR_TYPE = %d）===\n", ERROR_TYPE);

    if (ERROR_TYPE == 1) {
        printf("[ 除以零 ]\n");
        demo_div_zero();
    }
    if (ERROR_TYPE == 2) {
        printf("[ 取模零 ]\n");
        demo_mod_zero();
    }
    if (ERROR_TYPE == 3) {
        printf("[ 陣列越界 ]\n");
        demo_array_oob();
    }
    if (ERROR_TYPE == 4) {
        printf("[ 堆疊溢位 ]\n");
        demo_stack_overflow();
    }
    if (ERROR_TYPE == 5) {
        printf("[ sqrt 負數引數 ]\n");
        demo_sqrt_neg();
    }
    if (ERROR_TYPE == 6) {
        printf("[ 空指標解參考 ]\n");
        demo_null_deref();
    }

    printf("(若看到此行表示 ERROR_TYPE 超出範圍，無錯誤觸發)\n");
    return 0;
}
