from .base_test import BasePerformanceTest
import sqlalchemy
import logging
logger = logging.getLogger(__name__)

class SQLPerformanceTest(BasePerformanceTest):
    @staticmethod
    def try_drop(engine, table):
        try:
            engine.execute('drop table {}'.format(table))
        except Exception as e:
            logger.error('Failed to drop table {}'.format(table))        

    def __init__(self, src_conn_str, dst_conn_str, src_tables = [], dst_tables = []) -> None:
        super().__init__()
        self.src_conn_str = src_conn_str
        self.dst_conn_str = dst_conn_str
        self.src_engine = sqlalchemy.create_engine(src_conn_str)
        self.dst_engine = sqlalchemy.create_engine(dst_conn_str)
        self.src_conn = self.src_engine.connect()
        self.dst_conn = self.dst_engine.connect()
        self.src_tables = src_tables
        self.dst_tables = dst_tables

    def cleanup(self):
        self.src_conn.close()
        self.dst_conn.close()
        for t in self.src_tables:
            SQLPerformanceTest.try_drop(self.src_engine, t)
        for t in self.dst_tables:
            SQLPerformanceTest.try_drop(self.dst_engine, t)
