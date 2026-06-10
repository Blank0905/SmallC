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
                        output += chr(val & 0xFF)            # 取低 8 bit，避免 signed char 為負時 chr() 崩潰
                    elif specifier == 's':
                        output += self.memory.read_string(val)
                    elif specifier == 'x':
                        output += format(val & 0xFFFFFFFF, 'x')  # 以 unsigned 32-bit 印 hex，符合 C 的 %x 語意
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
        fmt = self.memory.read_string(format_addr)
        try:
            user_input = input()
        except EOFError:
            return -1

        def skip_space(index):
            while index < len(user_input) and user_input[index].isspace():
                index += 1
            return index

        def read_digits(index, valid_chars, allow_sign=False):
            start = index
            if allow_sign and index < len(user_input) and user_input[index] in "+-":
                index += 1
            digit_start = index
            while index < len(user_input) and user_input[index].lower() in valid_chars:
                index += 1
            if index == digit_start:
                return None, start
            return user_input[start:index], index

        input_pos = 0
        pos = 0
        arg_idx = 0
        assigned = 0

        while pos < len(fmt):
            if fmt[pos].isspace():
                input_pos = skip_space(input_pos)
                pos += 1
                continue

            if fmt[pos] != '%':
                if input_pos >= len(user_input) or user_input[input_pos] != fmt[pos]:
                    break
                input_pos += 1
                pos += 1
                continue

            if pos + 1 < len(fmt):
                specifier = fmt[pos+1]
                if specifier == '%':
                    if input_pos >= len(user_input) or user_input[input_pos] != '%':
                        break
                    input_pos += 1
                    pos += 2
                    continue

                if arg_idx >= len(args):
                    break
                target_addr = args[arg_idx]

                if specifier == 'd':
                    input_pos = skip_space(input_pos)
                    token, next_pos = read_digits(input_pos, set("0123456789"), allow_sign=True)
                    if token is None:
                        break
                    val = int(token, 10)
                    self.memory.write_int(target_addr, val)
                    input_pos = next_pos
                    arg_idx += 1
                    assigned += 1
                elif specifier == 'c':
                    if input_pos >= len(user_input):
                        break
                    val = ord(user_input[input_pos])
                    self.memory.write_char(target_addr, val)
                    input_pos += 1
                    arg_idx += 1
                    assigned += 1
                elif specifier == 's':
                    input_pos = skip_space(input_pos)
                    start = input_pos
                    while input_pos < len(user_input) and not user_input[input_pos].isspace():
                        input_pos += 1
                    if input_pos == start:
                        break
                    current_val = user_input[start:input_pos]
                    for i, char in enumerate(current_val):
                        self.memory.write_char(target_addr + i, ord(char))
                    self.memory.write_char(target_addr + len(current_val), 0)
                    arg_idx += 1
                    assigned += 1
                elif specifier == 'x':
                    input_pos = skip_space(input_pos)
                    sign = ""
                    if input_pos < len(user_input) and user_input[input_pos] in "+-":
                        sign = user_input[input_pos]
                        input_pos += 1
                    if input_pos + 1 < len(user_input) and user_input[input_pos:input_pos+2].lower() == "0x":
                        input_pos += 2
                    token, next_pos = read_digits(input_pos, set("0123456789abcdef"))
                    if token is None:
                        break
                    self.memory.write_int(target_addr, int(sign + token, 16))
                    input_pos = next_pos
                    arg_idx += 1
                    assigned += 1
                else:
                    break
                pos += 2
            else:
                break
        return assigned
    
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
            raise RuntimeError("Runtime Error: pow() exponent must be non-negative.")
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
