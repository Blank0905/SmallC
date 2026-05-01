import sys
import os
from lexer import Lexer, Token
from sc_parser import Parser
from interpreter import Interpreter
from memory import Memory
from symtable import SymbolTable
from sc_builtins import BuiltinManager


class REPL:
    def __init__(self):
        # 這是我們的「程式碼緩衝區」，每一行程式碼會存成 List 裡的一個字串
        self.code_buffer = []
        # 紀錄緩衝區是否被修改過（用來在 QUIT 時警告使用者）
        self.is_dirty = False

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
            elif command == 'NEW':
                self.cmd_new()
            elif command == 'RUN':
                self.cmd_run()
            elif command == 'CLEAR':
                self.cmd_clear()
            elif command == 'ABOUT':
                self.cmd_about()
            # 判斷是否為其他預留指令 (防止被當成 C 程式碼)
            elif command in ('SAVE', 'EDIT', 'DELETE', 'INSERT', 'APPEND', 'CHECK', 'TRACE', 'VARS', 'FUNCS'):
                print(f"指令 {command} 尚未實作！")
            else:
                # 作業規定：如果不是任何已知指令，就視為 Small-C 程式碼，直接加入緩衝區！
                self.code_buffer.append(line)
                self.is_dirty = True # 標記為已修改

    # ==========================================
    # 指令實作區
    # ==========================================
    
    def cmd_help(self, args):
        print("可用指令：LOAD, SAVE, LIST, EDIT, DELETE, INSERT, APPEND, NEW, RUN, CHECK, TRACE, VARS, FUNCS, HELP, ABOUT, CLEAR, QUIT")

    def cmd_new(self):
        """清空緩衝區"""
        self.code_buffer.clear()
        self.is_dirty = False
        print("Buffer cleared.")

    def cmd_list(self, args):
        """列出緩衝區的程式碼 (先實作最基本的全部列出)"""
        if not self.code_buffer:
            print("Buffer is empty.")
            return
        
        # 顯示每一行，並標上行號 (1-indexed)
        for i, code_line in enumerate(self.code_buffer):
            print(f"{i + 1:3d} | {code_line}")

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

    def cmd_quit(self):
        """離開 REPL，如果有未儲存的修改需警告"""
        if self.is_dirty:
            ans = input("Buffer has unsaved changes. Really quit? (y/N): ")
            if ans.lower() != 'y':
                return False # 取消離開
        return True # 確認離開

    def cmd_run(self):
        source_code = '\n'.join(self.code_buffer) # 把 buffer 裡的每一項，用換行符號連接成一個大字串
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        parser_obj = Parser(tokens)
        nodes = parser_obj.parse()

        mem = Memory() # 建立新的記憶體環境
        sym = SymbolTable(mem)
        builtins_mgr = BuiltinManager(mem)


        interpreter = Interpreter(symtable=sym, memory=mem, builtins=builtins_mgr)
        try:
            interpreter.visit(nodes)
        except Exception as e:
            print(f"執行期錯誤: {e}")

    def cmd_clear(self):
        self.code_buffer = []
        return

    def cmd_about(self):
        print(">> Small-C Interactive Interpreter v1.0")
        print(">> System Software Final Project, Spring 2026")
        print("作者1, 2, 3")


# # 為了方便測試，可以直接執行此檔案
# if __name__ == "__main__":
#     repl = REPL()
#     repl.start()
