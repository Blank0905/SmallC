from lexer import Lexer, Token

def main():
    # 模擬使用者輸入
    code = "2 + (10 * 0x9F) / 2 == 50 && 1 != 0 || 3 >= 2"
    
    # 初始化 Lexer
    lexer = Lexer(code)
    
    # 取得並印出所有 Token
    while True:
        token = lexer.get_next_token()
        print(token)
        if token.type == 'EOF':
            break

if __name__ == "__main__":
    main()