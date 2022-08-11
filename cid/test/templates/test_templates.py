import sh
import os
import sqlparse
from mako.template import Template


def prettify(sql):
    return sqlparse.format(sql, reindent=True, keyword_case='upper', strip_comments=True, reindent_aligned=True)

def show_diff(f1, f2):
    print(sh.diff(f1, f2, _ok_code=[0,1], color=True, ignore_all_space=True, minimal=True, strip_trailing_cr=True, ignore_blank_lines=True))


files =[
    './cid/builtin/core/data/queries/cid/ec2_running_cost.sql',
    './cid/builtin/core/data/queries/cid/ri_sp_mapping.sql',
    './cid/builtin/core/data/queries/cid/summary_view.sql',
    './cid/builtin/core/data/queries/kpi/kpi_instance_all_view.sql',
    './cid/builtin/core/data/queries/trends/monthly_bill_by_account.sql',
]

for fn in files:
    base_path, base_name = os.path.split(fn)
    base_path =  './cid/test/templates/'+os.path.split(base_path)[1]
    print(":------------------------------------" )
    print (fn)
    data = [
        {'cur_table_name': '${cur_table_name}', 'cur_has_savings_plan': False, 'cur_has_reservations': False, 'baseline': base_path + '/test_' + os.path.splitext(base_name)[0] + '.sql'},
        {'cur_table_name': '${cur_table_name}', 'cur_has_savings_plan': True,  'cur_has_reservations': False, 'baseline': base_path + '/test_' + os.path.splitext(base_name)[0] + '_sp.sql'},
        {'cur_table_name': '${cur_table_name}', 'cur_has_savings_plan': False, 'cur_has_reservations': True,  'baseline': base_path + '/test_' + os.path.splitext(base_name)[0] + '_ri.sql'},
        {'cur_table_name': '${cur_table_name}', 'cur_has_savings_plan': True,  'cur_has_reservations': True,  'baseline': base_path + '/test_' + os.path.splitext(base_name)[0] + '_sp_ri.sql'},
    ]
    for options in data:
        rendered = prettify(Template(open(fn).read()).render(**options))
        baseline= prettify(open(options['baseline']).read())

        with open('/tmp/1.sql', 'w') as f:
            f.write(rendered)
        with open('/tmp/2.sql', 'w') as f:
            f.write(baseline)

        print()
        print (options['baseline'])
        show_diff('/tmp/1.sql','/tmp/2.sql')
