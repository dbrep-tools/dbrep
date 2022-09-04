class InvalidTestError(Exception):
    pass

class InvalidTestConfigError(InvalidTestError):
    pass

class InvalidTestConnectionError(InvalidTestError):
    pass

class InvalidTestDriverError(InvalidTestError):
    pass

class InvalidTestRuntimeError(InvalidTestError):
    pass

class ReplicationError(Exception):
    pass

class FailedReplicationError(ReplicationError):
    pass

class BadReplicationError(ReplicationError):
    pass