
import win32com.client
import ctypes
import multiprocessing as mp
import time

from sl4p import *
from pydis_broker.apiprocess import ApiProcess, API_PROC_TYPE
from pydis_broker.creon_plus.adaptor_impl import CreonPlusMsgAdaptor
from pydis_broker.creon_plus.base_tr import CpSession
from pydis_broker.creon_plus.query_tr import CpMarketEye, CpCodeMgr
from pydis_broker.dto import BrokerMessage

log = sl4p.getLogger(__file__, debugprt=1)


class CreonPlusApiProcess(ApiProcess):
    def _get_queryinstance_by_trcode(self, trcode:str):
        class_name = trcode
        if class_name in globals().keys():
            return globals().get(class_name).get_instance()
        else:
            log.error(f"cannot found query class matched with trcode '{trcode}'")
            return None

    def __init__(self, securityConfig, inReqQ: mp.Queue, subQ: mp.Queue, pushQ: mp.Queue,
                 outQ: mp.Queue, process_type: API_PROC_TYPE = API_PROC_TYPE.NOT_INITED):
        super().__init__(securityConfig, inReqQ, subQ, pushQ, outQ, process_type)
        self.adaptor = CreonPlusMsgAdaptor()

    def connect_server(self):
        if not CpSession.is_available():
            log.error("CREON PLUS와 통신이 불가능합니다.")

    def account_login(self):
        self.connect_server()

    def run(self, loop_delay_sec=0.05):
        self.account_login()
        log.info("CreonPlusApiProcess account_login() completed !!")
        CpSession.tick_order()
        CpSession.tick_query()
        log.info("{}".format(CpSession.tick_real()))

        while True:
            try: # ALL 4, REQUEST 1, SUBSCRIBE 2
                if self.process_type.value % 3 == 1 and self.inReqQ.qsize() > 0:
                    workMsg: BrokerMessage = self.inReqQ.get()
                    api_tx_msg = self.adaptor.transcript(workMsg)

                    queryInst = self._get_queryinstance_by_trcode(api_tx_msg['trcode'])
                    resObject = queryInst.request_query(api_tx_msg)

                    api_rx_msg = {'tr_id': api_tx_msg['tr_id']}
                    api_rx_msg['resObject'] = resObject
                    resBrkMsg: BrokerMessage = self.adaptor.reverse_transcript(workMsg, api_rx_msg)

                    self.outQ.put(resBrkMsg)


                elif self.process_type.value % 2 == 0 and self.subQ.qsize() > 0:
                    api_tx_msg = self.subQ.get()
                    tr_id = api_tx_msg['tr_id']
                    pass

                else:
                    time.sleep(loop_delay_sec)


            except:
                log.exception(f"Exception occurred !!!  - XingApiProcess.f`run.while-loop")
                time.sleep(0.5)






    # TODO: 아래는 구현할일 없을 것 같은데, 부모에서 아예 제거할까?
    def transcript(self):
        pass

    def request_api(self):
        pass

    def subscribe_api(self):
        pass

    def reverse_transcript(self):
        pass

