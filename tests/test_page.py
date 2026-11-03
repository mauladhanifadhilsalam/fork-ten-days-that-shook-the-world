"""The page's script is one scope: a second top-level `var` or `function` of a name already declared there
silently replaces the first. That has broken the page twice (the Faction Map's SIDE labels replaced the
fight's map of blocs to sides; a speed table named VEH replaced the moves' vehicles), with every other
check green. This finds any name declared twice at the top level of src/app.html."""
import os, re, unittest

PAGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'app.html')


def script(text):
    """the inline script's lines (the one without src=)"""
    m = re.search(r'<script>\n(.*?)</script>', text, re.S)
    return (m.group(1) if m else text).split('\n')


def top_level_names(lines):
    names = {}

    def declare(part, at):
        m = re.match(r'\s*([A-Za-z_$][\w$]*)', part)
        if m:
            names.setdefault(m.group(1), []).append(at)

    def split(body):
        depth, cur, parts, ended = 0, '', [], False
        for ch in body:
            if ch in '([{':
                depth += 1
            elif ch in ')]}':
                depth -= 1
            if ch == ',' and depth == 0:
                parts.append(cur); cur = ''
            elif ch == ';' and depth == 0:
                parts.append(cur); ended = True; break
            else:
                cur += ch
        if not ended and cur.strip():
            parts.append(cur)
        return parts, ended

    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'function ([A-Za-z_$][\w$]*)\s*\(', line)
        if m:
            names.setdefault(m.group(1), []).append(i + 1)
        elif line.startswith('var '):
            parts, ended = split(line[4:])
            for p in parts:
                declare(p, i + 1)
            # a declaration that runs on over indented lines: `var A = 1,\n  B = 2;`
            while not ended and i + 1 < len(lines) and lines[i + 1].startswith('  ') and not lines[i + 1].startswith('   '):
                i += 1
                parts, ended = split(lines[i])
                for p in parts:
                    if re.match(r'\s*[A-Za-z_$][\w$]*\s*=', p):
                        declare(p, i + 1)
        i += 1
    return names


class TopLevelNames(unittest.TestCase):
    def test_no_name_is_declared_twice(self):
        with open(PAGE, encoding='utf-8') as fh:
            names = top_level_names(script(fh.read()))
        twice = {k: v for k, v in names.items() if len(v) > 1}
        self.assertFalse(twice, f'declared more than once at the top level of src/app.html (line numbers in the script): {twice}')

    def test_the_check_sees_a_continued_declaration(self):
        names = top_level_names(['var A = 1,', '  VEH = { a: 1 };', 'var VEH = 2;', 'function f() {', '  var VEH = 3;', '}'])
        self.assertEqual(names.get('VEH'), [2, 3], 'a name on the continuation line of a var counts; one inside a function does not')


if __name__ == '__main__':
    unittest.main()
