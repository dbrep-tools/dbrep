
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

    def __init__(self, connection_config):        
        self.driver_name = connection_config['driver']
        self.driver = importlib.import_module(self.driver_name)
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

    def _execute(self, *args, **kwargs):
        raise NotImplementedError
        try:
            return self.conn.execute(*args, **kwargs)
        except ConnectionError:
            self.conn = self.engine.connect()
            return self.conn.execute(*args, **kwargs)


    def get_latest_rid(self, config):
        query = self.make_query(self.template_select_rid.format(
            src=DBAPIEngine._make_query_from_config(config),
            rid=config['rid']
        ))
        with self.conn.cursor() as cur:
            res = cur.execute(query).fetchall()
        if res is None or len(res) == 0:
            return None
        return res[0][0]

    def begin_incremental_fetch(self, config, min_rid):
        template = self.template_select_inc if min_rid else self.template_select_inc_null
        query = self.make_query(template.format(
            src=DBAPIEngine._make_query_from_config(config),
            rid=config['rid'],
            rid_value=min_rid
        ))
        if self.active_cursor:
            self.active_cursor.close()

        self.active_cursor = self.conn.cursor()
        self.active_cursor.execute(query)

    def begin_full_fetch(self, config):
        query = self.make_query(self.template_select_all.format(
            src=DBAPIEngine._make_query_from_config(config)
        ))
        if self.active_cursor:
            self.active_cursor.close()

        self.active_cursor = self.conn.cursor()
        self.active_cursor.execute(query)

    def begin_insert(self, config):
        name = config['table']
        if 'schema' in config:
            name = '{}.{}'.format(config['schema'], name)
        self.active_insert = 'insert into {}'.format(name)

    def fetch_batch(self, batch_size):
        if not self.active_cursor:
            raise Exception()
        print(self.active_cursor.description)
        raise Exception(self.active_cursor.description)
        keys = list(self.active_cursor.description)
        return keys, self.active_cursor.fetchmany(batch_size)

    def insert_batch(self, names, batch):
        str_names = ','.join(names)
        str_values = ','.join([':{}'.format(x) for x in names])
        print(self.conn.paramstyle)
        with self.conn.cursor() as cur:
            cur.executemany('{} ({}) values ({})'.format(self.active_insert, str_names, str_values), [dict(zip(names, x)) for x in batch])
        self.conn.commit()

    def close(self):
        if self.active_cursor:
            self.active_cursor.close()
        self.conn.close()

add_engine_factory(DBAPIEngine.id, DBAPIEngine)