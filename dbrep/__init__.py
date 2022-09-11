__version__ = '0.0.9'

engine_factories = {}

def add_engine_factory(name, factory):
    global engine_factories
    engine_factories[name] = factory

def init_factory():
    from .engines.engine_sqlalchemy import SQLAlchemyEngine
    from .engines.engine_dbapi import DBAPIEngine
    add_engine_factory(SQLAlchemyEngine.id, SQLAlchemyEngine)
    add_engine_factory(DBAPIEngine.id, DBAPIEngine)

def create_engine(name, config):
    global engine_factories
    if name not in engine_factories:
        raise KeyError("Uknonwn engine: {}".format(name))
    return engine_factories[name](config)

init_factory()