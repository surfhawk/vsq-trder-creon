import multiprocessing as mp
import threading as th
import time

from vsq_trder_creon.trder_base.apiprocess import API_PROC_TYPE
from vsq_trder_creon.trder_base.handler import ApiHandler

from vsq_trder_creon.trder.base_tr import CpSession
from vsq_trder_creon.trder.adaptor_impl import CreonPlusMsgAdaptor
from vsq_trder_creon.trder.apiprocess_impl import CreonPlusApiProcess

from sl4p import *
log = sl4p.getLogger(__file__)


class CreonPlusApiHandler(ApiHandler):
    def __init__(self, securityConfig):
        super().__init__(securityConfig)
        self.name='CreonPlusApiHandler'
        self.adaptor = CreonPlusMsgAdaptor()

        self.apiprocesses_instlist = [
            CreonPlusApiProcess(self.secConfig, self.inReqQ, self.subQ, self.pushQ, self.outQ, API_PROC_TYPE.PROC_ALL),
            # CreonPlusApiProcess(self.secConfig, self.inReqQ, self.subQ, self.pushQ, self.outQ, API_PROC_TYPE.PROC_SUBSCRIBE),
            CreonPlusApiProcess(self.secConfig, self.inReqQ, self.subQ, self.pushQ, self.outQ, API_PROC_TYPE.PROC_REQUEST),
        ]

        self.apiprocesses = [mp.Process(target=self.apiprocesses_instlist[i].run,
                                        daemon=True)
                             for i in range(len(self.apiprocesses_instlist))]

        self.pump_threads = [th.Thread(target=self.pump_insubq_to_subq, daemon=True, ),
                             th.Thread(target=self.pump_pushq_to_outq, daemon=True, )]


        # API 서버 실행
        cpConn = CpSession()
        if not cpConn.is_granted():
            log.error('관리자 권한이 없습니다.')
        if not cpConn.is_proc_running(CpSession.cp_procstr):
            cpConn.run_cp(securityConfig)
            time.sleep(25)
        retry = 0
        while not cpConn.is_available():
            retry += 1
            if retry > 7:
                log.error(f'Creon+ 서버 통신 실패. 재시도 횟수 제한 도달 !! ({retry})')
                return

            log.warn(f'Creon+ 서버 통신 실패. 대기 후 재확인 ... ({retry})')
            time.sleep(8)


        log.info('Creon+ 서버 통신 확인 완료.')
        # TODO: 더미 요청 한번 해줍시다 api handler에서...


    def terminate(self):
        super().terminate()
        CpSession.terminate_cp()

    # TODO: impl
    def pump_insubq_to_subq(self, loop_delay_sec=0.05):
        return

    # TODO: impl
    def pump_pushq_to_outq(self, loop_delay_sec=0.05):
        return

