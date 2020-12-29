import pythoncom
import win32com.client
import ctypes
import abc
import psutil
import os
import time
from enum import Enum
from pydis_broker.sync.cipher import AESCipher
from sl4p import *
log = sl4p.getLogger(__file__)


class CpBaseEvent:
    @abc.abstractmethod
    def set_params(self, comObj, event_name, callbackInst=None, **kwargs):
        pass

    @abc.abstractmethod
    def OnReceived(self):
        pass


class CpComUtil:
    @staticmethod
    def get_comobj(trpath):
        _comobj = win32com.client.Dispatch(trpath)
        return _comobj

    @staticmethod
    def get_event_comobj(trpath, event_name, EventClass: CpBaseEvent, callbackInst=None, **kwargs):
        obj = CpComUtil.get_comobj(trpath)
        handler = win32com.client.WithEvents(obj, EventClass)
        handler.set_params(obj, event_name, callbackInst, **kwargs)
        return obj


class CpTrTypeE(Enum):
    ORDER = 0
    QUERY = 1
    REAL = 2


class CpSession:
    _cpCybos = None
    _cpTdUtil = None
    _inst = None

    dib_procstr = 'DibServer'
    cp_procstr = 'CpStart'
    aos_procstr = 'aos'

    @classmethod
    def create_inst_if_none(cls):
        if cls._inst is None:
            cls._inst = cls()

    @property
    def cpCybos(self):
        if CpSession._cpCybos is None:
            CpSession._cpCybos = CpComUtil.get_comobj('CpUtil.CpCybos')
        return CpSession._cpCybos

    @property
    def cpTdUtil(self):
        if CpSession._cpTdUtil is None:
            CpSession._cpTdUtil = CpComUtil.get_comobj('CpTrade.CpTdUtil')
        return CpSession._cpTdUtil

    @classmethod
    def is_granted(cls):
        # 프로세스가 관리자 권한으로 실행 여부
        if ctypes.windll.shell32.IsUserAnAdmin():
            log.debug('정상: 관리자권한으로 실행된 프로세스입니다.')
            return True
        else:
            log.error('오류: 일반권한으로 실행됨. 관리자 권한으로 실행해 주세요')
            return False

    @classmethod
    def tick(cls, check_type_str, wait_divratio=1, force_wait=False):
        """
        Check limit request time and count. Then wait required time.
        Args:
            check_type <str>: "ORDER" or "QUERY" or "REAL"
        No Returns
        """
        check_type = CpTrTypeE[check_type_str]

        cls.create_inst_if_none()
        remainTime = cls._inst.cpCybos.LimitRequestRemainTime
        remainCount = cls._inst.cpCybos.GetLimitRemainCount(check_type.value)  # 시세 제한\
        log.debug(f'tick {check_type.name} remains:  cnt {remainCount},  {remainTime/1000:.2f} s')

        if force_wait:
            log.debug(f'tick {check_type.name} ~  do force_wait sleep()  {remainTime/1000:.2f} s  .... ')
            time.sleep(remainTime / 1000)
            remainTime = cls._inst.cpCybos.LimitRequestRemainTime
            remainCount = cls._inst.cpCybos.GetLimitRemainCount(check_type.value)  # 시세 제한

        if remainCount <= 0:
            while remainCount <= 0:
                time.sleep(remainTime / (1000*wait_divratio))
                remainCount = cls._inst.cpCybos.GetLimitRemainCount(check_type.value)  # 시세 제한
                remainTime = cls._inst.cpCybos.LimitRequestRemainTime

        return remainCount, remainTime

    @classmethod
    def tick_order(cls, wait_divratio=3):
        return cls.tick(CpTrTypeE.ORDER.name, wait_divratio)
    @classmethod
    def tick_query(cls, wait_divratio=3):
        return cls.tick(CpTrTypeE.QUERY.name, wait_divratio)
    @classmethod
    def tick_real(cls, wait_divratio=3):
        return cls.tick(CpTrTypeE.REAL.name, wait_divratio)

    @classmethod
    def is_proc_running(cls, proc_name):
        for proc in psutil.process_iter():
            try:
                if proc_name in proc.name():
                    return True
            except:
                continue
        return False


    @classmethod
    def run_cp(cls, secConfig):
        if not cls.is_proc_running(cls.cp_procstr):
            os.system('@echo off && path C:\CREON\STARTER\; '
                      '&& start coStarter.exe /prj:cp /id:{} /pwd:{} /pwdcert:{} /autostart'.format(
                AESCipher(bytes(secConfig.key)).decrypt(secConfig.id).decode('utf-8'),
                AESCipher(bytes(secConfig.key)).decrypt(secConfig.pwd).decode('utf-8'),
                AESCipher(bytes(secConfig.key)).decrypt(secConfig.cert_pwd).decode('utf-8'), )
            )
            log.info('run CreonPlus.exe ...')
        else:
            log.warn('CreonPlus.exe is already running !!')


    @classmethod
    def terminate_cp(cls):
        _term = 0
        if cls.is_proc_running(cls.dib_procstr):
            os.system('TASKKILL /F /T /IM "DibServer.exe"')
            log.info('DibServer terminated')
            _term += 1
        if cls.is_proc_running(cls.cp_procstr):
            os.system('TASKKILL /F /T /IM "CpStart.exe"')
            os.system('wmic process where name="CpStart.exe" call terminate')
            log.info('CpStart terminated')
            _term += 1
        if cls.is_proc_running(cls.aos_procstr):
            for _proc in ['aosrts.exe', 'aostray.exe', 'mf40nt.exe']:
                os.system(f'TASKKILL /F /T /IM "{_proc}"')
                os.system(f'wmic process where name="{_proc}" call terminate')
            log.info('SecurityAos terminated')
            _term += 1

        if _term == 0:
            log.warn('Both DibServer and CpStart were not running !!  Terminating skipped.')
            return False
        else:
            return True


    @classmethod
    def is_available(cls):
        cls.create_inst_if_none()
        # 연결 여부 체크
        if (cls._inst.cpCybos.IsConnect == 0):
            log.error("PLUS가 정상적으로 연결되지 않음. ")
            return False

        # 주문 관련 초기화
        if (cls._inst.cpTdUtil.TradeInit(0) != 0):
            log.error("주문 초기화 실패")
            return False

        return True





