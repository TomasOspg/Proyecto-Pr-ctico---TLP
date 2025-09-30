# -*- coding: utf-8 -*-
"""
Analizador de archivos .brik (Tetris y Snake)
Desarrolladores -> Juan Mateo Mayorga Duque - Tomas Ospina Gaviria

"""
import json
import re
import os

# ========================================
# 1️⃣ Clase Tokenizer
# ========================================
class Tokenizer:
    def __init__(self, source_code):
        self.source = source_code
        self.tokens = []

    def tokenize(self):
        lines = self.source.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Regex para los cuatro tipos de tokens
            regex_tokens = re.findall(r'"([^"]*)"|(\d+(\.\d+)?)|([{}[\]=,])|([a-zA-Z_@][a-zA-Z0-9_]*)', line)
            
            for group in regex_tokens:
                if group[0]:  # STRING
                    self.tokens.append(('STRING', group[0]))
                elif group[1]:  # NUMBER
                    if '.' in group[1]:
                        self.tokens.append(('NUMBER', float(group[1])))
                    else:
                        self.tokens.append(('NUMBER', int(group[1])))
                elif group[3]:  # OPERATOR
                    self.tokens.append(('OPERATOR', group[3]))
                elif group[4]:  # IDENTIFIER
                    self.tokens.append(('IDENTIFIER', group[4]))
        
        return self.tokens
    
# ========================================
# 2️⃣ Clase Parser
# ========================================
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.symbol_table = {}

    def parse(self):
        while self.peek_token() is not None:
            key_token = self.get_token()
            if key_token[0] != 'IDENTIFIER':
                raise SyntaxError(f"Se esperaba un identificador, se encontró {key_token[1]}")
            
            eq_token = self.get_token()
            if eq_token[1] != '=':
                raise SyntaxError(f"Se esperaba '=', se encontró {eq_token[1]}")
            
            value = self.parse_value()
            self.symbol_table[key_token[1]] = value
            
        return self.symbol_table

    def get_token(self):
        if self.current_token_index < len(self.tokens):
            token = self.tokens[self.current_token_index]
            self.current_token_index += 1
            return token
        return None

    def peek_token(self):
        if self.current_token_index < len(self.tokens):
            return self.tokens[self.current_token_index]
        return None

    def parse_value(self):
        token = self.peek_token()
        if token is None:
            raise SyntaxError("Se esperaba un valor después de '='")
        
        token_type, token_value = token
        if token_type in ['STRING', 'NUMBER']:
            self.current_token_index += 1
            return token_value
        elif token_type == 'OPERATOR' and token_value == '{':
            return self.parse_block()
        elif token_type == 'OPERATOR' and token_value == '[':
            return self.parse_list()
        
        raise SyntaxError(f"Valor inesperado '{token_value}'")

    def parse_block(self):
        self.get_token()  # Consume '{'
        block_content = {}
        
        while self.peek_token() and self.peek_token()[1] != '}':
            key_token = self.get_token()
            if key_token[0] != 'IDENTIFIER':
                raise SyntaxError(f"Se esperaba un identificador en bloque, se encontró {key_token[1]}")
            
            eq_token = self.get_token()
            if eq_token[1] != '=':
                raise SyntaxError(f"Se esperaba '=', se encontró {eq_token[1]}")
            
            value = self.parse_value()
            block_content[key_token[1]] = value

        self.get_token()  # Consume '}'
        return block_content

    def parse_list(self):
        self.get_token()  # Consume '['
        list_content = []
        
        while self.peek_token() and self.peek_token()[1] != ']':
            token_type, token_value = self.peek_token()
            if token_type == 'IDENTIFIER':
                self.get_token()
                if token_value not in self.symbol_table:
                    raise NameError(f"Identificador '{token_value}' no definido.")
                list_content.append(self.symbol_table[token_value])
            else:
                item = self.parse_value()
                list_content.append(item)
            
            if self.peek_token() and self.peek_token()[1] == ',':
                self.get_token()  # Consume ','
                
        self.get_token()  # Consume ']'
        return list_content

# ========================================
# Funciones auxiliares
# ========================================
def load_file_content(filepath):
    if not os.path.exists(filepath):
        print(f"Error: El archivo '{filepath}' no se encontró.")
        return None
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def save_ast_to_file(ast, filepath):
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(ast, file, indent=4)
        print(f"AST guardado en '{filepath}'")
    except Exception as e:
        print(f"Error al guardar el archivo: {e}")

# ========================================
# Ejecución principal
# ========================================
if __name__ == "__main__":
    carpeta_actual = os.path.dirname(os.path.abspath(__file__))  # Carpeta donde está analizador.py
    
    for nombre_archivo in ["tetris.brik", "snake.brik"]:
        file_path = os.path.join(carpeta_actual, nombre_archivo)
        source_code = load_file_content(file_path)
        
        if source_code:
            print(f"\n=== Analizando {nombre_archivo} ===\n")
            
            # Lexer
            tokenizer = Tokenizer(source_code)
            tokens = tokenizer.tokenize()
            print("Tokens:")
            for t in tokens:  # Muestra todos los tokens
                print(t)
            
            # Parser y Tabla de símbolos
            parser = Parser(tokens)
            try:
                ast = parser.parse()
                print("\nAST / Tabla de símbolos:")
                print(json.dumps(ast, indent=4))
                
                # Guardar AST en la misma carpeta
                ast_file_path = os.path.join(carpeta_actual, f"{nombre_archivo}.ast")
                save_ast_to_file(ast, ast_file_path)
            except (SyntaxError, NameError) as e:
                print(f"Error: {e}")