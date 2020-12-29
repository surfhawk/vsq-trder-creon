from vsq_trder_creon.trder_base.adaptor import MsgAdaptor
from vsq_trder_creon.sync.dto import BrokerMessage, BRK_MSG_TYPE, BRK_SEC_APIS
from collections import OrderedDict as odict
import pandas as pd
from sl4p import *
log = sl4p.getLogger(__file__)


class CreonPlusMsgAdaptor(MsgAdaptor):
    def __init__(self):
        pass

    def transcript(self, workMsg: BrokerMessage):
        tr_id = workMsg.param['tr_id']
        api_tx_msg = odict()
        api_tx_msg['tr_id'] = tr_id
        api_tx_msg['work_msg_json'] = workMsg.to_json()

        if tr_id == 'list_market_codes':
            api_tx_msg['trcode'] = 'CpCodeMgr'
            api_tx_msg['query'] = 'get_code_list'
            api_tx_msg['query_params'] = workMsg.param['market']

        elif tr_id == 'price_itemlist':
            api_tx_msg['trcode'] = 'CpMarketEye'
            api_tx_msg['itemlist'] = workMsg.param['itemlist']

        else:
            log.error(f"tr_id '{tr_id}' can not be transcripted!  (not supported)")
            raise KeyError

        return api_tx_msg


    def reverse_transcript_data(self, api_rx_msg):
        tr_id = api_rx_msg.get('tr_id')
        rx_data = odict()
        rx_data['tr_id'] = tr_id

        if tr_id == 'list_market_codes':
            rx_data['list'] = api_rx_msg['resObject']

        elif tr_id == 'price_itemlist':
            rx_data['list'] = api_rx_msg['resObject']
            pass

        else:
            log.error(f"tr_id '{tr_id}' can not be reverse-transcripted!  (not supported)")
            raise KeyError

        return rx_data


    def reverse_transcript(self, workMsg: BrokerMessage, api_rx_msg=None, rx_data=None):
        if rx_data is None:
            rx_data = self.reverse_transcript_data(api_rx_msg)

        RES_BRK_MSG_TYPE: BRK_MSG_TYPE = BRK_MSG_TYPE.UNINIT
        tr_id = workMsg.param['tr_id']

        if tr_id == 'list_market_codes':
            RES_BRK_MSG_TYPE = BRK_MSG_TYPE.RESPONSE

        elif tr_id == 'price_itemlist':
            RES_BRK_MSG_TYPE = BRK_MSG_TYPE.RESPONSE

        else:
            log.error(f"tr_id '{tr_id}' can not be reverse-transcripted!  (not supported)")
            raise KeyError

        resBrkMsg = BrokerMessage(workMsg.work_uid, workMsg.dest, workMsg.src, RES_BRK_MSG_TYPE,
                                  workMsg.param, rx_data, apip=BRK_SEC_APIS.DAISHIN_CP)
        return resBrkMsg
