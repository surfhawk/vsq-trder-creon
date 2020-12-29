from abc import abstractmethod
from pydis_broker.dto import BrokerMessage


class MsgAdaptor:
    @abstractmethod
    def transcript(self, workMsg: BrokerMessage):
        raise NotImplementedError

    @abstractmethod
    def reverse_transcript(self, workMsg: BrokerMessage, api_rx_msg):
        raise NotImplementedError