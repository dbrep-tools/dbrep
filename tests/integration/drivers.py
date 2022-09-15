import time
import copy
from multiprocessing.sharedctypes import Value

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
        import confluent_kafka
        import confluent_kafka.admin
        self.kafka_ = confluent_kafka
        self.config_ = copy.deepcopy(config)
        self.config_.update({
            'group.id': 'TestDriver'
        })
        self.admin_ = confluent_kafka.admin.AdminClient(self.config_)
        self.producer_ = confluent_kafka.Producer(self.config_)

    def create_topic_(self, name, **kwargs):
        topic_def = self.kafka_.admin.NewTopic(name, kwargs.get('num_partitions', 3))
        res = self.admin_.create_topics([topic_def])[name]
        while not res.done():
            time.sleep(0.01)
        print(res.exception())

    def delete_topic_(self, name, **kwargs):
        res = self.admin_.delete_topics([name])[name]
        while not res.done():
            time.sleep(0.01)
        print(res.exception())

    def push_topic_(self, topic, **kwargs):
        self.producer_.produce(topic, kwargs.get('msg'), kwargs.get('key'))
        self.producer_.flush()

    def execute(self, query):
        fquery = query
        if isinstance(query, str):
            fquery = {'cmd': query}
        if not isinstance(fquery, dict):
            raise TypeError('Query should be str or dict, but got {}'.format(type(query)))
        cmd_raw = fquery['cmd'].lower()
        cmd, topic = [x.strip() for x in cmd_raw.split(' ')]
        cmd = cmd.lower()
        if cmd == 'create':
            return self.create_topic_(topic, **fquery)
        elif cmd == 'delete':
            return self.delete_topic_(topic, **fquery)
        elif cmd == 'push':
            return self.push_topic_(topic, **fquery)
        else:
            raise ValueError('Unsupported command: {}'.format(cmd))
    
            

    def fetchall(self, config):
        conf = copy.deepcopy(self.config_)
        conf.update({
            'enable.auto.commit': False,
            'auto.offset.reset': 'earliest'
        })
        consumer = self.kafka_.Consumer(conf)
        try:
            consumer.subscribe([config['topic']])
            raw = consumer.consume(num_messages=config.get('min_msg', 1))
            while True:
                msg = consumer.poll(0.1)
                if msg is None:
                    break
                raw.append(msg)
        finally:
            consumer.close()
        return raw

    def dispose(self):
        pass