/* test7.sc — switch / case 完整測試
 * 展示：整數 case、char case、fall-through、default、巢狀 switch、
 *       多個 case 共用同一 body（week-end 合併） */

void print_day(int d) {
    switch (d) {
        case 1: printf("Monday\n");    break;
        case 2: printf("Tuesday\n");   break;
        case 3: printf("Wednesday\n"); break;
        case 4: printf("Thursday\n");  break;
        case 5: printf("Friday\n");    break;
        case 6:                        /* fall-through */
        case 7: printf("Weekend\n");   break;
        default: printf("Invalid day: %d\n", d);
    }
}

void print_grade(char g) {
    switch (g) {
        case 'A': printf("Excellent\n"); break;
        case 'B': printf("Good\n");      break;
        case 'C': printf("Average\n");   break;
        case 'D': printf("Below avg\n"); break;
        default:  printf("Unknown grade\n");
    }
}

void test_fallthrough(int x) {
    printf("x=%d falls: ", x);
    switch (x) {
        case 1:
            printf("one ");
            /* 故意 fall-through */
        case 2:
            printf("two ");
            /* 故意 fall-through */
        case 3:
            printf("three");
            break;
        default:
            printf("other");
    }
    printf("\n");
}

int classify(int n) {
    int sign;
    int parity;
    /* 巢狀 switch */
    sign = n > 0 ? 1 : n < 0 ? -1 : 0;
    switch (sign) {
        case 1:
            switch (n % 2) {
                case 0: return 1;   /* 正偶 */
                case 1: return 2;   /* 正奇 */
            }
        case -1: return -1;         /* 負數 */
        default: return 0;          /* 零 */
    }
    return -99;
}

int main() {
    int i;

    printf("=== 整數 case（星期）===\n");
    for (i = 1; i <= 7; i = i + 1) {
        print_day(i);
    }
    print_day(0);
    print_day(8);

    printf("=== char case（成績）===\n");
    print_grade('A');
    print_grade('B');
    print_grade('C');
    print_grade('D');
    print_grade('E');

    printf("=== Fall-through ===\n");
    test_fallthrough(1);   /* expect: one two three */
    test_fallthrough(2);   /* expect: two three */
    test_fallthrough(3);   /* expect: three */
    test_fallthrough(4);   /* expect: other */

    printf("=== 巢狀 switch + classify ===\n");
    printf("classify(4)  = %d  (expect 1, 正偶)\n",  classify(4));
    printf("classify(7)  = %d  (expect 2, 正奇)\n",  classify(7));
    printf("classify(-3) = %d  (expect -1, 負數)\n", classify(-3));
    printf("classify(0)  = %d  (expect 0, 零)\n",    classify(0));

    return 0;
}
