def get_callables(obj):
    return [key for key, val in obj.__dict__.items() if callable(val)
            and not key.startswith("__")]