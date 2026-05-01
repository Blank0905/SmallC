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
            'strcmp':self.builtin_strcmp,
            'strcat':self.builtin_strcat,
            'printf':self.builtin_printf,

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
    def builtin_strcmp(self, char1, char2):
        s1 = self.memory.read_string(char1)
        s2 = self.memory.read_string(char2)
        if s1 == s2:
            return 0
        elif s1 < s2:
            return -1
        else:
            return 1
    def builtin_strcat(self, dest, src):
        source = self.memory.read_string(src)
        dest_l = self.builtin_strlen(dest)
        for i in range(len(source)):
            self.memory.write_char(dest + dest_l + i, source[i])
        self.memory.write_char(dest + dest_l + len(source), '\0')
        return dest
    def builtin_printf(self, format_addr, *args):
        fmt = self.memory.read_string(format_addr)# 1. 把格式化字串 (例如 "Hello %s, score: %d\n") 從記憶體讀出來
        output = ""
        pos = 0
        arg_idx = 0
        while pos < len(fmt):
            if fmt[pos] == '%' and pos + 1 < len(fmt):
                specifier = fmt[pos+1]
                if specifier == '%':
                    output += '%'
                else:
                    if arg_idx >= len(args):
                        raise RuntimeError("Runtime Error: printf arguments not enough")
                    val = args[arg_idx]
                    arg_idx += 1
                    
                    if specifier == 'd':
                        output += str(val)
                    elif specifier == 'c':
                        output += chr(val)
                    elif specifier == 's':
                        output += self.memory.read_string(val)
                    elif specifier == 'x':
                        output += hex(val)[2:] # 把 Python 的 '0x...' 去掉 0x
                    else:
                        output += '%' + specifier # 遇到不認識的，就原樣印出
                pos += 2
            else:
                output += fmt[pos]
                pos += 1
        # 組合好整個字串後，一口氣印在終端機上
        sys.stdout.write(output)
        sys.stdout.flush()
        return len(output)
