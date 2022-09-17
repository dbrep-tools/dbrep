import copy
import functools
import confluent_kafka

from .engine_base import BaseEngine
from .. import add_engine_factory


class KafkaEngine(BaseEngine):
    id = 'kafka'
    
    def __init__(self, connection_config):
        self.kafka_config_ = copy.deepcopy(connection_config['kafka'])
        self.format_ = connection_config['format']
        if self.format_ not in ('JSONRow',):
            raise 

    def get_latest_rid(self, config):
        
        return None

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
            raise Exception()
        keys = [x[0] if isinstance(x, tuple) else x.name for x in self.active_cursor.description]
        return keys, self.active_cursor.fetchmany(batch_size)

    def insert_batch(self, names, batch):
        self.insert_batch_(names, batch)
        self.conn.commit()

    def close(self):
        if self.active_cursor:
            self.active_cursor.close()
        self.conn.close()

add_engine_factory(DBAPIEngine.id, DBAPIEngine)