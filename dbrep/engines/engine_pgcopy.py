
import csv
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

        cw = csv.writer(buffer, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        cw.writerows(batch)
        #template = ';'.join(['%s']*len(names))
        buffer.seek(0)

        query = """
        copy {} from stdin csv delimiter ';'
        """.format(self.active_insert)

        with self.conn.cursor() as cur:
            cur.copy_expert(query, buffer)
        self.conn.commit()

add_engine_factory(PGCopyEngine.id, PGCopyEngine)