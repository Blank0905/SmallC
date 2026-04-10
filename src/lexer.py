class Token:
    def __init__(self, type, value, line):
        self.type = type   # 例如: 'INT_TYPE', 'PLUS', 'INT_CONST', 'ID'
        self.value = value # 例如: 'int', '+', 42, 'x'
        self.line = line   # 記錄行號，方便出錯時回報

    def __str__(self):
        return f"Token({self.type}, {self.value}, Line {self.line})"

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0        # 當前字元位置
        self.current_char = self.text[self.pos] if self.text else None
        self.line = 1       # 記錄行號以供錯誤回報

    def advance(self):
        """移動到下一個字元"""
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def next_char(self):
        """偷看下一個字元但不移動指標"""
        next_pos = self.pos + 1
        if next_pos > len(self.text) - 1:
            return None
        return self.text[next_pos]

    def skip_whitespace(self):
        """跳過空白、換行與定位符"""
        while self.current_char is not None and self.current_char.isspace():
            if self.current_char == '\n':
                self.line += 1
            self.advance()

    def _string(self):
        """處理字串常數 "..." """
        result = ''
        self.advance() # 跳過開頭引號
        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()
        self.advance() # 跳過結尾引號
        return Token('STRING_CONST', result, self.line)

    def integer(self):
        """讀取整數常數（包含十進位與十六進位）"""
        result = ''
        
        # 處理十六進位 0x 或 0X
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

        # 處理一般十進位 
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)
    
    def _identifier(self):
        """處理變數名稱與關鍵字"""
        result = ''
        # 持續讀取字母、數字或底線
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()

        # 關鍵字對照表
        keywords = {
            'int': 'INT_TYPE',
            'char': 'CHAR_TYPE',
            'void': 'VOID_TYPE',
            'if': 'IF',
            'while': 'WHILE',
            'for': 'FOR',
            'do': 'DO',
            'else': 'ELSE',
            'break': 'BREAK',
            'continue': 'CONTINUE',
            'return': 'RETURN',
            'main': 'MAIN'
        }

        # 查表決定 Token 類型
        token_type = keywords.get(result, 'ID')
        return Token(token_type, result, self.line)
    
    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # 辨識整數
            if self.current_char.isdigit():
                return Token('INT_CONST', self.integer(), self.line)
            
            if self.current_char.isalpha() or self.current_char == '_':
                return self._identifier()
            
            # 字串處理
            if self.current_char == '"':
                return self._string()

            # 辨識算術運算子
            if self.current_char == '+':
                if self.next_char() == '+':
                    self.advance()
                    self.advance()
                    return Token('PLUS_ONE', '++', self.line)
                if self.next_char() == '=':
                    self.advance()
                    self.advance()
                    return Token('ADD_ASSIGN', '+=', self.line)
                self.advance()
                return Token('PLUS', '+', self.line)
            
            if self.current_char == '&':#&
                if self.next_char() == '&':#&&
                    self.advance(); self.advance()
                    return Token('LOGIC_AND', '&&', self.line)
                self.advance()
                return Token('BIT_AND', '&', self.line)
            
            if self.current_char == '|':
                if self.next_char() == '|':
                    self.advance(); self.advance()
                    return Token('LOGIC_OR', '||', self.line)
                self.advance()
                return Token('BIT_OR', '|', self.line)
            
            if self.current_char == '>':
                if self.next_char() == '=':
                    self.advance(); self.advance()
                    return Token('GE', '>=', self.line)
                if self.next_char() == '>':
                    self.advance(); self.advance()
                    return Token('RSHIFT', '>>', self.line)
                self.advance()
                return Token('GT', '>', self.line)
            
            if self.current_char == '<':
                if self.next_char() == '=':
                    self.advance(); self.advance()
                    return Token('LE', '<=', self.line)
                if self.next_char() == '<':
                    self.advance()
                    self.advance()
                    return Token('LSHIFT', '<<', self.line)
                self.advance()
                return Token('LT', '<', self.line)

            if self.current_char == '-':
                if self.next_char == '-':
                    self.advance()
                    self.advance()
                    return Token('MINUS_ONE', '--', self.line)
                if self.next_char == '=':
                    self.advance()
                    self.advance()
                    return Token('SUB_ASSIGN', '-=', self.line)
                self.advance()
                return Token('MINUS', '-', self.line)
            
            if self.current_char == '*':
                if self.next_char == '=':
                    self.advance()
                    self.advance()
                    return Token('MUL_ASSIGN', '*=', self.line)
                self.advance()
                return Token('MUL', '*', self.line)
            
            if self.current_char == '/':
                if self.next_char == '=':
                    self.advance()
                    self.advance()
                    return Token('DIV_ASSIGN', '/=', self.line)
                self.advance()
                return Token('DIV', '/', self.line)
            
            if self.current_char == '^':
                self.advance()
                return Token('XOR', '^', self.line)
            
            if self.current_char == '=':
                if self.next_char() == '=': #==
                    self.advance()
                    self.advance()
                    return Token('EQ', '==', self.line)
                self.advance()
                return Token('ASSIGN', '=', self.line)
            
            if self.current_char == '!':
                if self.next_char() == '=': #!=
                    self.advance(); self.advance()
                    return Token('NEQ', '!=', self.line)
                self.advance()
                return Token('NOT', '!', self.line)
            
            if self.current_char == '%':
                if self.next_char() == '=':
                    self.advance(); self.advance()
                    return Token('MOD_ASSIGN', '%=', self.line)
                self.advance()
                return Token('MOD', '%', self.line)
            
            # 辨識括號
            if self.current_char == '(':
                self.advance()
                return Token('LPAREN', '(', self.line)
            
            if self.current_char == ')':
                self.advance()
                return Token('RPAREN', ')', self.line)

            # 如果遇到無法辨識的字元，報錯
            raise Exception(f'Lexer Error: Unknown character {self.current_char} at line {self.line}')

        return Token('EOF', None, self.line) # 結束符號


                 # 最後印出 EOF