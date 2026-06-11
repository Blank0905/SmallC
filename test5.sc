/* test5.sc — 指標操作
 * 展示：指標宣告、& 取址、* 解參考、指標算術（+/- 整數、指標相減）、
 *       陣列名退化、指標前後綴 ++/--、傳址修改 */

void swap(int *a, int *b) {
    int temp;
    temp = *a;
    *a = *b;
    *b = temp;
}

int dot_product(int *u, int *v, int n) {
    int i;
    int result;
    result = 0;
    for (i = 0; i < n; i = i + 1) {
        result += *(u + i) * *(v + i);
    }
    return result;
}

int main() {
    int x;
    int y;
    int *p;
    int *q;
    int arr[5];
    int vec1[3];
    int vec2[3];
    int i;

    /* 基本指標 */
    printf("=== 基本指標操作 ===\n");
    x = 42;
    p = &x;
    printf("x = %d, *p = %d  (expect 42, 42)\n", x, *p);
    *p = 99;
    printf("After *p=99: x = %d  (expect 99)\n", x);

    /* 傳址 swap */
    printf("=== 傳址修改（swap）===\n");
    x = 3;  y = 7;
    printf("Before: x=%d, y=%d\n", x, y);
    swap(&x, &y);
    printf("After:  x=%d, y=%d  (expect 7, 3)\n", x, y);

    /* 指標算術 */
    printf("=== 指標算術（int*，步長 = 4 bytes）===\n");
    for (i = 0; i < 5; i = i + 1) {
        arr[i] = (i + 1) * 10;   /* 10 20 30 40 50 */
    }
    p = arr;
    q = &arr[4];
    printf("*(p+2)   = %d  (expect 30)\n", *(p + 2));
    printf("*(arr+4) = %d  (expect 50)\n", *(arr + 4));
    printf("q - p    = %d  (expect 4)\n",  q - p);
    printf("p - q    = %d  (expect -4)\n", p - q);

    /* 陣列名退化：arr[i] == *(arr+i) */
    printf("=== 陣列名退化 ===\n");
    for (i = 0; i < 5; i = i + 1) {
        printf("arr[%d]==%d, *(arr+%d)==%d, match=%d\n",
               i, arr[i], i, *(arr + i), arr[i] == *(arr + i));
    }

    /* 指標 ++/-- */
    printf("=== 指標 ++/-- ===\n");
    p = arr;
    p++;
    printf("*p after p++  = %d  (expect 20)\n", *p);
    ++p;
    printf("*p after ++p  = %d  (expect 30)\n", *p);
    p--;
    printf("*p after p--  = %d  (expect 20)\n", *p);

    /* 內積（展示以指標存取陣列）*/
    printf("=== 內積 [1,2,3]·[4,5,6] ===\n");
    vec1[0] = 1; vec1[1] = 2; vec1[2] = 3;
    vec2[0] = 4; vec2[1] = 5; vec2[2] = 6;
    printf("dot = %d  (expect 32)\n", dot_product(vec1, vec2, 3));

    return 0;
}
