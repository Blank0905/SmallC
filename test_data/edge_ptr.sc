/* edge_ptr.sc — 指標算術邊際測試
 *
 * 範圍：指標 + 整數、整數 + 指標、指標 - 整數、指標 - 指標、+=、-=
 *      （不含 ++/--，因解譯器目前尚未對指標實作這兩個運算子）
 * 重點：C 的指標算術以「元素」為單位，會自動乘上 sizeof（int*→4、char*→1）
 *
 * 用法：在 src/ 下啟動 REPL，LOAD ../edge_ptr.sc 後 RUN，
 *      逐行對照每行尾端的 (expect ...)。全部相符才算通過。
 */

int main() {
    int arr[5];
    int *p;
    int *q;
    char str[6];
    char *cp;
    char *cq;

    arr[0] = 10;
    arr[1] = 20;
    arr[2] = 30;
    arr[3] = 40;
    arr[4] = 50;

    /* ===== Part 1：指標變數的算術（應全部正確，每步跨 sizeof bytes）===== */
    printf("=== int* (sizeof = 4) ===\n");
    p = arr;                 /* p 指向 arr[0] */

    /* A. 指標 + 整數 */
    printf("A1 *(p+2)      = %d  (expect 30)\n", *(p + 2));
    printf("A2 *(p+4)      = %d  (expect 50)  <- 最後一個元素\n", *(p + 4));

    /* B. 整數 + 指標（加法交換律也要成立）*/
    printf("B1 *(2+p)      = %d  (expect 30)\n", *(2 + p));

    /* C. 指標 - 整數 */
    q = &arr[4];             /* q 指向 arr[4] */
    printf("C1 *(q-1)      = %d  (expect 40)\n", *(q - 1));
    printf("C2 *(q-4)      = %d  (expect 10)\n", *(q - 4));

    /* D. 指標 - 指標：結果是「相差幾個元素」，不是 byte 數 */
    printf("D1 q - p       = %d  (expect 4,  not 16)\n", q - p);
    printf("D2 p - q       = %d  (expect -4)\n", p - q);

    /* E. p += n / p -= n：以元素為單位移動 */
    p = arr;
    p += 3;                  /* -> arr[3] */
    printf("E1 (p+=3) *p   = %d  (expect 40)\n", *p);
    p -= 2;                  /* -> arr[1] */
    printf("E2 (p-=2) *p   = %d  (expect 20)\n", *p);

    /* H. 邊界：+0 不動、同位相減為 0、尾後一格(one-past-the-end)距離 */
    p = arr;
    printf("H1 *(p+0)      = %d  (expect 10)\n", *(p + 0));
    printf("H2 p - p       = %d  (expect 0)\n", p - p);
    q = p + 5;               /* 指向尾後一格（合法位置，不可解參考）*/
    printf("H3 (p+5) - p   = %d  (expect 5)\n", q - p);

    /* ===== char*：每步只跨 1 byte ===== */
    str[0] = 'H';
    str[1] = 'e';
    str[2] = 'l';
    str[3] = 'l';
    str[4] = 'o';
    str[5] = 0;

    printf("=== char* (sizeof = 1) ===\n");
    cp = str;
    printf("G1 *cp         = %c  (expect H)\n", *cp);
    cp += 2;                 /* 前進 2 bytes -> str[2] */
    printf("G2 (cp+=2) *cp = %c  (expect l)\n", *cp);
    cp -= 1;                 /* 後退 1 byte  -> str[1] */
    printf("G3 (cp-=1) *cp = %c  (expect e)\n", *cp);
    cq = &str[4];
    cp = str;
    printf("G4 cq - cp     = %d  (expect 4)\n", cq - cp);

    /* ===== Part 2：陣列名退化成指標（本次修正）=====
     * 修正前 arr 在符號表型別是 'int'，(arr+i) 不被當指標、不乘 sizeof；
     * 現在 _get_node_type 對陣列名回傳 'int*'，(arr+i) 會正確乘 sizeof，
     * 使 C 的恆等式 arr[i] == *(arr+i) 成立。
     */
    printf("=== Part 2: array name decay ===\n");
    printf("K1 *(arr+3)    = %d  (expect 40)\n", *(arr + 3));
    printf("K2 arr[3]      = %d  (expect 40)\n", arr[3]);

    /* ===== Part 3：指標 ++ / --（本次新增）=====
     * 以元素為單位前進/後退；前綴回傳新值、後綴回傳舊值。
     */
    printf("=== Part 3: pointer ++/-- ===\n");
    p = arr;
    p++;                     /* 前進一個 int -> arr[1] */
    printf("P1 (p++) *p    = %d  (expect 20)\n", *p);
    ++p;                     /* -> arr[2] */
    printf("P2 (++p) *p    = %d  (expect 30)\n", *p);
    p--;                     /* -> arr[1] */
    printf("P3 (p--) *p    = %d  (expect 20)\n", *p);
    p = arr;
    q = p++;                 /* 後綴：q 拿到舊指標(arr[0])，p 前進到 arr[1] */
    printf("P4 *(q=p++)    = %d  (expect 10)\n", *q);
    printf("P5 *p after++  = %d  (expect 20)\n", *p);
    cp = str;
    cp++;                    /* char* 只走 1 byte -> str[1] */
    printf("P6 (cp++) *cp  = %c  (expect e)\n", *cp);

    return 0;
}
