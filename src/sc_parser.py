from lexer import Lexer, Token
from ast_node import *

class Parser:
    """
    遞迴下降解析器（Recursive Descent Parser）
    
    把 Lexer 產生的 Token 串，依照 SmallC 的語法規則，
    組合成一棵抽象語法樹（AST）。

    運算子優先級（由低到高）：
      = += -= *= /= %=    賦值（右結合）
      ? :                 三元
      ||                  邏輯 OR
      &&                  邏輯 AND
      |                   位元 OR
      ^                   位元 XOR
      &                   位元 AND
      == !=               等號比較
      < > <= >=           大小比較
      << >>               位元移位
      + -                 加減
      * / %               乘除餘
      (前置) ! ~ - ++ --  一元前置
      (後置) ++ -- []()   後置與呼叫
    """

    def __init__(self, tokens):
        self.tokens = tokens        # 完整 Token 列表（含 EOF）
        self.pos = 0
        self.current_token = self.tokens[0]

    # ─── 基礎工具 ─────────────────────────────────────────────────────────────

    def advance(self):
        """消費目前 token，移動到下一個"""
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]

    def eat(self, token_type):
        """
        確認目前 token 的類型是 token_type，然後消費它。
        如果類型不符，拋出語法錯誤。
        """
        if self.current_token.type == token_type:
            token = self.current_token
            self.advance()
            return token
        raise SyntaxError(
            f"Parser Error: Expected {token_type}, "
            f"got {self.current_token.type}('{self.current_token.value}') "
            f"at line {self.current_token.line}"
        )

    def peek(self, offset=1):
        """預看 offset 個位置後的 token，不移動指標"""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]  # 回傳 EOF

    def is_type_keyword(self):
        """目前 token 是否為型別關鍵字"""
        return self.current_token.type in ('INT_TYPE', 'CHAR_TYPE', 'VOID_TYPE')

    # ─── 型別解析 ──────────────────────────────────────────────────────────────

    def parse_type(self):
        """
        解析型別，例如：int、char、void、int*、char**
        回傳 TypeNode
        """
        base = self.current_token.value     # 'int' | 'char' | 'void'
        self.advance()                      # 消費型別關鍵字
        depth = 0
        while self.current_token.type == 'MUL':  # 每個 * 增加一層指標
            depth += 1
            self.advance()
        return TypeNode(base, depth)

    # ─── 頂層解析 ──────────────────────────────────────────────────────────────

    def parse_program(self):
        """
        解析整個程式。
        程式由若干個全域宣告或函式定義組成，直到 EOF。
        回傳 ProgramNode。
        """
        declarations = []
        while self.current_token.type != 'EOF':
            # 如果目前是 int/char/void，走全域宣告 (變數或函式)
            if self.is_type_keyword():
                declarations.append(self.parse_top_level())
            else:
                # 否則，這是一條「全域即時執行語句」
                declarations.append(self.parse_statement())
        return ProgramNode(declarations)

    def parse_top_level(self):
        """
        解析頂層項目（函式定義 或 全域變數宣告）。
        兩者都以「型別 識別字」開頭，靠後面是否有 '(' 來區分。

            int add(...)   → 函式定義
            int x = 5;     → 全域變數宣告
        """
        type_node = self.parse_type()
        name_token = self.eat('ID')
        name = name_token.value

        if self.current_token.type == 'LPAREN':
            # 函式定義
            return self.parse_func_def(type_node, name, name_token.line)
        else:
            # 全域變數宣告
            return self.parse_var_decl_rest(type_node, name, name_token.line)

    # ─── 函式定義 ──────────────────────────────────────────────────────────────

    def parse_func_def(self, return_type, name, line):
        """
        已知型別與名稱，從 '(' 開始解析函式定義。
        格式：( params ) block
        """
        self.eat('LPAREN')
        params = self.parse_params()
        self.eat('RPAREN')
        body = self.parse_block()
        return FuncDefNode(return_type, name, params, body, line)

    def parse_params(self):
        """
        解析函式參數列表，例如：int a, char* s, int b
        回傳 list of VarDeclNode。
        空參數列表（void 或空括號）回傳 []。
        """
        params = []
        # 空參數：() 或 (void)
        if self.current_token.type == 'RPAREN':
            return params
        if self.current_token.type == 'VOID_TYPE' and self.peek().type == 'RPAREN':
            self.advance()  # 消費 void
            return params

        # 第一個參數
        params.append(self.parse_single_param())
        # 後續參數
        while self.current_token.type == 'COMMA':
            self.eat('COMMA')
            params.append(self.parse_single_param())
        return params

    def parse_single_param(self):
        """解析單一參數，例如 int a 或 char* s"""
        type_node = self.parse_type()
        name = self.eat('ID').value
        line = self.current_token.line
        return VarDeclNode(type_node, name, line)

    # ─── 區塊與語句 ────────────────────────────────────────────────────────────

    def parse_block(self):
        """
        解析大括號區塊：{ statement* }
        回傳 BlockNode。
        """
        self.eat('LBRACE')
        stmts = []
        while self.current_token.type != 'RBRACE':
            if self.current_token.type == 'EOF':
                raise SyntaxError(f"Parser Error: Unclosed block, missing '}}'")
            stmts.append(self.parse_statement())
        self.eat('RBRACE')
        return BlockNode(stmts)

    def parse_statement(self):
        """
        解析一條語句，根據目前 token 類型分派：
          - 型別關鍵字     → 變數宣告
          - if             → if 語句
          - while          → while 迴圈
          - do             → do-while 迴圈
          - for            → for 迴圈
          - return         → return 語句
          - break          → break
          - continue       → continue
          - {              → 巢狀區塊
          - 其他           → 表達式語句
        """
        t = self.current_token.type

        if self.is_type_keyword():
            return self.parse_var_decl()
        elif t == 'IF':
            return self.parse_if()
        elif t == 'SWITCH':
            return self.parse_switch()
        elif t == 'WHILE':
            return self.parse_while()
        elif t == 'DO':
            return self.parse_do_while()
        elif t == 'FOR':
            return self.parse_for()
        elif t == 'RETURN':
            return self.parse_return()
        elif t == 'BREAK':
            line = self.current_token.line
            self.advance()
            self.eat('SEMI')
            return BreakNode(line)
        elif t == 'CONTINUE':
            line = self.current_token.line
            self.advance()
            self.eat('SEMI')
            return ContinueNode(line)
        elif t == 'LBRACE':
            return self.parse_block()
        else:
            return self.parse_expr_stmt()

    # ─── 變數宣告 ──────────────────────────────────────────────────────────────

    def parse_var_decl(self):
        """
        解析變數宣告語句，例如：
            int x;
            int x = 5;
            int a[10];
            char* s = "hi";
        """
        line = self.current_token.line
        type_node = self.parse_type()
        name = self.eat('ID').value
        return self.parse_var_decl_rest(type_node, name, line)

    def parse_var_decl_rest(self, type_node, name, line):
        """
        已知型別與名稱，解析宣告的剩餘部分（初始值、陣列大小、分號）。
        """
        array_size = None
        init_expr = None

        if self.current_token.type == 'LBRACK':
            # 陣列宣告：int a[10]
            self.eat('LBRACK')
            array_size = self.parse_expr()
            self.eat('RBRACK')

        if self.current_token.type == 'ASSIGN':
            # 初始值：int x = 5
            self.eat('ASSIGN')
            init_expr = self.parse_expr()

        self.eat('SEMI')
        return VarDeclNode(type_node, name, line, init_expr, array_size)

    # ─── 控制流程語句 ──────────────────────────────────────────────────────────

    def parse_if(self):
        """
        解析 if-else，例如：
            if (x > 0) { ... }
            if (x > 0) { ... } else { ... }
            if (x > 0) { ... } else if (y > 0) { ... }  ← else if 鏈
        """
        line = self.current_token.line
        self.eat('IF')
        self.eat('LPAREN')
        condition = self.parse_expr()
        self.eat('RPAREN')
        then_block = self.parse_statement()  # 可以是 block 或單一語句
        else_block = None
        if self.current_token.type == 'ELSE':
            self.eat('ELSE')
            else_block = self.parse_statement()  # else if 或 else { }
        return IfNode(condition, then_block, line, else_block)

    def parse_while(self):
        """解析 while 迴圈：while (cond) body"""
        line = self.current_token.line
        self.eat('WHILE')
        self.eat('LPAREN')
        condition = self.parse_expr()
        self.eat('RPAREN')
        body = self.parse_statement()      
        return WhileNode(condition, body, line)

    def parse_do_while(self):
        """解析 do-while：do body while (cond);"""
        line = self.current_token.line
        self.eat('DO')
        body = self.parse_statement()
        self.eat('WHILE')
        self.eat('LPAREN')
        condition = self.parse_expr()
        self.eat('RPAREN')
        self.eat('SEMI')       
        return DoWhileNode(body, condition, line)

    def parse_for(self):
        """
        解析 for 迴圈：for (init; cond; update) body
        init 可以是變數宣告或表達式，三個部分都可省略。
        """
        line = self.current_token.line
        self.eat('FOR')
        self.eat('LPAREN')

        # 初始化
        if self.current_token.type == 'SEMI':
            init = None
            self.eat('SEMI')
        elif self.is_type_keyword():
            init = self.parse_var_decl()   # 已含 SEMI
        else:
            init = self.parse_expr()
            self.eat('SEMI')

        # 條件
        if self.current_token.type == 'SEMI':
            condition = None
        else:
            condition = self.parse_expr()
        self.eat('SEMI')

        # 更新
        if self.current_token.type == 'RPAREN':
            update = None
        else:
            update = self.parse_expr()

        self.eat('RPAREN')
        body = self.parse_statement()
        
        return ForNode(init, condition, update, body, line)

    def parse_return(self):
        """解析 return 語句：return; 或 return expr;"""
        line = self.current_token.line
        self.eat('RETURN')
        if self.current_token.type == 'SEMI':
            self.eat('SEMI')
            return ReturnNode(None)
        value = self.parse_expr()
        self.eat('SEMI')
        return ReturnNode(value, line)

    def parse_expr_stmt(self):
        """解析表達式語句（expr 後面接 ;）"""
        line = self.current_token.line
        expr = self.parse_expr()
        self.eat('SEMI')
        return ExprStmtNode(expr, line)
    
    def parse_switch(self):
        line = self.current_token.line
        self.eat('SWITCH')
        self.eat('LPAREN')
        condition_expr = self.parse_expr()
        self.eat('RPAREN')
        self.eat('LBRACE')

        cases = []
        default_stmt = None
        
        while self.current_token.type != 'RBRACE':
            if self.current_token.type =='CASE':
                self.eat('CASE')
                case_val = self.eat('INT_CONST').value
                self.eat('COLON')

                case_stmts = []
                while self.current_token.type not in ('CASE', 'DEFAULT', 'RBRACE'):
                    case_stmts.append(self.parse_statement())
                cases.append((case_val, BlockNode(case_stmts)))
            
            elif self.current_token.type == 'DEFAULT':
                self.eat('DEFAULT')
                self.eat('COLON')
                default_stmts = []
                while self.current_token.type not in ('CASE', 'DEFAULT', 'RBRACE'):
                    default_stmts.append(self.parse_statement())
                default_stmt = BlockNode(default_stmts)
            
            else:
                self.advance()

        self.eat('RBRACE')
        return SwitchNode(condition_expr, cases, default_stmt, line)

    # ─── 表達式（依優先級由低到高） ────────────────────────────────────────────

    def parse_expr(self):
        """
        最低優先級入口，處理賦值與三元運算。
        賦值是右結合（x = y = 5 → x = (y = 5)）。
        """
        return self.parse_assignment()

    def parse_assignment(self):
        """
        賦值：target = expr | target += expr | ...
        先嘗試解析右邊，如果遇到賦值運算子才確認是賦值。
        """
        #line = self.current_token.line
        left = self.parse_ternary()

        ASSIGN_OPS = ('ASSIGN', 'ADD_ASSIGN', 'SUB_ASSIGN',
                      'MUL_ASSIGN', 'DIV_ASSIGN', 'MOD_ASSIGN')
        if self.current_token.type in ASSIGN_OPS:
            line = self.current_token.line
            op = self.current_token.value
            self.advance()
            value = self.parse_assignment()  # 右結合：遞迴自己
            return AssignNode(left, op, value, line)

        return left

    def parse_ternary(self):
        """三元運算：condition ? then_expr : else_expr"""
        condition = self.parse_logic_or()
        if self.current_token.type == 'QUESTION':
            self.eat('QUESTION')
            then_expr = self.parse_expr()
            self.eat('COLON')
            else_expr = self.parse_ternary()  # 右結合
            return TernaryNode(condition, then_expr, else_expr)
        return condition

    def parse_logic_or(self):
        """邏輯 OR：a || b"""
        left = self.parse_logic_and()
        while self.current_token.type == 'LOGIC_OR':
            op = self.current_token.value
            self.advance()
            right = self.parse_logic_and()
            left = BinOpNode(left, op, right)
        return left

    def parse_logic_and(self):
        """邏輯 AND：a && b"""
        left = self.parse_bit_or()
        while self.current_token.type == 'LOGIC_AND':
            op = self.current_token.value
            self.advance()
            right = self.parse_bit_or()
            left = BinOpNode(left, op, right)
        return left

    def parse_bit_or(self):
        """位元 OR：a | b"""
        left = self.parse_bit_xor()
        while self.current_token.type == 'BIT_OR':
            op = self.current_token.value
            self.advance()
            right = self.parse_bit_xor()
            left = BinOpNode(left, op, right)
        return left

    def parse_bit_xor(self):
        """位元 XOR：a ^ b"""
        left = self.parse_bit_and()
        while self.current_token.type == 'XOR':
            op = self.current_token.value
            self.advance()
            right = self.parse_bit_and()
            left = BinOpNode(left, op, right)
        return left

    def parse_bit_and(self):
        """位元 AND：a & b"""
        left = self.parse_equality()
        while self.current_token.type == 'BIT_AND':
            op = self.current_token.value
            self.advance()
            right = self.parse_equality()
            left = BinOpNode(left, op, right)
        return left

    def parse_equality(self):
        """等號比較：a == b、a != b"""
        left = self.parse_relational()
        while self.current_token.type in ('EQ', 'NEQ'):
            op = self.current_token.value
            self.advance()
            right = self.parse_relational()
            left = BinOpNode(left, op, right)
        return left

    def parse_relational(self):
        """大小比較：a < b、a > b、a <= b、a >= b"""
        left = self.parse_shift()
        while self.current_token.type in ('LT', 'GT', 'LE', 'GE'):
            op = self.current_token.value
            self.advance()
            right = self.parse_shift()
            left = BinOpNode(left, op, right)
        return left

    def parse_shift(self):
        """位元移位：a << 2、a >> 1"""
        left = self.parse_additive()
        while self.current_token.type in ('LSHIFT', 'RSHIFT'):
            op = self.current_token.value
            self.advance()
            right = self.parse_additive()
            left = BinOpNode(left, op, right)
        return left

    def parse_additive(self):
        """加減：a + b、a - b"""
        left = self.parse_multiplicative()
        while self.current_token.type in ('PLUS', 'MINUS'):
            op = self.current_token.value
            self.advance()
            right = self.parse_multiplicative()
            left = BinOpNode(left, op, right)
        return left

    def parse_multiplicative(self):
        """乘除餘：a * b、a / b、a % b"""
        left = self.parse_unary()
        while self.current_token.type in ('MUL', 'DIV', 'MOD'):
            op = self.current_token.value
            self.advance()
            right = self.parse_unary()
            left = BinOpNode(left, op, right)
        return left

    def parse_unary(self):
        """
        前置一元運算：
          -x、+x（正負號）
          !x（邏輯非）
          ~x（位元非）
          ++x、--x（前置遞增/遞減）
          *x（dereference）
          &x（取址）
          (type)x（強制轉型）
        """
        t = self.current_token.type

        if t in ('MINUS', 'PLUS', 'NOT', 'BIT_NOT'):
            op = self.current_token.value
            self.advance()
            return UnaryOpNode(op, self.parse_unary())

        if t in ('INC', 'DEC'):
            op = self.current_token.value
            self.advance()
            return UnaryOpNode(op, self.parse_unary(), prefix=True)

        if t == 'MUL':  # dereference *x
            self.advance()
            return UnaryOpNode('*', self.parse_unary())

        if t == 'BIT_AND':  # 取址 &x
            self.advance()
            return UnaryOpNode('&', self.parse_unary())

        # 強制轉型：(int)、(char*)...
        if t == 'LPAREN' and self.is_type_keyword_at(self.pos + 1):
            self.eat('LPAREN')
            type_node = self.parse_type()
            self.eat('RPAREN')
            return CastNode(type_node, self.parse_unary())

        return self.parse_postfix()

    def is_type_keyword_at(self, pos):
        """輔助：確認指定位置的 token 是否為型別關鍵字"""
        if pos < len(self.tokens):
            return self.tokens[pos].type in ('INT_TYPE', 'CHAR_TYPE', 'VOID_TYPE')
        return False

    def parse_postfix(self):
        """
        後置運算：
          x++、x--（後置遞增/遞減）
          a[i]   （陣列索引）
          f(...)  （函式呼叫）
        """
        node = self.parse_primary()

        while True:
            if self.current_token.type in ('INC', 'DEC'):
                op = self.current_token.value
                self.advance()
                node = UnaryOpNode(op, node, prefix=False)

            elif self.current_token.type == 'LBRACK':
                self.eat('LBRACK')
                index = self.parse_expr()
                self.eat('RBRACK')
                node = ArrayIndexNode(node, index)

            elif self.current_token.type == 'LPAREN':
                # 函式呼叫（從 primary 傳上來的 VarNode 轉為 FuncCallNode）
                line = self.current_token.line
                self.eat('LPAREN')
                args = self.parse_args()
                self.eat('RPAREN')
                name = node.name if isinstance(node, VarNode) else str(node)
                node = FuncCallNode(name, args, line)

            else:
                break

        return node

    def parse_args(self):
        """解析函式呼叫的引數列表，回傳 list of ASTNode"""
        args = []
        if self.current_token.type == 'RPAREN':
            return args
        args.append(self.parse_expr())
        while self.current_token.type == 'COMMA':
            self.eat('COMMA')
            args.append(self.parse_expr())
        return args

    def parse_primary(self):
        """
        最高優先級（原子單元）：
          數字字面量、字元字面量、字串字面量
          識別字（變數名稱）
          括號表達式 (expr)
        """
        t = self.current_token.type

        if t == 'INT_CONST':
            val = self.current_token.value
            self.advance()
            return IntLiteralNode(val)

        if t == 'CHAR_CONST':
            val = self.current_token.value
            self.advance()
            return CharLiteralNode(val)

        if t == 'STRING_CONST':
            val = self.current_token.value
            self.advance()
            return StringLiteralNode(val)

        if t == 'ID':
            name = self.current_token.value
            line = self.current_token.line
            self.advance()
            return VarNode(name, line)

        if t == 'LPAREN':
            self.eat('LPAREN')
            node = self.parse_expr()
            self.eat('RPAREN')
            return node

        raise SyntaxError(
            f"Parser Error: Unexpected token {self.current_token.type}"
            f"('{self.current_token.value}') at line {self.current_token.line}"
        )

    # ─── 對外介面 ──────────────────────────────────────────────────────────────

    def parse(self):
        """parser 的對外入口，回傳整個程式的 AST"""
        return self.parse_program()
