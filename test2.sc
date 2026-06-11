/* test2.sc — 控制流程完整測試
 * 展示：if/else if/else、while、for、do-while、break、continue、巢狀迴圈 */

int main() {
    int score;
    int i;
    int j;
    int sum;
    int count;

    /* if / else if / else */
    printf("=== if / else if / else ===\n");
    score = 85;
    if (score >= 90) {
        printf("Grade: A\n");
    } else if (score >= 80) {
        printf("Grade: B  (expect B)\n");
    } else if (score >= 70) {
        printf("Grade: C\n");
    } else {
        printf("Grade: F\n");
    }

    /* while */
    printf("=== while：1+2+...+100 ===\n");
    sum = 0;
    i = 1;
    while (i <= 100) {
        sum += i;
        i = i + 1;
    }
    printf("Sum = %d  (expect 5050)\n", sum);

    /* for */
    printf("=== for：平方表 1~5 ===\n");
    for (i = 1; i <= 5; i = i + 1) {
        printf("%d^2 = %d\n", i, i * i);
    }

    /* do-while（至少執行一次）*/
    printf("=== do-while ===\n");
    sum = 0;
    i = 1;
    do {
        sum += i;
        i = i + 1;
    } while (i <= 5);
    printf("do-while sum 1..5 = %d  (expect 15)\n", sum);

    /* break（內層跳出，外層繼續）*/
    printf("=== 巢狀 break ===\n");
    count = 0;
    for (i = 0; i < 3; i = i + 1) {
        for (j = 0; j < 3; j = j + 1) {
            if (j == 1) break;   /* 內層每次只跑 j=0 */
            count = count + 1;
        }
    }
    printf("count = %d  (expect 3)\n", count);

    /* continue（跳過不符合條件的迭代）*/
    printf("=== continue：印 1~20 中非 3 的倍數，超過 15 停 ===\n");
    for (i = 1; i <= 20; i = i + 1) {
        if (i % 3 == 0) continue;
        if (i > 15) break;
        printf("%d ", i);
    }
    printf("\n(expect: 1 2 4 5 7 8 10 11 13 14)\n");

    return 0;
}
