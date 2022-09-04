
from asyncio.log import logger
import functools
import logging
from typing import Callable

logger = logging.getLogger(__name__)

def push_batch(engine, names, data, batch_size):
    for off in range(0, len(data), batch_size):
        batch = data[off:(off + batch_size)]
        logger.debug('Pushing dst-batch [{}:{}] of size {}'.format(off, min(len(batch), off+batch_size), len(batch)))
        engine.insert_batch(names, batch)
        logger.debug('Pushed dst-batch [{}:{}] of size {}'.format(off, min(len(batch), off+batch_size), len(batch)))

def pull_batch(engine, batch_size):
    logger.debug('Pulling src-batch')
    names, batch = engine.fetch_batch(batch_size)
    logger.debug('Pulled src-batch of size {}'.format(len(batch)))
    return names, batch

def run_pull_push(src_engine, dst_engine, src_batch_size = 1000, dst_batch_size = 1000):
    counter = 0
    while True:
        names, data = pull_batch(src_engine, src_batch_size)
        if data is None or len(data) == 0:
            return
        push_batch(dst_engine, names, data, dst_batch_size)
        counter += 1
        logging.info('Processed {} batch of size {}.'.format(counter, len(data)))

def full_refresh(src_engine, dst_engine, config):
    logger.info('Starting replication.')
    src_engine.begin_full_fetch(config['src'])
    dst_engine.begin_insert(config['dst'])        
    run_pull_push(src_engine, dst_engine, config['src'].get('batch_size', 1000), config['dst'].get('batch_size', 1000))        
    logger.info('Replication finished.')

def incremental_update(src_engine, dst_engine, config):
    logger.debug('Making request to get <src> latest rid...')
    src_rid = src_engine.get_latest_rid(config['src'])
    if src_rid is None:
        raise NotImplemented

    logger.debug('Making request to get <dst> latest rid...')
    dst_rid = dst_engine.get_latest_rid(config['dst'])

    logger.info('Latest rids: <src>={}, <dst>={}'.format(src_rid, dst_rid))
    logger.info('Starting replication.')
    while not dst_rid or dst_rid < src_rid:
        src_engine.begin_incremental_fetch(config['src'], dst_rid)
        dst_engine.begin_insert(config['dst'])        
        run_pull_push(src_engine, dst_engine, config['src'].get('batch_size', 1000), config['dst'].get('batch_size', 1000))

        logger.info('Finished sync. Updating <dst> rid...')
        dst_rid = dst_engine.get_latest_rid(config['dst'])
        logger.info('Latest rids: <src>={} (old), <dst>={} (updated)'.format(src_rid, dst_rid))
    logger.info('Replication finished.')