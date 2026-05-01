int main() {
    printf("%d\n", 5 >= 5 && 3 < 4);
    printf("%d\n", 5 > 10 || 3 < 4);
    printf("%d\n", !(5 > 3));
    printf("%d\n", -5+3);
    printf("%d\n", 0xFF & 0x0F);
    printf("%d\n", 0xA0 | 0x05);
    printf("%d\n", 0xFF ^ 0x0F);
    printf("%d\n", ~0);
    printf("%d\n", 1 << 8);
    printf("%d\n", 256 >> 4);
    printf("0x%x\n", (0xAB & 0xF0) | 0x0C);
    return 0;
}
