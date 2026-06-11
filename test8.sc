/* test8.sc — #define 巨集展開與全域變數
 * 展示：object-like #define、巨集作為常數／陣列大小、
 *       全域變數跨函式共享、前向使用全域變數（CHECK 不誤報）*/

#define ARRAY_SIZE 10
#define MAX_VAL    1000
#define NEG_CONST  -999

int global_count;
int global_sum;
int global_max;

/* global_max 定義在 accumulate 後才宣告，測試前向全域變數 */
void accumulate(int n) {
    global_count = global_count + 1;
    global_sum   = global_sum + n;
    if (n > global_max) {
        global_max = n;
    }
}

void reset_globals() {
    global_count = 0;
    global_sum   = 0;
    global_max   = NEG_CONST;
}

int clamp(int val, int lo, int hi) {
    if (val < lo) return lo;
    if (val > hi) return hi;
    return val;
}

int main() {
    int arr[ARRAY_SIZE];
    int i;

    printf("=== #define 常數 ===\n");
    printf("ARRAY_SIZE = %d  (expect 10)\n",   ARRAY_SIZE);
    printf("MAX_VAL    = %d  (expect 1000)\n", MAX_VAL);
    printf("NEG_CONST  = %d  (expect -999)\n", NEG_CONST);

    /* 巨集當陣列大小 */
    printf("=== 陣列（大小由巨集決定）===\n");
    for (i = 0; i < ARRAY_SIZE; i = i + 1) {
        arr[i] = (i + 1) * (i + 1);   /* 1 4 9 16 ... 100 */
    }
    printf("arr[0]=%d  arr[9]=%d  (expect 1, 100)\n", arr[0], arr[9]);

    /* 全域變數 */
    printf("=== 全域變數跨函式 ===\n");
    reset_globals();
    for (i = 1; i <= ARRAY_SIZE; i = i + 1) {
        accumulate(i * 3);   /* 3 6 9 ... 30 */
    }
    printf("count = %d  (expect 10)\n",  global_count);
    printf("sum   = %d  (expect 165)\n", global_sum);    /* 3+6+...+30 = 3*(1+...+10) = 3*55 */
    printf("max   = %d  (expect 30)\n",  global_max);

    /* clamp */
    printf("=== clamp(val, lo, hi) ===\n");
    printf("clamp(5,1,10)   = %d  (expect 5)\n",  clamp(5, 1, 10));
    printf("clamp(-5,1,10)  = %d  (expect 1)\n",  clamp(-5, 1, 10));
    printf("clamp(999,1,10) = %d  (expect 10)\n", clamp(MAX_VAL - 1, 1, 10));

    return 0;
}
