import os
from cid.utils import set_parameters
from cid.common import Cid

import inspect

def test_basic_csv2view():
	with open('test.csv', 'w') as file_:
		file_.write('''a,b\nc,d'e''')

	Cid().csv2view(input='test.csv', name='res', athena_database='athenacurcfn_cur1')

	with open('res.sql') as file_:
		sql = file_.read()

	assert "CREATE OR REPLACE VIEW res AS" in sql
	assert "ROW('c', 'd e')" in sql
	assert "(a, b)" in sql

