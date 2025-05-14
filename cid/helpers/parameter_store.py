from cid.exceptions import CidCritical

class AthenaStore():
    def __init__(self, athena, view_name='cid_parameters'):
        self.athena = athena
        self.view_name = view_name

    def dump(self, data):
        ''' load from athena
        '''
        # FIXME: make it multi view
        self.athena.query(self._generate_view_query(data, self.view_name))

    def load(self):
        ''' load from athena
        '''
        try:
            res = self.athena.query(f'''select * from  {self.view_name}''', include_header=True)
        except CidCritical as exc:
            if 'TABLE_NOT_FOUND' in str(exc):
                res = []
            else:
                raise
        return [{k:v for k, v in zip(res[0], row)} for row in res[1:]]

    def _to_sql_str(self, val):
        if val is None:
            return "''"
        return "'" + str(val).replace("'", "''") + "'"

    def _generate_view_query(self, data, name):
        all_keys = {key for dictionary in data for key in dictionary.keys()}
        lines = ',\n            '.join([f'''ROW({','.join([self._to_sql_str(line.get(k)) for k in all_keys])})''' for line in data])
        query = f"""
            CREATE OR REPLACE VIEW {name} AS
            SELECT *
            FROM (
                VALUES
                {lines}
            ) ignored_table_name ({','.join([key for key in all_keys])})
        """
        return query

class ParametersController(AthenaStore):
    def load_parameters(self, context):
        data = self.load()
        return { line.get('parameter'):line.get('value') for line in data}

    def dump_parameters(self, params, context=None):
        data = [{'parameter': key, 'value': ','.join(val) if isinstance(val, list) else val, 'context': str(context) } for key, val in params.items()]
        self.dump(data)