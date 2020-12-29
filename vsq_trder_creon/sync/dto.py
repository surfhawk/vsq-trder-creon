# -*- coding: utf-8 -*-
from enum import Enum
from typing import List, Dict
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

class BRK_MSG_TYPE(Enum):
    ERROR = -404
    UNINIT = -1
    DENIED = 0
    ACCEPTED = 1

    CONNECT = 10
    CLOSE = -10
    CLOSED = -11

    REQUEST = 500
    SUBSCRIBE = 550

    RESPONSE = 200
    PUSH = 201

    HEARTBEAT = 45454

class BRK_SEC_APIS(Enum):
    EBEST_XING = '이베스트증권_XING'
    DAISHIN_CP = '대신증권_CREON_PLUS'

@dataclass_json
@dataclass
class BrokerMessage:
    work_uid: str
    src: List = field(default_factory=list)
    dest: List = field(default_factory=list)
    type: BRK_MSG_TYPE = field(default=BRK_MSG_TYPE.UNINIT)
    param: dict = field(default_factory=dict)
    data: dict = field(default_factory=dict)
    desc: str = ''
    apip: BRK_SEC_APIS = field(default=BRK_SEC_APIS.EBEST_XING)

#TODO: remove example main code
if __name__ == '__main__':
    msg = BrokerMessage('uid8838')
    print(msg)


    msg = BrokerMessage('a03042', (37781, 'sdf'), (37777, 'zzz'), BRK_MSG_TYPE.CONNECT, {}, {}, 'desc')
    msg_json = msg.to_json()
    print(msg.to_json())

    deserialized_obj = BrokerMessage.from_json(msg_json)
    print(deserialized_obj)