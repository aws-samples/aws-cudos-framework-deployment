import re
import csv
import logging
from io import StringIO

from cid.exceptions import CidCritical

logger = logging.getLogger(__name__)

def escape_sql(text, character='_'):
    """ escape for sql statement """
    return re.sub('[^0-9a-zA-Z]+', character, str(text))

def escape_text(text, character='_'):
    """ escape for sql statement """
    return str(text).replace("'", "''")

def read_nonblank_lines(lines):
    """ returns non blank lines from file"""
    for line in lines:
        line_rstrip = line.rstrip()
        if line_rstrip:
            yield line_rstrip

def read_csv(input_file_name):
    """ Read CSV """
    sniffer = csv.Sniffer()
    try:
        # AWS Organization returns a CSV with a BOM (byte order mark) character = U+FEFF to specify encoding
        first_character = open(input_file_name, errors='ignore').read(1)
        encoding = 'utf-8-sig' if first_character == '\ufeff' else 'utf-8'

        with open(input_file_name, encoding=encoding, errors='ignore') as file_:
            text = '\n'.join([line for line in read_nonblank_lines(file_)]) # AWS Organization produces a CSV with empty lines
            dialect = sniffer.sniff(text)
            data = [row for row in csv.DictReader(StringIO(text), dialect=dialect, skipinitialspace=True)]

    except FileNotFoundError:
        raise CidCritical(f'File not found: {repr(input_file_name)}')
    except PermissionError:
        raise CidCritical(f'Insufficient permission to read {repr(input_file_name)}!')
    except IsADirectoryError:
        raise CidCritical(f'{repr(input_file_name)} is a directory!')
    except Exception as _err:
        raise CidCritical(_err)
    return data

def csv2view(input_file_name: str, name: str, output_file_name: str=None) -> None:
    """ Make an sql mapping from sql """
    logger.debug(f"input {input_file_name}")
    data = read_csv(input_file_name)
    lines = []
    for line in data:
        arr = ", ".join([f'\'{escape_text(val, " ")}\'' for val in line.values()])
        lines.append(f'ROW({arr})')

    if not lines:
        CidCritical(f'There is no data to write, exiting"')

    headers = data[0].keys()

    row_lines = '\n, '.join(lines)
    cols = ', '.join([escape_sql(c.lower()) for c in headers ])

    sql = (f'''
CREATE OR REPLACE VIEW {escape_sql(name.lower())} AS
SELECT *
FROM
(
VALUES
  {row_lines}
) ignored_table_name ({cols})
    '''.strip())
    if len(sql) > 262144:
        logger.warning(f'The maximum allowed query string length is 262144 bytes. Current sql size: {len(sql)}')
    output_file_name = output_file_name or name + '.sql'
    with open(output_file_name, 'w') as file_:
        file_.write(sql)
    print(f'Output: {output_file_name}')
