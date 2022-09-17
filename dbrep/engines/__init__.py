engine_factories = {}

def add_engine_factory(factory):
    global engine_factories
    engine_factories[factory.id] = factory

def create_engine(name, config):
    global engine_factories
    if name not in engine_factories:
        raise KeyError("Uknonwn engine: {}".format(name))
    return engine_factories[name](config)