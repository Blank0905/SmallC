import sys
import os
from lexer import Lexer, Token
from sc_parser import Parser
from interpreter import Interpreter
from memory import Memory
from symtable import SymbolTable
from sc_builtins import BuiltinManager
from ast_node import FuncDefNode
from preprocessor import Preprocessor


class REPL:
    def __init__(self):
        # 這是我們的「程式碼緩衝區」，每一行程式碼會存成 List 裡的一個字串
        self.code_buffer = []
        # 紀錄緩衝區是否被修改過（用來在 QUIT 時警告使用者）
        self.is_dirty = False

        self.last_sym = None       # 上次執行的符號表
        self.last_mem = None       # 上次執行的記憶體
        self.last_builtins = None  # 上次執行的內建函式管理器

    def _type_name(self, type_node):
        return type_node.base_type + ("*" * type_node.pointer_depth)

    def _char_repr(self, value):
        try:
            return repr(chr(value if value >= 0 else value + 256))
        except Exception:
            return "?"

    def _parse_buffer(self):
        source_code = '\n'.join(self.code_buffer)
        source_code = Preprocessor().process(source_code)
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        parser_obj = Parser(tokens)
        return parser_obj.parse()

    def _format_live_symbol(self, symbol):
        if symbol.is_array:
            elements = []
            step = 4 if symbol.data_type == 'int' else 1
            for i in range(min(symbol.array_len, 10)):
                addr = symbol.address + i * step
                if symbol.data_type == 'int':
                    elements.append(str(self.last_mem.read_int(addr)))
                else:
                    elements.append(str(self.last_mem.read_char(addr)))
            preview = ", ".join(elements)
            if symbol.array_len > 10:
                preview += ", ..."
            return f"  {symbol.data_type} {symbol.name}[{symbol.array_len}] = [{preview}]"

        if symbol.data_type.endswith('*'):
            ptr_val = self.last_mem.read_int(symbol.address)
            base_type = symbol.data_type[:-1]
            try:
                pointed_val = self.last_mem.read_char(ptr_val) if base_type == 'char' else self.last_mem.read_int(ptr_val)
                return f"  {symbol.data_type} {symbol.name} = address: {ptr_val} (points to value: {pointed_val})"
            except Exception:
                return f"  {symbol.data_type} {symbol.name} = address: {ptr_val} (invalid address)"

        if symbol.data_type == 'int':
            return f"  int {symbol.name} = {self.last_mem.read_int(symbol.address)}"
        if symbol.data_type == 'char':
            val = self.last_mem.read_char(symbol.address)
            return f"  char {symbol.name} = {val} ({self._char_repr(val)})"
        return f"  {symbol.data_type} {symbol.name} = ?"

    def start(self):
        """啟動互動式介面"""
        banner = r"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                  ║
