import difflib

import sqlparse
import re


def pretty_sql(sql):
    """Show pretty sql"""

    # replace Athena keyworks form quoted to unquoted
    text = (sql
        .replace('"approx_distinct"', "approx_distinct")
        .replace('"split_part"', 'split_part')
        .replace('"date_trunc"', 'date_trunc')
        .replace('"sum"', "SUM")
        .replace('"concat"', "concat")
        .replace('"greatest"', 'greatest')
        .replace('"count"', "count")
        .replace(' != ', ' <> ')
        .replace(' AS ', ' ')
        .replace(' as ', ' ')
        .replace('\n, ', ', ')
        .replace(',\n ', ', ')
        .replace(',\n ', ', ')
    )
    text = re.sub('\s+?,\s+', ', ', text)
    #text = re.sub('(?:[^(])CASE(.+?)END', '\(CASE\1END\)', text)
    return sqlparse.format(
        text,
        strip_comments=True,
        reindent=True,
        reindent_aligned=False,
        keyword_case ='upper',
        identifier_case='upper',
        comma_first=False,
    )

def diff(a: str, b: str) -> str:
    """Show clor diff"""
    output = []
    matcher = difflib.SequenceMatcher(None, a, b)

    green = '\x1b[38;5;16;48;5;2m'
    red = '\x1b[38;5;16;48;5;1m'
    endgreen = '\x1b[0m'
    endred = '\x1b[0m'

    for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
        if opcode == 'equal':
            output.append(a[a0:a1])
        elif opcode == 'insert':
            output.append(f'{green}{b[b0:b1]}{endgreen}')
        elif opcode == 'delete':
            output.append(f'{red}{a[a0:a1]}{endred}')
        elif opcode == 'replace':
            output.append(f'{green}{b[b0:b1]}{endgreen}')
            output.append(f'{red}{a[a0:a1]}{endred}')
    return ''.join(output)

