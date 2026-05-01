from ast_node import *

class Interpreter:
    def __init__(self, symtable, memory, builtins):
        self.symtable = symtable
        self.memory = memory
        self.builtins = builtins
        self.string_pool = {}

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
        data_type = node.type_node.base_type # 拿出他的型別

        symbol = self.symtable.define_var(name=node.name, data_type=data_type, is_array=(node.array_size is not None)) # 去符號表註冊此變數，symbol會是一個Symbol物件

        # 如果宣告時有給初始值 (init_expr)
        if node.init_expr is not None:
            value = self.visit(node.init_expr) # 這邊會拿到等號右邊的值

            if data_type == 'int': #根據變數宣告的型別來寫入值
                self.memory.write_int(symbol.address, value)
            elif data_type == 'char':
                self.memory.write_char(symbol.address, value)
        return None

    def visit_VarNode(self, node):
        """碰到變數名稱，例如程式碼裡的 `x + 5` 的 `x`，就要去記憶體把它的值拿出來"""
        
        # 1. 去符號表查這個變數放在哪裡
        symbol = self.symtable.lookup(node.name)
        
        # 2. 去記憶體的那個位址，把數字讀出來並回傳
        if symbol.data_type == 'int':
            return self.memory.read_int(symbol.address)
        elif symbol.data_type == 'char':
            return self.memory.read_char(symbol.address)
        else:
            # 如果是指標或陣列，我們通常是需要它的位址，而不是裡面的值
            return symbol.address
    
    def visit_StringLiteralNode(self, node):
        """碰到字串字面量 (例如 "Hello")，實作字串池 (String Pooling) 避免記憶體浪費"""
        
        # 檢查字串池，如果這個字串以前存過了，直接回傳舊位址！
        if node.value in self.string_pool:
            return self.string_pool[node.value]
            
        # 如果是第一次遇到，再去做配置與寫入
        s_bytes = node.value.encode('utf-8')
        addr = self.memory.alloc_global(len(s_bytes) + 1)
        
        for i, byte_val in enumerate(s_bytes):
            self.memory.write_char(addr + i, byte_val)
        self.memory.write_char(addr + len(s_bytes), 0)
        
        # 存好之後，把它記錄到字串池裡
        self.string_pool[node.value] = addr
        return addr

    def visit_FuncCallNode(self, node):
        """處理函式呼叫，例如 printf("Hello %d", a);"""
        
        # 1. 遞迴把刮號裡面所有的參數都先算出來
        args_values = []
        for arg in node.args:
            args_values.append(self.visit(arg))
            
        # 2. 判斷是不是我們已經寫好的內建函式 (例如 printf, strcmp)
        if self.builtins.is_builtin(node.name):
            # 直接交給 BuiltinManager 去執行，並回傳它執行的結果！
            return self.builtins.call(node.name, args_values)
        else:
            # (我們之後會在這裡處理使用者自己寫的自訂函式)
            raise NotImplementedError(f"自訂函式 '{node.name}' 的呼叫尚未實作！")
   
    def visit_AssignNode(self, node):
        """處理變數重新賦值，例如 a = 10; 或 a += 5;"""

        right_val = self.visit(node.value) # 把等號右邊的值從node裡面讀出來

        if isinstance(node.target, VarNode): # 看左邊這個變數是不是VarNode
            symbol = self.symtable.lookup(node.target.name)
            addr = symbol.address
            data_type = symbol.data_type
        else:
            raise NotImplementedError("目前只支援對普通變數賦值，指標或陣列賦值尚未實作") # 未完成
        
        if node.op != '=': # 處理 +=, -=, *=, /=
            if data_type == 'int':
                old_val = self.memory.read_int(addr)
            elif data_type == 'char':
                old_val = self.memory.read_char(addr)

            if node.op == '+=':right_val = old_val + right_val
            elif node.op == '-=': right_val = old_val - right_val
            elif node.op == '*=': right_val = old_val * right_val
            elif node.op == '/=': right_val = old_val // right_val
            elif node.op == '%=': right_val = old_val % right_val

        if data_type == 'int':
            self.memory.write_int(addr, right_val)
        elif data_type =='char':
            self.memory.write_char(addr, right_val)

        return right_val

    def visit_ExprStmtNode(self, node): # 應該是回傳整個式子
        """處理加上了分號的純表達式，例如 a = 10;"""
        # 直接把裡面的表達式拿出來執行即可
        return self.visit(node.expr)