║   ██████╗ ███╗   ███╗  █████╗  ██╗      ██╗         ██████╗                      ║
║  ██╔════╝ ████╗ ████║ ██╔══██╗ ██║      ██║        ██╔════╝                      ║
║  ███████╗ ██╔████╔██║ ███████║ ██║      ██║        ██║                           ║
║  ╚════██║ ██║╚██╔╝██║ ██╔══██║ ██║      ██║        ██║                           ║
║  ███████║ ██║ ╚═╝ ██║ ██║  ██║ ███████╗ ███████╗   ╚██████╗                      ║
║  ╚══════╝ ╚═╝     ╚═╝ ╚═╝  ╚═╝ ╚══════╝ ╚══════╝    ╚═════╝                      ║
║                                                                                  ║
║ >> Small-C Interactive Interpreter v1.0                                          ║
║ >> System Software Final Project, Spring 2026                                    ║
╚══════════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        print("Type 'HELP' for a list of commands.")

        # 無窮迴圈，不斷接收使用者輸入
        while True:
            try:
                # 顯示提示符 sc>
                line = input("sc> ")
            except EOFError: # 處理 Ctrl+D
                break
            except KeyboardInterrupt: # 處理 Ctrl+C
                print("\nType 'QUIT' to exit.")
                continue

            # 去除頭尾多餘空白
            line = line.strip()
            if not line:
                continue

            # 切割字串，分離「指令」與「後面的參數」
            parts = line.split(maxsplit=1)
            command = parts[0].upper() # 指令統一轉大寫比較
            args = parts[1] if len(parts) > 1 else ""

            # === 指令分發區 ===
            if command in ('QUIT', 'EXIT'):
                if self.cmd_quit():
                    break
            elif command == 'HELP':
                self.cmd_help(args)
            elif command == 'LIST':
                self.cmd_list(args)
            elif command == 'LOAD':
                self.cmd_load(args)
            elif command == 'SAVE':
                self.cmd_save(args)
            elif command == 'DELETE':
                self.cmd_delete(args)
            elif command == 'INSERT':
                self.cmd_insert(args)
            elif command == 'APPEND':
                self.cmd_append()
            elif command == 'VARS':
                self.cmd_vars()
            elif command == 'FUNCS':
                self.cmd_funcs()
            elif command == 'NEW':
                self.cmd_new()
            elif command == 'RUN':
                self.cmd_run()
            elif command == 'CHECK':
                self.cmd_check()
            elif command == 'CLEAR':
                self.cmd_clear()
            elif command == 'ABOUT':
                self.cmd_about()
            elif command == 'EDIT':
                self.cmd_edit(args)
            # 判斷是否為其他預留指令 (防止被當成 C 程式碼)
            elif command in ('TRACE', 'VARS', 'FUNCS'):
                print(f"指令 {command} 尚未實作！")
            else:
                # 作業規定：如果不是任何已知指令，就視為 Small-C 程式碼，直接加入緩衝區！
                self.code_buffer.append(line)
                self.is_dirty = True # 標記為已修改  

    # ─── 程式管理指令 ─────────────────────────────────────────────────────
    def cmd_load(self, args):
        """從檔案載入程式碼到緩衝區"""
        if not args:
            print("Error: Missing filename. Usage: LOAD <filename>")
            return
        try:
            with open(args, 'r', encoding='utf-8') as f:
                # 讀取所有行並去除換行符號
                self.code_buffer = [line.rstrip('\n') for line in f.readlines()]
            self.is_dirty = False
            print(f"Loaded {len(self.code_buffer)} lines from {args}")
        except Exception as e:
            print(f"Error loading file: {e}")

    def cmd_save(self, args):
        """從緩衝區存代碼成檔案"""
        if not args:
            print("Error: Missing filename. Usage: SAVE <filename>")
            return
        try:
            with open(args, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.code_buffer) + '\n')
            self.is_dirty = False
            print(f"Saved {len(self.code_buffer)} lines to {args}")
        except Exception as e:
            print(f"Error saving file: {e}")

    def cmd_list(self, args):
        """列出緩衝區的程式碼 (先實作最基本的全部列出)"""
        if not self.code_buffer:
            print("Buffer is empty.")
            return

        if args and '-' in args:          # LIST 3-7
            parts = args.split('-')
            start, end = int(parts[0]), int(parts[1])
        elif args and args.isdigit():
            start = end = int(args)
        else:
            start = 1
            end = len(self.code_buffer)

        for i in range(start - 1, min(end, len(self.code_buffer))):
            print(f"{i + 1:3d} | {self.code_buffer[i]}")

    def cmd_edit(self, args):
        """EDIT <n>：將第 n 行顯示給使用者，輸入新內容取代該行，直接 Enter 則保留原行"""
        if not args or not args.isdigit():
            print("Error: Usage: EDIT <line_number>")
            return
        n = int(args)
        if n < 1 or n > len(self.code_buffer):
            print(f"Error: Line {n} out of range (1-{len(self.code_buffer)})")
            return
        
        print(f"{n:3d} | {self.code_buffer[n - 1]}")
        new_content = input(f"{n:3d} > ")
        if new_content:  # 有輸入東西才取代
            self.code_buffer[n - 1] = new_content
            self.is_dirty = True
            print(f"Line {n} updated.")
        else:
            print(f"Line {n} unchanged.")

    def cmd_delete(self, args):
        """DELETE <n> / DELETE <n1>-<n2>：刪除特定行或範圍"""
        if not self.code_buffer:
            print("Buffer is empty.")
            return

        if args and '-' in args:
            parts = args.split('-')
            start, end = int(parts[0]), int(parts[1])
        elif args and args.isdigit():
            start = end = int(args)
        else:
            print("Error: Usage: DELETE <n> or DELETE <n1>-<n2>")
            return

        if start < 1 or end > len(self.code_buffer) or start > end:
            print(f"Error: Invalid range (1-{len(self.code_buffer)})")
            return

        del self.code_buffer[start - 1 : end]  # slice 一次刪掉整段
        self.is_dirty = True
        print(f"Deleted {end - start + 1} line(s).")

    def cmd_insert(self, args):
        """INSERT <n>：在第 n 行之前插入程式碼，輸入 . 結束"""
        if not args or not args.isdigit():
            print("Error: Usage: INSERT <line_number>")
            return
        n = int(args)
        if n < 1 or n > len(self.code_buffer) + 1:
            print(f"Error: Line {n} out of range (1-{len(self.code_buffer) + 1})")
            return
        print("Enter code lines (type '.' on a line by itself to finish):")
        insert_pos = n - 1
        count = 0
        while True:
            line = input(f"{insert_pos + count + 1:3d} > ")
            if line == '.':
                break
            self.code_buffer.insert(insert_pos + count, line)
            count += 1
        if count > 0:
            self.is_dirty = True
            print(f"Inserted {count} line(s) at line {n}.")

    def cmd_append(self):
        """APPEND：在緩衝區末尾進入多行輸入模式，輸入 . 結束"""
        print("Enter code lines (type '.' on a line by itself to finish):")
        count = 0
        while True:
            line = input(f"{len(self.code_buffer) + 1:3d} > ")
            if line == '.':
                break
            self.code_buffer.append(line)
            count += 1
        if count > 0:
            self.is_dirty = True
            print(f"Appended {count} line(s).")

    def cmd_new(self):
        """清空緩衝區並重置所有執行狀態"""
        if self.is_dirty:
            ans = input("Buffer has unsaved changes. Really clear? (y/N): ")
            if ans.lower() != 'y':
                return
        # 清空緩衝區並重置所有執行狀態
        self.code_buffer.clear()
        self.is_dirty = False
        self.last_sym = None
        self.last_mem = None
        self.last_builtins = None
        print("Buffer cleared and execution state reset.")

    # ───執行與除錯指令 ─────────────────────────────────────────────────────

    def cmd_run(self):
        try:
            nodes = self._parse_buffer()
        except SyntaxError as e:
            print(f"[!] 語法錯誤: {e}")
            return
        except Exception as e:
            print(f"[!] 解析錯誤: {e}")
            return

        mem = Memory() # 建立新的記憶體環境
        sym = SymbolTable(mem)
        builtins_mgr = BuiltinManager(mem)

        interpreter = Interpreter(symtable=sym, memory=mem, builtins=builtins_mgr)
        self.last_sym = sym
        self.last_mem = mem
        self.last_builtins = builtins_mgr
        try:
            interpreter.visit(nodes)
        except Exception as e:
            print(f"[*] 執行 main 時發生未預期錯誤: {e}")

    def cmd_check(self):
        """CHECK：只做語法檢查，不執行程式"""
        if not self.code_buffer:
            print("Buffer is empty.")
            return
        try:
            self._parse_buffer()
            print("No syntax errors found.")
        except SyntaxError as e:
            print(f"{e}")
        except Exception as e:
            print(f"{e}")

    def cmd_vars(self):
        """VARS：顯示所有全域變數的名稱、型別與當前值"""
        if self.last_sym is None:
            print("No execution data. Run your program first.")
            return

        global_vars = [
            symbol for symbol in self.last_sym.globals.values()
            if symbol.sym_type == 'VAR'
        ]
        if not global_vars:
            print("No global variables.")
            return

        for symbol in global_vars:
            print(self._format_live_symbol(symbol))

    def cmd_funcs(self):
        """FUNCS：列出內建函式與目前緩衝區中的使用者函式"""
        builtins_mgr = self.last_builtins or BuiltinManager(self.last_mem or Memory())
        for name in builtins_mgr.functions.keys():
            print(f"  {name}()  [built-in]")

        if not self.code_buffer:
            return

        try:
            nodes = self._parse_buffer()
        except SyntaxError as e:
            print(f"[!] 語法錯誤，無法列出使用者函式: {e}")
            return
        except Exception as e:
            print(f"[!] 解析錯誤，無法列出使用者函式: {e}")
            return

        user_funcs = [
            node for node in nodes.declarations
            if isinstance(node, FuncDefNode)
        ]

        if not user_funcs:
            print("  (no user-defined functions)")
            return

        for func_node in user_funcs:
            params = ", ".join(
                f"{self._type_name(p.type_node)} {p.name}" for p in func_node.params
            )
            ret_type = self._type_name(func_node.return_type)
            line_no = func_node.line if func_node.line is not None else "?"
            print(f"  {ret_type} {func_node.name}({params})  [line {line_no}]")

    # ─── 系統指令 ─────────────────────────────────────────────────────
    def cmd_help(self, args):
        help_info = {
            'LOAD':   "LOAD <filename>：從檔案載入 Small-C 原始碼",
            'SAVE':   "SAVE <filename>：儲存目前程式緩衝區至檔案",
            'LIST':   "LIST / LIST <n> / LIST <n1>-<n2>：列出程式碼（全部／單行／範圍）",
            'EDIT':   "EDIT <n>：編輯特定行的程式碼",
            'DELETE': "DELETE <n> / DELETE <n1>-<n2>：刪除特定行或範圍",
            'INSERT': "INSERT <n>：在特定行之前插入程式碼",
            'APPEND': "APPEND：在緩衝區末尾進入多行輸入模式（輸入 . 結束）",
            'NEW':    "NEW：清除緩衝區並重置執行狀態",
            'RUN':    "RUN：執行目前緩衝區的程式",
            'CHECK':  "CHECK：進行語法與語意檢查但不執行",
            'TRACE':  "TRACE ON / TRACE OFF：開啟／關閉執行追蹤模式",
            'VARS':   "VARS：顯示目前所有全域變數名稱、型別與值",
            'FUNCS':  "FUNCS：顯示目前已定義的所有函式清單",
            'HELP':   "HELP / HELP <command>：顯示輔助說明",
            'ABOUT':  "ABOUT：顯示解譯器資訊",
            'CLEAR':  "CLEAR：清除終端機畫面",
            'QUIT':   "QUIT / EXIT：結束解譯器",
        }
        if args and args.upper() in help_info:
            print(help_info[args.upper()])
        else:
            print("═" * 50)
            print("  Small-C REPL 指令說明")
            print("═" * 50)
            for cmd, desc in help_info.items():
                print(f"  {desc}")
            print("═" * 50)

    def cmd_about(self):
        print(">> Small-C Interactive Interpreter v1.0")
        print(">> System Software Final Project, Spring 2026")
        print("作者1, 2, 3")

    def cmd_clear(self):
        """清除終端機畫面"""
        import os
        os.system('cls')  # Windows 用 cls
    
    def cmd_quit(self):
        """離開 REPL，如果有未儲存的修改需警告"""
        if self.is_dirty:
            ans = input("Buffer has unsaved changes. Really quit? (y/N): ")
            if ans.lower() != 'y':
                return False # 取消離開
        return True # 確認離開
