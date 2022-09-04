
import copy

class TestDriverSQLAlchemy:
    def __init__(self, config):
        import sqlalchemy
        self.engine = sqlalchemy.create_engine(config['conn-str'])
        self.engine.connect().close() #raise exception if can not connect
        self.config = copy.deepcopy(config)

    def execute(self, query):
        self.engine.execute(query)

    def fetchall(self, config):
        cursor = self.engine.execute('select * from {}'.format(config['table']))
        keys = cursor.keys()
        data = cursor.fetchall()
        cursor.close() 
        return list(keys), [list(x) for x in data]

    def dispose(self):
        self.engine.dispose()