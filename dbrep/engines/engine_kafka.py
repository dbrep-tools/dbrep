from asyncio import base_tasks
from asyncore import poll
from collections import Counter
import copy
import functools
from multiprocessing import active_children
from multiprocessing.dummy import Value
import confluent_kafka

from .engine_base import BaseEngine
from . import add_engine_factory
from ..conversions import create_conversion



class KafkaEngine(BaseEngine):
    id = 'kafka'

    @staticmethod
    def get_latest_messages(topic, config):
        import confluent_kafka
        consumer = confluent_kafka.Consumer(config)
        try:
            consumer.subscribe([topic])
            topic_meta = consumer.list_topics().topics[topic]
            partitions = [confluent_kafka.TopicPartition(topic, k) for k in topic_meta.partitions]
            for p in partitions:
                (lo, ho) = consumer.get_watermark_offsets(p)
                p.offset = max(lo, ho - 1)
            consumer.assign(partitions)
            msgs = consumer.consume(len(topic_meta.partitions), timeout=1.0)
        finally:
            consumer.close()
        return [x for x in msgs if x is not None and x.error() is None]

    @staticmethod
    def restart_from_beginning(consumer, topic):
        topic_meta = consumer.list_topics().topics[topic]
        consumer.poll(1.0) #poll to restore offsets
        partitions = [confluent_kafka.TopicPartition(topic, k) for k in topic_meta.partitions]
        for p in partitions:
            p.offset = confluent_kafka.OFFSET_BEGINNING
        consumer.assign(partitions)

    def flatten_configs_(self, *configs):
        cfg = copy.deepcopy(self.kafka_config_)
        for c in configs:
            cfg.update(c)
        return cfg 

    def activate_consumer_(self, topic, *configs):
        if self.active_consumer_ is not None:
            self.active_consumer_.close()
            self.active_consumer_ = None
        cfg = self.flatten_configs_(*configs)
        self.active_consumer_ = confluent_kafka.Consumer(cfg)
        self.active_consumer_.subscribe([topic])
        self.active_topic_ = topic

    def activate_producer_(self, topic, *configs):
        if self.active_producer_ is not None:
            self.active_producer_ = None
        cfg = self.flatten_configs_(*configs)
        remove = ['group.id', 'max.poll.interval.ms']
        for r in remove:
            if r in cfg:
                del cfg[r]
        self.active_producer_ = confluent_kafka.Producer(cfg)
        self.active_topic_ = topic
    
    def __init__(self, connection_config):
        self.kafka_config_ = copy.deepcopy(connection_config['kafka'])
        self.conversion_ = create_conversion(connection_config['format'], connection_config.get('format-config', {}))
        self.active_consumer_ = None
        self.active_producer_ = None
        self.default_timeout_ = 10.0

    def get_latest_rid(self, config):
        override = {
            'auto.offset.reset': 'latest',
            'enable.auto.commit': False
        } 
        msgs = KafkaEngine.get_latest_messages(config['topic'], self.flatten_configs_(config.get('kafka', {}), override))
        if msgs is None or len(msgs) == 0:
            return None
        objs = [self.conversion_.from_bytes(x.value()) for x in msgs]
        return max([x[config['rid']] for x in objs])

    def begin_incremental_fetch(self, config, min_rid):
        override = {
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        } 
        self.activate_consumer_(config['topic'], config.get('kafka', {}), override)
        self.timeout_ = config.get('timeout', self.default_timeout_)

    def begin_full_fetch(self, config):
        override = {
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        } 
        self.activate_consumer_(config['topic'], config.get('kafka', {}), override)
        KafkaEngine.restart_from_beginning(self.active_consumer_, config['topic'])
        self.timeout_ = config.get('timeout', self.default_timeout_)

    def begin_insert(self, config):
        self.activate_producer_(config['topic'], config.get('kafka', {}))

    def fetch_batch(self, batch_size):
        if not self.active_consumer_:
            raise Exception("No active consumer!")
        objs = []
        msgs = self.active_consumer_.consume(batch_size, self.timeout_)
        if len(msgs) > 0:
            self.active_consumer_.commit(asynchronous=False)
        errs = [x.error() for x in msgs if x is not None and x.error() is not None]
        objs = [self.conversion_.from_bytes(x.value()) for x in msgs if x is not None and x.error() is None]

        keys = list(Counter([k for x in objs for k in x.keys()]).keys())
        batch = [[obj.get(k) for k in keys] for obj in objs]

        return keys, batch

    def insert_batch(self, names, batch):
        if self.active_producer_ is None:
            raise Exception("No active producer!")
        for row in batch:
            if len(names) != len(row):
                raise ValueError('Length of keys is not the same as length of values in row!')
            obj = dict(zip(names, row))
            bts = self.conversion_.to_bytes(obj)
            self.active_producer_.produce(self.active_topic_, bts)
        self.active_producer_.flush()       

    def close(self):
        if self.active_consumer_ is not None:
            self.active_consumer_.close()
            self.active_consumer_ = None

add_engine_factory(KafkaEngine)