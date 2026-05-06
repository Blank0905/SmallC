# ─── 基底類別 ─────────────────────────────────────────────────────────────────

class ASTNode:
    """所有 AST 節點的基底類別"""
    pass

# ─── 字面量（Literals） ────────────────────────────────────────────────────────

class IntLiteralNode(ASTNode):
    """整數字面量，例如 42、0xff"""
    def __init__(self, value):
        self.value = value          # int，例如 42

class CharLiteralNode(ASTNode):
    """字元字面量，例如 'a'、'\n'"""
    def __init__(self, value):
        self.value = value          # str（單一字元），例如 'a'

class StringLiteralNode(ASTNode):
    """字串字面量，例如 "hello" """
    def __init__(self, value):
        self.value = value          # str，例如 'hello'

# ─── 變數與型別 ────────────────────────────────────────────────────────────────

class VarNode(ASTNode):
    """讀取變數的值，例如 x"""
    def __init__(self, name, line):
        self.name = name            # str，變數名稱
        self.line = line            # 行號，方便報錯

class TypeNode(ASTNode):
    """型別節點，例如 int、char、void、int*"""
    def __init__(self, base_type, pointer_depth=0):
        self.base_type = base_type      # 'int' | 'char' | 'void'
        self.pointer_depth = pointer_depth  # 0=普通, 1=指標(*), 2=雙指標(**)

# ─── 宣告（Declarations） ─────────────────────────────────────────────────────

class VarDeclNode(ASTNode):
    """變數宣告，例如 int x; 或 int x = 5;"""
    def __init__(self, type_node, name, line, init_expr=None, array_size=None):
        self.type_node = type_node      # TypeNode
        self.name = name                # str，變數名稱
        self.init_expr = init_expr      # ASTNode | None，初始值
        self.array_size = array_size    # ASTNode | None，陣列大小（int a[10] 的 10）
        self.line = line

class FuncDefNode(ASTNode):
    """函式定義，例如 int add(int a, int b) { return a + b; }"""
    def __init__(self, return_type, name, params, body, line=None, text=None):
        self.return_type = return_type  # TypeNode
        self.name = name                # str，函式名稱
        self.params = params            # list of VarDeclNode（參數列表）
        self.body = body                # BlockNode
        self.line = line                # 函式名稱所在行號

# ─── 運算式（Expressions） ────────────────────────────────────────────────────

class BinOpNode(ASTNode):
    """二元運算，例如 a + b、x == y"""
    def __init__(self, left, op, right):
        self.left = left        # ASTNode
        self.op = op            # str，運算子符號，例如 '+'
        self.right = right      # ASTNode

class UnaryOpNode(ASTNode):
    """一元運算，例如 -x、!flag、~bits、++i、*ptr、&x"""
    def __init__(self, op, operand, prefix=True):
        self.op = op            # str，例如 '-'、'!'、'++'
        self.operand = operand  # ASTNode
        self.prefix = prefix    # True=前置(++i), False=後置(i++)

class AssignNode(ASTNode):
    """賦值，例如 x = 5、x += 1"""
    def __init__(self, target, op, value, line):
        self.target = target    # ASTNode（左值：VarNode、ArrayIndexNode 等）
        self.op = op            # str，例如 '='、'+='
        self.value = value      # ASTNode
        self.line = line

class TernaryNode(ASTNode):
    """三元運算，例如 a ? b : c"""
    def __init__(self, condition, then_expr, else_expr):
        self.condition = condition
        self.then_expr = then_expr
        self.else_expr = else_expr

class FuncCallNode(ASTNode):
    """函式呼叫，例如 printf("hi")、add(1, 2)"""
    def __init__(self, name, args, line):
        self.name = name        # str，函式名稱
        self.args = args        # list of ASTNode
        self.line = line

class ArrayIndexNode(ASTNode):
    """陣列索引，例如 a[i]"""
    def __init__(self, array, index):
        self.array = array      # ASTNode（陣列變數）
        self.index = index      # ASTNode（索引表達式）

class CastNode(ASTNode):
    """強制轉型，例如 (int)x、(char*)p"""
    def __init__(self, type_node, expr):
        self.type_node = type_node  # TypeNode
        self.expr = expr            # ASTNode

# ─── 語句（Statements） ────────────────────────────────────────────────────────

class BlockNode(ASTNode):
    """大括號區塊，包含一串語句，例如 { int x = 1; return x; }"""
    def __init__(self, statements):
        self.statements = statements    # list of ASTNode

class ExprStmtNode(ASTNode):
    """表達式語句（expression + 分號），例如 x = 1;"""
    def __init__(self, expr, line):
        self.expr = expr        # ASTNode
        self.line = line

class IfNode(ASTNode):
    """if-else，例如 if (x > 0) { ... } else { ... }"""
    def __init__(self, condition, then_block, line, else_block=None):
        self.condition = condition      # ASTNode
        self.then_block = then_block    # ASTNode（BlockNode 或單一語句）
        self.else_block = else_block    # ASTNode | None
        self.line = line

class WhileNode(ASTNode):
    """while 迴圈，例如 while (i < 10) { ... }"""
    def __init__(self, condition, body, line):
        self.condition = condition      # ASTNode
        self.body = body                # ASTNode
        self.line = line

class DoWhileNode(ASTNode):
    """do-while 迴圈，例如 do { ... } while (x > 0);"""
    def __init__(self, body, condition, line):
        self.body = body            # ASTNode
        self.condition = condition  # ASTNode
        self.line = line

class ForNode(ASTNode):
    """for 迴圈，例如 for (int i=0; i<10; i++) { ... }"""
    def __init__(self, init, condition, update, body, line):
        self.init = init            # ASTNode | None（初始化）
        self.condition = condition  # ASTNode | None（條件）
        self.update = update        # ASTNode | None（更新）
        self.body = body            # ASTNode
        self.line = line

class ReturnNode(ASTNode):
    """return 語句，例如 return x + 1;"""
    def __init__(self, value=None, line = -1):
        self.value = value      # ASTNode | None（void 函式 return; 時為 None）
        self.line = line

class BreakNode(ASTNode):
    """break; 語句"""
    def __init__(self, line):
        self.line = line

class ContinueNode(ASTNode):
    """continue; 語句"""
    def __init__(self, line):
        self.line = line

class ProgramNode(ASTNode):
    """整個程式（最頂層節點），包含所有全域宣告與函式定義"""
    def __init__(self, declarations):
        self.declarations = declarations    # list of ASTNode