#https://day-think.tumblr.com/post/88186167106/cybosplus-%EB%9E%91-python-%EC%82%AC%EC%9A%A9-%EC%9D%BC%EB%B0%98%ED%99%94
# import new
class CpClass:
    cnt = 0

    @classmethod
    def Bind(self, usr_obj):
        # handler = new.classobj('CpClass_%s' % CpClass.cnt, (CpClass,), {})
        handler = type('CpClass_%s' % CpClass.cnt, (CpClass,), {})
        handler.idx = CpClass.cnt
        handler.com_obj = win32com.client.Dispatch(usr_obj.com_str)
        handler.usr_obj = usr_obj
        win32com.client.WithEvents(handler.com_obj, handler)
        CpClass.cnt = CpClass.cnt + 1
        return handler

    @classmethod
    def Request(cls, api_tx_msg):
        # cls.received = False
        cls.usr_obj.request(cls.com_obj, api_tx_msg)

    @classmethod
    def OnReceived(cls):
        # cls.received = True
        cls.usr_obj.response(cls.com_obj)


class StkMst:
    def __init__(self):
        # COM 연결하는데 필요한 문자열
        self.com_str = "dscbo1.StockMst"

    # request 메소드와 첫번째 인자로 com_obj가 필요
    def request(self, com_obj, api_tx_msg):
        com_obj.SetInputValue(0, "A000660")
        self.received = False
        com_obj.Request()
        log.info('rq [%s]'%self.__class__.__name__)

    # 이벤트 발생시  첫번쨰 인자로 com_obj가 필요
    def response(self, com_obj):
        log.info('rp [%s]'%self.__class__.__name__)
        log.info(com_obj.GetHeaderValue(1))

        self.received = True

class MarketEye:
    def __init__(self):
        self.com_str = 'CpSysDib.MarketEye'
        self.req_fields = [
            0, 2, 3, 4, 5,  # shcode, 대비부호, 전일대비, 현재가, open
            6, 7, 8, 9, 10,  # high, low, ask1, bid1, vol
            11, 12, 13, 14, 15,  # trd_val, 장구분, ask_totvol, bid_totvol, ask1_vol
            16, 17, 20, 23, 24,  # bid1_vol, itemname, listed_sh, adj_close_yesterday, vol_power
            28, 29, 30, 31, 33,  # 예상체결가, 예상가대비, 예상가대비부호, 예상체결수량, 상한가
            34, 38, 42, 43, 48,  # 하한가, out_price, out_ask1, out_bid1, out_ask1_vol
            49, 53, 54, 57, 76,  # out_bid1_vol, out_exflag, out_predprice, out_predvol, 유보율
            109,  # 분기유보율
        ]

        self.req_keys = [
            'item', 'sign', 'dprc_l1d', 'price', 'open',
            'high', 'low', 'ask1', 'bid1', 'vol',
            'trd_val', 'exflag', 'ask_totvol', 'bid_totvol', 'ask1_vol',
            'bid1_vol', 'itemname', 'listed_sh', 'close_l1d', 'vol_power',
            'predprice', 'preddprc', 'predsign', 'predvol', 'uplmtprc',
            'dnlmtprc', 'out_price', 'out_ask1', 'out_bid1', 'out_ask1_vol',
            'out_bid1_vol', 'out_exflag', 'out_predprice', 'out_predvol', 'reserve_ratio',
            'reserve_ratio_q',
        ]

    def request(self, com_obj, api_tx_msg):
        self.api_tx_msg = api_tx_msg
        com_obj.SetInputValue(0, self.req_fields)
        com_obj.SetInputValue(1, api_tx_msg['shcode_li'])

        self.received = False
        com_obj.Request()
        log.info('rq [%s]'%self.__class__.__name__)

    def response(self, com_obj):
        log.info('rp [%s]'%self.__class__.__name__)
        data_li = list()
        for i in range(len(self.api_tx_msg['shcode_li'])):
            d = dict()
            for ki, kv in enumerate(self.req_keys):
                d[kv] = com_obj.GetDataValue(ki, i)
            data_li.append(d)

        self.data_li = data_li
        self.received = True

    def fetch_response(self):
        return self.data_li


