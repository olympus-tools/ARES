"""

"""
import functools

def safely_run(default_return=None, message:str=None, log_level:str=None, cb=None, log=None):
    """ provides try/except functionality via decorator
    
    Args: 
        default_return : default return value in case of failure -> depends on function 
        message[str] : logger message to display in case of failure
        log_level[str] : log level to use
    """
    logger_ = logger if log is None else log

    def wrap(fcn):
        @wraps(fcn)
        def wrapped_f(*args, **kwargs):
            logger_.trace(
                'Safley running function "%s" triggerd from file %s',
                fcn.__name__,
                inspect.getfile(fcn),
            )
            try:
                ret = fcn(*args, **kwargs)
                logger_.trace('Successfully run function "%s"', fcn.__name__)
            except Exception as e:
                lvl = (
                    log_level
                    if log_level is not None and getattr(logger_, log_level.lower())
                    else "ERROR"
                )
                msg = (
                    message
                    if message is not None
                    else f"Error while running function {fcn.__name__}: {e}"
                )
                log_func = getattr(logger_, lvl.lower())
                log_func("%s (log: %s)", msg, uuid.uuid4())
                logger_.debug(
                    "Error while running function %s from file %s",
                    fcn.__name__,
                    inspect.getfile(fcn),
                    exc_info=e,
                )
                if cb is not None:
                    cb(e)
                ret = default_return
            return ret

        return wrapped_f

    return wrap


def wrap(fcn):
    @wraps(fcn)
    def wrapped_f(*args, **kwargs):
        th = PrintJob(interval, fcn, callback)
        signal.signal(signal.SIGTERM, th.signal_handler)
        signal.signal(signal.SIGINT, th.signal_handler)
        th.start()
        try:
            res = fcn(*args, **kwargs)
        except Exception as e:
            th.stop()
            raise e
        th.stop()
        return res

    return wrapped_f

return wrap
