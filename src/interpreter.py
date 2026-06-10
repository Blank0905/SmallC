from ast_node import *

class ReturnException(Exception):
    """用來模擬 C 語言 return 中斷機制的自訂例外"""
    def __init__(self, value, has_value=True):
        self.value = value
        self.has_value = has_value

class BreakException(Exception):
    """用來模擬 C 語言 break 中斷迴圈的機制"""
    pass

class ContinueException(Exception):
    """用來模擬 C 語言 continue 跳過本次迴圈的機制"""
    pass

class Interpreter:
    def __init__(self, symtable, memory, builtins, program_buffer, trace):
        self.program_buffer = program_buffer
        self.trace = trace
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

    def _type_name(self, type_node):
        return type_node.base_type + ("*" * type_node.pointer_depth)

    def _array_element_type(self, symbol):
        if symbol.data_type.endswith('*'):
            return symbol.data_type[:-1]
        return symbol.data_type

    def _dereference_type(self, ptr_type):
        if not ptr_type.endswith('*'):
            raise RuntimeError(f"Semantic Error: cannot dereference non-pointer type '{ptr_type}'")
        return ptr_type[:-1]

    def _ensure_value_expr(self, node):
        data_type = self._get_node_type(node)
        if data_type == 'void':
            raise RuntimeError("Semantic Error: void function call cannot be used as a value")
        return data_type
    
    def _get_node_type(self, node):
        """輔助函式：推導 AST 節點運算後的資料型別"""
        if isinstance(node, VarNode):
            symbol = self.symtable.lookup(node.name)
            if symbol.is_array:                       # 陣列名在算術中退化成指向元素的指標
                return symbol.data_type + '*'
            return symbol.data_type
        if isinstance(node, UnaryOpNode) and node.op == '&':
            return self._get_node_type(node.operand) + "*"
        if isinstance(node, UnaryOpNode) and node.op == '*':
            t = self._get_node_type(node.operand)
            return self._dereference_type(t)
        if isinstance(node, ArrayIndexNode):
            # 陣列索引的結果型別 = 基底指標剝掉一層 *（基底不一定是具名陣列）
            base_type = self._get_node_type(node.array)
            return base_type[:-1] if base_type.endswith('*') else base_type
        if isinstance(node, CastNode):
            return self._type_name(node.type_node)
        if isinstance(node, FuncCallNode):
            if self.builtins.is_builtin(node.name):
                return 'int'
            symbol = self.symtable.lookup_func(node.name)
            return symbol.data_type
        if isinstance(node, BinOpNode):
            # 指標算術的結果型別跟著指標那一側（例如 p + 1 仍是指標）
            left_type = self._get_node_type(node.left)
            if left_type.endswith('*'):
                return left_type
            right_type = self._get_node_type(node.right)
            if right_type.endswith('*'):
                return right_type
            return 'int'
        return 'int'

    def _read_typed(self, addr, data_type):
        """依型別從記憶體讀值：char 讀 1 byte，其餘（int / 指標）讀 4 bytes"""
        if data_type == 'char':
            return self.memory.read_char(addr)
        return self.memory.read_int(addr)

    def _write_typed(self, addr, data_type, value):
        """依型別把值寫入記憶體"""
        if data_type == 'char':
            self.memory.write_char(addr, value)
        else:
            self.memory.write_int(addr, value)

    def _resolve_lvalue(self, node):
        """算出可賦值節點 (lvalue) 的記憶體位址與資料型別，回傳 (addr, data_type)。
        支援：普通變數、陣列索引 arr[i]、指標解參考 *expr。"""
        if isinstance(node, VarNode):
            symbol = self.symtable.lookup(node.name)
            return symbol.address, symbol.data_type
        if isinstance(node, ArrayIndexNode):
            base_addr = self.visit(node.array)
            index = self.visit(node.index)
            data_type = self._get_node_type(node)
            # 只有基底是具名陣列時才有長度可做邊界檢查
            if isinstance(node.array, VarNode):
                symbol = self.symtable.lookup(node.array.name)
                if symbol.is_array and (index < 0 or index >= symbol.array_len):
                    raise RuntimeError(
                        f"Runtime Error: array index out of bounds (index {index}, size {symbol.array_len})"
                    )
            size = 4 if data_type == 'int' else 1
            return base_addr + index * size, data_type
        if isinstance(node, UnaryOpNode) and node.op == '*':
            ptr_type = self._get_node_type(node.operand)
            data_type = self._dereference_type(ptr_type)
            addr = self.visit(node.operand)
            if addr == 0: # 位址 0 保留給 NULL，寫入空指標即為空指標存取
                raise RuntimeError("Runtime Error: null pointer dereference.")
            return addr, data_type
        raise RuntimeError("Runtime Error: invalid lvalue (此運算式無法取得位址)")

    def _visit_control_body(self, node):
        self.memory.push_frame()
        self.symtable.enter_block()
        try:
            return self.visit(node)
        finally:
            self.symtable.leave_block()
            self.memory.pop_frame()

    def _trace(self, node):
        if self.trace == False:
            return
        line = getattr(node, 'line', None) # line = node.line 但如果存取不到node.line會預設是None
        if not line:
            return
        stmt = '<unknown>'
        if self.program_buffer and 1 <= line <= len(self.program_buffer):
            stmt = self.program_buffer[line - 1].strip() # strip(): 移除字串頭尾的空白字元（包含半形/全形空格、換行符號 \n、Tab \t 等）
        print(f"[line {line}] {stmt}")


    # ==========================================
    # 執行各個 AST 節點的具體邏輯
    # ==========================================

    def visit_ProgramNode(self, node):
        """程式的最上層節點，裡面包著所有程式碼，我們就一行一行往下執行"""
        result = None
        for declaration in node.declarations:
            result = self.visit(declaration)

        # 全部定義都掃描完之後，看有沒有 main 函式，有的話就自動啟動！
        try:
            self.symtable.lookup_func("main")
        except Exception:
            return result
        main_call = FuncCallNode("main", [], 0)
        return self.visit_FuncCallNode(main_call)

    def visit_FuncCallNode(self, node):
        """處理函式呼叫，例如 printf("Hello %d", a);"""
        
        # 把刮號裡面所有的參數都先算出來
        args_values = []
        for arg in node.args:
            self._ensure_value_expr(arg)
            args_values.append(self.visit(arg))
            
        # 判斷是不是我們已經寫好的內建函式 (例如 printf, strcmp)
        if self.builtins.is_builtin(node.name):
            # 直接交給 BuiltinManager 去執行，並回傳它執行的結果！
            return self.builtins.call(node.name, args_values)
        else:
            func_symbol = self.symtable.lookup_func(node.name) # 去符號表找function名稱
            func_node = func_symbol.func_node

            if len(func_node.params) != len(args_values):
                raise RuntimeError(
                    f"Semantic Error: function '{node.name}' expected "
                    f"{len(func_node.params)} argument(s), got {len(args_values)}"
                )

            # === 備份目前的區域變數狀態 ===
            saved_locals = self.symtable.locals.copy()
            saved_block_scopes = list(self.symtable.block_scopes)
            saved_is_global = self.symtable.is_global_scope

            # 進入函式前：開啟全新記憶體框架與區域變數表
            self.memory.push_frame()
            self.symtable.enter_function()

            for param, arg_val in zip(func_node.params, args_values):
                data_type = self._type_name(param.type_node)
                param_symbol = self.symtable.define_var(
                    name=param.name,
                    data_type=data_type, # 變數的型別
                    is_array=False
                )
                if data_type == 'char':
                    self.memory.write_char(param_symbol.address, arg_val)
                else:
                    self.memory.write_int(param_symbol.address, arg_val)

            # 開始執行函式區塊
            ret_val = 0
            has_return = False
            return_type = self._type_name(func_node.return_type)

            try:
                try:
                    self.visit(func_node.body)
                except ReturnException as e: # 有return
                    # 接住 return 回來的值
                    has_return = True
                    if return_type != 'void' and not e.has_value:
                        raise RuntimeError(
                            f"Semantic Error: non-void function '{node.name}' should return a value"
                        )
                    if return_type == 'void' and e.has_value:
                        raise RuntimeError(
                            f"Semantic Error: void function '{node.name}' should not return a value"
                        )
                    ret_val = e.value
            finally:
                # 清空記憶體與符號表
                self.symtable.leave_function()
                self.memory.pop_frame()

                self.symtable.locals = saved_locals
                self.symtable.block_scopes = saved_block_scopes
                self.symtable.is_global_scope = saved_is_global

            if return_type != 'void' and not has_return:
                raise RuntimeError(
                    f"Semantic Error: non-void function '{node.name}' reached end without return"
                )
            
            return ret_val

    # ─── 字面量（Literals） ────────────────────────────────────────────────────────

    def visit_IntLiteralNode(self, node):
        """碰到純數字，執行結果就是數字本身"""
        return node.value

    def visit_CharLiteralNode(self, node):
        """碰到字元字面量，例如 'a'、'\n'"""
        return node.value
    
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

    # ─── 變數與型別 ────────────────────────────────────────────────────────────────

    def visit_VarNode(self, node):
        """碰到變數名稱，例如程式碼裡的 `x + 5` 的 `x`，就要去記憶體把它的值拿出來"""
        
        # 去符號表查這個變數放在哪裡
        symbol = self.symtable.lookup(node.name)
        
        # 如果這是陣列，不能去讀它的值
        if symbol.is_array:
            return symbol.address

        # 去記憶體的那個位址，把數字讀出來並回傳
        if symbol.data_type == 'int':
            return self.memory.read_int(symbol.address)
        elif symbol.data_type == 'char':
            return self.memory.read_char(symbol.address)
        else:
            # 指標變數：裡面存的是位址，用 read_int 讀出來
            return self.memory.read_int(symbol.address)

    def visit_ArrayIndexNode(self, node):
        """處理陣列讀取，例如: arr[i]、(*p)[i]"""
        # 透過 _resolve_lvalue 算出位址與元素型別（基底不限定是 VarNode）
        addr, data_type = self._resolve_lvalue(node)
        return self._read_typed(addr, data_type)

    # ─── 宣告（Declarations） ─────────────────────────────────────────────────────

    def visit_VarDeclNode(self, node):
        """處理變數宣告，包含陣列的大括號初始化"""
        self._trace(node)

        data_type = self._type_name(node.type_node)

        # 檢查是否為陣列
        is_array = (node.array_size is not None)
        array_len = 0
        if is_array:
            array_len = self.visit(node.array_size)
            if not isinstance(array_len, int) or array_len <= 0:
                raise RuntimeError(
                    f"Semantic Error: array '{node.name}' size must be a positive integer (got {array_len})"
                )

        # 去符號表註冊此變數
        symbol = self.symtable.define_var(
            name=node.name, 
            data_type=data_type, 
            is_array=is_array, 
            array_len=array_len
        )

        # 如果宣告時有給初始值
        if node.init_expr is not None:
            # 情況 A：如果是遇到我們新加的大括號初始化列表 InitListNode
            if isinstance(node.init_expr, InitListNode):
                if not is_array:
                    raise RuntimeError(f"Semantic Error: Initializer list cannot be used on non-array variable '{node.name}'")
                if len(node.init_expr.expressions) > array_len:
                    raise RuntimeError(
                        f"Semantic Error: excess elements in array initializer for '{node.name}' "
                        f"(size {array_len}, got {len(node.init_expr.expressions)})"
                    )
                
                # 遍歷大括號裡的每一個元素，把它算出來並依序寫入陣列對應的記憶體位置
                for i, expr in enumerate(node.init_expr.expressions):
                    val = self.visit(expr)
                    element_type = self._array_element_type(symbol)
                    
                    if element_type == 'int':
                        self.memory.write_int(symbol.address + i * 4, val)
                    elif element_type == 'char':
                        self.memory.write_char(symbol.address + i * 1, val)
            
            # 情況 B：char 陣列以字串字面初始化（例如 char str[6] = "hi";）
            # 逐 byte 複製字串內容到 str，截斷至 array_len-1 並保留 null terminator
            elif is_array and data_type == 'char' and isinstance(node.init_expr, StringLiteralNode):
                src_addr = self.visit(node.init_expr)
                i = 0
                while i < array_len - 1:
                    b = self.memory.read_char(src_addr + i)
                    if b == 0:
                        break
                    self.memory.write_char(symbol.address + i, b)
                    i += 1
                self.memory.write_char(symbol.address + i, 0)  # 確保 null-terminated

            # 情況 C：原本的普通單一變數初始化（例如 int x = 5; int *p = &x;）
            else:
                if data_type != 'void':
                    self._ensure_value_expr(node.init_expr)
                value = self.visit(node.init_expr)
                self._write_typed(symbol.address, data_type, value)  # 涵蓋 int / char / int* / char*
                    
        return None

    def visit_FuncDefNode(self, node):
        """當直譯器看到函式定義時，不需要立刻執行，只要把它記錄到符號表裡就好"""

        self.symtable.define_func(
            name=node.name,
            data_type=self._type_name(node.return_type),
            func_node=node
        )

        return None

    # ─── 運算式（Expressions） ────────────────────────────────────────────────────

    def visit_TernaryNode(self, node):
        """三元運算 cond ? a : b，依條件結果只計算其中一邊"""
        self._ensure_value_expr(node.condition)
        if self.visit(node.condition):
            self._ensure_value_expr(node.then_expr)
            return self.visit(node.then_expr)
        self._ensure_value_expr(node.else_expr)
        return self.visit(node.else_expr)

    def visit_CastNode(self, node):
        """強制轉型 (int)x、(char)x、(int*)p、(char*)p"""
        value = self.visit(node.expr)
        target = self._type_name(node.type_node)
        if target == 'char':
            value = int(value)
            return ((value + 128) % 256) - 128
        if target == 'int':
            value = int(value)
            return ((value + 2**31) % 2**32) - 2**31
        # 指標型別轉型：直接維持位址值（這個解譯器內就是整數）
        return int(value)

    def visit_BinOpNode(self, node):
        
        """碰到二元運算子 (例如加減乘除)"""
        self._ensure_value_expr(node.left)
        left = self.visit(node.left)

        if node.op == '&&':
            if left == 0:
                return 0
            else:
                self._ensure_value_expr(node.right)
                if self.visit(node.right) != 0:
                    return 1
                else: return 0
        elif node.op == '||':
            if left != 0:
                return 1
            else:
                self._ensure_value_expr(node.right)
                if self.visit(node.right) != 0:
                    return 1
                else: 
                    return 0
        
        self._ensure_value_expr(node.right)
        right = self.visit(node.right)
        
        left_type = self._get_node_type(node.left)
        right_type = self._get_node_type(node.right)

        if node.op == '+':
            # 指標 + 整數
            if left_type.endswith('*'):
                size = 4 if 'int' in left_type else 1
                return left + (right * size)
            # 整數 + 指標
            if right_type.endswith('*'):
                size = 4 if 'int' in right_type else 1
                return (left * size) + right
            return left + right

        elif node.op == '-':
            if left_type.endswith('*'):
                # 指標 - 指標：計算距離
                if right_type.endswith('*'):
                    size = 4 if 'int' in left_type else 1
                    return (left - right) // size
                # 指標 - 整數
                size = 4 if 'int' in left_type else 1
                return left - (right * size)
            return left - right
        elif node.op == '*':
            return left * right
        elif node.op == '/':
            if right == 0:
                raise RuntimeError("Runtime Error: Division by zero")
            # C 的整數除法朝 0 截斷，Python 的 // 朝 -∞ 取整，需自己處理
            q = abs(left) // abs(right)
            return -q if (left < 0) ^ (right < 0) else q
        elif node.op == '%':
            if right == 0:
                raise RuntimeError("Runtime Error: Modulo by zero")
            # C 餘數符號跟被除數一致：a == (a/b)*b + a%b
            q = abs(left) // abs(right)
            if (left < 0) ^ (right < 0):
                q = -q
            return left - q * right
        elif node.op == '&':
            return left & right
        elif node.op == '|':
            return left | right
        elif node.op == '^':
            return left ^ right
        elif node.op == '<<':
            return left << right
        elif node.op == '>>':
            return left >> right
        elif node.op == '>':
            return 1 if left > right else 0
        elif node.op == '<':
            return 1 if left < right else 0
        elif node.op == '>=':
            return 1 if left >= right else 0
        elif node.op == '<=':
            return 1 if left <= right else 0
        elif node.op == '==':
            return 1 if left == right else 0
        elif node.op == '!=':
            return 1 if left != right else 0

    def visit_UnaryOpNode(self, node):
        """處理單元運算子，例如 -5, +3, !flag, &x, *ptr"""
        
        # &x 取址：不能先算 operand 的值，要直接查符號表拿位址
        if node.op == '&':
            if isinstance(node.operand, VarNode): # 先檢查是否是VarNode
                symbol = self.symtable.lookup(node.operand.name)
                return symbol.address
            elif isinstance(node.operand, ArrayIndexNode):
                base_addr = self.visit(node.operand.array)
                index = self.visit(node.operand.index)
                symbol = self.symtable.lookup(node.operand.array.name)
                data_type = self._array_element_type(symbol)
                if data_type == 'int':
                    return base_addr + index * 4
                else:
                    return base_addr + index * 1
            else:
                raise RuntimeError("Runtime Error: Cannot take address of non-lvalue")

        # ++ / -- 需要寫回 lvalue：先解析位址，避免重複求值 operand 造成副作用
        # （同時支援 arr[0]++、(*p)++ 等非 VarNode 的 lvalue）
        if node.op in ('++', '--'):
            addr, data_type = self._resolve_lvalue(node.operand)
            old_value = self._read_typed(addr, data_type)
            # 指標以元素為單位前進/後退，int* 走 4、char* 走 1，一般數值走 1
            step = 4 if data_type == 'int*' else 1
            if node.op == '--':
                step = -step
            new_value = old_value + step
            self._write_typed(addr, data_type, new_value)
            return new_value if node.prefix else old_value

        # 其他運算子都需要先算出 operand 的值
        self._ensure_value_expr(node.operand)
        value = self.visit(node.operand)

        if node.op == '-':
            return -value
        elif node.op == '+':
            return value
        elif node.op == '!':
            return 1 if value == 0 else 0
        elif node.op == '~':
            return ~value
        elif node.op == '*':
            ptr_type = self._get_node_type(node.operand)
            data_type = self._dereference_type(ptr_type)
            addr = value  # operand 算出來就是記憶體位址
            if addr == 0: # 位址 0 保留給 NULL，解參考即為空指標存取
                raise RuntimeError("Runtime Error: null pointer dereference.")
            # 用型別推導決定讀幾個 bytes，支援 *(p+1)、*(char*)p 等運算式
            return self._read_typed(addr, data_type)
        else:
            raise RuntimeError(f"Runtime Error: Unknown unary operator '{node.op}'")

    def visit_AssignNode(self, node):
        """處理變數重新賦值，例如 a = 10; 或 arr[i] += 5;"""

        self._ensure_value_expr(node.value)
        right_val = self.visit(node.value) # 把等號右邊的值從node裡面讀出來

        # 解析左邊 lvalue 的位址與型別（支援變數、陣列索引 arr[i]、指標解參考 *expr）
        addr, data_type = self._resolve_lvalue(node.target)

        if node.op != '=': # 處理 +=, -=, *=, /=, %=
            old_val = self._read_typed(addr, data_type)

            # 處理指標複合運算的「比例因子 (Scaling Factor)」
            scale = 1
            if data_type.endswith('*'):
                scale = 4 if data_type.startswith('int') else 1

            if node.op == '+=':
                right_val = old_val + (right_val * scale) # 乘上型別大小
            elif node.op == '-=':
                right_val = old_val - (right_val * scale) # 乘上型別大小
            elif node.op == '*=':
                right_val = old_val * right_val
            elif node.op == '/=':
                if right_val == 0:
                    raise RuntimeError("Runtime Error: Division by zero")
                q = abs(old_val) // abs(right_val)
                right_val = -q if (old_val < 0) ^ (right_val < 0) else q
            elif node.op == '%=':
                if right_val == 0:
                    raise RuntimeError("Runtime Error: Modulo by zero")
                q = abs(old_val) // abs(right_val)
                if (old_val < 0) ^ (right_val < 0):
                    q = -q
                right_val = old_val - q * right_val

        self._write_typed(addr, data_type, right_val)
        return right_val

    # ─── 語句（Statements） ────────────────────────────────────────────────────────

    def visit_BlockNode(self, node):
        """處理大括號 { ... } 裡面的程式碼區塊"""
        
        for stmt in node.statements: # 把裡面的每一行程式碼，每一行都會是Node，依序拿出來跑
            self.visit(stmt)
            
        return None

    def visit_ExprStmtNode(self, node): # 應該是回傳整個式子
        """處理加上了分號的純表達式，例如 a = 10;"""
        self._trace(node)
        # 直接把裡面的表達式拿出來執行即可
        return self.visit(node.expr)

    def visit_IfNode(self, node):
        """處理if-else，例如 if (x > 0) { ... } else { ... }"""
        self._trace(node)
        self._ensure_value_expr(node.condition)
        if self.visit(node.condition) != 0:
            self._visit_control_body(node.then_block)
        elif node.else_block is not None:
            self._visit_control_body(node.else_block)
        return None
    
    def visit_ReturnNode(self, node):
        """處理 return 語句"""
        self._trace(node)
        value = 0
        has_value = node.value is not None
        if node.value is not None:
            self._ensure_value_expr(node.value)
            value = self.visit(node.value) # 算出 return 後面的數字
            
        # 像丟球一樣，把答案丟出去，瞬間中斷後面的所有程式碼！
        raise ReturnException(value, has_value)

    def visit_WhileNode(self, node):
        while True:
            self._trace(node)
            self._ensure_value_expr(node.condition)
            if self.visit(node.condition) == 0:
                break
            try:
                self._visit_control_body(node.body)
            except BreakException:
                break
            except ContinueException:
                continue  # 直接跳回去重新判斷條件

    def visit_DoWhileNode(self, node):
        while True:
            self._trace(node)
            try:
                self._visit_control_body(node.body)
            except BreakException:
                break
            except ContinueException:
                pass
            self._ensure_value_expr(node.condition)
            if self.visit(node.condition) == 0:
                break

    def visit_ForNode(self, node):
        self.memory.push_frame()
        self.symtable.enter_block()
        try:
            if node.init is not None:
                self._trace(node) # 追蹤初始化部分
                self.visit(node.init)
            while True:
                self._trace(node) # 追蹤條件判定
                if node.condition is not None:
                    self._ensure_value_expr(node.condition)
                if node.condition is not None and self.visit(node.condition) == 0:
                    break
                try:
                    self._visit_control_body(node.body)
                except BreakException:
                    break
                except ContinueException:
                    pass
                if node.update is not None:
                    # self._trace(node) # 更新部分是否追蹤可再商榷，目前通常追蹤一次 for 即可
                    self.visit(node.update)
        finally:
            self.symtable.leave_block()
            self.memory.pop_frame()

    def visit_SwitchNode(self, node):
        val = self.visit(node.expr) # 先算出 switch(x) 裡面 x 的值
        found = False

        try:
            # 遍歷所有 case 分支
            for case_val, block in node.cases:
                # 如果找到匹配的 case，或者已經在『穿透』(Fall-through) 狀態
                if val == case_val or found:
                    found = True
                    self.visit(block)
            
            # 如果跑完所有 case 都沒匹配到，且有 default 分支
            if not found and node.default_stmt:
                self.visit(node.default_stmt)
                
        except BreakException:
            # 捕捉到 break，代表要跳出 switch 區塊，正常結束此 visit 函式
            pass
            
        return None




    def visit_BreakNode(self, node):
        self._trace(node)
        raise BreakException()

    def visit_ContinueNode(self, node):
        self._trace(node)
        raise ContinueException()
