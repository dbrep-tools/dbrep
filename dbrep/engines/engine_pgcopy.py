
from io import StringIO

from .engine_dbapi import DBAPIEngine
from .. import add_engine_factory

class PGCopyEngine(DBAPIEngine):
    id = 'pgcopy'
    
    def __init__(self, connection_config):     
        print('Warning! This is experimental feature!')
        connection_config['driver'] = 'psycopg2'
        super().__init__(connection_config)

    def insert_batch(self, names, batch):
        buffer = StringIO()

        header = ';'.join(names)
        body = [';'.join([str(y) for y in x]) for x in batch]
        buffer.writelines([header] + body)
        buffer.seek(0)

        with self.conn.cursor() as cur:
            cur.copy_from(buffer, self.active_insert, sep=";")
        self.conn.commit()

add_engine_factory(PGCopyEngine.id, PGCopyEngine)