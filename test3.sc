/* test3.sc — 遞迴函式
 * 展示：費波那契（雙遞迴）、階乘、Euclidean GCD（迴圈版）
 *       函式呼叫堆疊隔離、多函式共存、前向呼叫 */

int fib(int n) {
    if (n <= 0) return 0;
    if (n == 1) return 1;
    return fib(n - 1) + fib(n - 2);
}

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int gcd(int a, int b) {
    int temp;
    while (b != 0) {
        temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

int lcm(int a, int b) {
    return a / gcd(a, b) * b;   /* 先除後乘，避免中途溢位 */
}

int main() {
    int i;

    printf("=== 費波那契數列 F(0)..F(12) ===\n");
    for (i = 0; i <= 12; i = i + 1) {
        printf("F(%d) = %d\n", i, fib(i));
    }

    printf("=== 階乘 0!..10! ===\n");
    for (i = 0; i <= 10; i = i + 1) {
        printf("%d! = %d\n", i, factorial(i));
    }

    printf("=== 最大公因數 / 最小公倍數 ===\n");
    printf("GCD(48, 18)   = %d  (expect 6)\n",   gcd(48, 18));
    printf("GCD(100, 75)  = %d  (expect 25)\n",  gcd(100, 75));
    printf("GCD(17, 13)   = %d  (expect 1)\n",   gcd(17, 13));
    printf("LCM(4, 6)     = %d  (expect 12)\n",  lcm(4, 6));
    printf("LCM(12, 18)   = %d  (expect 36)\n",  lcm(12, 18));

    return 0;
}
