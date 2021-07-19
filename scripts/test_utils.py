import time
import functools

def timer(function_without_args=None, *args, **kwargs):
    
    # print(type(func_no_args), len(args), len(kwargs))
    precision = {
        's': 1,
        'ms': 1000,
    }
    # Default args
    unit = 'ms'
    rnd = 0
    
    def _decorate(func):
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            diff = (end-start) * precision[unit]
            if rnd:
                diff = round(diff,rnd)
            print(f'\'{func.__name__}\' finished in {diff} {unit}')
            return result
        return wrapper
    
    if function_without_args:
        return _decorate(function_without_args)
    
    if 'unit' in kwargs:
        unit = kwargs['unit']
    if 'round' in kwargs:
        rnd = kwargs['round']
    
    return _decorate