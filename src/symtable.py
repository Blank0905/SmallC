class Symbol:
    """
    紀錄單一變數或函式的資訊
    """
    def __init__(self, name, sym_type, data_type, address=None, is_global=False, is_array=False, array_len=0, func_node=None):
        self.name = name               # 變數或函式名稱
        self.sym_type = sym_type       # 'VAR' 或 'FUNC'
        self.data_type = data_type     # 'int', 'char', 'int*', 'char*', 'void'
        
        # 變數專用
        self.address = address         # 在 Memory 中的位址
        self.is_global = is_global     # 是否為全域變數
        self.is_array = is_array       # 是否為陣列
        self.array_len = array_len     # 陣列長度 (若是陣列)
        
        # 函式專用
        self.func_node = func_node     # 指向 AST 的 FuncDefNode，方便呼叫時執行


class SymbolTable:
    """
    符號表與作用域管理器
    依照 Small-C 規定：
    - 只有「全域」與「函式區域」兩層作用域。
    - 不支援 `if` 或 `while` 內部的區塊變數宣告。
    """
    
    def __init__(self, memory):
        self.memory = memory
        self.globals = {}   # 全域符號表 (name -> Symbol)
        self.locals = {}    # 區域符號表 (name -> Symbol)
        self.is_global_scope = True  # 目前是否在全域

    def reset(self):
        """重置符號表（用於 REPL 的 NEW 指令）"""
        self.globals.clear()
        self.locals.clear()
        self.is_global_scope = True

    def enter_function(self):
        """進入函式，開啟新的區域作用域"""
        self.locals.clear()
        self.is_global_scope = False

    def leave_function(self):
        """離開函式，清空區域作用域並回到全域"""
        self.locals.clear()
        self.is_global_scope = True

    def _get_type_size(self, data_type):
        """取得資料型別的大小 (bytes)"""
        if data_type in ('int', 'int*', 'char*'):
            return 4
        elif data_type == 'char':
            return 1
        elif data_type == 'void':
            return 0
        else:
            raise TypeError(f"Unknown data type: {data_type}")

    def define_var(self, name, data_type, is_array=False, array_len=0):
        """宣告變數，自動分配記憶體並記錄在符號表中"""
        scope_dict = self.globals if self.is_global_scope else self.locals
        
        if name in scope_dict:
            raise Exception(f"Semantic Error: Redefinition of variable '{name}'")

        # 計算所需記憶體空間
        element_size = self._get_type_size(data_type)
        total_size = element_size * array_len if is_array else element_size

        # 呼叫 Memory 分配空間
        if self.is_global_scope:
            addr = self.memory.alloc_global(total_size)
        else:
            addr = self.memory.alloc_local(total_size)

        symbol = Symbol(
            name=name, 
            sym_type='VAR', 
            data_type=data_type, 
            address=addr, 
            is_global=self.is_global_scope,
            is_array=is_array,
            array_len=array_len
        )
        scope_dict[name] = symbol
        return symbol

    def define_func(self, name, data_type, func_node):
        """宣告函式（只存在於全域）"""
        if name in self.globals:
            raise Exception(f"Semantic Error: Redefinition of function '{name}'")
            
        symbol = Symbol(
            name=name,
            sym_type='FUNC',
            data_type=data_type,
            is_global=True,
            func_node=func_node
        )
        self.globals[name] = symbol
        return symbol

    def lookup(self, name):
        """尋找變數或函式（先找區域，再找全域）"""
        if not self.is_global_scope and name in self.locals:
            return self.locals[name]
        if name in self.globals:
            return self.globals[name]
        raise Exception(f"Semantic Error: Undefined symbol '{name}'")
