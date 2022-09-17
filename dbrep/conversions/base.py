class BaseFormat:
    id = 'abstract'
    
    def __init__(self, config):
        pass

    def from_bytes(self, bytes):
        raise NotImplemented('BaseFormat.from_bytes not implemented')
    
    def to_bytes(self, object):
        raise NotImplemented('BaseFormat.to_bytes not implemented')