int main() {
    int i;
    int j;
    int count = 0;
    
    for (i = 0; i < 3; i = i+1) {
        
        for (j = 0; j < 3 ;j = j+1){
            if (j == 1) {
                break;
            }
            count ++ ;
        }
        
    }
    
    // 外層跑 3 次，內層每次遇到 j==1 就 break，所以內層每次只會讓 count 加 1 (j==0 時)
    // 預期結果: count 應該是 3
    printf("Nested break count: %d\n", count);
    
    return 0;
}