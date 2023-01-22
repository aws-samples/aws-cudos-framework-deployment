import os
import csv
import logging

logger = logging.getLogger(__name__)

def csv2view(input_file_name: str, name: str, output_file_name: str=None) -> None:
    """ Make an sql mapping from sql """
    logger.debug(f"input {input_file_name}")
    with open(input_file_name) as file_:
        data = [d for d in csv.DictReader(file_)]

    lines = []
    for line in data:
        arr = ", ".join(["\'" + val.replace("'", ' ') + "\'" for val in line.values()])
        lines.append(f'ROW({arr})')

    row_lines = '\n, '.join(lines)
    cols = ', '.join([c.lower().replace(' ','_') for c in data[0].keys()])

    sql = (f'''
CREATE OR REPLACE VIEW {name} AS
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
