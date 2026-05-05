from lexer import Lexer, Token
from sc_parser import Parser
from ast_node import *
from repl import REPL 


def main():
    repl = REPL()
    repl.start() # test

if __name__ == "__main__":
    main()