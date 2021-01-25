from datetime import datetime as dt
from collections import OrderedDict as odict
from vsq_trder_creon.trder.base_tr import CpSession, CpComUtil
import abc
import time
import numpy as np
import pandas as pd


# import pythoncom
# pythoncom.CoInitializeEx(0)
# pythoncom.CoInitialize()

from sl4p import *
log = sl4p.getLogger(__file__)

class CpQueryTr:
    _inst = None

    @classmethod
    def get_instance(cls):
        """
        You must implement __init__() method in inherited class.
        Returns: cls._inst
        """
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    @abc.abstractmethod
    def request_query(self, api_tx_msg: dict):
        pass

    def cast_df_cols(self, df, cols, dtype):
        df.loc[:, cols] = df.loc[:, cols].astype(dtype)
        return df
    def cast_df_int2chr(self, df, cols):
        def _try_chr(e):
            try:
                return chr(e)
            except:
                return ''
        df.loc[:, cols] = df.loc[:, cols].applymap(_try_chr)
        print(df)
        return df

    def cast_df_intfloatcharstr_cols(self, df, int_cols=None, float_cols=None, char_cols=None, str_cols=None):
        if isinstance(char_cols, np.ndarray):
            df = self.cast_df_int2chr(df, char_cols)
        if isinstance(int_cols, np.ndarray):
            df = self.cast_df_cols(df, int_cols, np.int64)
        if isinstance(float_cols, np.ndarray):
            df = self.cast_df_cols(df, float_cols, np.float64)
        if isinstance(str_cols, np.ndarray):
            df = self.cast_df_cols(df, str_cols, str)
        return df

    def open_init(self):
        """
        Pre-Initialize work
        - dispatch COM object with self._trpath

        No Returns:
        """
        self.comobj = CpComUtil.get_comobj(self._trpath)

    def finish_init(self):
        """
        Post-Initialize work
        - logging initializing completion messages, casting type information

        No Returns:
        """
        log.info(f"'{self.__class__.__name__}' instance  initialized !")
        try:
            log.info("  └  {} fields -  int ({})   float({})  char({})  str({})".format(
                len(self.req_fields), len(self.keys_int), len(self.keys_float), len(self.keys_char), len(self.keys_str)))
        except:
            pass


# TODO: Refactor
class CpCodeMgr(CpQueryTr):
    _trpath = 'CpUtil.CpCodeMgr'
    # 종목코드 관리하는 클래스
    def __init__(self):
        self.open_init()
        self.finish_init()

    def get_all_code_list(self):
        kospi = self.get_code_list(1)
        kosdaq = self.get_code_list(2)
        return kospi + kosdaq

    # 마켓에 해당하는 종목코드 리스트 반환하는 메소드
    def get_code_list(self, market):
        """
        :param market: 1:코스피, 2:코스닥, ...
        :return: market에 해당하는 코드 list
        """
        code_list = self.comobj.GetStockListByMarket(market)
        # time.sleep(0.25)
        return code_list

    # 부구분코드를 반환하는 메소드
    def get_section_code(self, code):
        section_code = self.comobj.GetStockSectionKind(code)
        return section_code

    # 종목 코드를 받아 종목명을 반환하는 메소드
    def get_code_name(self, code):
        code_name = self.comobj.CodeToName(code)
        return code_name


    @sl4p_time()
    def request_query(self, api_tx_msg: dict):
        query = api_tx_msg['query']
        query_params = api_tx_msg['query_params']
        log.info(f"request_query called - query '{query}'")

        res = None
        if query == 'get_code_list':
            if query_params == 'ALL':
                code_li = list(self.get_all_code_list())
            elif query_params == 'KOSPI':
                code_li = list(self.get_code_list(1))
            elif query_params == 'KOSDAQ':
                code_li = list(self.get_code_list(2))
            else:
                code_li = list()
            res = code_li

        return res


