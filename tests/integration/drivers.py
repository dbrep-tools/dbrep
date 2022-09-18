from collections import Counter
import time
import copy
import errors
from dbrep.conversions import create_conversion
import dbrep.conversions.json_row

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
        self.kafka_module = confluent_kafka
        self.config_ = copy.deepcopy(config['kafka'])
        cfg = copy.deepcopy(self.config_)
        self.config_.update({
            'group.id': 'TestDriver'
        })
        
        if 'max.poll.interval.ms' in cfg:
            del cfg[' max.poll.interval.ms']
        self.admin_ = confluent_kafka.admin.AdminClient(cfg)
        self.producer_ = confluent_kafka.Producer(cfg)
        self.conversion_ = create_conversion(config['format'], config.get('format-config', {}))

    def create_topic_(self, name, **kwargs):
        topic_def = self.kafka_module.admin.NewTopic(name, kwargs.get('num_partitions', 3))
        res = self.admin_.create_topics([topic_def])[name]
        while not res.done():
            time.sleep(0.01)
        if res.exception():
            raise res.exception()

    def delete_topic_(self, name, **kwargs):
        res = self.admin_.delete_topics([name])[name]
        while not res.done() and name in self.admin_.list_topics().topics:
            time.sleep(0.01)
        if res.exception():
            raise res.exception()
        time.sleep(5.0)

    def push_topic_(self, topic, **kwargs):
        self.producer_.produce(topic, self.conversion_.to_bytes(kwargs.get('msg')), kwargs.get('key'))
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
        consumer = self.kafka_module.Consumer(conf)
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
        
        errs = [x.error() for x in raw if x is not None and x.error() is not None]
        objs = [self.conversion_.from_bytes(x.value()) for x in raw if x is not None and x.error() is None]

        keys = list(Counter([k for x in objs for k in x.keys()]).keys())
        batch = [[obj.get(k) for k in keys] for obj in objs]

        return keys, batch

    def dispose(self):
        pass

def make_test_driver(config):
    if 'test-driver' not in config:
        raise errors.InvalidTestConfigError('Connection config should also specify which test-driver to use, but it is missing `test-driver` field!')
    if config['test-driver'] == 'sqlalchemy':
        try:
            return TestDriverSQLAlchemy(config)
        except Exception as e:
            raise errors.InvalidTestDriverError('Failed to create sqlalchemy engine for test driver', e) from e
    elif config['test-driver'] == 'kafka':
        try:
            return TestDriverKafka(config)
        except Exception as e:
            raise errors.InvalidTestDriverError('Failed to create kafka engine for test driver', e) from e
    else:
        raise errors.InvalidTestConfigError('Unexpected test-driver: {}'.format(config['test-driver']))