from enum import Enum
from json import dumps

import json
from hyper import HTTP20Connection
from hyper.tls import init_context

from apns2.errors import exception_class_for_reason


class NotificationPriority(Enum):
    Immediate = 10
    Delayed = 5


class APNsClient(object):
    def __init__(self, cert_file, use_sandbox=False, use_alternative_port=False):
        server = 'api.development.push.apple.com' if use_sandbox else 'api.push.apple.com'
        port = 2197 if use_alternative_port else 443
        ssl_context = init_context()
        ssl_context.load_cert_chain(cert_file)
        self.__connection = HTTP20Connection(server, port, ssl_context=ssl_context)

    def send_notification(self, token_hex, notification, priority=NotificationPriority.Immediate, topic=None):
        json_payload = dumps(notification.dict(), ensure_ascii=False, separators=(',', ':')).encode('utf-8')

        headers = {
            'apns-priority': priority.value
        }
        if topic:
            headers['apns-topic'] = topic

        url = '/3/device/{}'.format(token_hex)
        stream_id = self.__connection.request('POST', url, json_payload, headers)
        resp = self.__connection.get_response(stream_id)
        if resp.status != 200:
            raw_data = resp.read().decode('utf-8')
            data = json.loads(raw_data)
            raise exception_class_for_reason(data['reason'])
