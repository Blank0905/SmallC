#include <iostream>
using namespace std;
int main() {
    int arr[2];
    int *p;
    
    arr[0] = 100;
    arr[1] = 200;
    
    p = &arr[0];
    printf("arr[0] address: %d\n", p);
    printf("arr[0] value: %d\n", *p);
    
    // 邊際測試：加 1 會前進 1 byte 還是 4 bytes？
    p = p + 1; 
    printf("p + 1 address: %d\n", p);
    printf("*(p + 1) value: %d\n", *p); // 這裡預期會讀到錯誤的錯位數值，而非 
    printf("p address : %d\n", p);
    
    // 正確存取 arr[1] 的位址應該要是 + 4
    p = &arr[0] + 4;
    printf("Correct arr[1] value: %d\n", *p); 
    
    return 0;
}