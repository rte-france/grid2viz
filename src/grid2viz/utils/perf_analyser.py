import inspect
import time
import functools
import logging

logger = logging.getLogger(__name__)


def whoami():
    return inspect.stack()[1][3]


def timeit(func):
    """
    logging function execute duration.
    """
    timed_method_name = str(func).split(' ')[1]  # _name_ not working so we parse the function id

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_timestamp = time.time()
        result = func(*args, **kwargs)
        logger.warning('{method} : {duration}'.format(method=timed_method_name, duration=time.time() - start_timestamp))
        return result

    return wrapper

