# SmallC 作業範例程式碼 (1-18)

### 範例一
```c
printf("%d\n", 2 + 3 * 4);
printf("%d\n", (2 + 3) * 4);
printf("%d\n", 100 / 7);
printf("%d\n", 100 % 7);
printf("%d\n", -5 + 3);
printf("%d\n", 2 + 3 * 4 - 8 / 2);
printf("%d\n", ((2 + 3) * (4 - 1)) / 5);
```

### 範例二
```c
printf("%d\n", 5 > 3);
printf("%d\n", 5 < 3);
printf("%d\n", 5 == 5);
printf("%d\n", 5 != 5);
printf("%d\n", 5 >= 5 && 3 < 4);
printf("%d\n", 5 > 10 || 3 < 4);
printf("%d\n", !(5 > 3));
```

### 範例三
```c
printf("%d\n", 0xFF & 0x0F);
printf("%d\n", 0xA0 | 0x05);
printf("%d\n", 0xFF ^ 0x0F);
printf("%d\n", ~0);
printf("%d\n", 1 << 8);
printf("%d\n", 256 >> 4);
printf("0x%x\n", (0xAB & 0xF0) | 0x0C);
```

### 範例四
```c
int x = 10;
int y = 20;
int z;
z = x + y;
printf("x=%d, y=%d, z=%d\n", x, y, z);
x += 5;
y -= 3;
printf("x=%d, y=%d\n", x, y);
char ch = 'A';
printf("ch=%c (ASCII=%d)\n", ch, ch);
VARS
```

### 範例五
```c
printf("abs(-42) = %d\n", abs(-42));
printf("max(10, 25) = %d\n", max(10, 25));
printf("min(10, 25) = %d\n", min(10, 25));
printf("pow(2, 10) = %d\n", pow(2, 10));
printf("sqrt(144) = %d\n", sqrt(144));
printf("sqrt(150) = %d\n", sqrt(150));
int a = max(abs(-7), min(3, 5));
printf("a = %d\n", a);
printf("pow(2,0)=%d, pow(2,1)=%d, pow(2,-1)=%d\n", pow(2,0), pow(2,1), pow(2,-1));
```

### 範例六
```c
int score = 85;
if (score >= 90) {
    printf("Grade: A\n");
} else if (score >= 80) {
    printf("Grade: B\n");
} else if (score >= 70) {
    printf("Grade: C\n");
} else {
    printf("Grade: F\n");
}

int n = 17;
if (n % 2 == 0) {
    printf("%d is even\n", n);
} else {
    printf("%d is odd\n", n);
}
```

### 範例七
```c
int i = 1;
int sum = 0;
while (i <= 100) {
    sum += i;
    i = i + 1;
}
printf("1+2+...+100 = %d\n", sum);

NEW
int i;
for (i = 1; i <= 9; i = i + 1) {
    printf("%d * %d = %d\n", i, i, i * i);
}
```

### 範例八
```c
int i;
for (i = 1; i <= 20; i = i + 1) {
    if (i % 3 == 0) {
        continue;
    }
    if (i > 15) {
        break;
    }
    printf("%d ", i);
}
printf("\n");
```

### 範例九
```c
int arr[10];
int i;
for (i = 0; i < 10; i = i + 1) {
    arr[i] = (i + 1) * 10;
}
for (i = 0; i < 10; i = i + 1) {
    printf("arr[%d] = %d\n", i, arr[i]);
}
```

### 範例十
```c
char name[40];
strcpy(name, "Hello");
printf("name = \"%s\", length = %d\n", name, strlen(name));
strcat(name, " World");
printf("name = \"%s\", length = %d\n", name, strlen(name));
printf("strcmp result: %d\n", strcmp("abc", "abd"));
printf("atoi(\"12345\") = %d\n", atoi("12345"));
```

### 範例十一
```c
int x = 42;
int *ptr;
ptr = &x;
printf("x = %d\n", x);
printf("*ptr = %d\n", *ptr);
*ptr = 99;
printf("x = %d\n", x);
printf("ptr points to address %d\n", ptr);
```

### 範例十二
```c
/* Bubble Sort Demo */
void swap(int *a, int *b) {
    int temp;
    temp = *a;
    *a = *b;
    *b = temp;
}

void bubble_sort(int *arr, int n) {
    int i;
    int j;
    for (i = 0; i < n - 1; i = i + 1) {
        for (j = 0; j < n - i - 1; j = j + 1) {
            if (arr[j] > arr[j + 1]) {
                swap(&arr[j], &arr[j + 1]);
            }
        }
    }
}

void print_array(int *arr, int n) {
    int i;
    for (i = 0; i < n; i = i + 1) {
        printf("%d ", arr[i]);
    }
    printf("\n");
}

int main() {
    int data[8];
    data[0] = 64; data[1] = 25; data[2] = 12; data[3] = 22;
    data[4] = 11; data[5] = 90; data[6] = 45; data[7] = 31;
    
    printf("Before sorting: ");
    print_array(data, 8);
    
    bubble_sort(data, 8);
    
    printf("After sorting: ");
    print_array(data, 8);
    
    return 0;
}
```

### 範例十三
```c
int fibonacci(int n) {
    if (n <= 0) return 0;
    if (n == 1) return 1;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main() {
    int i;
    printf("Fibonacci sequence:\n");
    for (i = 0; i < 15; i = i + 1) {
        printf("F(%d) = %d\n", i, fibonacci(i));
    }
    return 0;
}
```

### 範例十四
```c
int gcd(int a, int b) {
    int temp;
    while (b != 0) {
        
        temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

int main() {
    int result;
    result = gcd(48, 18);
    printf("GCD(48, 18) = %d\n", result);
    return 0;
}
```

### 範例十五
```c
int main() {
    int i;
    int sum = 0;
    for (i = 1; i <= 10; i = i + 1) {
        sum += i * i;
    }
    printf("Sum of squares: %d\n", sum);
    return 0;
}
```

### 範例十六
```c
int x = 10 / 0; // Runtime error: division by zero.
int arr[5];
arr[10] = 99; // Runtime error: array index out of bounds.
printf("%d\n", sqrt(-1)); // Runtime error: sqrt() argument must be non-negative.

// 語法錯誤範例
int y = ; // Syntax error: unexpected token ';', expected expression.
if ( ) { } // Syntax error: unexpected token ')', expected expression.

APPEND
int main() {
   int x = 10;
   printf("%d\n", x) // 缺少分號
   return 0;
}
.
CHECK
// 會顯示 Error at line 3: expected ';' after expression statement.
```

### 範例十七
```c
/* 展示 FUNCS 指令 */
sc> LOAD bubble_sort.sc
sc> CHECK
sc> FUNCS
// 會列出所有已定義的函式，包含自定義與內建函式
```

### 範例十八
```c
/* 完整的互動式程式開發過程 */
sc> NEW
sc> int n = 29;
sc> int i;
sc> int is_prime = 1;
sc> 


/* 包裝成函式 */
int is_prime(int n) {
   int i;
   if (n < 2) return 0;
   for (i = 2; i * i <= n; i = i + 1) {
       if (n % i == 0) return 0;
   }
   return 1;
}

int main() {
   int i;
   int count = 0;
   printf("Prime numbers from 2 to 100:\n");
   for (i = 2; i <= 100; i = i + 1) {
       if (is_prime(i)) {
           printf("%d ", i);
           count = count + 1;
       }
   }
   printf("\nTotal: %d primes\n", count);
   return 0;
}
```
