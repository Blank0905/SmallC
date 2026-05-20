import sys
import math
import random

class BuiltinManager:
    def __init__(self, memory):
        self.memory = memory
        
        # 將 C 語言的函式名稱，對應到 Python 的實作方法
        self.functions = {
            # 輸入與輸出函式
            'putchar': self.builtin_putchar,
            'printf':self.builtin_printf,
            'puts':self.builtin_puts,
            'getchar':self.builtin_getchar,
            'scanf':self.builtin_scanf,

            # 字串處理函式
            'strlen':self.builtin_strlen,
            'strcpy':self.builtin_strcpy,
            'strcmp':self.builtin_strcmp,
            'strcat':self.builtin_strcat,
        
            # 數學函式
            'abs': self.builtin_abs,
            'max': self.builtin_max,
            'min': self.builtin_min,
            'pow':self.builtin_pow,
            'sqrt':self.builtin_sqrt,
            'mod':self.builtin_mod,
            'rand':self.builtin_rand,
            'srand':self.builtin_srand,

            #記憶體與工具函式
            'memset':self.builtin_memset,
            'sizeof_int': self.builtin_sizeof_int,
            'sizeof_char': self.builtin_sizeof_char,
            'atoi':self.builtin_atoi,
            'itoa':self.builtin_itoa,
            'exit':self.builtin_exit,

        }
    def is_builtin(self, name):
        """檢查某個函式名稱是否為內建函式"""
        return name in self.functions
    def call(self, name, args):
        """執行內建函式並回傳結果"""
        func = self.functions[name]
        return func(*args)

    # ─── 輸入與輸出函式 ────────────────────────────────────────────────────────
    def builtin_putchar(self, ch):
        """putchar(int ch): 輸出一個字元到終端機"""
        sys.stdout.write(chr(ch))
        sys.stdout.flush()
        return ch

    def builtin_printf(self, format_addr, *args):
        fmt = self.memory.read_string(format_addr)#  把格式化字串 (例如 "Hello %s, score: %d\n") 從記憶體讀出來
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
    
    def builtin_puts(self, addr):
        s = self.memory.read_string(addr)
        print(s)
        return 0
    
    def builtin_getchar(self):
        char = sys.stdin.read(1)
        if not char:
            return -1
        return ord(char)
    
    def builtin_scanf(self, format_addr, *args):
        #因為printf還支援%s,%x所以這邊也加上
        fmt = self.memory.read_string(format_addr)
        try:
            user_input = input().split()
        except EOFError:
            return -1
        
        arg_idx = 0
        count = 0
        pos = 0

        while pos < len(fmt) and arg_idx < len(args) and count < len(user_input):
            if fmt[pos] == '%' and pos + 1 < len(fmt):
                specifier = fmt[pos+1]
                target_addr = args[arg_idx]
                current_val = user_input[count]

                if specifier == 'd':
                    #(bytes = 4)
                    val = int(user_input[count])
                    self.memory.write_int(target_addr, val)
                    count +=1
                    arg_idx +=1
                elif specifier == 'c':
                    #(byte = 1)
                    val = ord(user_input[count][0])
                    self.memory.write_char(target_addr, val)
                    count +=1
                    arg_idx +=1
                elif specifier == 's':
                    for i, char in enumerate(current_val):
                        self.memory.write_char(target_addr + i, ord(char))
                    self.memory.write_char(target_addr + len(current_val), 0)
                    count += 1
                    arg_idx +=1
                elif specifier == 'x':
                    self.memory.write_int(target_addr, int(current_val, 16))
                    count +=1
                    arg_idx+=1

                pos +=2
            else:
                pos +=1
        return count
    
    # ─── 字串處理函式 ────────────────────────────────────────────────────────
    def builtin_strlen(self, addr):
        s = self.memory.read_string(addr)
        length  = len(s)
        return length

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

    # ─── 數學函式 ────────────────────────────────────────────────────────
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
            raise RuntimeError("Runtime Error: sqrt() argument must be non-negative.")
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


    # ─── 記憶體與工具函數 ────────────────────────────────────────────────────────
    def builtin_memset(self, addr, value, size):
        for i in range(size):
            self.memory.write_char(addr + i, value)

    def builtin_sizeof_int(self):
        return 4

    def builtin_sizeof_char(self):
        return 1

    def builtin_atoi(self, addr):
        """把記憶體裡的字串讀出來，轉成整數後直接回傳整數值 (不寫回記憶體)"""
        s = self.memory.read_string(addr)
        try:
            return int(s)
        except (ValueError, TypeError):
            return 0  # C 語言標準：無法轉換時回傳 0

    def builtin_itoa(self, value, addr):
        """整數轉字串，寫到 addr 指向的 buffer 裡，回傳 addr"""
        s = str(value)
        for i in range(len(s)):
            self.memory.write_char(addr + i, ord(s[i]))  # ord() 轉成 ASCII 數值
        self.memory.write_char(addr + len(s), '\0')  # 補 0
        return addr
    
    def builtin_exit(self, code):
        print(f"\nProgram exited via exit({code})")
        raise SystemExit(code)
