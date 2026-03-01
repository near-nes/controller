# from complete_control.neural.NestClient import NESTClient

_nest = None
_initialized = False


def initialize_nest(coordinator_type=None):
    global _nest, _initialized
    if _initialized:
        return  # Already initialized
    import nest

    _nest = nest

    _initialized = True


def get_nest():
    if not _initialized:
        raise RuntimeError("Call initialize_nest() first!")
    return _nest


class NESTModule:
    def __getattr__(self, name):
        return getattr(get_nest(), name)


nest = NESTModule()
