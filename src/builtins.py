import sys
import math
import random

class BuiltinManager:
    def __init__(self, memory):
        self.memory = memory
        
        # 將 C 語言的函式名稱，對應到 Python 的實作方法
        self.functions = {
            # 數學函式
            'abs': self.builtin_abs,
            'max': self.builtin_max,
            'min': self.builtin_min,
            'pow':self.builtin_pow,
            'sqrt':self.builtin_sqrt,
            'mod':self.builtin_mod,
            'rand':self.builtin_rand,
            'srand':self.builtin_srand,
            
            # I/O 函式 (先留空)
            'putchar': self.builtin_putchar,
            'strlen':self.builtin_strlen,
            'puts':self.builtin_puts,
            'strcpy':self.builtin_strcpy,

        }
    def is_builtin(self, name):
        """檢查某個函式名稱是否為內建函式"""
        return name in self.functions
    def call(self, name, args):
        """執行內建函式並回傳結果"""
        func = self.functions[name]
        return func(*args)
    # ==========================================
    # 數學函式實作區
    # ==========================================
    def builtin_abs(self, x):
        return abs(x)
    def builtin_max(self, a, b):
        return max(a, b)
    def builtin_min(self, a, b):
        return min(a, b)
    def builtin_pow(self, base, exp):
        if exp < 0:
            return 0
        if exp == 0:
            return 1
        return int(base ** exp) #強轉成整數型別
    def builtin_sqrt(self, x):
        if x < 0 :
            raise RuntimeError("Runtime Error: sqrt of negative number")
        return math.isqrt(x)
    def builtin_mod (self, a, b):
        if b == 0:
             raise RuntimeError("Runtime Error: Division by zero in mod")
        return int(math.fmod(a, b))
    def builtin_rand(self):
        return random.randint(0, 32767)
    def builtin_srand(self, seed):
        """設定亂數種子"""
        random.seed(seed)
        return 0

    # ==========================================
    # I/O 函式實作區
    # ==========================================
    def builtin_putchar(self, ch):
        """putchar(int ch): 輸出一個字元到終端機"""
        sys.stdout.write(chr(ch))
        sys.stdout.flush()
        return ch
    def builtin_strlen(self, addr):
        s = self.memory.read_string(addr)
        length  = len(s)
        return length
    def builtin_puts(self, addr):
        s = self.memory.read_string(addr)
        print(s)
        return 0
    def builtin_strcpy(self,dest_addr, addr):
        s = self.memory.read_string(addr)
        l = len(s)
        for i in range(l):
            self.memory.write_char(dest_addr + i, s[i])
        self.memory.write_char(dest_addr + l, '\0')
        return dest_addr


