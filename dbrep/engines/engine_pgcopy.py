
from io import StringIO
from re import template

from .engine_dbapi import DBAPIEngine
from .. import add_engine_factory

class PGCopyEngine(DBAPIEngine):
    id = 'pgcopy'
    
    def __init__(self, connection_config):     
        print('Warning! This is experimental feature! Does not work with timestamps, dates, special characters in strings!')
        connection_config['driver'] = 'psycopg2'
        super().__init__(connection_config)

    def insert_batch(self, names, batch):
        buffer = StringIO()

        template = ';'.join(['%s']*len(names))

        with self.conn.cursor() as cur:
            body = [cur.mogrify(template, x).decode('utf8') for x in batch]
            buffer.write('\n'.join(body))
            buffer.seek(0)

            cur.copy_from(buffer, self.active_insert, sep=";", null='NULL')
        self.conn.commit()

add_engine_factory(PGCopyEngine.id, PGCopyEngine)