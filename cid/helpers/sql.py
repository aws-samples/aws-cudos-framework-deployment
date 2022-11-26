import sqlparse


def pretty_sql(sql):
    sql = sqlparse.format(sql,
        reindent=True,
        keyword_case='upper',
        strip_comments=True,
        reindent_aligned=True
    )

    if ' CREATE ' in sql and ' TABLE ' in sql:
        #additional prettifying for tables
        for word in (
            'ROW FORMAT SERDE',
            'WITH SERDEPROPERTIES',
            'STORED AS INPUTFORMAT',
            'OUTPUTFORMAT',
            '(',
            ')',
            'LOCATION',
            'TBLPROPERTIES '):
            sql = sql.replace(word, '\n' + word)
        sql = '\n'.join([l.strip() for l in sql.splitlines() if l.strip()])

    elif ' CREATE ' in sql and ' VIEW ' in sql:
        #additional prettifying for views
        sql = '\n'.join([l for l in sql.splitlines() if l.strip()])

    return sql
