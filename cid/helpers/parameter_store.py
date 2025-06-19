import logging
from datetime import datetime

from cid.exceptions import CidCritical

logger = logging.getLogger(__name__)

class AthenaStore():
    def __init__(self, athena, view_name='cid_parameters'):
        self.athena = athena
        self.view_name = view_name

    def dump(self, data):
        ''' dump data to athena
        '''
        try:
            # FIXME: make it multi view
            self.athena.query(self._generate_view_query(data, self.view_name))
        except (CidCritical, Exception) as exc:
            logger.debug(f'failed to save parameters store: {exc}')

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
        context_parameters = {}
        any_parameters = {}
        # get any context and then override with specific context
        for line in sorted(data, key=lambda x: x.get('date', '')): # latest should override
            any_parameters[line.get('parameter')] = line.get('value')
            if line.get('context') == str(context):
                context_parameters[line.get('parameter')] = line.get('value')
        return any_parameters | context_parameters

    def dump_parameters(self, params, context=None):
        data = self.load()
        logger.trace(f'loaded parameters {data}')
        params = dict(params)
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        #Update parameters if they are present already
        for line in data:
            for key, val in list(params.items()):
                if line.get('context') == str(context) and line.get('parameter') == key:
                    line['value'] = val
                    line['date'] = date
                    del params['key']

        #add parameters that are new
        for key, val in list(params.items()):
            data.append({
                'parameter': key, 'value': ','.join(val) if isinstance(val, list) else val,
                'context': str(context),
                'date': date
            })

        logger.trace(f'dumping parameters {data}')
        self.dump(data)