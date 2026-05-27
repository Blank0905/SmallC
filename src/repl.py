import os

from ast_node import FuncDefNode
from interpreter import BreakException, ContinueException, Interpreter, ReturnException
from lexer import Lexer
from memory import Memory
from preprocessor import Preprocessor
from sc_builtins import BuiltinManager
from sc_parser import Parser
from symtable import SymbolTable


class LiveREPL:
    def __init__(self):
        self.trace = False
        self.pending_lines = [] # 多行輸入暫存區(例如還沒收完一整個 function)
        self.code_buffer = []   # 程式碼緩衝區
        self.is_dirty = False   # 是否有未存檔修改
        self._reset_runtime()   # 建立持續性 runtime

    def _reset_runtime(self):
        self.mem = Memory()
        self.sym = SymbolTable(self.mem)
        self.builtins_mgr = BuiltinManager(self.mem)
        self.interpreter = Interpreter(
            symtable=self.sym,
            memory=self.mem,
            builtins=self.builtins_mgr,
            program_buffer=list(self.code_buffer),
            trace=self.trace,
        )

    def _type_name(self, type_node):
        return type_node.base_type + ("*" * type_node.pointer_depth)

    def _char_repr(self, value):
        try:
            return repr(chr(value if value >= 0 else value + 256))
        except Exception:
            return "?"

    def _format_live_symbol(self, symbol):
        if symbol.is_array:
            elements = []
            step = 4 if symbol.data_type == "int" else 1
            for i in range(min(symbol.array_len, 10)):
                addr = symbol.address + i * step
                if symbol.data_type == "int":
                    elements.append(str(self.mem.read_int(addr)))
                else:
                    elements.append(str(self.mem.read_char(addr)))
            preview = ", ".join(elements)
            if symbol.array_len > 10:
                preview += ", ..."
            return f"  {symbol.data_type} {symbol.name}[{symbol.array_len}] = [{preview}]"

        if symbol.data_type.endswith("*"):
            ptr_val = self.mem.read_int(symbol.address)
            base_type = symbol.data_type[:-1]
            try:
                pointed_val = self.mem.read_char(ptr_val) if base_type == "char" else self.mem.read_int(ptr_val)
                return f"  {symbol.data_type} {symbol.name} = address: {ptr_val} (points to value: {pointed_val})"
            except Exception:
                return f"  {symbol.data_type} {symbol.name} = address: {ptr_val} (invalid address)"

        if symbol.data_type == "int":
            return f"  int {symbol.name} = {self.mem.read_int(symbol.address)}"
        if symbol.data_type == "char":
            val = self.mem.read_char(symbol.address)
            return f"  char {symbol.name} = {val} ({self._char_repr(val)})"
        return f"  {symbol.data_type} {symbol.name} = ?"

    def _is_type_token(self, token):
        return token.type in ("INT_TYPE", "CHAR_TYPE", "VOID_TYPE")

    def _looks_like_top_level_decl(self, tokens):
        if len(tokens) < 3:
            return False
        if not self._is_type_token(tokens[0]):
            return False
        if tokens[1].type != "ID":
            return False
        return True

    def _has_unclosed_delimiters(self, source):
        paren = 0
        brace = 0
        bracket = 0
        in_string = False
        in_char = False
        escape = False
        in_line_comment = False
        in_block_comment = False

        i = 0
        while i < len(source):
            ch = source[i]
            nxt = source[i + 1] if i + 1 < len(source) else ""

            if in_line_comment:
                if ch == "\n":
                    in_line_comment = False
                i += 1
                continue

            if in_block_comment:
                if ch == "*" and nxt == "/":
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue

            if in_string or in_char:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif in_string and ch == '"':
                    in_string = False
                elif in_char and ch == "'":
                    in_char = False
                i += 1
                continue

            if ch == "/" and nxt == "/":
                in_line_comment = True
                i += 2
                continue
            if ch == "/" and nxt == "*":
                in_block_comment = True
                i += 2
                continue

            if ch == '"':
                in_string = True
            elif ch == "'":
                in_char = True
            elif ch == "(":
                paren += 1
            elif ch == ")":
                paren -= 1
            elif ch == "{":
                brace += 1
            elif ch == "}":
                brace -= 1
            elif ch == "[":
                bracket += 1
            elif ch == "]":
                bracket -= 1
            i += 1

        return in_string or in_char or in_block_comment or paren > 0 or brace > 0 or bracket > 0

    def _is_incomplete_error(self, exc, source):
        msg = str(exc)
        lowered = msg.lower()
        if "unclosed block" in lowered:
            return True
        if "got eof" in lowered:
            return True
        if "string not closed" in lowered:
            return True
        if "unterminated string literal" in lowered:
            return True
        if "unclosed block comment" in lowered:
            return True
        if "unexpected eof after backslash in string" in lowered:
            return True
        return self._has_unclosed_delimiters(source)

    def _parse_pending(self):
        source_code = "\n".join(self.pending_lines)
        processed = Preprocessor().process(source_code)
        tokens = Lexer(processed).tokenize()
        parser_obj = Parser(tokens)

        if self._looks_like_top_level_decl(tokens):
            node = parser_obj.parse_top_level()
        else:
            node = parser_obj.parse_statement()

        if parser_obj.current_token.type != "EOF":
            raise SyntaxError(
                f"Parser Error: Unexpected trailing token {parser_obj.current_token.type}"
                f"('{parser_obj.current_token.value}') at line {parser_obj.current_token.line}"
            )

        return node

    def _parse_full_buffer(self):
        source_code = "\n".join(self.code_buffer)
        processed = Preprocessor().process(source_code)
        tokens = Lexer(processed).tokenize()
        return Parser(tokens).parse()

    def _execute_pending(self):
        source_code = "\n".join(self.pending_lines)
        try:
            node = self._parse_pending()
        except Exception as exc:
            if self._is_incomplete_error(exc, source_code):
                return False
            print(f"[!] 語法錯誤: {exc}")
            self.pending_lines.clear()
            return True

        self.interpreter.program_buffer = list(self.code_buffer) + list(self.pending_lines)
        self.interpreter.trace = self.trace

        executed_ok = False
        try:
            self.interpreter.visit(node)
            executed_ok = True
        except (BreakException, ContinueException, ReturnException):
            print("[!] Semantic Error: break/continue/return cannot appear at top level.")
        except Exception as exc:
            print(f"[!] 執行錯誤: {exc}")
        finally:
            if executed_ok:
                self.code_buffer.extend(self.pending_lines)
                self.is_dirty = True
            self.pending_lines.clear()
        return True

    # ─── 程式管理指令 ─────────────────────────────────────────────────────
    def _cmd_load(self, args):
        if not args:
            print("Error: Missing filename. Usage: LOAD <filename>")
            return
        if self.is_dirty:
            ans = input("Buffer has unsaved changes. Really load? (y/N): ")
            if ans.lower() != "y":
                return
        try:
            with open(args, "r", encoding="utf-8") as f:
                self.code_buffer = [line.rstrip("\n") for line in f.readlines()]
            self.is_dirty = False
            print(f"Loaded {len(self.code_buffer)} lines from {args}")
        except Exception as exc:
            print(f"Error loading file: {exc}")

    def _cmd_save(self, args):
        if not args:
            print("Error: Missing filename. Usage: SAVE <filename>")
            return
        try:
            with open(args, "w", encoding="utf-8") as f:
                f.write("\n".join(self.code_buffer) + "\n")
            self.is_dirty = False
            print(f"Saved {len(self.code_buffer)} lines to {args}")
        except Exception as exc:
            print(f"Error saving file: {exc}")

    def _cmd_list(self, args):
        if not self.code_buffer:
            print("Buffer is empty.")
            return

        try:
            if args and "-" in args:
                start_s, end_s = args.split("-", 1)
                start = int(start_s.strip())
                end = int(end_s.strip())
            elif args:
                start = end = int(args.strip())
            else:
                start = 1
                end = len(self.code_buffer)
        except ValueError:
            print("Error: Usage LIST / LIST <n> / LIST <n1>-<n2>")
            return

        if start < 1 or end < start:
            print("Error: Invalid range")
            return

        max_line = len(self.code_buffer)
        for i in range(start - 1, min(end, max_line)):
            print(f"{i + 1:3d} | {self.code_buffer[i]}")

    def _cmd_edit(self, args):
        if not args or not args.isdigit():
            print("Error: Usage: EDIT <line_number>")
            return
        n = int(args)
        if n < 1 or n > len(self.code_buffer):
            print(f"Error: Line {n} out of range (1-{len(self.code_buffer)})")
            return

        print(f"{n:3d} | {self.code_buffer[n - 1]}")
        new_content = input(f"{n:3d} > ")
        if new_content:
            self.code_buffer[n - 1] = new_content
            self.is_dirty = True
            print(f"Line {n} updated.")
        else:
            print(f"Line {n} unchanged.")

    def _cmd_delete(self, args):
        if not self.code_buffer:
            print("Buffer is empty.")
            return

        if args and "-" in args:
            try:
                start_s, end_s = args.split("-", 1)
                start = int(start_s.strip())
                end = int(end_s.strip())
            except ValueError:
                print("Error: Usage: DELETE <n> or DELETE <n1>-<n2>")
                return
        elif args and args.isdigit():
            start = end = int(args)
        else:
            print("Error: Usage: DELETE <n> or DELETE <n1>-<n2>")
            return

        if start < 1 or end > len(self.code_buffer) or start > end:
            print(f"Error: Invalid range (1-{len(self.code_buffer)})")
            return

        del self.code_buffer[start - 1: end]
        self.is_dirty = True
        print(f"Deleted {end - start + 1} line(s).")

    def _cmd_insert(self, args):
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
            try:
                line = input(f"{insert_pos + count + 1:3d} > ")
            except EOFError:
                break
            if line == ".":
                break
            self.code_buffer.insert(insert_pos + count, line)
            count += 1
        if count > 0:
            self.is_dirty = True
            print(f"Inserted {count} line(s) at line {n}.")

    def _cmd_append(self):
        print("Enter code lines (type '.' on a line by itself to finish):")
        count = 0
        while True:
            try:
                line = input(f"{len(self.code_buffer) + 1:3d} > ")
            except EOFError:
                break
            if line == ".":
                break
            self.code_buffer.append(line)
            count += 1
        if count > 0:
            self.is_dirty = True
            print(f"Appended {count} line(s).")

    def _cmd_new(self):
        if self.is_dirty:
            ans = input("Buffer has unsaved changes. Really clear? (y/N): ")
            if ans.lower() != "y":
                return
        self.pending_lines.clear()
        self.code_buffer.clear()
        self.is_dirty = False
        self._reset_runtime()
        print("Buffer cleared and execution state reset.")

    # ─── 執行與除錯指令 ─────────────────────────────────────────────────────
    def _cmd_run(self):
        if not self.code_buffer:
            print("Buffer is empty.")
            return
        try:
            program_node = self._parse_full_buffer()
        except SyntaxError as exc:
            print(f"[!] 語法錯誤: {exc}")
            return
        except Exception as exc:
            print(f"[!] 解析錯誤: {exc}")
            return

        self._reset_runtime()
        self.interpreter.program_buffer = list(self.code_buffer)
        self.interpreter.trace = self.trace
        try:
            self.interpreter.visit(program_node)
        except Exception as exc:
            print(f"[*] 執行 main 時發生未預期錯誤: {exc}")

    def _cmd_check(self):
        if not self.code_buffer:
            print("Buffer is empty.")
            return
        try:
            self._parse_full_buffer()
            print("No errors found.")
        except SyntaxError as exc:
            print(f"{exc}")
        except Exception as exc:
            print(f"{exc}")

    def _cmd_trace(self, args):
        flag = args.upper()
        if flag == "ON":
            self.trace = True
            self.interpreter.trace = True
            print("trace is on")
        elif flag == "OFF":
            self.trace = False
            self.interpreter.trace = False
            print("trace is off")
        else:
            print("Error: Usage TRACE ON|OFF")

    def _cmd_vars(self):
        global_vars = [
            symbol for symbol in self.sym.globals.values() if symbol.sym_type == "VAR"
        ]
        if not global_vars:
            print("No global variables.")
            return
        for symbol in global_vars:
            print(self._format_live_symbol(symbol))

    def _cmd_funcs(self):
        for name in self.builtins_mgr.functions.keys():
            print(f"  {name}()  [built-in]")

        user_funcs = [
            symbol for symbol in self.sym.globals.values() if symbol.sym_type == "FUNC"
        ]
        if not user_funcs:
            print("  (no user-defined functions)")
            return

        for sym in user_funcs:
            func_node = sym.func_node
            if not isinstance(func_node, FuncDefNode):
                continue
            params = ", ".join(
                f"{self._type_name(p.type_node)} {p.name}" for p in func_node.params
            )
            ret_type = self._type_name(func_node.return_type)
            line_no = func_node.line if func_node.line is not None else "?"
            print(f"  {ret_type} {func_node.name}({params})  [line {line_no}]")

    # ─── 系統指令 ─────────────────────────────────────────────────────
    def _cmd_help(self, args):
        help_info = {
            "HELP": "HELP / HELP <command>：顯示輔助說明",
            "LOAD": "LOAD <filename>：從檔案載入 Small-C 原始碼至緩衝區",
            "SAVE": "SAVE <filename>：儲存目前緩衝區至檔案",
            "LIST": "LIST / LIST <n> / LIST <n1>-<n2>：列出緩衝區程式碼",
            "EDIT": "EDIT <n>：編輯緩衝區第 n 行",
            "DELETE": "DELETE <n> / DELETE <n1>-<n2>：刪除緩衝區指定行",
            "INSERT": "INSERT <n>：在第 n 行之前插入多行程式碼(. 結束)",
            "APPEND": "APPEND：在緩衝區末尾追加多行程式碼(. 結束)",
            "NEW": "NEW：清除緩衝區並重置執行狀態",
            "RESET": "RESET：同 NEW",
            "RUN": "RUN：執行緩衝區內的完整程式(會重置執行狀態)",
            "CHECK": "CHECK：對緩衝區做語法檢查不執行",
            "TRACE": "TRACE ON / TRACE OFF：開啟／關閉執行追蹤模式",
            "VARS": "VARS：顯示目前全域變數名稱、型別與值",
            "FUNCS": "FUNCS：顯示內建函式與使用者函式",
            "CLEAR": "CLEAR：清除終端機畫面",
            "ABOUT": "ABOUT：顯示解譯器資訊",
            "QUIT": "QUIT / EXIT：結束解譯器",
        }
        key = args.upper()
        if key in help_info:
            print(help_info[key])
            return

        print("═" * 50)
        print("  Small-C Live REPL 指令說明")
        print("═" * 50)
        for desc in help_info.values():
            print(f"  {desc}")
        print("═" * 50)

    def _cmd_about(self):
        print(">> Small-C Interactive Interpreter v1.0 (Live Mode)")
        print(">> System Software Final Project, Spring 2026")
        print("作者1, 2, 3")

    def _confirm_quit(self):
        if self.is_dirty:
            ans = input("Buffer has unsaved changes. Really quit? (y/N): ")
            if ans.lower() != "y":
                return False
        return True

    def _dispatch_command(self, line):
        parts = line.strip().split(maxsplit=1)
        if not parts:
            return True
        command = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ""

        if command in ("QUIT", "EXIT"):
            return False if self._confirm_quit() else True
        if command == "HELP":
            self._cmd_help(args)
            return True
        if command == "LOAD":
            self._cmd_load(args)
            return True
        if command == "SAVE":
            self._cmd_save(args)
            return True
        if command == "LIST":
            self._cmd_list(args)
            return True
        if command == "EDIT":
            self._cmd_edit(args)
            return True
        if command == "DELETE":
            self._cmd_delete(args)
            return True
        if command == "INSERT":
            self._cmd_insert(args)
            return True
        if command == "APPEND":
            self._cmd_append()
            return True
        if command in ("NEW", "RESET"):
            self._cmd_new()
            return True
        if command == "RUN":
            self._cmd_run()
            return True
        if command == "CHECK":
            self._cmd_check()
            return True
        if command == "TRACE":
            self._cmd_trace(args)
            return True
        if command == "VARS":
            self._cmd_vars()
            return True
        if command == "FUNCS":
            self._cmd_funcs()
            return True
        if command == "CLEAR":
            os.system("cls")
            return True
        if command == "ABOUT":
            self._cmd_about()
            return True
        return None

    def start(self):
        banner = r"""
╔═════════════════════════════════════════════════════════════════╗
║                                                                 ║
║   ██████╗ ███╗   ███╗  █████╗  ██╗      ██╗         ██████╗     ║
║  ██╔════╝ ████╗ ████║ ██╔══██╗ ██║      ██║        ██╔════╝     ║
║  ███████╗ ██╔████╔██║ ███████║ ██║      ██║        ██║          ║
║  ╚════██║ ██║╚██╔╝██║ ██╔══██║ ██║      ██║        ██║          ║
║  ███████║ ██║ ╚═╝ ██║ ██║  ██║ ███████╗ ███████╗   ╚██████╗     ║
║  ╚══════╝ ╚═╝     ╚═╝ ╚═╝  ╚═╝ ╚══════╝ ╚══════╝    ╚═════╝     ║
║                                                                 ║
║ >> Small-C Interactive Interpreter v1.0 (Live Mode)             ║
║ >> System Software Final Project, Spring 2026                   ║
╚═════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        print("Type 'HELP' for a list of commands.")

        while True:
            prompt = f"{len(self.pending_lines)} > " if self.pending_lines else "sc> "
            try:
                line = input(prompt)
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\nType 'QUIT' to exit.")
                self.pending_lines.clear()
                continue

            if not self.pending_lines:
                command_result = self._dispatch_command(line)
                if command_result is False:
                    break
                if command_result is True:
                    continue

            self.pending_lines.append(line)
            self._execute_pending()
