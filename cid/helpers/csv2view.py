import re
import csv
import logging

from cid.exceptions import CidCritical

logger = logging.getLogger(__name__)

def escape(text, character='_'):
    """ escape for sql statement """
    return re.sub('[^0-9a-zA-Z]+', character, text)


def csv2view(input_file_name: str, name: str, output_file_name: str=None) -> None:
    """ Make an sql mapping from sql """
    logger.debug(f"input {input_file_name}")

    sniffer = csv.Sniffer()
    try:
        with open(input_file_name) as file_:
            dialect = sniffer.sniff(file_.read(2000))
            file_.seek(0)
            data = [d for d in csv.DictReader(file_, dialect=dialect)]
            
    except FileNotFoundError:
        raise CidCritical(f'File not found: {repr(input_file_name)}')
    except PermissionError:
        raise CidCritical(f'Insufficient permission to read {repr(input_file_name)}!')
    except IsADirectoryError:
        raise CidCritical(f'{repr(input_file_name)} is a directory!')
    except Exception as _err:
        raise CidCritical(_err)
    
    lines = []
    
    for line in data:
        arr = ", ".join([f'\'{escape(val, " ")}\'' for val in line.values()])
        lines.append(f'ROW({arr})')

    if not lines:
        CidCritical(f'There is no data to write, exiting"')
        
    headers = data[0].keys()
    
    row_lines = '\n, '.join(lines)
    cols = ', '.join([escape(c.lower()) for c in headers ])

    sql = (f'''
CREATE OR REPLACE VIEW {escape(name.lower())} AS
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