def th_price_listitem(itemlist, reslist):
    pythoncom.CoInitializeEx(0)
    pythoncom.CoInitialize()


    # remain_cnt, wait_ms = CpSession.tick_query()
    # time.sleep(1 + wait_ms//1000)


    print(f"itemlist ({len(itemlist)}), {itemlist[0]}")
    mkteye = MarketEye()
    cpeye = CpClass.Bind(mkteye)
    cpeye.Request({'shcode_li': itemlist})

    while not mkteye.received:
        pythoncom.PumpWaitingMessages()
        # log.info(f'r` {mkteye.received}')
        time.sleep(0.02)
    log.info(f'received: {mkteye.received}')
    res = mkteye.fetch_response()
    log.info(f'data_li: {res[:5]}')

    if isinstance(reslist, list):
        reslist.append(res)
    elif isinstance(reslist, mp.Queue.__class__):
        reslist.put(res)
    #pythoncom.CoUninitialize()
    return


import numpy as np
import threading as mth
import multiprocessing as mp
@sl4p_time()   # 5.7454s,  # 5.7404s
def mth_price_listitem(itemlist, nth=5):
    chunks = np.array_split(itemlist, nth)
    reslist = list()

    _th_list = [mth.Thread(target=th_price_listitem, args=(chunks[i], reslist,)) for i in range(nth)]
    print(_th_list)
    for _th in _th_list:
        _th.start()
        print(_th.name+ " ")
        time.sleep(0.05)

    for _th in _th_list:
        _th.join(3)

    return reslist


@sl4p_time()
def mp_price_listitem(itemlist, nth=5):
    chunks = np.array_split(itemlist, nth)
    resmpq = list()
    mpq = mp.Queue()

    _th_list = [mp.Process(target=th_price_listitem, args=(chunks[i], mpq,)) for i in range(nth)]
    print(_th_list)
    for _pr in _th_list:
        _pr.start()
        print(_pr.name+ " ")
        time.sleep(0.05)

    for _pr in _th_list:
        _pr.join(3)

    return resmpq





if __name__ == '__main__':
    # CpClass 에 사용자가 정의한 객체를 Binding
    # stkmst = StkMst()
    # cpchart = CpClass.Bind(stkmst)
    # cpchart.Request({})
    # print('requested')
    # # log.info(f'received: {cpchart.received}')
    #
    # while not stkmst.received:
    #     pythoncom.PumpWaitingMessages()
    #     log.info(f'r` {stkmst.received}')
    #     time.sleep(0.5)
    # log.info(f'received: {stkmst.received}')




    # mkteye = MarketEye()
    # cpeye = CpClass.Bind(mkteye)
    # cpeye.Request({'shcode_li': ['A005930', 'A000660', 'A178920']})
    #
    # while not mkteye.received:
    #     pythoncom.PumpWaitingMessages()
    #     log.info(f'r` {mkteye.received}')
    #     time.sleep(0.5)
    # log.info(f'received: {mkteye.received}')
    # log.info(f'data_li: {mkteye.fetch_response()}')
    # 앞에 이렇게 카운트 초기화 요청을 날려주면, 뒤에 MP MTH가 동작 안한다..... 왜 그럴까?)


    # remain_cnt, wait_ms = CpSession.tick_query()
    # time.sleep(1 + wait_ms//1000)



    from pydis_broker.creon_plus.query_tr import CpCodeMgr
    cpCodeMgr = CpCodeMgr.get_instance()
    all_codes = cpCodeMgr.get_all_code_list()


    # reslist = mth_price_listitem(all_codes, 16)
    reslist = mp_price_listitem(all_codes[:1000], 6)  # 프로세스 여는데 시간이 오래걸려서 mth보다 별로이다.

    # reslist = list()
    # th_price_listitem(all_codes, reslist)
    log.info(f"mth_price_listitem reslist ({len(reslist)})")
    exit()