/* test10.sc — 綜合算法展示：質數篩法（Sieve of Eratosthenes）
 * 整合：#define 巨集、陣列、巢狀迴圈、函式、指標傳遞、printf 格式化
 * 驗算：100 以內質數共 25 個，總和 1060 */

#define LIMIT 100
#define LINE  10

void sieve(int *flags, int n) {
    int i;
    int j;
    for (i = 0; i <= n; i = i + 1) {
        flags[i] = 1;
    }
    flags[0] = 0;
    flags[1] = 0;
    for (i = 2; i * i <= n; i = i + 1) {
        if (flags[i]) {
            for (j = i * i; j <= n; j = j + i) {
                flags[j] = 0;
            }
        }
    }
}

int count_primes(int *flags, int n) {
    int i;
    int cnt;
    cnt = 0;
    for (i = 2; i <= n; i = i + 1) {
        if (flags[i]) cnt = cnt + 1;
    }
    return cnt;
}

int sum_primes(int *flags, int n) {
    int i;
    int s;
    s = 0;
    for (i = 2; i <= n; i = i + 1) {
        if (flags[i]) s = s + i;
    }
    return s;
}

void print_primes(int *flags, int n) {
    int i;
    int col;
    col = 0;
    for (i = 2; i <= n; i = i + 1) {
        if (flags[i]) {
            printf("%d ", i);
            col = col + 1;
            if (col % LINE == 0) printf("\n");
        }
    }
    if (col % LINE != 0) printf("\n");
}

/* 判斷某數是否為質數（單獨函式，用以驗證篩法結果）*/
int is_prime(int n) {
    int i;
    if (n < 2) return 0;
    for (i = 2; i * i <= n; i = i + 1) {
        if (n % i == 0) return 0;
    }
    return 1;
}

int main() {
    int flags[LIMIT + 1];
    int cnt;
    int s;
    int i;
    int ok;

    printf("=== Sieve of Eratosthenes（上限 %d）===\n", LIMIT);
    sieve(flags, LIMIT);
    print_primes(flags, LIMIT);

    cnt = count_primes(flags, LIMIT);
    s   = sum_primes(flags, LIMIT);
    printf("Count = %d  (expect 25)\n", cnt);
    printf("Sum   = %d  (expect 1060)\n", s);

    /* 交叉驗證：篩法結果應與 is_prime() 完全一致 */
    printf("=== 交叉驗證 sieve vs is_prime ===\n");
    ok = 1;
    for (i = 0; i <= LIMIT; i = i + 1) {
        if (flags[i] != is_prime(i)) {
            printf("MISMATCH at %d: sieve=%d, is_prime=%d\n",
                   i, flags[i], is_prime(i));
            ok = 0;
        }
    }
    if (ok) {
        printf("All %d values match.  (expect: pass)\n", LIMIT + 1);
    }

    /* 小範例：2~20 的質數密度 */
    printf("=== 2~20 質數密度 ===\n");
    for (i = 2; i <= 20; i = i + 1) {
        printf("%d: %s\n", i, flags[i] ? "prime" : "composite");
    }

    return 0;
}
