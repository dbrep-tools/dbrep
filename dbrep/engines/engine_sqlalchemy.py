
# Performance notes (based on simple test, without detailed hyperparameters and size comparisons):
# 1) pandas uses sqlalchemy with execute(table.insert(), data) -- set it as baseline
#    there are 3 option for insert method: None, 'multi' and custom (e.g. PG COPY)
# 2) None is versatile and fastest (100% time)
# 3) 'multi' is unexpectedly slower (700% time)
# 4) PG COPY is much faster (30% time)
# 5) None performance is attained using sqlalchemy.execute and passing list of dictionaries for bind params
# 6) Much faster alternative is insert values (), (), (), () using mogrify on python side ~50% time
#
# HENCE primary solution to test against pandas: mogrify inside python, insert with several simple executes

import functools

from .engine_base import BaseEngine
from .. import add_engine_factory

class SQLAlchemyEngine(BaseEngine):
    id = 'sqlalchemy'
    def __init__(self, connection_config):
        import sqlalchemy #import only here when it will be actually used
        def make_table_(table_name, col_names):
            return sqlalchemy.Table(table_name, sqlalchemy.MetaData(),
                        *[sqlalchemy.Column(x) for x in col_names]
                    )

        self.engine = sqlalchemy.create_engine(connection_config['conn-str'])
        self.conn = self.engine.connect()
        self.template_select_inc = 'select * from {src} where {rid} > {rid_value} order by {rid}'
        self.template_select_inc_null = 'select * from {src} order by {rid}'
        self.template_select_all = 'select * from {src}'
        self.template_select_rid = 'select max({rid}) from {src}'
        self.template_truncate = 'truncate table {src}'
        self.make_query = sqlalchemy.text
        self.make_table = lambda table_name, col_names: make_table_(table_name, col_names)
        self.active_insert = None
        self.active_cursor = None

    def _execute(self, *args, **kwargs):
        try:
            return self.conn.execute(*args, **kwargs)
        except ConnectionError:
            self.conn = self.engine.connect()
            return self.conn.execute(*args, **kwargs)

    def get_latest_rid(self, config):
        query = self.make_query(self.template_select_rid.format(
            src='({}) t'.format(config['query']) if 'query' in config else config['table'],
            rid=config['rid']
        ))
        res = self._execute(query).fetchall()
        if res is None or len(res) == 0:
            return None
        return res[0][0]

    def begin_incremental_fetch(self, config, min_rid):
        template = self.template_select_inc if min_rid else self.template_select_inc_null
        query = self.make_query(template.format(
            src='({}) t'.format(config['query']) if 'query' in config else config['table'],
            rid=config['rid'],
            rid_value=min_rid
        ))
        self.active_cursor = self._execute(query)

    def begin_full_fetch(self, config):
        query = self.make_query(self.template_select_all.format(
            src='({}) t'.format(config['query']) if 'query' in config else config['table']
        ))
        self.active_cursor = self._execute(query)

    def begin_insert(self, config):
        self.active_insert = functools.partial(self.make_table, table_name=config['table'])

    def fetch_batch(self, batch_size):
        if not self.active_cursor:
            raise Exception()
        keys = list(self.active_cursor.keys())
        return keys, self.active_cursor.fetchmany(batch_size)

    def insert_batch(self, names, batch):
        self._execute(self.active_insert(col_names=names).insert(), [dict(zip(names, x)) for x in batch])

    def truncate(self, config):
        self._execute(self.truncate_template.format(config['table']))

    def create(self, config):
        self._execute(config['create'])
    
    def close(self):
        self.conn.close()
        self.engine.dispose()

add_engine_factory(SQLAlchemyEngine.id, SQLAlchemyEngine)