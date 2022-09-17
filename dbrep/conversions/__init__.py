
conversions = {}

def add_conversion(factory):
    global conversions
    conversions[factory.id] = factory

def create_conversion(name, config):
    global conversions
    return conversions[name](config)