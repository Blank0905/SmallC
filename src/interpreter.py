from ast_node import *

class ReturnException(Exception):
    """用來模擬 C 語言 return 中斷機制的自訂例外"""
    def __init__(self, value):
        self.value = value

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
        self.in_block_scope = False  # 追蹤是否在 if/while/for 區塊內

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

    def _visit_control_body(self, node):
        old_flag = self.in_block_scope
        self.in_block_scope = True
        try:
            return self.visit(node)
        finally:
            self.in_block_scope = old_flag

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
            main_sym = self.symtable.lookup("main")
            if main_sym.sym_type == 'FUNC':               
                # 假裝我們在寫程式呼叫 main()
                main_call = FuncCallNode("main", [], 0)
                return self.visit_FuncCallNode(main_call)
        except Exception as e:
            if "not found" not in str(e).lower():
                print(f"[*] 執行 main 時發生未預期錯誤: {e}")        
        return result

    def visit_FuncCallNode(self, node):
        """處理函式呼叫，例如 printf("Hello %d", a);"""
        
        # 把刮號裡面所有的參數都先算出來
        args_values = []
        for arg in node.args:
            args_values.append(self.visit(arg))
            
        # 判斷是不是我們已經寫好的內建函式 (例如 printf, strcmp)
        if self.builtins.is_builtin(node.name):
            # 直接交給 BuiltinManager 去執行，並回傳它執行的結果！
            return self.builtins.call(node.name, args_values)
        else:
            func_symbol = self.symtable.lookup(node.name) # 去符號表找function名稱
            func_node = func_symbol.func_node

            if len(func_node.params) != len(args_values):
                raise RuntimeError(
                    f"Semantic Error: function '{node.name}' expected "
                    f"{len(func_node.params)} argument(s), got {len(args_values)}"
                )

            # === 備份目前的區域變數狀態 ===
            saved_locals = self.symtable.locals.copy()
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
            old_block_flag = self.in_block_scope
            self.in_block_scope = False  # 進入新函式，重置區塊旗標以允許開頭宣告

            try:
                try:
                    self.visit(func_node.body)
                except ReturnException as e: # 有return
                    # 接住 return 回來的值
                    ret_val = e.value
            finally:
                self.in_block_scope = old_block_flag # 恢復原本的旗標狀態
                    
                # 清空記憶體與符號表
                self.symtable.leave_function()
                self.memory.pop_frame()

                self.symtable.locals = saved_locals
                self.symtable.is_global_scope = saved_is_global
            
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
        """處理陣列讀取，例如: arr[i]"""
        # 取得陣列的起始位置 (base_addr)
        base_addr = self.visit(node.array)
        
        # 算出索引值 (index)
        index = self.visit(node.index)
        
        # 找出陣列元素的型別 (要知道是 int 還是 char，才能決定讀幾個 bytes)
        symbol = self.symtable.lookup(node.array.name)
        data_type = self._array_element_type(symbol)

        # 邊界檢查
        if symbol.is_array and (index < 0 or index >= symbol.array_len):
            raise RuntimeError(f"Runtime Error: array index out of bounds. (index {index}, size {symbol.array_len})")
            
        # 根據型別，計算實際記憶體位置並讀取
        if data_type == 'int':
            # int 佔 4 個 bytes
            target_addr = base_addr + index * 4
            return self.memory.read_int(target_addr)
        elif data_type == 'char':
            # char 佔 1 個 byte
            target_addr = base_addr + index * 1
            return self.memory.read_char(target_addr)

    # ─── 宣告（Declarations） ─────────────────────────────────────────────────────

    def visit_VarDeclNode(self, node):
        """處理變數宣告，例如: int x = 1 + 2 * 3; 或 int arr[10];"""
        self._trace(node)
        # Small-C 不允許在 if/while/for 區塊內宣告變數
        if self.in_block_scope:
            raise RuntimeError(f"Semantic Error: Small-C 不支援在控制流區塊內宣告變數 '{node.name}'，請將宣告移至函式開頭")

        data_type = self._type_name(node.type_node) # 拿出他的型別

        # 如果是陣列，要先算出陣列長度
        is_array = (node.array_size is not None)
        array_len = 0
        if is_array:
            array_len = self.visit(node.array_size) # 把中括號裡的表達式算出來 (例如 10)
            if not isinstance(array_len, int) or array_len <= 0: # 檢查陣列長度是否合法
                raise RuntimeError(
                    f"Semantic Error: array '{node.name}' size must be a positive integer (got {array_len})"
                )

        # 去符號表註冊此變數 (把算出來的長度傳進去)
        symbol = self.symtable.define_var(
            name=node.name, 
            data_type=data_type, 
            is_array=is_array, 
            array_len=array_len
        )

        # 如果宣告時有給初始值 (init_expr)
        if node.init_expr is not None:
            value = self.visit(node.init_expr) # 這邊會拿到等號右邊的值

            if data_type == 'int': #根據變數宣告的型別來寫入值
                self.memory.write_int(symbol.address, value)
            elif data_type == 'char':
                self.memory.write_char(symbol.address, value)
        return None

    def visit_FuncDefNode(self, node):
        """當直譯器看到函式定義時，不需要立刻執行，只要把它記錄到符號表裡就好"""

        self.symtable.define_func(
            name=node.name,
            data_type=node.return_type.base_type,
            func_node=node
        )

        return None

    # ─── 運算式（Expressions） ────────────────────────────────────────────────────

    def visit_TernaryNode(self, node):
        """三元運算 cond ? a : b，依條件結果只計算其中一邊"""
        if self.visit(node.condition):
            return self.visit(node.then_expr)
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
        left = self.visit(node.left)

        if node.op == '&&':
            if left == 0:
                return 0
            else:
                if self.visit(node.right) != 0:
                    return 1
                else: return 0
        elif node.op == '||':
            if left != 0:
                return 1
            else:
                if self.visit(node.right) != 0:
                    return 1
                else: 
                    return 0
        
        right = self.visit(node.right)
        
        # 根據運算子種類，執行真正的 Python 運算
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

        # 其他運算子都需要先算出 operand 的值
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
            addr = value  # operand 算出來就是記憶體位址
            # 判斷要讀 int 還是 char
            if addr == None: #指標沒指向任何東西 取值會報錯
                raise RuntimeError("Runtime Error: null pointer dereference.") 
            if isinstance(node.operand, VarNode):
                symbol = self.symtable.lookup(node.operand.name)
                if symbol.data_type == 'char*':
                    return self.memory.read_char(addr)
            return self.memory.read_int(addr)  # 預設讀 int
        elif node.op == '++':
            if isinstance(node.operand, VarNode):
                symbol = self.symtable.lookup(node.operand.name)
                addr = symbol.address
                new_value = value + 1
                if symbol.data_type == 'int':
                    self.memory.write_int(addr, new_value)
                    if node.prefix:
                        return new_value
                    else:
                        return value
                elif symbol.data_type == 'char':
                    self.memory.write_char(addr, new_value)
                    if node.prefix:
                        return new_value
                    else:
                        return value
            #elif isinstance(node.operand, ArrayIndexNode):  # arr[0]++;


        elif node.op == '--':
            if isinstance(node.operand, VarNode):
                symbol = self.symtable.lookup(node.operand.name)
                addr = symbol.address
                new_value = value - 1
                if symbol.data_type == 'int':
                    self.memory.write_int(addr, new_value)
                    if node.prefix:
                        return new_value
                    else:
                        return value
                elif symbol.data_type == 'char':
                    self.memory.write_char(addr, new_value)
                    if node.prefix:
                        return new_value
                    else:
                        return value
        else:
            raise RuntimeError(f"Runtime Error: Unknown unary operator '{node.op}'")

    def visit_AssignNode(self, node):
        """處理變數重新賦值，例如 a = 10; 或 arr[i] += 5;"""

        right_val = self.visit(node.value) # 把等號右邊的值從node裡面讀出來

        if isinstance(node.target, VarNode): # 看左邊這個變數是不是VarNode
            symbol = self.symtable.lookup(node.target.name)
            addr = symbol.address
            data_type = symbol.data_type
        elif isinstance(node.target, ArrayIndexNode): # 看左邊這個變數是不是ArrayIndexNode
            base_addr = self.visit(node.target.array) # 例如拿到 arr 的開頭位址
            index = self.visit(node.target.index)     # 拿到中括號裡的數字
            
            # 從符號表找出這是 int 還是 char 陣列
            symbol = self.symtable.lookup(node.target.array.name)
            data_type = self._array_element_type(symbol)

            # 邊界檢查
            if symbol.is_array and (index < 0 or index >= symbol.array_len):
                raise RuntimeError(f"Runtime Error: array index out of bounds (index {index}, size {symbol.array_len})")
            
            # 算出真正的記憶體位址
            if data_type == 'int':
                addr = base_addr + index * 4
            elif data_type == 'char':
                addr = base_addr + index * 1
        elif isinstance(node.target, UnaryOpNode) and node.target.op == '*':  # *ptr = 99;
            addr = self.visit(node.target.operand)  # 算出 ptr 裡面存的位址
            # 判斷要寫 int 還是 char
            data_type = 'int'
            if isinstance(node.target.operand, VarNode):
                symbol = self.symtable.lookup(node.target.operand.name)
                data_type = symbol.data_type[:-1] if symbol.data_type.endswith('*') else symbol.data_type
        
        else:
            raise NotImplementedError("目前只支援對普通變數、陣列與指標賦值")
        
        if node.op != '=': # 處理 +=, -=, *=, /=
            if data_type == 'int':
                old_val = self.memory.read_int(addr)
            elif data_type == 'char':
                old_val = self.memory.read_char(addr)

            if node.op == '+=': right_val = old_val + right_val
            elif node.op == '-=': right_val = old_val - right_val
            elif node.op == '*=': right_val = old_val * right_val
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

        if data_type == 'int':
            self.memory.write_int(addr, right_val)
        elif data_type =='char':
            self.memory.write_char(addr, right_val)
        elif data_type in ('int*', 'char*'):  # 指標本質上就是 4-byte 整數（存位址）
            self.memory.write_int(addr, right_val)

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
        if self.visit(node.condition) != 0:
            self._visit_control_body(node.then_block)
        elif node.else_block is not None:
            self._visit_control_body(node.else_block)
        return None
    
    def visit_ReturnNode(self, node):
        """處理 return 語句"""
        self._trace(node)
        value = 0
        if node.value is not None:
            value = self.visit(node.value) # 算出 return 後面的數字
            
        # 像丟球一樣，把答案丟出去，瞬間中斷後面的所有程式碼！
        raise ReturnException(value)

    def visit_WhileNode(self, node):
        while True:
            self._trace(node)
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
            if self.visit(node.condition) == 0:
                break

    def visit_ForNode(self, node):
        if node.init is not None:
            self._trace(node) # 追蹤初始化部分
            self.visit(node.init)
        while True:
            self._trace(node) # 追蹤條件判定
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
