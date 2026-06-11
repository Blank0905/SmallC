/* test6.sc — char 型別與字串操作
 * 展示：char 基本算術、有號環繞（200→-56）、ASCII 轉換、
 *       strlen/strcpy/strcat/strcmp、自訂字串函式（to_upper） */

int my_strlen(char *s) {
    int len;
    len = 0;
    while (s[len] != 0) {
        len = len + 1;
    }
    return len;
}

void to_upper(char *s) {
    int i;
    for (i = 0; s[i] != 0; i = i + 1) {
        if (s[i] >= 'a' && s[i] <= 'z') {
            s[i] = s[i] - 32;
        }
    }
}

int count_char(char *s, char target) {
    int i;
    int cnt;
    cnt = 0;
    for (i = 0; s[i] != 0; i = i + 1) {
        if (s[i] == target) {
            cnt = cnt + 1;
        }
    }
    return cnt;
}

int main() {
    char buf[64];
    char c;

    /* char 基本操作與 ASCII */
    printf("=== char 基本操作 ===\n");
    c = 'A';
    printf("'A' ASCII = %d  (expect 65)\n", c);
    printf("c + 1 = %c  (expect B)\n", c + 1);
    printf("'Z' - 'A' = %d  (expect 25)\n", 'Z' - 'A');
    printf("'0' = %d  (expect 48)\n", '0');

    /* char 有號 8-bit 環繞 */
    printf("=== char 有號環繞 ===\n");
    char cc;
    cc = 127;
    printf("char 127  = %d  (expect 127)\n", cc);
    cc = 127 + 1;
    printf("char 128  = %d  (expect -128)\n", cc);
    cc = 200;
    printf("char 200  = %d  (expect -56)\n", cc);

    /* 標準字串函式 */
    printf("=== 字串函式 ===\n");
    strcpy(buf, "Hello");
    printf("strcpy: \"%s\", strlen=%d  (expect Hello, 5)\n", buf, strlen(buf));
    strcat(buf, " World");
    printf("strcat: \"%s\", strlen=%d  (expect Hello World, 11)\n", buf, strlen(buf));
    printf("strcmp(\"abc\",\"abd\") = %d  (expect <0)\n",  strcmp("abc", "abd"));
    printf("strcmp(\"abc\",\"abc\") = %d  (expect 0)\n",   strcmp("abc", "abc"));
    printf("strcmp(\"abd\",\"abc\") = %d  (expect >0)\n",  strcmp("abd", "abc"));

    /* 自訂 my_strlen */
    printf("=== 自訂 my_strlen ===\n");
    printf("my_strlen(\"Hello\")  = %d  (expect 5)\n",  my_strlen("Hello"));
    printf("my_strlen(\"\")       = %d  (expect 0)\n",  my_strlen(""));
    printf("my_strlen(\"abc\")    = %d  (expect 3)\n",  my_strlen("abc"));

    /* 自訂 to_upper */
    printf("=== 自訂 to_upper ===\n");
    strcpy(buf, "hello, world!");
    to_upper(buf);
    printf("%s  (expect HELLO, WORLD!)\n", buf);

    /* 自訂 count_char */
    printf("=== count_char ===\n");
    printf("count 'l' in \"hello world\" = %d  (expect 3)\n",
           count_char("hello world", 'l'));

    return 0;
}
