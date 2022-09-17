
conversions = {}

def add_conversion(factory):
    global conversions
    conversions[factory.id] = factory

def get_conversion(name):
    return conversions[name]