class CpMarketEye(CpQueryTr):
    _trpath = 'CpSysDib.MarketEye'

    def __init__(self):
        self.open_init()
        self.MAX_REQ_LEN = 200

        ch = 'chr'
        _i = 'int64'
        _fl = 'float64'
        s = 'str'

        # https://money2.creontrade.com/e5/mboard/ptype_basic/HTS_Plus_Helper/DW_Basic_Read_Page.aspx?boardseq=284&seq=131&page=1&searchString=MarketEYe&p=8841&v=8643&m=9505
        self.req_fields_types = np.array([
            [0, 'item', s], [2, 'sign', ch], [3, 'dprc_l1d', _i], [4, 'price', _i],
            [5, 'open', _i], [6, 'high', _i], [7, 'low', _i], [8, 'ask1', _i],
            # shcode, 대비부호, 전일대비, 현재가    //    open, high, low, ask1

            [9, 'bid1', _i], [10, 'vol', _i], [11, 'trd_val', _i], [12, 'exflag', ch],
            [13, 'ask_totvol', _i], [14, 'bid_totvol', _i], [15, 'ask1_vol', _i], [16, 'bid1_vol', _i],
            # bid1, vol, trd_val, 장구분    //    ask_totvol, bid_totvol, ask1_vol, bid1_vol

            [17, 'itemname', s], [20, 'listed_sh', _i], [23, 'close_l1d', _i], [24, 'vol_power', _fl],
            [28, 'predprice', _i], [29, 'preddprc', _i], [30, 'predsign', ch], [31, 'predvol', _i],
            # itemname, listed_sh, close_l1d, vol_power   //   예상체결가, 예상가대비, 예상가대비부호, 예상체결수량

            [33, 'uplmtprc', _i], [34, 'dnlmtprc', _i], [38, 'out_price', _i], [42, 'out_ask1', _i],
            [43, 'out_bid1', _i], [48, 'out_ask1_vol', _i], [49, 'out_bid1_vol', _i], [53, 'out_exflag', ch],
            # 상한가, 하한가, 시간외 out_price, out_ask1    //    out_bid1, out_ask1_vol, out_bid1_vol, out_exflag

            [54, 'out_predprice', _i], [57, 'out_predvol', _i], [76, 'reserve_ratio', _fl], [109, 'reserve_ratio_q', _fl],
            # out_predprice, out_predvol, 유보율, 분기유보율
        ])

        self.req_fields = self.req_fields_types[:,0]
        self.req_keys = self.req_fields_types[:,1]

        self.keys_char = self.req_fields_types[self.req_fields_types[:,2] == ch][:,1]
        self.keys_int = self.req_fields_types[self.req_fields_types[:,2] == _i][:,1]
        self.keys_float = self.req_fields_types[self.req_fields_types[:,2] == _fl][:,1]
        self.keys_str = self.req_fields_types[self.req_fields_types[:,2] == s][:,1]

        print(self.req_fields)
        print(self.req_keys)
        print(self.keys_char)
        print(self.keys_int)

        self.cast_cols_args = [self.keys_int, self.keys_float, self.keys_char, self.keys_str]

        self.finish_init()


    @sl4p_time()
    def request_query(self, api_tx_msg: dict):
        itemlist = api_tx_msg['itemlist']
        log.info(f"request_query called - ({len(itemlist)}) {itemlist[:5]} ..")

        data_li = list()
        ci = 0
        while ci <= len(itemlist):
            data_li.extend(self._request(itemlist[ci:ci+self.MAX_REQ_LEN]))
            ci += self.MAX_REQ_LEN

        # cast and return
        res_df: pd.DataFrame = pd.DataFrame(data_li)
        res_df = self.cast_df_intfloatcharstr_cols(res_df, *self.cast_cols_args)
        return res_df.to_dict('records')


    def _request(self, shcode_li):
        self.comobj.SetInputValue(0, self.req_fields)
        self.comobj.SetInputValue(1, shcode_li)

        CpSession.tick_query()
        self.comobj.BlockRequest()

        data_li = list()
        for i in range(len(shcode_li)):
            d = odict()
            for ki, kv in enumerate(self.req_keys):
                d[kv] = self.comobj.GetDataValue(ki, i)
            data_li.append(d)

        return data_li



if __name__ == '__main__':
    CpSession.tick_query()
    CpSession.tick_order()

    cpCodeMgr = CpCodeMgr.get_instance()
    all_codes = cpCodeMgr.request_query({'query': 'get_code_list', 'query_params': 'ALL'})
    #all_codes = cpCodeMgr.get_all_code_list()


    # count 초기화를 위한 1 query
    cpMarketEye = CpMarketEye.get_instance()
    test0 = pd.DataFrame(cpMarketEye.request_query({'itemlist': ['A005930']})).iloc[:2]
    print(test0.iloc[0], test0.dtypes.to_dict())
    CpSession.tick("QUERY", force_wait=True)
    # remain_cnt, wait_ms = CpSession.tick_query()
    # time.sleep(1 + wait_ms//1000)


    cpMarketEye = CpMarketEye.get_instance()
    cpMarketEye2 = CpMarketEye.get_instance()


    for _ in range(100):
        st_dt = dt.now()
        res_df = pd.DataFrame(cpMarketEye.request_query({'itemlist': all_codes}))
        print(res_df.shape)
        end_dt = dt.now()
        elapsed = (end_dt - st_dt).total_seconds()
        # log.info(f"Elapsed {elapsed:.3f} secs")     # 3.848 s,  3.768 s  3.903    4.361    3.672    3.958

        #res_df.to_csv(f'market_eye_res_df__{end_dt:%Y%m%d_%H%M%S}.csv', encoding='cp949')

    print(cpMarketEye == cpMarketEye2)

    remain_cnt, wait_ms = CpSession.tick_query()
    import time
    time.sleep(1 + wait_ms//1000)