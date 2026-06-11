/* test4.sc — 一維陣列操作
 * 展示：陣列宣告、初始化列表、索引存取、傳陣列給函式（退化為指標）、插入排序 */

void print_array(int *arr, int n) {
    int i;
    for (i = 0; i < n; i = i + 1) {
        printf("%d", arr[i]);
        if (i < n - 1) printf(" ");
    }
    printf("\n");
}

void insertion_sort(int *arr, int n) {
    int i;
    int j;
    int key;
    for (i = 1; i < n; i = i + 1) {
        key = arr[i];
        j = i - 1;
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j];
            j = j - 1;
        }
        arr[j + 1] = key;
    }
}

int array_sum(int *arr, int n) {
    int i;
    int s;
    s = 0;
    for (i = 0; i < n; i = i + 1) {
        s += arr[i];
    }
    return s;
}

int main() {
    int data[8];
    int init[5];
    int sum;
    int i;

    /* 逐元素賦值 */
    data[0] = 64; data[1] = 25; data[2] = 12; data[3] = 22;
    data[4] = 11; data[5] = 90; data[6] = 45; data[7] = 31;

    printf("Before sort: ");
    print_array(data, 8);

    insertion_sort(data, 8);

    printf("After sort:  ");
    print_array(data, 8);
    /* 期望：11 12 22 25 31 45 64 90 */

    sum = array_sum(data, 8);
    printf("Sum = %d  (expect 300)\n", sum);
    printf("Avg = %d  (expect 37)\n", sum / 8);

    /* 初始化列表 */
    printf("=== 初始化列表 ===\n");
    int arr2[5] = {10, 20, 30, 40, 50};
    for (i = 0; i < 5; i = i + 1) {
        printf("arr2[%d] = %d\n", i, arr2[i]);
    }

    /* 用迴圈填值，然後反向列印 */
    printf("=== 反向列印 ===\n");
    for (i = 0; i < 5; i = i + 1) {
        init[i] = (i + 1) * 11;   /* 11 22 33 44 55 */
    }
    for (i = 4; i >= 0; i = i - 1) {
        printf("%d ", init[i]);
    }
    printf("\n(expect: 55 44 33 22 11)\n");

    return 0;
}
