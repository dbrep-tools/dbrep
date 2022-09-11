import functools
import importlib

from .engine_base import BaseEngine
from .. import add_engine_factory

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

    def __init__(self, connection_config):     
        self.driver_name = connection_config['driver']
        self.driver = importlib.import_module(self.driver_name)
        if self.driver.paramstyle != 'pyformat':
            raise NotImplementedError('Support for drivers with paramstyle other than pyformat is not implemented!')
        self.fn_insert = DBAPIEngine._insert_pyformat

        driver_keywords = ['dsn', 'database', 'user', 'host', 'password']
        driver_params = {k: v for k,v in connection_config.items() if k in driver_keywords}
        driver_params.update(connection_config.get('driver-params', {}))
        self.conn = self.driver.connect(**driver_params)
        self.template_select_inc = 'select * from {src} where {rid} > {rid_value} order by {rid}'
        self.template_select_inc_null = 'select * from {src} order by {rid}'
        self.template_select_all = 'select * from {src}'
        self.template_select_rid = 'select max({rid}) from {src}'
        self.active_cursor = None
        self.active_insert = None
        

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
        self.active_insert = name

    def fetch_batch(self, batch_size):
        if not self.active_cursor:
            raise Exception()
        keys = [x[0] if isinstance(x, tuple) else x.name for x in self.active_cursor.description]
        return keys, self.active_cursor.fetchmany(batch_size)

    def insert_batch(self, names, batch):
        with self.conn.cursor() as cur:
            self.fn_insert(cur, self.active_insert, names, batch)
        self.conn.commit()

    def close(self):
        if self.active_cursor:
            self.active_cursor.close()
        self.conn.close()

add_engine_factory(DBAPIEngine.id, DBAPIEngine)