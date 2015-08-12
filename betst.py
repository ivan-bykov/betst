import logging
import urllib.parse
import urllib.request
import smsc_api

FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

CP = 'utf-8'
HANDLERS = {}
ERRORS = \
{
    1: 'User data type error',
    2: 'Phone number: missed',
    3: 'Phone number: bad value',
    4: 'Message text: missed',
    5: 'Message text: bad value',
    6: 'External API error',
}

def get_handler(hname):
    handler = HANDLERS.get(hname, HandlerError)
    if handler is HandlerError:
        raise HandlerError('not found', hname)
    if isinstance(handler, Handler):
        return handler
    res = handler()
    HANDLERS[hname] = res
    logger.debug('%s: init handler', hname)
    return res

class HandlerError(Exception):
    pass

class Handler:
    def sendraw(self, data):
        raise NotImplemented

    name = NotImplemented

    def send(self, data):
        rc = self.check(data)
        if rc:
            logger.info('%s: %s', self.name, rc)
        else:
            rc = self.sendraw(data)
            if rc['status'] == 'ok':
                logger.info('%s: %s bytes -> %s',
                    self.name, len(data['text'].encode(CP)), rc['phone'])
            else:
                logger.info('%s: %s', self.name, rc)
        return rc

    def check(self, data):
        if not isinstance(data, dict):
            return {'status': 'error', 'phone': None,
                'error_code': 1, 'error_msg': ERRORS[1]}
        if 'phone' not in data:
            return {'status': 'error', 'phone': None,
                'error_code': 2, 'error_msg': ERRORS[2]}
        if not (isinstance(data['phone'], str) and data['phone']):
            return {'status': 'error', 'phone': None,
                'error_code': 3, 'error_msg': ERRORS[3]}
        if 'text' not in data:
            return {'status': 'error', 'phone': data['phone'],
                'error_code': 4, 'error_msg': ERRORS[4]}
        if not (isinstance(data['text'], str) and data['text']):
            return {'status': 'error', 'phone': data['phone'],
                'error_code': 5, 'error_msg': ERRORS[5]}

class smscru(Handler):
    name = 'post.smsc.ru'

    def __init__(self):
        self.sms = smsc_api.SMSC()

    def sendraw(self, data):
        rc = self.sms.send_sms(data['phone'], data['text'])
        # (<id>, <sms count>, <cost>, <balance>) - Ok
        # (<id>, -<error code>) - Error
        if len(rc) == 4:
            return {'status': 'ok', 'phone': data['phone']}
        else:
            return {'status': 'error', 'phone': data['phone'],
                'error_code': 6, 'error_msg': repr(rc)}

HANDLERS[smscru.name] = smscru

class smstrafficru(Handler):
    name = 'post.smstraffic.ru'
    page = 'http://www.smstraffic.ru/send.cgi'

    def sendraw(self, data):
        post = {'number': data['phone'], 'message': data['text']}
        try:
            post = urllib.parse.urlencode(post)
            post = post.encode(CP)
            request = urllib.request.Request(self.page)
            request.add_header('Content-Type',
                'application/x-www-form-urlencoded;charset=%s' % CP)
            f = urllib.request.urlopen(request, post)
            f.read()
        except BaseException as exc:
            return {'status': 'error', 'phone': data['phone'],
                'error_code': 6, 'error_msg': repr(exc)}
        else:
            return {'status': 'ok', 'phone': data['phone']}

HANDLERS[smstrafficru.name] = smstrafficru
