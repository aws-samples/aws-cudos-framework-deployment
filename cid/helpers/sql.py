from pygments import highlight, lexers, formatters
from pygments_pprint_sql import SqlFilter

from pygments.formatters.other import NullFormatter


def pretty_sql(sql):
    """ make a human readable SQL"""

    lexer = lexers.MySqlLexer()
    lexer.add_filter(SqlFilter())

    formatter = NullFormatter() # for color: = formatters.TerminalFormatter()

    pretty = highlight(sql, lexer, formatter)

    # postprocessing. (FIXME: check if this can be done in SQLFilter)
    pretty = pretty.replace(' , ', '\n , ').replace('SELECT', 'SELECT\n  ')

    return pretty
