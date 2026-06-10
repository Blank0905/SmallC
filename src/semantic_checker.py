from ast_node import (
    ArrayIndexNode,
    AssignNode,
    BinOpNode,
    BlockNode,
    BreakNode,
    CastNode,
    ContinueNode,
    DoWhileNode,
    ExprStmtNode,
    ForNode,
    FuncCallNode,
    FuncDefNode,
    IfNode,
    InitListNode,
    IntLiteralNode,
    ProgramNode,
    ReturnNode,
    SwitchNode,
    TernaryNode,
    UnaryOpNode,
    VarDeclNode,
    VarNode,
)


class SemanticChecker:
    """Static semantic checks used by CHECK without executing the program."""

    def __init__(self, builtin_names=None):
        self.builtin_names = set(builtin_names or [])
        self.functions = {}
        self.scopes = []
        self.loop_depth = 0
        self.switch_depth = 0
        self.current_function = None

    def check(self, node):
        method = getattr(self, f"check_{type(node).__name__}", None)
        if method is None:
            return None
        return method(node)

    def _line(self, node):
        line = getattr(node, "line", None)
        return f" at line {line}" if line and line > 0 else ""

    def _type_name(self, type_node):
        return type_node.base_type + ("*" * type_node.pointer_depth)

    def _enter_scope(self):
        self.scopes.append({})

    def _leave_scope(self):
        self.scopes.pop()

    def _define_var(self, node):
        scope = self.scopes[-1]
        if node.name in scope:
            raise Exception(
                f"Semantic Error: Redefinition of variable '{node.name}'{self._line(node)}"
            )
        scope[node.name] = node

    def _lookup_var(self, node):
        for scope in reversed(self.scopes):
            if node.name in scope:
                return scope[node.name]
        raise Exception(f"Semantic Error: Undefined symbol '{node.name}'{self._line(node)}")

    def _decl_type(self, decl):
        data_type = self._type_name(decl.type_node)
        if decl.array_size is not None:
            return data_type + "*"
        return data_type

    def _dereference_type(self, ptr_type, node):
        if not ptr_type.endswith("*"):
            raise Exception(
                f"Semantic Error: cannot dereference non-pointer type '{ptr_type}'{self._line(node)}"
            )
        return ptr_type[:-1]

    def _expr_type(self, node):
        if isinstance(node, VarNode):
            return self._decl_type(self._lookup_var(node))
        if isinstance(node, UnaryOpNode) and node.op == "&":
            return self._expr_type(node.operand) + "*"
        if isinstance(node, UnaryOpNode) and node.op == "*":
            return self._dereference_type(self._expr_type(node.operand), node)
        if isinstance(node, ArrayIndexNode):
            return self._dereference_type(self._expr_type(node.array), node)
        if isinstance(node, CastNode):
            return self._type_name(node.type_node)
        if isinstance(node, BinOpNode):
            left_type = self._expr_type(node.left)
            if left_type.endswith("*"):
                return left_type
            right_type = self._expr_type(node.right)
            if right_type.endswith("*"):
                return right_type
        return "int"

    def _check_lvalue(self, node):
        if isinstance(node, VarNode):
            self._lookup_var(node)
            return
        if isinstance(node, ArrayIndexNode):
            self.check(node.array)
            self.check(node.index)
            return
        if isinstance(node, UnaryOpNode) and node.op == "*":
            self._dereference_type(self._expr_type(node.operand), node)
            self.check(node.operand)
            return
        raise Exception(f"Runtime Error: invalid lvalue{self._line(node)}")

    def check_ProgramNode(self, node):
        self._enter_scope()
        try:
            for decl in node.declarations:
                if isinstance(decl, FuncDefNode):
                    if decl.name in self.functions or decl.name in self.scopes[0]:
                        raise Exception(
                            f"Semantic Error: Redefinition of function '{decl.name}'{self._line(decl)}"
                        )
                    self.functions[decl.name] = decl

            for decl in node.declarations:
                if isinstance(decl, VarDeclNode):
                    self.check(decl)
                elif isinstance(decl, FuncDefNode):
                    self.check(decl)
        finally:
            self._leave_scope()

    def check_FuncDefNode(self, node):
        previous_function = self.current_function
        self.current_function = node
        self._enter_scope()
        try:
            for param in node.params:
                self._define_var(param)
            self.check(node.body)
        finally:
            self._leave_scope()
            self.current_function = previous_function

    def check_VarDeclNode(self, node):
        self._define_var(node)
        if node.array_size is not None:
            self.check(node.array_size)
            if (
                isinstance(node.array_size, IntLiteralNode)
                and isinstance(node.init_expr, InitListNode)
                and len(node.init_expr.expressions) > node.array_size.value
            ):
                raise Exception(
                    f"Semantic Error: excess elements in array initializer for '{node.name}' "
                    f"(size {node.array_size.value}, got {len(node.init_expr.expressions)})"
                    f"{self._line(node)}"
                )
        if node.init_expr is not None:
            self.check(node.init_expr)

    def check_BlockNode(self, node):
        for stmt in node.statements:
            self.check(stmt)

    def check_ExprStmtNode(self, node):
        self.check(node.expr)

    def check_VarNode(self, node):
        self._lookup_var(node)

    def check_AssignNode(self, node):
        self._check_lvalue(node.target)
        self.check(node.value)

    def check_ArrayIndexNode(self, node):
        self.check(node.array)
        self.check(node.index)

    def check_FuncCallNode(self, node):
        for arg in node.args:
            self.check(arg)
        if node.name in self.builtin_names:
            return
        func = self.functions.get(node.name)
        if func is None:
            raise Exception(f"Semantic Error: Undefined function '{node.name}'{self._line(node)}")
        if len(func.params) != len(node.args):
            raise Exception(
                f"Semantic Error: function '{node.name}' expected "
                f"{len(func.params)} argument(s), got {len(node.args)}{self._line(node)}"
            )

    def check_BinOpNode(self, node):
        self.check(node.left)
        self.check(node.right)

    def check_UnaryOpNode(self, node):
        if node.op in ("++", "--"):
            self._check_lvalue(node.operand)
        elif node.op == "*":
            self._dereference_type(self._expr_type(node.operand), node)
            self.check(node.operand)
        else:
            self.check(node.operand)

    def check_TernaryNode(self, node):
        self.check(node.condition)
        self.check(node.then_expr)
        self.check(node.else_expr)

    def check_CastNode(self, node):
        self.check(node.expr)

    def check_InitListNode(self, node):
        for expr in node.expressions:
            self.check(expr)

    def check_IfNode(self, node):
        self.check(node.condition)
        self._enter_scope()
        try:
            self.check(node.then_block)
        finally:
            self._leave_scope()
        if node.else_block is not None:
            self._enter_scope()
            try:
                self.check(node.else_block)
            finally:
                self._leave_scope()

    def check_WhileNode(self, node):
        self.check(node.condition)
        self.loop_depth += 1
        self._enter_scope()
        try:
            self.check(node.body)
        finally:
            self._leave_scope()
            self.loop_depth -= 1

    def check_DoWhileNode(self, node):
        self.loop_depth += 1
        self._enter_scope()
        try:
            self.check(node.body)
        finally:
            self._leave_scope()
            self.loop_depth -= 1
        self.check(node.condition)

    def check_ForNode(self, node):
        self._enter_scope()
        self.loop_depth += 1
        try:
            if node.init is not None:
                self.check(node.init)
            if node.condition is not None:
                self.check(node.condition)
            if node.update is not None:
                self.check(node.update)
            self._enter_scope()
            try:
                self.check(node.body)
            finally:
                self._leave_scope()
        finally:
            self.loop_depth -= 1
            self._leave_scope()

    def check_SwitchNode(self, node):
        self.check(node.expr)
        self.switch_depth += 1
        try:
            for case_val, block in node.cases:
                self.check(case_val)
                self._enter_scope()
                try:
                    self.check(block)
                finally:
                    self._leave_scope()
            if node.default_stmt is not None:
                self._enter_scope()
                try:
                    self.check(node.default_stmt)
                finally:
                    self._leave_scope()
        finally:
            self.switch_depth -= 1

    def check_ReturnNode(self, node):
        if self.current_function is None:
            raise Exception(f"Semantic Error: return cannot appear at top level{self._line(node)}")
        if node.value is not None:
            self.check(node.value)

    def check_BreakNode(self, node):
        if self.loop_depth == 0 and self.switch_depth == 0:
            raise Exception(f"Semantic Error: break cannot appear outside loop or switch{self._line(node)}")

    def check_ContinueNode(self, node):
        if self.loop_depth == 0:
            raise Exception(f"Semantic Error: continue cannot appear outside loop{self._line(node)}")
