import re


DEFINE_RE = re.compile(r'^\s*#\s*define\s+([A-Za-z_]\w*)(.*)$', re.IGNORECASE)
IDENT_RE = re.compile(r'\b[A-Za-z_]\w*\b')


class Preprocessor:
    """Handle simple object-like #define directives before lexing."""

    def __init__(self):
        self.macros = {}

    def process(self, source_code):
        processed_lines = []
        in_block_comment = False

        for line_no, line in enumerate(source_code.splitlines(), start=1):
            stripped = line.lstrip()

            if not in_block_comment and stripped.startswith('#'):
                match = DEFINE_RE.match(line)
                if not match:
                    raise SyntaxError(f"Preprocessor Error: Unsupported directive at line {line_no}")

                name, rest = match.groups()
                if rest.startswith('('):
                    raise SyntaxError(
                        f"Preprocessor Error: Function-like macro '{name}' is not supported at line {line_no}"
                    )

                self.macros[name] = rest.strip()
                processed_lines.append("")
                continue

            expanded, in_block_comment = self._expand_line(line, in_block_comment)
            processed_lines.append(expanded)

        return "\n".join(processed_lines)

    def _expand_line(self, line, in_block_comment):
        result = []
        i = 0
        in_string = False
        in_char = False
        escape = False

        while i < len(line):
            ch = line[i]
            next_ch = line[i + 1] if i + 1 < len(line) else ''

            if in_block_comment:
                result.append(ch)
                if ch == '*' and next_ch == '/':
                    result.append(next_ch)
                    i += 2
                    in_block_comment = False
                else:
                    i += 1
                continue

            if in_string or in_char:
                result.append(ch)
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif in_string and ch == '"':
                    in_string = False
                elif in_char and ch == "'":
                    in_char = False
                i += 1
                continue

            if ch == '/' and next_ch == '/':
                result.append(line[i:])
                break

            if ch == '/' and next_ch == '*':
                result.append(ch)
                result.append(next_ch)
                i += 2
                in_block_comment = True
                continue

            if ch == '"':
                result.append(ch)
                in_string = True
                i += 1
                continue

            if ch == "'":
                result.append(ch)
                in_char = True
                i += 1
                continue

            if ch.isalpha() or ch == '_':
                start = i
                i += 1
                while i < len(line) and (line[i].isalnum() or line[i] == '_'):
                    i += 1
                ident = line[start:i]
                result.append(self._expand_macro(ident, {ident}))
                continue

            result.append(ch)
            i += 1

        return "".join(result), in_block_comment

    def _expand_macro(self, ident, seen):
        if ident not in self.macros:
            return ident

        replacement = self.macros[ident]

        def replace_nested(match):
            nested = match.group(0)
            if nested in seen:
                return nested
            return self._expand_macro(nested, seen | {nested})

        return IDENT_RE.sub(replace_nested, replacement)
