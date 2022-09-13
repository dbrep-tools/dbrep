
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
        source = config['table']
        if 'schema' in config:
            source = '{}.{}'.format(config['schema'], config['table'])            
        cursor = self.engine.execute('select * from {}'.format(source))
        keys = cursor.keys()
        data = cursor.fetchall()
        cursor.close() 
        return list(keys), [list(x) for x in data]

    def dispose(self):
        self.engine.dispose()

class TestDriverKafka:
    def __init__(self, config):
        pass

    def execute(self, query):
        pass

    def fetchall(self, config):
        pass

    def dispose(self):
        pass