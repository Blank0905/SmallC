from lexer import Lexer, Token
from parser import Parser
from ast_node import *


def simple_print(node, depth=0):
    if node is None: return
    indent = "  " * depth
    # 印出節點的類別名稱
    print(f"{indent}{type(node).__name__}:")
    
    # 暴力掃過該物件的所有屬性
    if hasattr(node, '__dict__'):
        for key, value in vars(node).items():
            if isinstance(value, list):
                print(f"{indent}  {key}:")
                for item in value:
                    simple_print(item, depth + 2)
            elif hasattr(value, '__dict__'):
                print(f"{indent}  {key}:")
                simple_print(value, depth + 2)
            else:
                print(f"{indent}  {key}: {value}")
def main():
    lexer = Lexer("int x = 5; int main() { return x; }")
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast_root = parser.parse()
    
    print("\n--- AST ---")
    simple_print(ast_root)

if __name__ == "__main__":
    main()