STRATEGIES = {}

def export_strategy(site_official_pascal):
    def decorator(cls):
        STRATEGIES[(site_official_pascal, cls.__name__)] = cls
        return cls
    return decorator
