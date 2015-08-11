#coding: cp1251

import logging
import smsc_api

FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

HANDLERS = {}
ERRORS = \
{
    1: 'User data type error',
    2: 'Phone number: missed',
    3: 'Phone number: bad format',
    4: 'Message text: missed',
    5: 'Message text: bad format',
    6: 'External API error',
}

def get_handler(hname):
    handler = HANDLERS.get(hname, HandlerError)
    if handler is HandlerError:
        raise HandlerError('not found', hname)
    if isinstance(handler, Handler):
        return handler
    return handler()

class HandlerError(Exception):
    pass

class Handler:
    def sendraw(self, data):
        raise NotImplemented()

    def send(self, data):
        rc = self.sendraw(data)
        if rc['status'] == 'ok':
            logger.info('%s: %s bytes',
                rc['phone'], len(data['text'].encode('utf-8')))
        else:
            logger.info('%s', rc)
        return rc

    name = NotImplemented
    single = NotImplemented

    def check(self, data):
        if not isinstance(data, dict):
            return {'status': 'error', 'phone': None,
                'error_code': 1, 'error_msg': ERRORS[0]}
        if 'phone' not in data:
            return {'status': 'error', 'phone': None,
                'error_code': 2, 'error_msg': ERRORS[1]}
        if not (isinstance(data['phone'], str) and data['phone']):
            return {'status': 'error', 'phone': None,
                'error_code': 3, 'error_msg': ERRORS[2]}
        if 'text' not in data:
            return {'status': 'error', 'phone': data['phone'],
                'error_code': 4, 'error_msg': ERRORS[2]}
        if not (isinstance(data['text'], str) and data['text']):
            return {'status': 'error', 'phone': data['phone'],
                'error_code': 5, 'error_msg': ERRORS[3]}

class smscru(Handler):
    name = 'post.smsc.ru'
    single = True

    def __init__(self):
        self.sms = smsc_api.SMSC()

    def sendraw(self, data):
        check = self.check(data)
        if check:
            return check
        rc = self.sms.send_sms(data['phone'], data['text'])
        # возвращает массив (<id>, <количество sms>, <стоимость>, <баланс>)
        # в случае успешной отправки
        # либо массив (<id>, -<код ошибки>) в случае ошибки
        if len(rc) == 4:
            return {'status': 'ok', 'phone': data['phone']}
        else:
            return {'status': 'error', 'phone': data['phone'],
                'error_code': 6, 'error_msg': repr(rc)}

HANDLERS[smscru.name] = smscru
