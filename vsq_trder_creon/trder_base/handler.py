import multiprocessing as mp
import abc
import time

from sl4p import *
log = sl4p.getLogger(__file__)

class ApiHandler:
    def __init__(self, securityConfig):
        self.name = 'ApiHandler'
        self.secConfig = securityConfig

        self.inReqQ = mp.Queue()
        self.inSubQ = mp.Queue()
        self.subQ = mp.Queue()
        self.pushQ = mp.Queue()
        self.outQ = mp.Queue()

        self.map_workmsglist_dict = dict()
        self.recv_terminate = False

        self.pump_threads = list()
        self.apiprocesses = list()

    def run(self):
        print(f'apiHandler {self.name} run()')

        for _th in self.pump_threads:
            _th.start()

        for _proc in self.apiprocesses:
            time.sleep(3)
            _proc.start()
            print('apiProcess {} run()'.format(_proc.name))

    def terminate(self):
        log.info(f"terminate {self.name} signal triggered ...")
        self.recv_terminate = True
        for _ap in self.apiprocesses:
            _ap.terminate()
            time.sleep(0.5)
        log.info(f"{self.name}.apiprocesses terminated")

        for _th in self.pump_threads:
            _th.join(1)
        log.info(f"{self.name}.pump_threads terminated")
        log.info(f"{self.name} terminated")


    @abc.abstractmethod
    def pump_insubq_to_subq(self, loop_delay_sec = 0.05):
        pass

    @abc.abstractmethod
    def pump_pushq_to_outq(self, loop_delay_sec=0.05):
        pass


