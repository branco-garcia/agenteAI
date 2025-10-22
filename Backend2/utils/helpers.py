def serializar_objeto_simple(obj):
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, list):
        return [serializar_objeto_simple(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: serializar_objeto_simple(value) for key, value in obj.items()}
    elif hasattr(obj, '__dict__'):
        result = {}
        for key, value in obj.__dict__.items():
            if not key.startswith('_'):
                try:
                    result[key] = serializar_objeto_simple(value)
                except:
                    result[key] = str(value)
        return result
    else:
        return str(obj)