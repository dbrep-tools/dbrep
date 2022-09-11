class BasePerformanceTest:
    def __init__(self):
        pass

    def setup(self):
        raise NotImplementedError("BasePerformanceTest is not implemented!")

    def cleanup(self):
        raise NotImplementedError("BasePerformanceTest is not implemented!")

    def reset(self):
        raise NotImplementedError("BasePerformanceTest is not implemented!")