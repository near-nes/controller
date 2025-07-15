from neural.NestClient import NESTClient

_nest = None
_initialized = False


def initialize_nest(coordinator_type):
    global _nest, _initialized
    if _initialized:
        return  # Already initialized

    if coordinator_type == "MUSIC":
        import nest

        _nest = nest
    else:
        _nest = NESTClient

    _initialized = True


def get_nest():
    if not _initialized:
        raise RuntimeError("Call initialize_nest() first!")
    return _nest


class NESTModule:
    def __getattr__(self, name):
        return getattr(get_nest(), name)


nest = NESTModule()
