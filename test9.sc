/* test9.sc — 三元運算子、複合賦值、前後綴 ++/--
 * 展示：? : 含巢狀三元、+= -= *= /= %=、前綴後綴 ++ -- 的回傳值差異 */

int abs_val(int x) {
    return x >= 0 ? x : -x;
}

int max2(int a, int b) {
    return a > b ? a : b;
}

int min2(int a, int b) {
    return a < b ? a : b;
}

char score_to_grade(int score) {
    return score >= 90 ? 'A' :
           score >= 80 ? 'B' :
           score >= 70 ? 'C' :
           score >= 60 ? 'D' : 'F';
}

int main() {
    int a;
    int b;
    int res;
    int scores[6];
    char grade;
    int i;

    printf("=== 三元運算子 ===\n");
    printf("abs_val(-7) = %d  (expect 7)\n", abs_val(-7));
    printf("abs_val(5)  = %d  (expect 5)\n", abs_val(5));
    printf("max2(3, 9)  = %d  (expect 9)\n", max2(3, 9));
    printf("min2(3, 9)  = %d  (expect 3)\n", min2(3, 9));

    printf("=== 巢狀三元（成績轉換）===\n");
    scores[0] = 95; scores[1] = 83; scores[2] = 72;
    scores[3] = 61; scores[4] = 50; scores[5] = 100;
    for (i = 0; i < 6; i = i + 1) {
        grade = score_to_grade(scores[i]);
        printf("score=%d -> grade=%c\n", scores[i], grade);
    }
    /* expect: A B C D F A */

    printf("=== 複合賦值 += -= *= /= %%= ===\n");
    a = 10;
    a += 5;  printf("a += 5  -> %d  (expect 15)\n", a);
    a -= 3;  printf("a -= 3  -> %d  (expect 12)\n", a);
    a *= 2;  printf("a *= 2  -> %d  (expect 24)\n", a);
    a /= 4;  printf("a /= 4  -> %d  (expect 6)\n",  a);
    a %= 4;  printf("a %%= 4  -> %d  (expect 2)\n",  a);

    printf("=== 前後綴 ++ / -- 回傳值 ===\n");
    a = 5;
    res = ++a;
    printf("++a: a=%d, res=%d  (expect 6, 6)\n", a, res);

    b = 5;
    res = b++;
    printf("b++: b=%d, res=%d  (expect 6, 5)\n", b, res);

    a = 10;
    res = --a;
    printf("--a: a=%d, res=%d  (expect 9, 9)\n", a, res);

    res = a--;
    printf("a--: a=%d, res=%d  (expect 8, 9)\n", a, res);

    printf("=== 表達式中混用 ===\n");
    a = 3;
    b = a++ * 2 + ++a;   /* a++=3（a變4）, ++a=5（a變5）, 3*2+5=11 */
    printf("a++ * 2 + ++a (初始 a=3): b=%d, a=%d  (expect 11, 5)\n", b, a);

    return 0;
}
