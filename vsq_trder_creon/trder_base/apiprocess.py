import abc
import multiprocessing as mp
from enum import Enum

class API_PROC_TYPE(Enum):
    NOT_INITED = None
    PROC_REQUEST = 1
    PROC_SUBSCRIBE = 2
    PROC_ALL = 4

class ApiProcess:
    def __init__(self, securityConfig,
                 inReqQ: mp.Queue, subQ: mp.Queue, pushQ: mp.Queue, outMpQ: mp.Queue,
                 process_type: API_PROC_TYPE = API_PROC_TYPE.NOT_INITED):
        self.secConfig = securityConfig

        self.inReqQ = inReqQ
        self.subQ = subQ
        self.pushQ = pushQ
        self.outQ = outMpQ
        self.process_type: API_PROC_TYPE = process_type

    @abc.abstractmethod
    def connect_server(self):
        raise NotImplementedError
    @abc.abstractmethod
    def account_login(self):
        raise NotImplementedError
    @abc.abstractmethod
    def run(self):
        raise NotImplementedError


    @abc.abstractmethod
    def transcript(self):
        raise NotImplementedError
    @abc.abstractmethod
    def request_api(self):
        raise NotImplementedError
    @abc.abstractmethod
    def subscribe_api(self):
        raise NotImplementedError
    @abc.abstractmethod
    def reverse_transcript(self):
        raise NotImplementedError
