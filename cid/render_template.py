import click
from mako.template import Template


@click.command(name='test_template', context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True,
))
@click.argument('file')
@click.pass_context
def main(ctx, file):
    options = {ctx.args[i][2:]: ctx.args[i+1] for i in range(0, len(ctx.args), 2)}
    #print('rendering', file)
    mapping = {'True': True, 'False': False}
    for k, v in options.items():
        options[k] = mapping.get(v, v)
    #print(options)
    print(Template(open(file).read()).render(**options))


if __name__ == '__main__':
    main()

import sqlparse
from mako.template import Template

fn = './cid/builtin/core/data/queries/cid/ri_sp_mapping'
fn = './cid/builtin/core/data/queries/cid/ec2_running_cost'
fn_t = fn+'.sql'

data = [
# {'cur_table_name': '${cur_table_name}',  'cur_has_savings_plan': False, 'cur_has_reservations': False, 'baseline': fn+'_ri.sql'},
 {'cur_table_name': '${cur_table_name}',  'cur_has_savings_plan': True, 'cur_has_reservations': False, 'baseline': fn + '_sp.sql'},
 {'cur_table_name': '${cur_table_name}',  'cur_has_savings_plan': False, 'cur_has_reservations': True, 'baseline': fn + '_ri.sql'},
 {'cur_table_name': '${cur_table_name}',  'cur_has_savings_plan': True, 'cur_has_reservations':  True, 'baseline': fn + '_sp_ri.sql'},
]
import sh
file = fn_t
def prettify(sql):
    return sqlparse.format(sql, reindent=True, keyword_case='upper', strip_comments=True, reindent_aligned=True)

def show_diff(f1, f2):
    print(sh.diff(f1, f2, _ok_code=[0,1], color=True, ignore_all_space=True, minimal=True, strip_trailing_cr=True, ignore_blank_lines=True))

for options in data:
    rendered = prettify(Template(open(file).read()).render(**options))
    baseline= prettify(open(options['baseline']).read())

    with open('/tmp/1.sql', 'w') as f:
        f.write(rendered)
    with open('/tmp/2.sql', 'w') as f:
        f.write(baseline)

    print()
    print (options['baseline'])
    show_diff('/tmp/1.sql','/tmp/2.sql')
