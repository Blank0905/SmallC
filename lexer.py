class Token:
    def __init__(self, type, value, line):
        self.type = type   # 例如: 'INT_TYPE', 'PLUS', 'INT_CONST', 'ID'
        self.value = value # 例如: 'int', '+', 42, 'x'
        self.line = line   # 記錄行號，方便出錯時回報 [cite: 138]

    def __str__(self):
        return f"Token({self.type}, {self.value}, Line {self.line})"

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0        # 當前字元位置
        self.current_char = self.text[self.pos] if self.text else None
        self.line = 1       # 記錄行號以供錯誤回報 [cite: 6]

    def advance(self):
        """移動到下一個字元"""
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        """跳過空白、換行與定位符 [cite: 19]"""
        while self.current_char is not None and self.current_char.isspace():
            if self.current_char == '\n':
                self.line += 1
            self.advance()

    def integer(self):
        """讀取整數常數（包含十進位與十六進位） [cite: 18]"""
        result = ''
        
        # 處理十六進位 0x 或 0X [cite: 18]
        if self.current_char == '0':
            result += self.current_char
            self.advance()
            if self.current_char in ('x', 'X'):
                result += self.current_char
                self.advance()
                while self.current_char is not None and \
                      (self.current_char.isdigit() or self.current_char.lower() in 'abcdef'):
                    result += self.current_char
                    self.advance()
                return int(result, 16)

        # 處理一般十進位 [cite: 18]
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)
    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # 辨識整數 [cite: 18]
            if self.current_char.isdigit():
                return Token('INT_CONST', self.integer(), self.line)

            # 辨識算術運算子 [cite: 39, 43]
            if self.current_char == '+':
                self.advance()
                return Token('PLUS', '+', self.line)
            if self.current_char == '-':
                self.advance()
                return Token('MINUS', '-', self.line)
            if self.current_char == '*':
                self.advance()
                return Token('MUL', '*', self.line)
            if self.current_char == '/':
                self.advance()
                return Token('DIV', '/', self.line)
            
            # 辨識括號 [cite: 39]
            if self.current_char == '(':
                self.advance()
                return Token('LPAREN', '(', self.line)
            if self.current_char == ')':
                self.advance()
                return Token('RPAREN', ')', self.line)

            # 如果遇到無法辨識的字元，報錯 [cite: 6]
            raise Exception(f'Lexer Error: Unknown character {self.current_char} at line {self.line}')

        return Token('EOF', None, self.line) # 結束符號


                 # 最後印出 EOF