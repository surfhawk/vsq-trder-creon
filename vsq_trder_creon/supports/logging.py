import logging

logger = None

#TODO impl
class ImitateLogger:
    pass

try:
    from sl4p import *
    logger = sl4p.getLogger(__file__)
except:
    try:
        # Python default logging
        # TODO impl
        logger = ImitateLogger()
    except:
        # Python default logging
        # TODO impl
        logger = logging.getLogger('vsq_trder_creon__default__')