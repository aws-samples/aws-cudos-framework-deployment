import difflib

from cid.utils import cid_print

def diff(text1, text2):
    """ Return SQL diff """
    res = {}
    ndiff = difflib.ndiff(
        text1.splitlines(keepends=True),
        text2.splitlines(keepends=True),
    )
    lines = ''.join(ndiff)
    res['lines'] = lines
    res['+'] = 0
    res['-'] = 0
    res['='] = 0
    for line in lines.splitlines():
        if line.startswith('-'): res['-'] += 1
        elif line.startswith('+'): res['+'] += 1
        elif line.startswith(' '): res['='] += 1
    res['diff'] = res['+'] + res['-']
    res['printable'] = diff_2_cid_print(lines)
    return res

def diff_2_cid_print(lines):
    """ convert ndiff to printable color format """
    new_lines = []
    next_line_chars = []
    for line in lines.splitlines()[::-1]:
        color = 'END'
        new_line = ''
        if line.startswith('-'):
            color = 'RED'
        elif line.startswith('+'):
            color = 'GREEN'
        elif line.startswith(' '):
            color = 'GREY'

        if not line.startswith('?'):
            new_line = f'<{color}>'
            bold = False
            last_bold = False
            for i, c in enumerate(line):
                bold = (i in next_line_chars)

                if bold and not last_bold:
                    new_line += f'<BOLD><{color}>'
                if last_bold and not bold:
                    new_line += f'<END><{color}>'
                new_line += c
                last_bold = bold
            new_line += '<END>'
            next_line_chars = []
        else:
            next_line_chars = []
            for i, c in enumerate(line):
                if c not in [' ', '?']:
                    next_line_chars.append(i)
        new_lines.append(new_line)
    return ('\n'.join(new_lines[::-1]))

def print_diff(diff):
    """ print diff to stdout """
    return cid_print(diff_2_cid_print(diff))


def test_diff_2_cid_print():
    res = diff_2_cid_print(diff_sql('SELECT * FROM aaa', 'SELECT * FROM    "aaa" ')['lines'])
    assert res == '<YELLOW>  SELECT<END>\n<YELLOW>     *<END>\n<RED>- FROM aaa<END>\n<GREEN>+ FROM <BOLD><GREEN>"<END><GREEN>aaa<BOLD><GREEN>"<END>\n'