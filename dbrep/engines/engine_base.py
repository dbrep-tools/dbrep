class BaseEngine:
    """
    Base abstract class for engine (connection) to data source/destination (e.g. database, message queue or pubsub).
    Purpose of this class is to provide getter/setter interface.
    """
    id = 'abstract'
    def __init__(self):
        pass

    def get_latest_rid(self, config):
        raise NotImplemented

    def begin_incremental_fetch(self, config, min_rid):
        raise NotImplemented

    def begin_full_fetch(self, config):
        raise NotImplemented

    def truncate(self, config):
        raise NotImplemented

    def create(self, config):
        raise NotImplemented
