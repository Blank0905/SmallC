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
        self.escape_map = {'n': '\n', 't': '\t', '0': '\0', '\\': '\\', "'": "'", '"': '"'}
        self.keywords = {
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
            'return': 'RETURN'
        }

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

    def _char(self):
        """處理字元常數 '...'"""
        self.advance() # 跳過 '
        if self.current_char == "'":
            raise Exception(f"Lexer Error: Empty character constant at line {self.line}")
        
        if self.current_char == '\\': # 跳脫序列
            self.advance()
            val = self.escape_map.get(self.current_char, self.current_char)
        else:
            val = self.current_char
            
        self.advance()
        if self.current_char != "'":
            raise Exception(f"Lexer Error: Character not closed at line {self.line}")
        self.advance() # 跳過結尾 '
        return Token('CHAR_CONST', val, self.line)
    
    def _string(self):
        """處理字串常數 "..." 並支援跳脫序列"""
        result = ''
        self.advance()  # 跳過開頭引號 "
        
        while self.current_char is not None and self.current_char != '"':
            if self.current_char == '\\':  # 偵測到跳脫字元
                self.advance()
                result += self.escape_map.get(self.current_char, self.current_char)
            else:
                result += self.current_char
            self.advance()
            
        if self.current_char != '"':
            raise Exception(f"Lexer Error: String not closed at line {self.line}")
            
        self.advance()  # 跳過結尾引號 "
        
        return Token('STRING_CONST', result + '\0', self.line)
        
    def _skip_single_line_comment(self):
        """跳過 // 註解"""
        # 進來前 get_next_token 已經確認過是 // 了
        # 消耗掉開頭的兩個 /
        self.advance()
        self.advance()
        # 一直讀到行末或檔案結束
        while self.current_char is not None and self.current_char != '\n':
            self.advance()
        # 停在 \n，交給下一輪 skip_whitespace 處理

    def _skip_multi_line_comment(self):
        """跳過 /* */ 註解"""
        # 消耗掉開頭的 /*
        self.advance()
        self.advance()
        
        while self.current_char is not None:
            # 偵測結尾 */
            if self.current_char == '*' and self.next_char() == '/':
                self.advance() # 消耗 *
                self.advance() # 消耗 /
                return 
            
            if self.current_char == '\n':
                self.line += 1
            self.advance()
            
        # 如果沒看到 */ 就結束了，拋出錯誤
        raise Exception(f'Lexer Error: Unclosed block comment at line {self.line}')

    def integer(self):
        """讀取整數常數（包含十進位與十六進位）"""
        
        # 處理十六進位 0x 或 0X
        if self.current_char == '0' and self.next_char() in ('x', 'X'):
            self.advance()
            self.advance()
            hex_digits = ''
            while self.current_char is not None and (self.current_char.isdigit() or self.current_char.lower() in 'abcdef'):
                hex_digits += self.current_char
                self.advance()
            if not hex_digits:
                raise Exception(f'Lexer Error: Invalid hexadecimal literal at line {self.line}')
            return int(hex_digits, 16)

        # 處理一般十進位
        result = ''
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

        # 查表決定 Token 類型
        token_type = self.keywords.get(result, 'ID')
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
            
            #字元處理
            if self.current_char == '\'':
                return self._char()
            
            # 字串處理
            if self.current_char == '"':
                return self._string()

            # 辨識算術運算子
            if self.current_char == '+':
                if self.next_char() == '+':
                    self.advance()
                    self.advance()
                    return Token('INC', '++', self.line)
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
                if self.next_char() == '-':
                    self.advance()
                    self.advance()
                    return Token('DEC', '--', self.line)
                if self.next_char() == '=':
                    self.advance()
                    self.advance()
                    return Token('SUB_ASSIGN', '-=', self.line)
                if self.next_char() == '>':
                    self.advance()
                    self.advance()
                    return Token('ARROW', '->', self.line)
                self.advance()
                return Token('MINUS', '-', self.line)
            
            if self.current_char == '*':
                if self.next_char() == '=':
                    self.advance()
                    self.advance()
                    return Token('MUL_ASSIGN', '*=', self.line)
                self.advance()
                return Token('MUL', '*', self.line)
            
            if self.current_char == '/':
                if self.next_char() == '/':
                    self._skip_single_line_comment()
                    continue  # 註解跳過後，繼續找下一個真正的 Token
                if self.next_char() == '*':
                    self._skip_multi_line_comment()
                    continue
                if self.next_char() == '=':
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
            
            if self.current_char == '(':
                self.advance()
                return Token('LPAREN', '(', self.line)
            
            if self.current_char == ')':
                self.advance()
                return Token('RPAREN', ')', self.line)
            
            if self.current_char == '[':
                self.advance()
                return Token('LBRACK', '[', self.line)
            
            if self.current_char == ']':
                self.advance()
                return Token('RBRACK', ']', self.line)
            
            if self.current_char == '{':
                self.advance()
                return Token('LBRACE', '{', self.line)
            
            if self.current_char == '}':
                self.advance()
                return Token('RBRACE', '}', self.line)
            
            if self.current_char == ':':
                self.advance()
                return Token('COLON', ':', self.line)
            
            if self.current_char == ',':
                self.advance()
                return Token('COMMA', ',', self.line)
            
            if self.current_char == ';':
                self.advance()
                return Token('SEMI', ';', self.line)
            
            if self.current_char == '?':
                self.advance()
                return Token('QUESTION', '?', self.line)
            
            if self.current_char == '~':
                self.advance()
                return Token('BIT_NOT', '~', self.line)
            

            # 如果遇到無法辨識的字元，報錯
            raise Exception(f'Lexer Error: Unknown character {self.current_char} at line {self.line}')

        return Token('EOF', None, self.line) # 結束符號


                 # 最後印出 EOF