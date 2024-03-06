STRATEGIES = {}

def export_strategy(site_official):
    def decorator(cls):
        STRATEGIES[(site_official, cls.__name__)] = cls
        return cls
    return decorator
