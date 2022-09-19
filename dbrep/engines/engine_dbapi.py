import importlib

from .engine_base import BaseEngine
from . import add_engine_factory

class DBAPIEngine(BaseEngine):
    id = 'dbapi'
    
    @staticmethod
    def _make_query_from_config(config):
        if 'query' in config:
            return '({}) t'.format(config['query'])
        if 'schema' in config:
            return '{}.{}'.format(config['schema'], config['table'])
        return '{}'.format(config['table'])

    @staticmethod
    def _insert_pyformat(cursor, table, names, values):
        col_names = ','.join(names)
        val_names = ','.join(['%({})s'.format(x) for x in names])
        query = 'insert into {} ({}) values ({})'.format(table, col_names, val_names)
        cursor.executemany(query, [dict(zip(names, x)) for x in values])
        
    @staticmethod
    def _insert_format_optimized(cursor, table, names, values, batch_size=1000):
        batch_rows = max(1, int(batch_size / len(names)))
        col_names = ','.join(names)
        row_tmplt = '({})'.format(','.join(['%s']*len(names)))
        query_top = 'insert into {} ({}) values '.format(table, col_names)
        for i in range(0, len(values), batch_rows):
            batch = values[i:min(i+batch_rows, len(values))]
            query = query_top + ','.join([row_tmplt]*len(batch))
            cursor.execute(query, [v for x in batch for v in x])
    
    @staticmethod
    def _insert_pyformat_optimized(cursor, table, names, values, batch_size=1000):
        batch_rows = max(1, int(batch_size / len(names)))
        col_names = ','.join(names)
        row_tmplts = [
            '({})'.format(','.join(['%(i{})s'.format(i * len(names) + j) for j in range(len(names))]))
            for i in range(batch_rows)
        ]
        query_top = 'insert into {} ({}) values '.format(table, col_names)
        for i in range(0, len(values), batch_rows):
            batch = values[i:min(i+batch_rows, len(values))]
            query = query_top + ','.join(row_tmplts[:len(batch)])
            params = [v for x in batch for v in x]
            cursor.execute(query, {'i{}'.format(i):x for (i,x) in enumerate(params)})
        
    def __init__(self, connection_config):     
        self.driver_name = connection_config['driver']
        self.driver = importlib.import_module(self.driver_name)
        if self.driver_name in ('mysql.connector', 'psycopg2'):
            self.fn_insert_ = DBAPIEngine._insert_format_optimized
        elif self.driver.paramstyle == 'pyformat':
            self.fn_insert_ = DBAPIEngine._insert_pyformat_optimized
        elif self.driver.paramstyle == 'format':
            self.fn_insert_ = DBAPIEngine._insert_format_optimized
        else:
            raise NotImplementedError('Support for drivers with paramstyle other than [pyformat, format] is not implemented!')
        
        driver_keywords = ['dsn', 'database', 'user', 'host', 'port', 'password']
        driver_params = {k: v for k,v in connection_config.items() if k in driver_keywords}
        driver_params.update(connection_config.get('driver-params', {}))
        self.conn = self.driver.connect(**driver_params)

        self.template_select_inc = 'select * from {src} where {rid} > {rid_value} order by {rid}'
        self.template_select_inc_null = 'select * from {src} order by {rid}'
        self.template_select_all = 'select * from {src}'
        self.template_select_rid = 'select max({rid}) from {src}'
        self.execute_batch_elems = connection_config.get('execute_batch_num_elems', 1000)
        self.active_cursor = None
        self.active_insert = None

    def insert_batch_(self, names, batch):
        with self.conn.cursor() as cur:
            self.fn_insert_(cur, self.active_insert, names, batch,
                            batch_size=self.override_execute_batch_elems or self.execute_batch_elems)        

    def get_latest_rid(self, config):
        query = self.template_select_rid.format(
            src=DBAPIEngine._make_query_from_config(config),
            rid=config['rid']
        )
        with self.conn.cursor() as cur:
            cur.execute(query)
            res = cur.fetchall()
        if res is None or len(res) == 0:
            return None
        return res[0][0]

    def begin_incremental_fetch(self, config, min_rid):
        template = self.template_select_inc if min_rid else self.template_select_inc_null
        query = template.format(
            src=DBAPIEngine._make_query_from_config(config),
            rid=config['rid'],
            rid_value=min_rid
        )
        if self.active_cursor:
            self.active_cursor.close()

        self.active_cursor = self.conn.cursor()
        self.active_cursor.execute(query)

    def begin_full_fetch(self, config):
        query = self.template_select_all.format(
            src=DBAPIEngine._make_query_from_config(config)
        )
        if self.active_cursor:
            self.active_cursor.close()

        self.active_cursor = self.conn.cursor()
        self.active_cursor.execute(query)

    def begin_insert(self, config):
        name = config['table']
        if 'schema' in config:
            name = '{}.{}'.format(config['schema'], name)
        self.override_execute_batch_elems = config.get('execute_batch_num_elems')
        self.active_insert = name

    def fetch_batch(self, batch_size):
        if not self.active_cursor:
            raise Exception("No active cursor!")
        keys = [x[0] if isinstance(x, tuple) else x.name for x in self.active_cursor.description]
        return keys, self.active_cursor.fetchmany(batch_size)

    def insert_batch(self, names, batch):
        self.insert_batch_(names, batch)
        self.conn.commit()

    def close(self):
        if self.active_cursor:
            self.active_cursor.close()
        self.conn.close()

add_engine_factory(DBAPIEngine)