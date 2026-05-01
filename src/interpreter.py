from ast_node import *

class Interpreter:
    def __init__(self, symtable, memory, builtins):
        self.symtable = symtable
        self.memory = memory
        self.builtins = builtins

    def visit(self, node):
        """
        Visitor 模式的核心引擎：
        它會偷看傳進來的 node 是什麼型別（例如 BinOpNode），
        然後自動去找對應的函式（例如 visit_BinOpNode）來執行！
        """
        if node is None:
            return None
        
        # 取得節點的類別名稱，組成方法名稱
        method_name = f'visit_{type(node).__name__}'
        
        # 利用 Python 的 getattr 動態尋找函式，找不到就報錯
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"Interpreter Error: 找不到處理 {type(node).__name__} 的方法！")

    # ==========================================
    # 執行各個 AST 節點的具體邏輯
    # ==========================================

    def visit_ProgramNode(self, node):
        """程式的最上層節點，裡面包著所有程式碼，我們就一行一行往下執行"""
        result = None
        for declaration in node.declarations:
            result = self.visit(declaration)
        return result

    def visit_IntLiteralNode(self, node):
        """碰到純數字，執行結果就是數字本身"""
        return node.value

    def visit_BinOpNode(self, node):
        """碰到二元運算子 (例如加減乘除)"""
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        # 2. 根據運算子種類，執行真正的 Python 運算
        # （把 node.op.type 改成直接比對 node.op 字串）
        if node.op == '+':
            return left + right
        elif node.op == '-':
            return left - right
        elif node.op == '*':
            return left * right
        elif node.op == '/':
            if right == 0:
                raise RuntimeError("Runtime Error: Division by zero")
            return left // right   # C語言的整數除法是無條件捨去，所以用 //

    def visit_VarDeclNode(self, node):
        """處理變數宣告，例如: int x = 1 + 2 * 3;"""
        value = 0
        
        # 如果宣告時有給初始值 (init_expr)
        if node.init_expr is not None:
            # 去算等號右邊的結果！(這裡就會觸發你去跑 visit_BinOpNode)
            value = self.visit(node.init_expr)
            
        # 我們之後會在這裡把 value 存進 symtable 和 memory，
        # 但為了讓你現在就能看到成果，我們先偷偷把它印出來！
        print(f"[*] 成功宣告變數 '{node.name}'，等號右邊計算的結果為: {value}")
        
        return value

