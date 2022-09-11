from base.sql import SQLPerformanceTest
import dbrep
import dbrep.replication
from dbrep.engines.engine_sqlalchemy import SQLAlchemyEngine
from dbrep.engines.engine_dbapi import DBAPIEngine
from dbrep.engines.engine_pgcopy import PGCopyEngine
import pandas as pd
import sqlalchemy
import time
import sys

class SingleColSQLTest(SQLPerformanceTest):
    def __init__(self, src_conn_str, dst_conn_str, src_type, dst_type, num_rows, values) -> None:
        self.src_table = 'test_single_col_src'
        self.dst_table = 'test_single_col_dst'
        super().__init__(src_conn_str, dst_conn_str, src_tables=[self.src_table], dst_tables=[self.dst_table])
        self.src_type = src_type
        self.dst_type = dst_type
        self.num_rows = num_rows
        self.values = values

    def setup(self):
        try:
            self.src_conn.execute('create table {} (rid serial, col {})'.format(self.src_table, self.src_type))
            self.dst_conn.execute('create table {} (rid integer, col {})'.format(self.dst_table, self.dst_type))
        except Exception as e:
            self.cleanup()
            
        batch_size = 100
        for k in range(0, self.num_rows, batch_size):
            act_size = min(k+batch_size, self.num_rows) - k
            act_vals = ['({})'.format(self.values[i % len(self.values)]) for i in range(act_size)]
            query = 'insert into {} (col) values {}'.format(self.src_table, ','.join(act_vals))
            self.src_conn.execute(query)

    def reset(self):
        self.dst_conn.execute('truncate table {}'.format(self.dst_table))


def run_dbrep_sqla_full_copy(test):
    src = SQLAlchemyEngine({'conn-str':test.src_conn_str})
    dst = SQLAlchemyEngine({'conn-str':test.dst_conn_str})
    dbrep.replication.full_copy(src, dst, {
        'src': {'table': test.src_table, 'rid': 'rid', 'batch_size': 10000},
        'dst': {'table': test.dst_table, 'rid': 'rid', 'batch_size': 10000}
    })


def run_dbrep_sqla_increment(test):
    src = SQLAlchemyEngine({'conn-str':test.src_conn_str})
    dst = SQLAlchemyEngine({'conn-str':test.dst_conn_str})
    dbrep.replication.incremental_update(src, dst, {
        'src': {'table': test.src_table, 'rid': 'rid', 'batch_size': 10000},
        'dst': {'table': test.dst_table, 'rid': 'rid', 'batch_size': 10000}
    })



def run_dbrep_dbapi_full_copy(test):
    src_desc, src_conn1 = test.src_conn_str.split('://')
    src_cred, src_db1 = src_conn1.split('@')
    dst_desc, dst_conn1 = test.dst_conn_str.split('://')
    dst_cred, dst_db1 = dst_conn1.split('@')

    src = DBAPIEngine({'conn-str':test.src_conn_str, 'driver': src_desc.split('+')[-1],
        'user': src_cred.split(':')[0], 'password': src_cred.split(':')[1],
        'host': src_db1.split('/')[0].split(':')[0], 'database': src_db1.split('/')[-1]
    })
    dst = DBAPIEngine({'conn-str':test.dst_conn_str, 'driver': dst_desc.split('+')[-1],
        'user': dst_cred.split(':')[0], 'password': dst_cred.split(':')[1],
        'host': dst_db1.split('/')[0].split(':')[0], 'database': dst_db1.split('/')[-1]
    })
    dbrep.replication.full_copy(src, dst, {
        'src': {'table': test.src_table, 'rid': 'rid', 'batch_size': 10000},
        'dst': {'table': test.dst_table, 'rid': 'rid', 'batch_size': 10000}
    })


def run_dbrep_pgcopy_full_copy(test):
    src_desc, src_conn1 = test.src_conn_str.split('://')
    src_cred, src_db1 = src_conn1.split('@')
    dst_desc, dst_conn1 = test.dst_conn_str.split('://')
    dst_cred, dst_db1 = dst_conn1.split('@')

    src = DBAPIEngine({'conn-str':test.src_conn_str, 'driver': src_desc.split('+')[-1],
        'user': src_cred.split(':')[0], 'password': src_cred.split(':')[1],
        'host': src_db1.split('/')[0].split(':')[0], 'database': src_db1.split('/')[-1]
    })
    dst = PGCopyEngine({'conn-str':test.dst_conn_str, 'driver': dst_desc.split('+')[-1],
        'user': dst_cred.split(':')[0], 'password': dst_cred.split(':')[1],
        'host': dst_db1.split('/')[0].split(':')[0], 'database': dst_db1.split('/')[-1]
    })
    dbrep.replication.full_copy(src, dst, {
        'src': {'table': test.src_table, 'rid': 'rid', 'batch_size': 10000},
        'dst': {'table': test.dst_table, 'rid': 'rid', 'batch_size': 10000}
    })

def run_pandas(test):
    src_engine = sqlalchemy.create_engine(test.src_conn_str)
    dst_engine = sqlalchemy.create_engine(test.dst_conn_str)
    df = pd.read_sql(test.src_table, src_engine)
    df[['col']].to_sql(test.dst_table, dst_engine, if_exists='append', index=False)


if __name__ == '__main__':
    test = SingleColSQLTest(
        'postgresql+psycopg2://postgres:postgres@postgres:5432/postgres',
        'postgresql+psycopg2://postgres:postgres@postgres:5432/postgres',
        'varchar(40)',
        'varchar(40)',
        1000000,
        ["'abcdefghj'", "'1234567'"]
    )
    print('Running setup...')
    test.setup()
    
    if len(sys.argv) >= 2 and sys.argv[1] == 'setup':
        print('Setup complete.')
    else:
        print('Running reset...')
        test.reset()
        print('Running replication...')
        t0 = time.time()
        run_dbrep_sqla_full_copy(test)
        t1 = time.time()
        print('run_dbrep_sqla_full_copy: {:.2f}'.format(t1-t0))
        
        print('Running reset...')
        test.reset()
        print('Running replication...')
        t0 = time.time()
        run_dbrep_sqla_increment(test)
        t1 = time.time()
        print('run_dbrep_sqla_increment: {:.2f}'.format(t1-t0))
        
        print('Running reset...')
        test.reset()
        print('Running replication...')
        t0 = time.time()
        run_dbrep_dbapi_full_copy(test)
        t1 = time.time()
        print('run_dbrep_dbapi_full_copy: {:.2f}'.format(t1-t0))
        
        print('Running reset...')
        test.reset()
        print('Running replication...')
        t0 = time.time()
        run_dbrep_pgcopy_full_copy(test)
        t1 = time.time()
        print('run_dbrep_pgcopy_full_copy: {:.2f}'.format(t1-t0))
        
        print('Running reset...')
        test.reset()
        print('Running replication...')
        t0 = time.time()
        run_pandas(test)
        t1 = time.time()
        print('run_pandas: {:.2f}'.format(t1-t0))

        test.cleanup()